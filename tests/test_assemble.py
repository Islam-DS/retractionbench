"""Tests for corpus assembly: exactly-once benchmark documents in the background pool."""

import json
from datetime import date
from pathlib import Path

import pytest

from retraction_bench.corpus.assemble import assemble_corpus, resolve_doi_to_pmid
from retraction_bench.schemas import (
    BenchmarkItem,
    Claim,
    ClaimPolarity,
    ClaimType,
    Evidence,
    EvidenceDirection,
    EvidenceTierMatch,
    EvidenceType,
    ItemType,
    NoticeSpecificity,
    Provenance,
    SourceAuthority,
    SourceEvidenceLevel,
    SupersededSource,
    SupersessionType,
)


class _FakeResponse:
    def __init__(self, json_data: dict) -> None:
        self._json = json_data

    def raise_for_status(self) -> None:
        pass

    def json(self) -> dict:
        return self._json


class _FakeClient:
    def __init__(self, doi_to_pmid: dict[str, str]) -> None:
        self._doi_to_pmid = doi_to_pmid
        self.calls: list[dict] = []

    def get(self, url: str, params: dict) -> _FakeResponse:
        self.calls.append(params)
        term = params["term"]
        doi = term.split("[AID]")[0]
        pmid = self._doi_to_pmid.get(doi)
        return _FakeResponse({"esearchresult": {"idlist": [pmid] if pmid else []}})

    def close(self) -> None:
        pass


@pytest.fixture(autouse=True)
def _ncbi_email(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("NCBI_EMAIL", "test@example.com")
    monkeypatch.delenv("NCBI_API_KEY", raising=False)


def _source() -> SupersededSource:
    return SupersededSource(
        source_registry_id="rw-1",
        external_ids={"pmid": "111"},
        title="A retracted paper",
        venue="Journal",
        original_date=date(2017, 6, 1),
        evidence_level=SourceEvidenceLevel.SYNTHESIS,
        notice_specificity=NoticeSpecificity.CATEGORICAL,
        notice_text_verified=True,
        notice_text="This article is retracted.",
        supersession_type=SupersessionType.RETRACTION,
        supersession_date=date(2018, 1, 1),
        verification_method="pubmed_retraction_tag",
        verification_confirmed=True,
        summary="Abstract of the retracted paper.",
    )


def _item() -> BenchmarkItem:
    return BenchmarkItem(
        item_id="RB-0001",
        question="A question?",
        domain="TestDomain",
        claim_type=ClaimType.CLINICAL_INTERVENTION,
        item_type=ItemType.SUPERSEDED_WITH_CURRENT_ANSWER,
        claim_polarity=ClaimPolarity.POSITIVE,
        replacement_exists=False,
        evidence_direction=EvidenceDirection.CONCORDANT,
        evidence_tier_match=EvidenceTierMatch.SAME_TIER,
        trap_claim=Claim(text="trap"),
        gold_claim=Claim(text="gold"),
        supporting_sources=["rw-1"],
        post_supersession_evidence=[
            Evidence(
                identifier="10.1234/example",
                evidence_type=EvidenceType.META_ANALYSIS,
                publication_date=date(2022, 1, 1),
                source_authority=SourceAuthority.META_ANALYSIS,
                note="Evidence note",
                independence_verified=True,
            )
        ],
        provenance=Provenance.DRAFT,
    )


def test_resolve_doi_to_pmid_returns_single_match() -> None:
    client = _FakeClient({"10.1234/example": "222"})
    assert resolve_doi_to_pmid("10.1234/example", client=client) == "222"


def test_resolve_doi_to_pmid_returns_none_for_no_match() -> None:
    client = _FakeClient({})
    assert resolve_doi_to_pmid("10.1234/missing", client=client) is None


def test_assemble_corpus_dedupes_benchmark_source_from_background(tmp_path: Path) -> None:
    background_path = tmp_path / "background.jsonl"
    background_path.write_text(
        json.dumps({"pmid": "111", "title": "dup", "abstract": "dup", "journal": "J", "pub_year": 2017})
        + "\n"
        + json.dumps({"pmid": "999", "title": "other", "abstract": "other", "journal": "J", "pub_year": 2020})
        + "\n",
        encoding="utf-8",
    )
    output_path = tmp_path / "corpus.jsonl"
    client = _FakeClient({"10.1234/example": "222"})

    stats = assemble_corpus(
        background_paths={"TestDomain": background_path},
        sources=[_source()],
        items=[_item()],
        output_path=output_path,
        client=client,
    )

    assert stats.background_deduped == 1  # pmid 111 removed from background, re-added as benchmark_source
    assert stats.background_written == 1  # pmid 999 kept
    assert stats.benchmark_source == 1
    assert stats.supersession_notice == 1
    assert stats.superseding_evidence == 1
    assert stats.superseding_evidence_unresolved == 0

    rows = [json.loads(line) for line in output_path.read_text(encoding="utf-8").strip().split("\n")]
    pmids = [r["pmid"] for r in rows]
    assert pmids.count("111") == 1  # exactly once, not duplicated between background and benchmark
    roles = {r["pmid"]: r["corpus_role"] for r in rows}
    assert roles["111"] == "benchmark_source"
    assert roles["999"] == "background"
    assert roles["222"] == "superseding_evidence"
    assert any(r["corpus_role"] == "supersession_notice" for r in rows)


def test_assemble_corpus_dedupes_background_pmid_repeated_within_one_domain(tmp_path: Path) -> None:
    """ADR-133: mesh_fetch.py's resumability bug duplicated rows within a single domain's own
    raw output (~75,000 rows in the real corpus). assemble_corpus must not pass those through.
    """
    background_path = tmp_path / "background.jsonl"
    background_path.write_text(
        json.dumps({"pmid": "999", "title": "other", "abstract": "other", "journal": "J", "pub_year": 2020})
        + "\n"
        + json.dumps({"pmid": "999", "title": "other", "abstract": "other", "journal": "J", "pub_year": 2020})
        + "\n",
        encoding="utf-8",
    )
    output_path = tmp_path / "corpus.jsonl"
    client = _FakeClient({})

    stats = assemble_corpus(
        background_paths={"TestDomain": background_path},
        sources=[],
        items=[],
        output_path=output_path,
        client=client,
    )

    assert stats.background_written == 1
    assert stats.background_deduped == 1
    rows = [json.loads(line) for line in output_path.read_text(encoding="utf-8").strip().split("\n")]
    assert [r["pmid"] for r in rows] == ["999"]


def test_assemble_corpus_dedupes_background_pmid_shared_across_two_domains(tmp_path: Path) -> None:
    """A paper can legitimately match two domains' MeSH queries -- it must still land in the
    corpus, and the index, exactly once.
    """
    domain_a_path = tmp_path / "a.jsonl"
    domain_b_path = tmp_path / "b.jsonl"
    row = {"pmid": "999", "title": "other", "abstract": "other", "journal": "J", "pub_year": 2020}
    domain_a_path.write_text(json.dumps(row) + "\n", encoding="utf-8")
    domain_b_path.write_text(json.dumps(row) + "\n", encoding="utf-8")
    output_path = tmp_path / "corpus.jsonl"
    client = _FakeClient({})

    stats = assemble_corpus(
        background_paths={"DomainA": domain_a_path, "DomainB": domain_b_path},
        sources=[],
        items=[],
        output_path=output_path,
        client=client,
    )

    assert stats.background_written == 1
    assert stats.background_deduped == 1
    rows = [json.loads(line) for line in output_path.read_text(encoding="utf-8").strip().split("\n")]
    assert [r["pmid"] for r in rows] == ["999"]


def test_assemble_corpus_writes_bare_notice_document_with_empty_text(tmp_path: Path) -> None:
    """notice_text_verified=True with notice_text=None is a real, deliberate annotation state
    (schemas.py's own SupersededSource invariant) -- confirmed the notice exists and is
    substantively bare, not that verification failed. It must still produce a document.
    """
    source = _source()
    source.notice_text_verified = True
    source.notice_text = None

    output_path = tmp_path / "corpus.jsonl"
    client = _FakeClient({"10.1234/example": "222"})
    stats = assemble_corpus(
        background_paths={},
        sources=[source],
        items=[_item()],
        output_path=output_path,
        client=client,
    )

    assert stats.supersession_notice == 1
    rows = [json.loads(line) for line in output_path.read_text(encoding="utf-8").strip().split("\n")]
    notice_row = next(r for r in rows if r["corpus_role"] == "supersession_notice")
    assert notice_row["abstract"] == ""
    assert notice_row["pmid"] == "rw-1-notice"


def test_assemble_corpus_includes_unverified_notice_that_still_has_text(tmp_path: Path) -> None:
    """ADR-136: notice_text_verified=False with real notice_text (secondhand, never confirmed
    against a primary source, ADR-042) is still retrievable -- it must produce a document.
    Verification status governs what the gold claim can assert, not what a retriever can find.
    """
    source = _source()
    source.notice_text_verified = False
    source.notice_text = "Reported secondhand: this article has been retracted."
    source.notice_specificity = NoticeSpecificity.UNVERIFIABLE

    output_path = tmp_path / "corpus.jsonl"
    client = _FakeClient({"10.1234/example": "222"})
    stats = assemble_corpus(
        background_paths={},
        sources=[source],
        items=[_item()],
        output_path=output_path,
        client=client,
    )

    assert stats.supersession_notice == 1
    rows = [json.loads(line) for line in output_path.read_text(encoding="utf-8").strip().split("\n")]
    notice_row = next(r for r in rows if r["corpus_role"] == "supersession_notice")
    assert notice_row["abstract"] == "Reported secondhand: this article has been retracted."


def test_assemble_corpus_omits_notice_document_only_when_no_text_and_unverified(tmp_path: Path) -> None:
    """The genuine no-document case: no text at all, and verification never confirmed any --
    nothing exists for a retriever to find (RB-0005/RB-0026/RB-0027/RB-0028's actual shape)."""
    source = _source()
    source.notice_text_verified = False
    source.notice_text = None
    source.notice_specificity = NoticeSpecificity.UNVERIFIABLE

    output_path = tmp_path / "corpus.jsonl"
    client = _FakeClient({"10.1234/example": "222"})
    stats = assemble_corpus(
        background_paths={},
        sources=[source],
        items=[_item()],
        output_path=output_path,
        client=client,
    )

    assert stats.supersession_notice == 0
    rows = [json.loads(line) for line in output_path.read_text(encoding="utf-8").strip().split("\n")]
    assert not any(r["corpus_role"] == "supersession_notice" for r in rows)


def test_assemble_corpus_counts_unresolved_evidence_without_dropping_silently(tmp_path: Path) -> None:
    output_path = tmp_path / "corpus.jsonl"
    client = _FakeClient({})  # nothing resolves
    stats = assemble_corpus(
        background_paths={},
        sources=[_source()],
        items=[_item()],
        output_path=output_path,
        client=client,
    )
    assert stats.superseding_evidence_unresolved == 1
    assert stats.superseding_evidence == 0
