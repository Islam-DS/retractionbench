"""Classifier validation metrics: agreement, confusion matrix, precision/recall, Cohen's kappa.

Generic over any set of string class labels -- used to score the claim-type
screen against human hand labels (docs/DECISIONS.md ADR-021), and reusable
for any future heuristic screen that needs the same treatment.
"""

import math
from dataclasses import dataclass, field


def wilson_ci(successes: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """95% Wilson score interval for a binomial proportion (default z=1.96)."""
    if n == 0:
        return (0.0, 0.0)
    phat = successes / n
    denom = 1 + z**2 / n
    center = (phat + z**2 / (2 * n)) / denom
    margin = (z * math.sqrt((phat * (1 - phat) + z**2 / (4 * n)) / n)) / denom
    return (center - margin, center + margin)


@dataclass
class ClassMetrics:
    label: str
    precision: float
    recall: float
    support: int  # count of this label in y_true
    predicted_count: int  # count of this label in y_pred


@dataclass
class ScoringResult:
    n: int
    agreement: int
    agreement_rate: float
    agreement_ci: tuple[float, float]
    confusion: dict[tuple[str, str], int]  # (true, pred) -> count
    per_class: list[ClassMetrics]
    cohens_kappa: float
    labels: list[str] = field(default_factory=list)


def score(y_true: list[str], y_pred: list[str], labels: list[str]) -> ScoringResult:
    """Score y_pred against y_true over the given closed label set."""
    n = len(y_true)
    assert n == len(y_pred)

    confusion = {(t, p): 0 for t in labels for p in labels}
    for t, p in zip(y_true, y_pred, strict=True):
        confusion[(t, p)] += 1

    agreement = sum(confusion[(label_, label_)] for label_ in labels)
    agreement_rate = agreement / n if n else float("nan")
    ci = wilson_ci(agreement, n)

    per_class = []
    for label_ in labels:
        tp = confusion[(label_, label_)]
        fp = sum(confusion[(t, label_)] for t in labels if t != label_)
        fn = sum(confusion[(label_, p)] for p in labels if p != label_)
        support = sum(confusion[(label_, p)] for p in labels)
        predicted_count = sum(confusion[(t, label_)] for t in labels)
        precision = tp / (tp + fp) if (tp + fp) else float("nan")
        recall = tp / (tp + fn) if (tp + fn) else float("nan")
        per_class.append(
            ClassMetrics(
                label=label_, precision=precision, recall=recall, support=support, predicted_count=predicted_count
            )
        )

    po = agreement_rate
    pe = 0.0
    for label_ in labels:
        p_true = sum(confusion[(label_, p)] for p in labels) / n
        p_pred = sum(confusion[(t, label_)] for t in labels) / n
        pe += p_true * p_pred
    kappa = (po - pe) / (1 - pe) if pe != 1 else float("nan")

    return ScoringResult(
        n=n,
        agreement=agreement,
        agreement_rate=agreement_rate,
        agreement_ci=ci,
        confusion=confusion,
        per_class=per_class,
        cohens_kappa=kappa,
        labels=labels,
    )


def committed_accuracy(y_true: list[str], y_pred: list[str], abstain_label: str) -> tuple[int, int]:
    """Accuracy restricted to rows where y_pred != abstain_label. Returns (correct, committed_n)."""
    committed = [(t, p) for t, p in zip(y_true, y_pred, strict=True) if p != abstain_label]
    correct = sum(1 for t, p in committed if t == p)
    return correct, len(committed)


@dataclass
class BinaryMetrics:
    tp: int
    fp: int
    fn: int
    tn: int
    recall: float
    recall_ci: tuple[float, float]
    precision: float
    precision_ci: tuple[float, float]


def binary_recall_precision(y_true: list[str], y_pred: list[str], positive_labels: set[str]) -> BinaryMetrics:
    """Collapse a multi-class problem into positive-vs-rest and score recall/precision with Wilson CIs.

    Used to measure "recall on clinical_intervention + clinical_observational
    combined" for the claim-type screen (ADR-021) -- the screen's actual job
    is a binary pass/exclude decision, not fine-grained classification, so
    that's the number that matters, not per-class recall on the 4-way split.
    """
    tp = fp = fn = tn = 0
    for t, p in zip(y_true, y_pred, strict=True):
        t_pos = t in positive_labels
        p_pos = p in positive_labels
        if t_pos and p_pos:
            tp += 1
        elif t_pos and not p_pos:
            fn += 1
        elif not t_pos and p_pos:
            fp += 1
        else:
            tn += 1

    recall = tp / (tp + fn) if (tp + fn) else float("nan")
    precision = tp / (tp + fp) if (tp + fp) else float("nan")
    recall_ci = wilson_ci(tp, tp + fn) if (tp + fn) else (float("nan"), float("nan"))
    precision_ci = wilson_ci(tp, tp + fp) if (tp + fp) else (float("nan"), float("nan"))

    return BinaryMetrics(
        tp=tp,
        fp=fp,
        fn=fn,
        tn=tn,
        recall=recall,
        recall_ci=recall_ci,
        precision=precision,
        precision_ci=precision_ci,
    )
