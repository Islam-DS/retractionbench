"""Tests for the classifier-validation scoring module, checked against hand-computed values."""

import math

import pytest

from retraction_bench.curate.scoring import binary_recall_precision, committed_accuracy, score, wilson_ci

# Hand-verified fixture: 10 items, 3 classes, worked out on paper alongside the test.
Y_TRUE = ["A", "A", "A", "B", "B", "B", "C", "C", "C", "C"]
Y_PRED = ["A", "A", "B", "B", "B", "C", "C", "C", "C", "A"]
LABELS = ["A", "B", "C"]


def test_agreement_count_and_rate() -> None:
    result = score(Y_TRUE, Y_PRED, LABELS)
    assert result.agreement == 7
    assert result.agreement_rate == pytest.approx(0.7)


def test_cohens_kappa_matches_hand_calculation() -> None:
    result = score(Y_TRUE, Y_PRED, LABELS)
    # po=0.7, pe=0.34 -> kappa = (0.7-0.34)/(1-0.34) = 0.5454...
    assert result.cohens_kappa == pytest.approx(0.545454545, abs=1e-6)


def test_per_class_precision_recall_matches_hand_calculation() -> None:
    result = score(Y_TRUE, Y_PRED, LABELS)
    by_label = {m.label: m for m in result.per_class}

    assert by_label["A"].precision == pytest.approx(2 / 3)
    assert by_label["A"].recall == pytest.approx(2 / 3)
    assert by_label["B"].precision == pytest.approx(2 / 3)
    assert by_label["B"].recall == pytest.approx(2 / 3)
    assert by_label["C"].precision == pytest.approx(0.75)
    assert by_label["C"].recall == pytest.approx(0.75)


def test_perfect_agreement_gives_kappa_one() -> None:
    result = score(Y_TRUE, Y_TRUE, LABELS)
    assert result.agreement == len(Y_TRUE)
    assert result.cohens_kappa == pytest.approx(1.0)


def test_wilson_ci_contains_point_estimate_and_widens_for_small_n() -> None:
    lo_small, hi_small = wilson_ci(7, 10)
    lo_large, hi_large = wilson_ci(700, 1000)
    assert lo_small < 0.7 < hi_small
    assert lo_large < 0.7 < hi_large
    assert (hi_small - lo_small) > (hi_large - lo_large)


def test_committed_accuracy_excludes_abstain_predictions() -> None:
    y_true = ["A", "B", "C", "A"]
    y_pred = ["A", "unclear", "unclear", "B"]
    correct, committed_n = committed_accuracy(y_true, y_pred, abstain_label="unclear")
    assert committed_n == 2  # rows 1 and 4 only
    assert correct == 1  # only row 1 (A/A) is correct; row 4 is A/B


def test_score_confusion_matrix_totals_equal_n() -> None:
    result = score(Y_TRUE, Y_PRED, LABELS)
    assert sum(result.confusion.values()) == len(Y_TRUE)
    assert not math.isnan(result.cohens_kappa)


def test_binary_recall_precision_matches_hand_calculation() -> None:
    # Collapsing A and B into "positive": hand-traced TP=5, FN=1, FP=1, TN=3.
    result = binary_recall_precision(Y_TRUE, Y_PRED, positive_labels={"A", "B"})
    assert (result.tp, result.fp, result.fn, result.tn) == (5, 1, 1, 3)
    assert result.recall == pytest.approx(5 / 6)
    assert result.precision == pytest.approx(5 / 6)
    assert result.recall_ci[0] < result.recall < result.recall_ci[1]
    assert result.precision_ci[0] < result.precision < result.precision_ci[1]


def test_binary_recall_precision_perfect_recall_and_precision() -> None:
    result = binary_recall_precision(Y_TRUE, Y_TRUE, positive_labels={"A", "B"})
    assert result.recall == pytest.approx(1.0)
    assert result.precision == pytest.approx(1.0)
    assert result.fp == 0
    assert result.fn == 0
