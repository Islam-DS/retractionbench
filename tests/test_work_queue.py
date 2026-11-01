"""Tests for the balanced, interleaved annotation work queue (ADR-038)."""

import pandas as pd

from retraction_bench.curate.work_queue import build_work_queue


def _pool() -> pd.DataFrame:
    rows = []
    for domain, ids in [
        ("A", ["1", "2", "3", "4"]),
        ("B", ["11", "12", "13", "14"]),
        ("C", ["21", "22", "23", "24"]),
    ]:
        for rid in ids:
            rows.append({"record_id": rid, "domain": domain, "author": f"Author {rid}"})
    return pd.DataFrame(rows)


def test_balances_evenly_across_domains_from_a_cold_start() -> None:
    queue = build_work_queue(_pool(), already_selected={}, n=6)
    pool = _pool().set_index("record_id")["domain"]
    counts = pool.loc[queue].value_counts()
    assert set(counts.index) == {"A", "B", "C"}
    assert counts.max() - counts.min() <= 1


def test_balances_against_a_head_start() -> None:
    # Domain A already has 2 selected; queue should favour B and C until they catch up.
    queue = build_work_queue(_pool(), already_selected={"1": "A", "2": "A"}, n=4)
    pool = _pool().set_index("record_id")["domain"]
    domains_picked = [pool.loc[rid] for rid in queue]
    assert domains_picked.count("A") == 0
    assert domains_picked.count("B") == 2
    assert domains_picked.count("C") == 2


def test_never_returns_already_selected_or_rejected() -> None:
    queue = build_work_queue(_pool(), already_selected={"1": "A"}, rejected=frozenset({"2", "11"}), n=9)
    assert "1" not in queue
    assert "2" not in queue
    assert "11" not in queue


def test_enforces_author_cap_against_already_selected() -> None:
    pool = _pool()
    pool.loc[pool["record_id"] == "3", "author"] = "Shared Author"
    pool.loc[pool["record_id"] == "4", "author"] = "Shared Author"
    already_selected = {"1": "A", "2": "A"}
    # Simulate "Shared Author" already at cap via two prior unrelated committed records
    # by giving 1 and 2 the same author name instead.
    pool.loc[pool["record_id"] == "1", "author"] = "Shared Author"
    pool.loc[pool["record_id"] == "2", "author"] = "Shared Author"

    # max_cluster_authors_per_batch disabled here so this test isolates author_cap alone,
    # not the stricter per-batch cluster cap (see the dedicated tests below for that).
    queue = build_work_queue(
        pool, already_selected=already_selected, author_cap=2, max_cluster_authors_per_batch=99, n=9
    )
    assert "3" not in queue
    assert "4" not in queue


def test_enforces_author_cap_within_the_queue_itself() -> None:
    pool = _pool()
    for rid in ["1", "2", "3", "4"]:
        pool.loc[pool["record_id"] == rid, "author"] = "Prolific Author"

    queue = build_work_queue(pool, already_selected={}, author_cap=2, max_cluster_authors_per_batch=99, n=12)
    domain_a_picked = [rid for rid in queue if rid in {"1", "2", "3", "4"}]
    assert len(domain_a_picked) <= 2


def test_per_batch_cluster_cap_limits_one_item_per_cluster_per_call() -> None:
    # Two different authors who co-author several papers together (a Boldt/Hempelmann-style
    # cluster) should contribute at most 1 item to a single batch, even though the standing
    # author_cap of 2 would otherwise allow a second.
    pool = _pool()
    for rid in ["1", "2", "3"]:
        pool.loc[pool["record_id"] == rid, "author"] = "Cluster Author One;Cluster Author Two"

    queue = build_work_queue(pool, already_selected={}, n=9)
    cluster_picked = [rid for rid in queue if rid in {"1", "2", "3"}]
    assert len(cluster_picked) <= 1


def test_per_batch_cluster_cap_does_not_block_a_different_cluster() -> None:
    # Domain A's cluster (record 1-3) uses up its one per-batch slot; a different cluster in
    # domain B should still be allowed once in the same batch.
    pool = _pool()
    for rid in ["1", "2", "3"]:
        pool.loc[pool["record_id"] == rid, "author"] = "Cluster Author One;Cluster Author Two"
    for rid in ["11", "12", "13"]:
        pool.loc[pool["record_id"] == rid, "author"] = "Other Cluster Author"

    queue = build_work_queue(pool, already_selected={}, n=9)
    a_cluster_picked = [rid for rid in queue if rid in {"1", "2", "3"}]
    b_cluster_picked = [rid for rid in queue if rid in {"11", "12", "13"}]
    assert len(a_cluster_picked) <= 1
    assert len(b_cluster_picked) <= 1
    assert len(a_cluster_picked) + len(b_cluster_picked) >= 1  # both clusters get a shot, not zeroed out


def test_per_batch_cluster_cap_does_not_restrict_non_clustered_authors() -> None:
    # An author appearing on only 1-2 records (below cluster_min_size) is not a "cluster" --
    # the per-batch restriction should not apply to ordinary co-authorship.
    queue = build_work_queue(_pool(), already_selected={}, n=12)
    assert len(queue) == 12  # nothing in the default fixture is clustered; all 12 are reachable


def test_stops_when_all_domains_exhausted() -> None:
    small_pool = pd.DataFrame({"record_id": ["1", "11"], "domain": ["A", "B"], "author": ["Author 1", "Author 11"]})
    queue = build_work_queue(small_pool, already_selected={}, n=10)
    assert len(queue) == 2


def test_deterministic_across_repeated_calls() -> None:
    queue1 = build_work_queue(_pool(), already_selected={}, n=6)
    queue2 = build_work_queue(_pool(), already_selected={}, n=6)
    assert queue1 == queue2
