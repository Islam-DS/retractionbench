"""Tests for embedding + FAISS index construction. Uses a fake embed_fn -- no real model
loaded in the test suite -- but real (lightweight) FAISS operations.
"""

import json
from pathlib import Path

import numpy as np
import pytest

from retraction_bench.corpus.embed_index import add_documents, build_index, load_index, search

pytest.importorskip("faiss")

DIM = 8


def _fake_embed_fn(texts: list[str]) -> np.ndarray:
    """Deterministic, distinguishable vectors: hash each text into a small fixed-dim vector."""
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


def test_build_index_reports_real_stats(tmp_path: Path) -> None:
    corpus_path = tmp_path / "corpus.jsonl"
    _write_corpus(
        corpus_path,
        [
            {"pmid": "1", "title": "Alpha", "abstract": "one", "domain": "A", "corpus_role": "background"},
            {"pmid": "2", "title": "Beta", "abstract": "two", "domain": "B", "corpus_role": "benchmark_source"},
        ],
    )
    index_dir = tmp_path / "index"
    stats = build_index(corpus_path, index_dir, embed_fn=_fake_embed_fn, batch_size=1)

    assert stats.record_count == 2
    assert stats.embedding_dim == DIM
    assert stats.build_seconds >= 0
    assert stats.index_size_bytes > 0
    assert (index_dir / "corpus.faiss").exists()
    assert (index_dir / "corpus_manifest.jsonl").exists()


def test_load_index_and_search_finds_the_matching_document(tmp_path: Path) -> None:
    corpus_path = tmp_path / "corpus.jsonl"
    _write_corpus(
        corpus_path,
        [
            {"pmid": "1", "title": "Zzzzzzzz", "abstract": "", "domain": "A", "corpus_role": "background"},
            {
                "pmid": "2",
                "title": "Aaaaaaaa",
                "abstract": "",
                "domain": "B",
                "corpus_role": "benchmark_source",
                "linked_source_registry_id": "rw-1",
            },
        ],
    )
    index_dir = tmp_path / "index"
    build_index(corpus_path, index_dir, embed_fn=_fake_embed_fn, batch_size=2)

    index, manifest = load_index(index_dir)
    assert len(manifest) == 2

    query_vector = _fake_embed_fn(["Aaaaaaaa "])
    results = search(index, manifest, query_vector, k=1)
    assert results[0]["pmid"] == "2"
    assert results[0]["corpus_role"] == "benchmark_source"
    assert results[0]["linked_source_registry_id"] == "rw-1"


def test_add_documents_appends_without_disturbing_existing_vectors(tmp_path: Path) -> None:
    corpus_path = tmp_path / "corpus.jsonl"
    _write_corpus(
        corpus_path,
        [{"pmid": "1", "title": "Zzzzzzzz", "abstract": "", "domain": "A", "corpus_role": "background"}],
    )
    index_dir = tmp_path / "index"
    build_index(corpus_path, index_dir, embed_fn=_fake_embed_fn, batch_size=1)

    added = add_documents(
        [
            {
                "pmid": "2",
                "title": "Aaaaaaaa",
                "abstract": "",
                "domain": "B",
                "corpus_role": "benchmark_source",
                "linked_source_registry_id": "rw-1",
            }
        ],
        index_dir,
        embed_fn=_fake_embed_fn,
    )
    assert added == 1

    index, manifest = load_index(index_dir)
    assert index.ntotal == 2
    assert len(manifest) == 2
    assert manifest[0]["pmid"] == "1"
    assert manifest[1]["pmid"] == "2"

    query_vector = _fake_embed_fn(["Aaaaaaaa "])
    results = search(index, manifest, query_vector, k=1)
    assert results[0]["pmid"] == "2"
    assert results[0]["linked_source_registry_id"] == "rw-1"
