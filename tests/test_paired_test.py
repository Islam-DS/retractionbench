import pytest

from retraction_bench.stats.paired_test import holm_correction, paired_bootstrap_permutation_test


def test_paired_test_point_estimate_matches_mean() -> None:
    result = paired_bootstrap_permutation_test([0.1, 0.2, 0.3, -0.1], seed=1)
    assert result.mean_diff == pytest.approx(0.125)


def test_paired_test_zero_diffs_gives_exact_null() -> None:
    result = paired_bootstrap_permutation_test([0.0] * 21, seed=1)
    assert result.mean_diff == 0.0
    assert result.ci_low == 0.0
    assert result.ci_high == 0.0
    assert result.p_value == 1.0


def test_paired_test_is_deterministic_given_seed() -> None:
    diffs = [0.1, -0.2, 0.3, 0.0, -0.1, 0.2, 0.15, -0.05]
    first = paired_bootstrap_permutation_test(diffs, seed=7)
    second = paired_bootstrap_permutation_test(diffs, seed=7)
    assert first.ci_low == second.ci_low
    assert first.ci_high == second.ci_high
    assert first.p_value == second.p_value


def test_paired_test_large_consistent_effect_is_significant() -> None:
    # Every item shows the same substantial negative shift -- a real, detectable effect.
    diffs = [-0.3] * 20
    result = paired_bootstrap_permutation_test(diffs, seed=1)
    assert result.ci_high < 0
    assert result.p_value < 0.05


def test_paired_test_rejects_empty_input() -> None:
    with pytest.raises(ValueError, match="at least one paired difference"):
        paired_bootstrap_permutation_test([])


def test_paired_test_single_value_collapses_to_point() -> None:
    result = paired_bootstrap_permutation_test([0.2], seed=1)
    assert result.n_items == 1
    assert result.mean_diff == result.ci_low == result.ci_high == 0.2
    assert result.p_value == 1.0


def test_holm_correction_matches_hand_computed_values() -> None:
    # The exact values reported in the paper (ADR-152), hand-verified: sorted p-values
    # 0.0067, 0.1887, 1.0000 with m=3 -> multipliers 3, 2, 1, then a running max.
    pvalues = {"llama": 1.0000, "gpt-oss": 0.1887, "qwen": 0.0067}
    adjusted = holm_correction(pvalues)
    assert adjusted["qwen"] == pytest.approx(0.0201, abs=1e-4)
    assert adjusted["gpt-oss"] == pytest.approx(0.3774, abs=1e-4)
    assert adjusted["llama"] == pytest.approx(1.0000, abs=1e-4)


def test_holm_correction_is_monotonic_non_decreasing_in_sorted_order() -> None:
    pvalues = {"a": 0.001, "b": 0.5, "c": 0.6, "d": 0.7}
    adjusted = holm_correction(pvalues)
    ordered = sorted(pvalues.items(), key=lambda kv: kv[1])
    values_in_order = [adjusted[name] for name, _ in ordered]
    assert values_in_order == sorted(values_in_order)


def test_holm_correction_never_exceeds_one() -> None:
    pvalues = {"a": 0.9, "b": 0.95, "c": 0.99}
    adjusted = holm_correction(pvalues)
    assert all(v <= 1.0 for v in adjusted.values())


def test_holm_correction_single_pvalue_is_unchanged() -> None:
    adjusted = holm_correction({"only": 0.03})
    assert adjusted["only"] == pytest.approx(0.03)


def test_holm_correction_rejects_empty() -> None:
    with pytest.raises(ValueError, match="at least one p-value"):
        holm_correction({})
