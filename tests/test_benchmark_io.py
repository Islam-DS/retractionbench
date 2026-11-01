"""Tests for validated JSONL persistence of the benchmark deliverable."""

from datetime import date
from pathlib import Path

from retraction_bench.curate.benchmark_io import (
    append_deferred,
    append_item,
    append_rejected,
    append_source,
    load_deferred,
    load_items,
    load_rejected,
    load_sources,
)
from retraction_bench.schemas import (
    BenchmarkItem,
    Claim,
    ClaimPolarity,
    ClaimType,
    DeferredCandidate,
    EvidenceDirection,
    EvidenceTierMatch,
    ItemType,
    NoticeSpecificity,
    Provenance,
    RejectedCandidate,
    RejectionReason,
    SourceEvidenceLevel,
    SupersededSource,
    SupersessionType,
)


def _source() -> SupersededSource:
    return SupersededSource(
        source_registry_id="rw-17019",
        external_ids={"pmid": "28591045"},
        title="Example retracted meta-analysis",
        venue="Medicine",
        original_date=date(2017, 6, 1),
        evidence_level=SourceEvidenceLevel.SYNTHESIS,
        notice_specificity=NoticeSpecificity.CATEGORICAL,
        notice_text_verified=True,
        supersession_type=SupersessionType.RETRACTION,
        supersession_date=date(2018, 1, 21),
        supersession_reasons=["Error in Analyses"],
        verification_method="pubmed_retraction_tag",
        verification_confirmed=True,
        summary="Example abstract.",
    )


def _item() -> BenchmarkItem:
    return BenchmarkItem(
        item_id="RB-0001",
        question="How much does tranexamic acid reduce blood loss during open myomectomy?",
        domain="(HSC) Medicine - Pharmacology",
        claim_type=ClaimType.CLINICAL_INTERVENTION,
        item_type=ItemType.SUPERSEDED_WITH_CURRENT_ANSWER,
        claim_polarity=ClaimPolarity.POSITIVE,
        replacement_exists=False,
        evidence_direction=EvidenceDirection.CONCORDANT,
        evidence_tier_match=EvidenceTierMatch.SAME_TIER,
        trap_claim=Claim(text="Example trap claim.", valid_from=date(2017, 6, 1), valid_until=date(2018, 1, 21)),
        gold_claim=Claim(text="Example gold claim.", valid_from=date(2022, 9, 1), valid_until=None),
        supporting_sources=["rw-17019"],
        provenance=Provenance.DRAFT,
    )


def test_append_and_load_source_round_trips(tmp_path: Path) -> None:
    path = tmp_path / "sources.jsonl"
    append_source(_source(), path=path)
    loaded = load_sources(path=path)
    assert len(loaded) == 1
    assert loaded[0].source_registry_id == "rw-17019"


def test_append_and_load_item_round_trips(tmp_path: Path) -> None:
    path = tmp_path / "items.jsonl"
    append_item(_item(), path=path)
    loaded = load_items(path=path)
    assert len(loaded) == 1
    assert loaded[0].item_id == "RB-0001"


def test_append_is_additive_not_overwriting(tmp_path: Path) -> None:
    path = tmp_path / "items.jsonl"
    append_item(_item(), path=path)
    second = _item()
    second.item_id = "RB-0002"
    append_item(second, path=path)
    loaded = load_items(path=path)
    assert [i.item_id for i in loaded] == ["RB-0001", "RB-0002"]


def test_load_missing_file_returns_empty_list(tmp_path: Path) -> None:
    assert load_items(path=tmp_path / "nonexistent.jsonl") == []
    assert load_sources(path=tmp_path / "nonexistent.jsonl") == []
    assert load_rejected(path=tmp_path / "nonexistent.jsonl") == []
    assert load_deferred(path=tmp_path / "nonexistent.jsonl") == []


def test_append_and_load_rejected_round_trips(tmp_path: Path) -> None:
    path = tmp_path / "rejected.jsonl"
    candidate = RejectedCandidate(
        source_registry_id="rw-5833",
        reason=RejectionReason.OTHER,
        notes=(
            "Claim-type screen false positive: EGF-stimulated cervical cancer cell-line "
            "study, mislabeled clinical_observational. Preclinical, not eligible."
        ),
        rejection_date=date(2026, 8, 6),
    )
    append_rejected(candidate, path=path)
    loaded = load_rejected(path=path)
    assert len(loaded) == 1
    assert loaded[0].source_registry_id == "rw-5833"


def test_append_and_load_deferred_round_trips(tmp_path: Path) -> None:
    path = tmp_path / "deferred.jsonl"
    candidate = DeferredCandidate(
        source_registry_id="rw-5684",
        notes="Blocked on paywalled guideline text since first opened; not worth a third pass "
        "with seven weeks left. Time budget, not candidate quality (ADR-078).",
        deferred_date=date(2026, 8, 10),
    )
    append_deferred(candidate, path=path)
    loaded = load_deferred(path=path)
    assert len(loaded) == 1
    assert loaded[0].source_registry_id == "rw-5684"
