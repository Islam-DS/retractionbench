"""Integration tests for the PE1 harness, entirely on a synthetic fixture -- never touches
the real 325,167-document corpus or the real 15-item benchmark. Mirrors
`tests/test_retrieval_ceiling.py`'s fake-embedding style so a tiny, real (not mocked) FAISS
index backs the test.
"""

from datetime import date
from pathlib import Path

import numpy as np
import pytest

from retraction_bench.corpus.embed_index import build_index, load_index
from retraction_bench.rag.recency_rerank import build_candidate_documents
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
    Provenance,
    SourceAuthority,
)

pytest.importorskip("faiss")

from retraction_bench.rag.pe1_harness import _target_pmids_for_item, run_pe1  # noqa: E402

DIM = 8


def _fake_embed_fn(texts: list[str]) -> np.ndarray:
    vectors = np.zeros((len(texts), DIM), dtype="float32")
    for i, text in enumerate(texts):
        for j, ch in enumerate(text[:DIM]):
            vectors[i, j % DIM] += ord(ch)
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return vectors / norms


def _item(item_id: str, question: str, evidence_identifier: str) -> BenchmarkItem:
    return BenchmarkItem(
        item_id=item_id,
        question=question,
        domain="(HSC) Medicine - Pharmacology",
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
                identifier=evidence_identifier,
                evidence_type=EvidenceType.META_ANALYSIS,
                publication_date=date(2023, 1, 1),
                source_authority=SourceAuthority.META_ANALYSIS,
                independence_verified=True,
            )
        ],
        provenance=Provenance.VERIFIED,
    )


@pytest.fixture()
def fixture_index(tmp_path: Path):
    rows = [
        {"pmid": "bg1", "title": "unrelated background doc one", "abstract": "", "domain": "d", "corpus_role": "background"},
        {"pmid": "bg2", "title": "unrelated background doc two", "abstract": "", "domain": "d", "corpus_role": "background"},
        {"pmid": "evidence-pmid", "title": "the question text", "abstract": "", "domain": "d", "corpus_role": "superseding_evidence", "linked_source_registry_id": "10.1/ev"},
        {"pmid": "trap-pmid", "title": "the question text", "abstract": "", "domain": "d", "corpus_role": "benchmark_source", "linked_source_registry_id": "rw-1"},
    ]
    corpus_path = tmp_path / "corpus.jsonl"
    with corpus_path.open("w", encoding="utf-8") as f:
        import json

        for r in rows:
            f.write(json.dumps(r) + "\n")

    index_dir = tmp_path / "index"
    build_index(corpus_path, index_dir, embed_fn=_fake_embed_fn)
    return load_index(index_dir)


# --- evaluation-only identification is separate from reranker input (Phase 9 test #6) ---


def test_target_pmids_for_item_reads_corpus_role_for_evaluation_only(fixture_index) -> None:
    _, manifest = fixture_index
    item = _item("RB-TEST", "the question text", "10.1/ev")
    targets = _target_pmids_for_item(item, manifest)
    assert targets == {"evidence-pmid"}


def test_reranker_input_never_carries_target_identity(fixture_index) -> None:
    """Even though `_target_pmids_for_item` can identify the replacement document, the
    CandidateDocument objects actually handed to the reranker carry no field that could
    reveal this -- checked structurally, not just by convention."""
    index, manifest = fixture_index
    hits = [
        {"pmid": "evidence-pmid", "corpus_role": "superseding_evidence", "linked_source_registry_id": "10.1/ev", "score": 0.9},
        {"pmid": "bg1", "corpus_role": "background", "linked_source_registry_id": None, "score": 0.5},
    ]
    candidates = build_candidate_documents(hits, pub_year_lookup={"evidence-pmid": 2023, "bg1": 2010})
    for c in candidates:
        assert not hasattr(c, "corpus_role")
        assert not hasattr(c, "linked_source_registry_id")


# --- full harness, item-by-item comparison (Phase 9 test #7) ---


def test_run_pe1_produces_one_row_per_item_with_resolved_evidence(fixture_index) -> None:
    index, manifest = fixture_index
    items = [_item("RB-TEST", "the question text", "10.1/ev")]
    pub_year_lookup = {"evidence-pmid": 2023, "trap-pmid": 2015, "bg1": 2010, "bg2": 2011}

    rows = run_pe1(items, index, manifest, pub_year_lookup, _fake_embed_fn, pool_k=4)

    assert len(rows) == 1
    row = rows[0]
    assert row["item_id"] == "RB-TEST"
    assert row["baseline_rank"] is not None
    assert row["reranked_rank"] is not None
    # Structural invariant from rag/recency_rerank.py: a pure reorder of a fixed pool can
    # never change hit@pool_size.
    assert row["baseline_hit@10"] == row["reranked_hit@10"]


def test_run_pe1_skips_items_with_no_resolved_evidence(fixture_index) -> None:
    index, manifest = fixture_index
    items = [_item("RB-UNRESOLVED", "the question text", "10.1/does-not-exist-in-corpus")]
    rows = run_pe1(items, index, manifest, pub_year_lookup={}, embed_fn=_fake_embed_fn, pool_k=4)
    assert rows == []


def test_hit_at_pool_size_is_structurally_invariant_under_pure_reorder(fixture_index) -> None:
    """Direct test of the property documented in `rag/recency_rerank.py`'s module docstring:
    reordering a fixed pool cannot change whether the target is IN the pool at all."""
    index, manifest = fixture_index
    items = [_item("RB-TEST", "the question text", "10.1/ev")]
    # Deliberately adversarial pub_year assignment, as different as possible from baseline order.
    pub_year_lookup = {"evidence-pmid": 1900, "trap-pmid": 2024, "bg1": 2023, "bg2": 2022}
    rows = run_pe1(items, index, manifest, pub_year_lookup, _fake_embed_fn, pool_k=4)
    row = rows[0]
    for k in (1, 3, 5, 10):
        if k >= 4:  # pool_k=4 here -- hit@k for k>=pool size is the structurally-invariant case
            assert row[f"baseline_hit@{k}"] == row[f"reranked_hit@{k}"]
