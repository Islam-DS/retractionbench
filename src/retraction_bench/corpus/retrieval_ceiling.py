"""Retrieval-ceiling measurement: the best any model could do given this corpus, measured
before any model call (docs/CORPUS_PLAN.md section 6, ADR-046/047/049).

For every benchmark item, finds the exact rank (1-indexed position in the full similarity
ranking, not just a hit/miss at a fixed k) of its trap source and its supersession notice.
Rank is the first-class measurement (ADR-049): item 1's result showed the trap source
retrieved at rank 1 while its notice first appeared at rank 5 -- the dangerous document
outranking its own correction is exactly the failure this benchmark's premise is about, and
a fixed-k hit/miss view would have reported both as simply "found," hiding the gap. Broken
out per domain (ADR-047) since the corpus's domain-size imbalance is a live question about
whether retrieval competition differs enough by domain to confound downstream results.
"""

import json
import statistics
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from retraction_bench.corpus.embed_index import load_index, search
from retraction_bench.schemas import BenchmarkItem

DEFAULT_K_VALUES = (1, 5, 10, 20, 50)
# Typical operating range for real RAG systems (author's framing) -- a notice ranked below
# this is effectively invisible in practice, regardless of what a full-corpus ceiling shows.
PRACTICAL_K = 10


@dataclass
class ItemCeilingResult:
    item_id: str
    domain: str
    trap_source_rank: int | None  # 1-indexed; None only if the source isn't in the corpus at all
    notice_rank: int | None  # None if the item has no notice document, or it isn't in the corpus
    rank_gap: int | None  # notice_rank - trap_source_rank; positive means the notice ranks worse

    def hit_at(self, k: int, rank: int | None) -> bool:
        return rank is not None and rank <= k

    @property
    def trap_source_hit_at(self) -> dict[int, bool]:
        return {k: self.hit_at(k, self.trap_source_rank) for k in DEFAULT_K_VALUES}

    @property
    def notice_hit_at(self) -> dict[int, bool]:
        return {k: self.hit_at(k, self.notice_rank) for k in DEFAULT_K_VALUES}


@dataclass
class DomainCeilingSummary:
    domain: str
    n_items: int
    trap_source_recall_at: dict[int, float]
    notice_recall_at: dict[int, float]
    mean_rank_gap: float | None
    median_rank_gap: float | None
    notice_ranks_worse_fraction: float | None  # fraction of items where notice_rank > trap_source_rank
    notice_invisible_in_practice_fraction: float | None  # fraction where notice_rank > PRACTICAL_K


def _find_rank(results: list[dict], role: str, target_ids: set[str]) -> int | None:
    for i, r in enumerate(results, start=1):
        if r["corpus_role"] == role and r.get("linked_source_registry_id") in target_ids:
            return i
    return None


def measure_item(
    item: BenchmarkItem,
    index,
    manifest: list[dict],
    embed_fn: Callable[[list[str]], np.ndarray],
) -> ItemCeilingResult:
    query_vector = embed_fn([item.question])
    # Exact rank requires ranking the whole corpus -- IndexFlatIP is brute-force regardless
    # of k, so this costs little more than a small-k search and avoids ever missing a rank
    # that happens to fall outside an arbitrarily chosen cutoff.
    results = search(index, manifest, query_vector, k=len(manifest))

    trap_source_ids = set(item.supporting_sources)
    trap_rank = _find_rank(results, "benchmark_source", trap_source_ids)
    notice_rank = _find_rank(results, "supersession_notice", trap_source_ids)
    rank_gap = notice_rank - trap_rank if (trap_rank is not None and notice_rank is not None) else None

    return ItemCeilingResult(
        item_id=item.item_id, domain=item.domain, trap_source_rank=trap_rank, notice_rank=notice_rank, rank_gap=rank_gap
    )


def measure_all(
    items: list[BenchmarkItem],
    index_dir: Path,
    embed_fn: Callable[[list[str]], np.ndarray],
    k_values: tuple[int, ...] = DEFAULT_K_VALUES,
) -> tuple[list[ItemCeilingResult], list[DomainCeilingSummary]]:
    index, manifest = load_index(index_dir)
    results = [measure_item(item, index, manifest, embed_fn) for item in items]

    by_domain: dict[str, list[ItemCeilingResult]] = {}
    for r in results:
        by_domain.setdefault(r.domain, []).append(r)

    summaries = []
    for domain, domain_results in by_domain.items():
        n = len(domain_results)
        trap_recall = {k: sum(r.hit_at(k, r.trap_source_rank) for r in domain_results) / n for k in k_values}
        notice_recall = {k: sum(r.hit_at(k, r.notice_rank) for r in domain_results) / n for k in k_values}
        gaps = [r.rank_gap for r in domain_results if r.rank_gap is not None]
        both_present = [r for r in domain_results if r.trap_source_rank is not None and r.notice_rank is not None]
        summaries.append(
            DomainCeilingSummary(
                domain=domain,
                n_items=n,
                trap_source_recall_at=trap_recall,
                notice_recall_at=notice_recall,
                mean_rank_gap=statistics.fmean(gaps) if gaps else None,
                median_rank_gap=statistics.median(gaps) if gaps else None,
                notice_ranks_worse_fraction=(
                    sum(1 for r in both_present if r.rank_gap > 0) / len(both_present) if both_present else None
                ),
                notice_invisible_in_practice_fraction=(
                    sum(1 for r in domain_results if not r.hit_at(PRACTICAL_K, r.notice_rank)) / n if n else None
                ),
            )
        )
    return results, summaries


def write_report(results: list[ItemCeilingResult], summaries: list[DomainCeilingSummary], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "practical_k": PRACTICAL_K,
        "per_item": [
            {
                "item_id": r.item_id,
                "domain": r.domain,
                "trap_source_rank": r.trap_source_rank,
                "notice_rank": r.notice_rank,
                "rank_gap": r.rank_gap,
            }
            for r in results
        ],
        "per_domain": [
            {
                "domain": s.domain,
                "n_items": s.n_items,
                "trap_source_recall_at": s.trap_source_recall_at,
                "notice_recall_at": s.notice_recall_at,
                "mean_rank_gap": s.mean_rank_gap,
                "median_rank_gap": s.median_rank_gap,
                "notice_ranks_worse_fraction": s.notice_ranks_worse_fraction,
                "notice_invisible_in_practice_fraction": s.notice_invisible_in_practice_fraction,
            }
            for s in summaries
        ],
    }
    output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
