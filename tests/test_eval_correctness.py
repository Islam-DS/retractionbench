import pytest

from retraction_bench.eval.correctness import compute_correctness, stratified_correctness
from retraction_bench.schemas import Correctness


def test_compute_correctness_counts_each_label() -> None:
    labels = [Correctness.CORRECT, Correctness.CORRECT, Correctness.INCORRECT, Correctness.REFUSED]
    item_ids = ["RB-0001", "RB-0002", "RB-0003", "RB-0004"]
    result = compute_correctness(labels, item_ids)
    assert result.n == 4
    assert result.counts[Correctness.CORRECT] == 2
    assert result.counts[Correctness.INCORRECT] == 1
    assert result.counts[Correctness.REFUSED] == 1


def test_compute_correctness_rates_sum_to_one() -> None:
    labels = [Correctness.CORRECT, Correctness.INCORRECT, Correctness.REFUSED, Correctness.INCORRECT]
    item_ids = ["RB-0001", "RB-0002", "RB-0003", "RB-0004"]
    result = compute_correctness(labels, item_ids)
    assert sum(result.rates.values()) == pytest.approx(1.0)


def test_compute_correctness_each_label_has_a_ci() -> None:
    labels = [Correctness.CORRECT] * 5 + [Correctness.INCORRECT] * 5
    item_ids = [f"RB-{i:04d}" for i in range(10)]
    result = compute_correctness(labels, item_ids)
    for label in Correctness:
        ci = result.cis[label]
        assert ci.ci_low <= result.rates[label] <= ci.ci_high


def test_compute_correctness_rejects_empty() -> None:
    with pytest.raises(ValueError, match="at least one label"):
        compute_correctness([], [])


def test_compute_correctness_rejects_mismatched_lengths() -> None:
    with pytest.raises(ValueError, match="same length"):
        compute_correctness([Correctness.CORRECT], ["RB-0001", "RB-0002"])


def test_compute_correctness_is_item_clustered_not_response_clustered() -> None:
    # 3 seeds of the same item, perfectly correlated -- item-clustered CI should be wider than
    # treating all 3 as independent responses, exactly the regression this project's bootstrap
    # module itself tests (tests/test_bootstrap.py).
    from retraction_bench.stats.bootstrap import bootstrap_proportion_ci_clustered

    labels = [Correctness.CORRECT] * 3 + [Correctness.INCORRECT] * 3
    item_ids = ["RB-0001"] * 3 + ["RB-0002"] * 3
    result = compute_correctness(labels, item_ids)
    direct = bootstrap_proportion_ci_clustered([lab == Correctness.CORRECT for lab in labels], item_ids)
    assert result.cis[Correctness.CORRECT].ci_low == direct.ci_low
    assert result.cis[Correctness.CORRECT].ci_high == direct.ci_high


def test_stratified_correctness_groups_by_key() -> None:
    rows = [
        (Correctness.CORRECT, "RB-0001"),
        (Correctness.CORRECT, "RB-0002"),
        (Correctness.INCORRECT, "RB-0003"),
        (Correctness.CORRECT, "RB-0004"),
        (Correctness.INCORRECT, "RB-0005"),
        (Correctness.REFUSED, "RB-0006"),
    ]
    domains = {"RB-0001": "A", "RB-0002": "A", "RB-0003": "A", "RB-0004": "A", "RB-0005": "A", "RB-0006": "A"}
    strata = stratified_correctness(rows, key_fn=lambda row: domains[row[1]])
    assert strata["A"].result is not None
    assert strata["A"].result.n == 6


def test_stratified_correctness_too_thin_reports_item_ids() -> None:
    rows = [(Correctness.CORRECT, "RB-0001"), (Correctness.INCORRECT, "RB-0002")]
    strata = stratified_correctness(rows, key_fn=lambda row: "ThinStratum")
    stratum = strata["ThinStratum"]
    assert stratum.result is None
    assert stratum.item_ids_if_too_thin == ["RB-0001", "RB-0002"]
