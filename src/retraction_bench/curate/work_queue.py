"""Balanced, interleaved annotation work queue (ANNOTATION.md section 3.3, ADR-038, ADR-041).

The benchmark is no longer sized to a fixed item count (ADR-037) -- annotation runs
until a fixed date and stops wherever it lands. That makes balance a live constraint,
not something to fix up at the end: if annotation proceeds domain by domain, stopping
early leaves an unusable, lopsided benchmark. This module always hands back candidates
from whichever domain is currently furthest behind, so the running counts stay roughly
equal no matter when annotation stops -- and it enforces two independent author-cluster
constraints: the standing cap of 2 per author across the whole benchmark (ADR-031,
checked against everything already committed, including candidates queued earlier in the
same call), and a stricter per-batch cap of 1 per cluster (ADR-041) -- a batch satisfying
the first without the second (e.g. two Boldt/Hempelmann items in one 5-item batch)
concentrates a famous scandal in a single sitting, which defeats the cap's purpose even
though it doesn't violate it.
"""

from collections import Counter

import pandas as pd

from retraction_bench.curate.author_clusters import author_record_map, clusters, parse_authors

DEFAULT_AUTHOR_CAP = 2
DEFAULT_CLUSTER_MIN_SIZE = 3
DEFAULT_MAX_CLUSTER_AUTHORS_PER_BATCH = 1


def build_work_queue(
    candidates: pd.DataFrame,
    already_selected: dict[str, str],
    rejected: frozenset[str] = frozenset(),
    author_cap: int = DEFAULT_AUTHOR_CAP,
    cluster_min_size: int = DEFAULT_CLUSTER_MIN_SIZE,
    max_cluster_authors_per_batch: int = DEFAULT_MAX_CLUSTER_AUTHORS_PER_BATCH,
    n: int | None = None,
) -> list[str]:
    """Return up to `n` candidate record_ids, ordered to keep per-domain counts balanced.

    candidates: full pool, columns record_id, domain, author (RW's semicolon-separated field).
    already_selected: record_id -> domain, for items already committed (annotated or in
        progress) -- their domain counts as a head start the queue balances against.
    rejected: record_ids to never offer again (ANNOTATION.md section 3.4).
    author_cap: max items per individual author across the whole benchmark (ADR-031).
    max_cluster_authors_per_batch: max items per author-cluster within THIS call's returned
        batch specifically (ADR-041) -- resets every call, unlike author_cap, which persists
        via already_selected across calls.
    """
    domain_counts = Counter(already_selected.values())
    for domain in candidates["domain"].unique():
        domain_counts.setdefault(domain, 0)

    committed = set(already_selected.keys())
    author_index = author_record_map(candidates)
    cluster_author_names = set(clusters(candidates, min_size=cluster_min_size).keys())
    batch_cluster_used: Counter[str] = Counter()

    by_domain: dict[str, list[tuple[str, list[str]]]] = {}
    for domain, group in candidates.groupby("domain"):
        rows = group.sort_values("record_id", key=lambda s: s.astype(int))
        by_domain[domain] = [(row["record_id"], parse_authors(row["author"])) for _, row in rows.iterrows()]

    domain_order = sorted(by_domain.keys())
    cursor = dict.fromkeys(domain_order, 0)

    queue: list[str] = []
    while n is None or len(queue) < n:
        progressed = False
        for domain in sorted(domain_order, key=lambda d: (domain_counts[d], d)):
            picked = _next_eligible(
                by_domain[domain],
                cursor,
                domain,
                committed,
                rejected,
                author_index,
                author_cap,
                cluster_author_names,
                batch_cluster_used,
                max_cluster_authors_per_batch,
            )
            if picked is not None:
                record_id, authors = picked
                queue.append(record_id)
                committed.add(record_id)
                domain_counts[domain] += 1
                for a in authors:
                    if a in cluster_author_names:
                        batch_cluster_used[a] += 1
                progressed = True
                break
        if not progressed:
            break  # every domain exhausted -- no eligible candidates remain anywhere
    return queue


def _next_eligible(
    rows: list[tuple[str, list[str]]],
    cursor: dict[str, int],
    domain: str,
    committed: set[str],
    rejected: frozenset[str],
    author_index: dict[str, set[str]],
    author_cap: int,
    cluster_author_names: set[str],
    batch_cluster_used: "Counter[str]",
    max_cluster_authors_per_batch: int,
) -> tuple[str, list[str]] | None:
    i = cursor[domain]
    while i < len(rows):
        record_id, authors = rows[i]
        i += 1
        if record_id in committed or record_id in rejected:
            continue
        if any(len(author_index.get(a, set()) & committed) >= author_cap for a in authors):
            continue
        cluster_authors_here = [a for a in authors if a in cluster_author_names]
        if any(batch_cluster_used[a] >= max_cluster_authors_per_batch for a in cluster_authors_here):
            continue
        cursor[domain] = i
        return record_id, authors
    cursor[domain] = i
    return None
