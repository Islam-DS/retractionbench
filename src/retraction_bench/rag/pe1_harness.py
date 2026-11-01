"""PE1 harness logic: retrieval-only, baseline-vs-reranked comparison for the replacement-
evidence documents. Pure functions over injected index/manifest/items/embed_fn so this is
testable against a synthetic fixture (`tests/test_pe1_replacement_retrieval_rerank.py`) without
touching the real 325,167-document corpus. `scripts/pe1_replacement_retrieval_rerank.py` is the
thin CLI wrapper that wires in the real corpus/index/items -- matching this project's existing
layering (`scripts/*.py` are thin entry points; logic lives under `src/`).

**Evaluation/input separation, load-bearing:** `_target_pmids_for_item` reads
`corpus_role`/`linked_source_registry_id` from the manifest -- exactly as
`replacement_retrieval_ceiling.py` already does -- but its output (a set of target PMIDs) is
used ONLY to score where a document landed in a ranking, in `_rank_of_any`. It is never passed
to `build_candidate_documents`/`rerank_by_recency` (`rag/recency_rerank.py`), which see only
`pmid`/`score`/`pub_year` for every candidate, with no concept of "which one is the target."
"""

from collections.abc import Callable

import numpy as np

from retraction_bench.corpus.embed_index import search
from retraction_bench.rag.recency_rerank import build_candidate_documents, rerank_by_recency
from retraction_bench.schemas import BenchmarkItem

HIT_K_VALUES = (1, 3, 5, 10)


def _target_pmids_for_item(item: BenchmarkItem, manifest: list[dict]) -> set[str]:
    """Evaluation-only. See module docstring."""
    target_identifiers = {ev.identifier for ev in item.post_supersession_evidence}
    return {
        m["pmid"]
        for m in manifest
        if m["corpus_role"] == "superseding_evidence" and m.get("linked_source_registry_id") in target_identifiers
    }


def _rank_of_any(pmids_in_order: list[str], target_pmids: set[str]) -> int | None:
    for i, pmid in enumerate(pmids_in_order, start=1):
        if pmid in target_pmids:
            return i
    return None


def run_pe1(
    items: list[BenchmarkItem],
    index,
    manifest: list[dict],
    pub_year_lookup: dict[str, int | None],
    embed_fn: Callable[[list[str]], np.ndarray],
    pool_k: int,
) -> list[dict]:
    """One row per item with resolved replacement evidence: baseline/reranked rank and
    hit@k for every k in HIT_K_VALUES. Items with no resolved evidence at all are skipped
    (matching `replacement_retrieval_ceiling.py`'s own scoping).
    """
    rows = []
    for item in items:
        target_pmids = _target_pmids_for_item(item, manifest)
        if not target_pmids:
            continue

        query_vector = embed_fn([item.question])
        hits = search(index, manifest, query_vector, k=pool_k)

        baseline_pmids = [h["pmid"] for h in hits]
        candidates = build_candidate_documents(hits, pub_year_lookup)
        reranked = rerank_by_recency(candidates)
        reranked_pmids = [c.pmid for c in reranked]

        baseline_rank = _rank_of_any(baseline_pmids, target_pmids)
        reranked_rank = _rank_of_any(reranked_pmids, target_pmids)

        row = {
            "item_id": item.item_id,
            "baseline_rank": baseline_rank,
            "reranked_rank": reranked_rank,
            # Diagnostic only, for sanity checks -- not used by any rank/hit@k computation above,
            # which is already complete by this point. Exposing the two pmid lists lets a caller
            # verify (without recomputing) that reranking never changes the document SET, only
            # the order -- the exact `set(baseline_pmids) == set(reranked_pmids)` check this
            # module's own module docstring and `rag/recency_rerank.py` both already guarantee.
            "baseline_pmids": baseline_pmids,
            "reranked_pmids": reranked_pmids,
        }
        for k in HIT_K_VALUES:
            row[f"baseline_hit@{k}"] = baseline_rank is not None and baseline_rank <= k
            row[f"reranked_hit@{k}"] = reranked_rank is not None and reranked_rank <= k
        rows.append(row)
    return rows
