"""Embedding + FAISS index construction (docs/CORPUS_PLAN.md, ADR-045/046).

Builds a flat, inner-product FAISS index over normalized BAAI/bge-large-en-v1.5 embeddings
of each corpus document's title + abstract. Reports real build time, peak memory, and
on-disk index size from the actual run -- the project protocol's reproduction path states real
requirements, not optimistic estimates (the author's explicit instruction, ADR-047).

Peak memory is measured via process RSS (`psutil`), sampled on a background thread while
the build runs, not `tracemalloc` -- `tracemalloc` only sees pure-Python heap allocations
and is blind to PyTorch/CUDA and FAISS's native (C/C++) allocations, which is where nearly
all of this workload's actual memory goes. Caught by checking the number against reality on
a smoke test before trusting it for the real run, not assumed correct because it ran without
error.

`embed_fn` is injectable so tests exercise the real indexing/ID-mapping logic without
loading the actual (large) sentence-transformers model.
"""

import json
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np
import psutil

if TYPE_CHECKING:
    import faiss

EMBED_MODEL_NAME = "BAAI/bge-large-en-v1.5"
DEFAULT_ENCODE_BATCH_SIZE = 64


@dataclass
class IndexBuildStats:
    record_count: int
    build_seconds: float
    peak_memory_mb: float
    index_size_bytes: int
    embedding_dim: int
    model_name: str


def _default_embed_fn() -> Callable[[list[str]], np.ndarray]:
    """Loads the real embedding model. Not called in tests -- injected there instead."""
    from sentence_transformers import SentenceTransformer

    model = SentenceTransformer(EMBED_MODEL_NAME)

    def embed(texts: list[str]) -> np.ndarray:
        # bge models expect a retrieval-style instruction prefix on the *query* side only;
        # corpus-side documents are embedded plain, per the model card.
        vectors = model.encode(texts, batch_size=DEFAULT_ENCODE_BATCH_SIZE, normalize_embeddings=True)
        return np.asarray(vectors, dtype="float32")

    return embed


class _PeakRSSSampler:
    """Samples this process's RSS on a background thread and tracks the max seen.

    RSS (resident set size) is real OS-reported physical memory in use -- it includes
    PyTorch/CUDA host-side allocations and FAISS's native memory, unlike tracemalloc's
    Python-heap-only view. Not a GPU memory reading (that's a separate number, `nvidia-smi`
    territory); this is host RAM, which is what actually gates whether the build runs at
    all on a given machine.
    """

    def __init__(self, interval_seconds: float = 0.5) -> None:
        self._interval = interval_seconds
        self._process = psutil.Process()
        self._peak_bytes = 0
        self._stop_event = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)

    def _run(self) -> None:
        while not self._stop_event.is_set():
            rss = self._process.memory_info().rss
            self._peak_bytes = max(self._peak_bytes, rss)
            self._stop_event.wait(self._interval)

    def __enter__(self) -> "_PeakRSSSampler":
        self._peak_bytes = self._process.memory_info().rss
        self._thread.start()
        return self

    def __exit__(self, *exc_info: object) -> None:
        self._stop_event.set()
        self._thread.join(timeout=self._interval * 2)

    @property
    def peak_bytes(self) -> int:
        return self._peak_bytes


def _read_corpus_rows(corpus_path: Path) -> list[dict]:
    rows = []
    with corpus_path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def build_index(
    corpus_path: Path,
    index_dir: Path,
    embed_fn: Callable[[list[str]], np.ndarray] | None = None,
    batch_size: int = DEFAULT_ENCODE_BATCH_SIZE,
) -> IndexBuildStats:
    """Reads the assembled corpus JSONL, embeds title+abstract per row, writes a FAISS
    index plus a parallel ID-mapping manifest to index_dir. Returns real measured stats.
    """
    import faiss

    embed_fn = embed_fn or _default_embed_fn()
    rows = _read_corpus_rows(corpus_path)

    start = time.time()
    with _PeakRSSSampler() as sampler:
        index = None
        manifest: list[dict] = []
        for i in range(0, len(rows), batch_size):
            batch = rows[i : i + batch_size]
            texts = [f"{r.get('title', '')} {r.get('abstract', '')}".strip() for r in batch]
            vectors = embed_fn(texts)
            if index is None:
                index = faiss.IndexFlatIP(vectors.shape[1])
            index.add(vectors)
            for r in batch:
                manifest.append(
                    {
                        "pmid": r["pmid"],
                        "domain": r.get("domain"),
                        "corpus_role": r.get("corpus_role", "background"),
                        "linked_source_registry_id": r.get("linked_source_registry_id"),
                    }
                )
        peak_bytes = sampler.peak_bytes

    build_seconds = time.time() - start

    index_dir.mkdir(parents=True, exist_ok=True)
    index_path = index_dir / "corpus.faiss"
    manifest_path = index_dir / "corpus_manifest.jsonl"
    faiss.write_index(index, str(index_path))
    with manifest_path.open("w", encoding="utf-8") as f:
        for entry in manifest:
            f.write(json.dumps(entry) + "\n")

    return IndexBuildStats(
        record_count=len(rows),
        build_seconds=build_seconds,
        peak_memory_mb=peak_bytes / 1e6,
        index_size_bytes=index_path.stat().st_size,
        embedding_dim=index.d,
        model_name=EMBED_MODEL_NAME,
    )


def add_documents(
    corpus_rows: list[dict],
    index_dir: Path,
    embed_fn: Callable[[list[str]], np.ndarray] | None = None,
) -> int:
    """Appends new rows to an existing on-disk index without re-embedding the rest of the
    corpus. For benchmark documents inserted after the freeze (docs/CORPUS_PLAN.md section 4's
    exactly-once mechanism; ADR-048's freeze policy explicitly reserves this path, distinct
    from a full corpus rebuild). Returns the number of vectors added.
    """
    import faiss

    embed_fn = embed_fn or _default_embed_fn()
    index, manifest = load_index(index_dir)
    texts = [f"{r.get('title', '')} {r.get('abstract', '')}".strip() for r in corpus_rows]
    vectors = embed_fn(texts)
    index.add(vectors)
    for r in corpus_rows:
        manifest.append(
            {
                "pmid": r["pmid"],
                "domain": r.get("domain"),
                "corpus_role": r.get("corpus_role", "background"),
                "linked_source_registry_id": r.get("linked_source_registry_id"),
            }
        )

    faiss.write_index(index, str(index_dir / "corpus.faiss"))
    with (index_dir / "corpus_manifest.jsonl").open("w", encoding="utf-8") as f:
        for entry in manifest:
            f.write(json.dumps(entry) + "\n")

    return len(corpus_rows)


def load_index(index_dir: Path) -> tuple["faiss.Index", list[dict]]:
    import faiss

    index = faiss.read_index(str(index_dir / "corpus.faiss"))
    manifest = []
    with (index_dir / "corpus_manifest.jsonl").open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                manifest.append(json.loads(line))
    return index, manifest


def search(index: "faiss.Index", manifest: list[dict], query_vector: np.ndarray, k: int) -> list[dict]:
    """Top-k manifest entries for a single query vector (shape (1, dim), normalized)."""
    scores, indices = index.search(query_vector, k)
    results = []
    for score, idx in zip(scores[0], indices[0], strict=True):
        if idx == -1:
            continue
        entry = dict(manifest[idx])
        entry["score"] = float(score)
        results.append(entry)
    return results
