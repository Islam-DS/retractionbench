"""Tests for retrieval-ceiling measurement. Real (lightweight) FAISS, fake embeddings."""

import json
from pathlib import Path

import numpy as np
import pytest

from retraction_bench.corpus.embed_index import build_index
from retraction_bench.corpus.retrieval_ceiling import PRACTICAL_K, measure_all, measure_item, write_report
from retraction_bench.schemas import (
    BenchmarkItem,
    Claim,
    ClaimPolarity,
    ClaimType,
    EvidenceDirection,
    EvidenceTierMatch,
    ItemType,
    Provenance,
)

pytest.importorskip("faiss")

DIM = 8


def _fake_embed_fn(texts: list[str]) -> np.ndarray:
    """Deterministic: vector is derived from the text's first DIM characters, so a query
    matching a document's exact text embeds identically (cosine similarity 1.0, guaranteed
    top rank), and unrelated text embeds very differently.
    """
    vectors = np.zeros((len(texts), DIM), dtype="float32")
    for i, text in enumerate(texts):
        for j, ch in enumerate(text[:DIM]):
            vectors[i, j % DIM] += ord(ch)
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return vectors / norms


def _write_corpus(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row) + "\n")


def _item(item_id: str, domain: str, question: str, source_id: str) -> BenchmarkItem:
    return BenchmarkItem(
        item_id=item_id,
        question=question,
        domain=domain,
        claim_type=ClaimType.CLINICAL_INTERVENTION,
        item_type=ItemType.SUPERSEDED_WITH_CURRENT_ANSWER,
        claim_polarity=ClaimPolarity.POSITIVE,
        replacement_exists=False,
        evidence_direction=EvidenceDirection.CONCORDANT,
        evidence_tier_match=EvidenceTierMatch.SAME_TIER,
        trap_claim=Claim(text="trap"),
        gold_claim=Claim(text="gold"),
        supporting_sources=[source_id],
        provenance=Provenance.DRAFT,
    )


def test_measure_item_ranks_exact_match_first(tmp_path: Path) -> None:
    corpus_path = tmp_path / "corpus.jsonl"
    _write_corpus(
        corpus_path,
        [
            {
                "pmid": "111",
                "title": "QUERYMATCH",
                "abstract": "",
                "domain": "DomainA",
                "corpus_role": "benchmark_source",
                "linked_source_registry_id": "rw-1",
            },
            {
                "pmid": "222",
                "title": "Somewhat different text",
                "abstract": "",
                "domain": "DomainA",
                "corpus_role": "supersession_notice",
                "linked_source_registry_id": "rw-1",
            },
            {
                "pmid": "999",
                "title": "Totally unrelated zzz",
                "abstract": "",
                "domain": "DomainA",
                "corpus_role": "background",
                "linked_source_registry_id": None,
            },
        ],
    )
    index_dir = tmp_path / "index"
    build_index(corpus_path, index_dir, embed_fn=_fake_embed_fn, batch_size=3)
    from retraction_bench.corpus.embed_index import load_index

    index, manifest = load_index(index_dir)

    item = _item("RB-0001", "DomainA", "QUERYMATCH", "rw-1")
    result = measure_item(item, index, manifest, embed_fn=_fake_embed_fn)

    assert result.trap_source_rank == 1  # exact text match, must be rank 1
    assert result.notice_rank is not None
    assert result.rank_gap == result.notice_rank - 1


def test_measure_all_computes_rank_gap_and_domain_stats(tmp_path: Path) -> None:
    corpus_path = tmp_path / "corpus.jsonl"
    _write_corpus(
        corpus_path,
        [
            {
                "pmid": "111",
                "title": "QUERYMATCH",
                "abstract": "",
                "domain": "DomainA",
                "corpus_role": "benchmark_source",
                "linked_source_registry_id": "rw-1",
            },
            {
                "pmid": "222",
                "title": "Somewhat unrelated notice text",
                "abstract": "",
                "domain": "DomainA",
                "corpus_role": "supersession_notice",
                "linked_source_registry_id": "rw-1",
            },
        ],
    )
    index_dir = tmp_path / "index"
    build_index(corpus_path, index_dir, embed_fn=_fake_embed_fn, batch_size=2)

    item = _item("RB-0001", "DomainA", "QUERYMATCH", "rw-1")
    results, summaries = measure_all([item], index_dir, embed_fn=_fake_embed_fn)

    assert results[0].trap_source_rank == 1
    summary = summaries[0]
    assert summary.domain == "DomainA"
    assert summary.n_items == 1
    assert summary.mean_rank_gap == results[0].rank_gap
    assert summary.notice_ranks_worse_fraction in (0.0, 1.0)
    assert summary.notice_invisible_in_practice_fraction in (0.0, 1.0)


def test_hit_at_derived_from_rank_matches_k_semantics(tmp_path: Path) -> None:
    corpus_path = tmp_path / "corpus.jsonl"
    _write_corpus(
        corpus_path,
        [
            {
                "pmid": "111",
                "title": "QUERYMATCH",
                "abstract": "",
                "domain": "DomainA",
                "corpus_role": "benchmark_source",
                "linked_source_registry_id": "rw-1",
            },
        ],
    )
    index_dir = tmp_path / "index"
    build_index(corpus_path, index_dir, embed_fn=_fake_embed_fn, batch_size=1)
    item = _item("RB-0001", "DomainA", "QUERYMATCH", "rw-1")
    results, _ = measure_all([item], index_dir, embed_fn=_fake_embed_fn, k_values=(1, 5))

    r = results[0]
    assert r.trap_source_hit_at[1] is True
    assert r.notice_rank is None  # no notice document indexed for this item
    assert r.notice_hit_at[5] is False


def test_practical_k_constant_is_ten() -> None:
    assert PRACTICAL_K == 10


def test_write_report_includes_rank_fields(tmp_path: Path) -> None:
    corpus_path = tmp_path / "corpus.jsonl"
    _write_corpus(
        corpus_path,
        [
            {
                "pmid": "111",
                "title": "QUERYMATCH",
                "abstract": "",
                "domain": "DomainA",
                "corpus_role": "benchmark_source",
                "linked_source_registry_id": "rw-1",
            }
        ],
    )
    index_dir = tmp_path / "index"
    build_index(corpus_path, index_dir, embed_fn=_fake_embed_fn, batch_size=1)
    item = _item("RB-0001", "DomainA", "QUERYMATCH", "rw-1")
    results, summaries = measure_all([item], index_dir, embed_fn=_fake_embed_fn)

    output_path = tmp_path / "report.json"
    write_report(results, summaries, output_path)
    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["per_item"][0]["trap_source_rank"] == 1
    assert "mean_rank_gap" in payload["per_domain"][0]
    assert payload["practical_k"] == 10
