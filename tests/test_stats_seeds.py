import pytest

from retraction_bench.stats.seeds import aggregate_across_seeds


def test_aggregate_across_seeds_computes_mean_and_std() -> None:
    result = aggregate_across_seeds({1: 0.5, 2: 0.6, 3: 0.7})
    assert result.mean == pytest.approx(0.6)
    assert result.std > 0
    assert result.n_seeds == 3


def test_aggregate_across_seeds_flags_below_min_seeds() -> None:
    result = aggregate_across_seeds({1: 0.5})
    assert result.below_min_seeds is True
    assert result.n_seeds == 1


def test_aggregate_across_seeds_three_seeds_not_flagged() -> None:
    result = aggregate_across_seeds({1: 0.5, 2: 0.5, 3: 0.5})
    assert result.below_min_seeds is False


def test_aggregate_across_seeds_zero_variance_when_identical() -> None:
    result = aggregate_across_seeds({1: 0.5, 2: 0.5, 3: 0.5})
    assert result.std == 0.0


def test_aggregate_across_seeds_rejects_empty() -> None:
    with pytest.raises(ValueError, match="at least one seed"):
        aggregate_across_seeds({})


def test_aggregate_across_seeds_preserves_values_by_seed() -> None:
    result = aggregate_across_seeds({10: 0.1, 20: 0.9})
    assert result.values_by_seed == {10: 0.1, 20: 0.9}
