import pytest

from retraction_bench.stats.bootstrap import (
    bootstrap_ci,
    bootstrap_proportion_ci,
    bootstrap_proportion_ci_clustered,
)


def test_bootstrap_ci_point_estimate_matches_mean() -> None:
    result = bootstrap_ci([1.0, 2.0, 3.0, 4.0, 5.0], seed=1)
    assert result.point_estimate == 3.0


def test_bootstrap_ci_interval_contains_point_estimate() -> None:
    result = bootstrap_ci([0.0, 1.0, 1.0, 1.0, 0.0], seed=1)
    assert result.ci_low <= result.point_estimate <= result.ci_high


def test_bootstrap_ci_is_deterministic_given_seed() -> None:
    values = [1.0, 5.0, 3.0, 9.0, 2.0, 7.0]
    first = bootstrap_ci(values, seed=7)
    second = bootstrap_ci(values, seed=7)
    assert first.ci_low == second.ci_low
    assert first.ci_high == second.ci_high


def test_bootstrap_ci_different_seeds_can_differ() -> None:
    values = [1.0, 5.0, 3.0, 9.0, 2.0, 7.0, 4.0, 8.0]
    a = bootstrap_ci(values, seed=1, n_resamples=200)
    b = bootstrap_ci(values, seed=2, n_resamples=200)
    # Not asserting inequality (resampling could coincidentally match) -- asserting both ran
    # and produced valid, ordered intervals is the real contract here.
    assert a.ci_low <= a.ci_high
    assert b.ci_low <= b.ci_high


def test_bootstrap_ci_rejects_empty_input() -> None:
    with pytest.raises(ValueError, match="at least one value"):
        bootstrap_ci([])


def test_bootstrap_ci_single_value_collapses_to_point() -> None:
    result = bootstrap_ci([4.0], seed=1)
    assert result.point_estimate == 4.0
    assert result.ci_low == 4.0
    assert result.ci_high == 4.0


def test_bootstrap_proportion_ci_all_true() -> None:
    result = bootstrap_proportion_ci([True, True, True], seed=1)
    assert result.point_estimate == 1.0
    assert result.ci_high == 1.0


def test_bootstrap_proportion_ci_mixed() -> None:
    result = bootstrap_proportion_ci([True, False, True, False, True], seed=1)
    assert result.point_estimate == pytest.approx(0.6)
    assert 0.0 <= result.ci_low <= result.point_estimate <= result.ci_high <= 1.0


def test_clustered_point_estimate_matches_unclustered() -> None:
    # same pooled rate either way -- only the CI's resampling unit should differ
    successes = [True, True, False, True, True, False]
    cluster_ids = ["a", "a", "a", "b", "b", "b"]
    clustered = bootstrap_proportion_ci_clustered(successes, cluster_ids, seed=1)
    unclustered = bootstrap_proportion_ci(successes, seed=1)
    assert clustered.point_estimate == pytest.approx(unclustered.point_estimate)


def test_clustered_ci_is_deterministic_given_seed() -> None:
    successes = [True, True, False, True, False, False, True, True]
    cluster_ids = ["a", "a", "b", "b", "c", "c", "d", "d"]
    first = bootstrap_proportion_ci_clustered(successes, cluster_ids, seed=3)
    second = bootstrap_proportion_ci_clustered(successes, cluster_ids, seed=3)
    assert first.ci_low == second.ci_low
    assert first.ci_high == second.ci_high


def test_clustered_ci_is_at_least_as_wide_as_unclustered_when_within_cluster_correlated() -> None:
    # 3 "seeds" per item, perfectly correlated within an item (all-or-nothing per item) --
    # exactly the shape this project's M1/M3/Correctness data has. Treating 12 correlated
    # responses (4 items x 3 seeds) as 12 independent draws must understate uncertainty
    # relative to treating the 4 items as the real independent unit.
    successes = [True, True, True, True, True, True, False, False, False, False, False, False]
    cluster_ids = ["item1", "item1", "item1", "item2", "item2", "item2",
                    "item3", "item3", "item3", "item4", "item4", "item4"]
    clustered = bootstrap_proportion_ci_clustered(successes, cluster_ids, seed=1)
    unclustered = bootstrap_proportion_ci(successes, seed=1)
    clustered_width = clustered.ci_high - clustered.ci_low
    unclustered_width = unclustered.ci_high - unclustered.ci_low
    assert clustered_width > unclustered_width


def test_clustered_rejects_mismatched_lengths() -> None:
    with pytest.raises(ValueError, match="same length"):
        bootstrap_proportion_ci_clustered([True, False], ["a"])


def test_clustered_rejects_empty_input() -> None:
    with pytest.raises(ValueError, match="at least one value"):
        bootstrap_proportion_ci_clustered([], [])


def test_clustered_single_cluster_collapses_to_point() -> None:
    result = bootstrap_proportion_ci_clustered([True, False, True], ["a", "a", "a"], seed=1)
    assert result.point_estimate == pytest.approx(2 / 3)
    assert result.ci_low == result.point_estimate == result.ci_high
