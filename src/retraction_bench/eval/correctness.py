"""Correctness -- whether an answer's substantive claim matches the current, verified gold
answer (`schemas.Correctness`: correct / incorrect / refused), scored across all four conditions,
not gated on citation the way M1 is (`docs/CORRECTNESS_RUBRIC.md`).

Per this project's standing rule against LLM-generated ground truth (the project protocol), the
author's own hand-scored labels (`data/human/correctness_hand_labels.csv`, 100 responses) are the
ground truth for this axis. This module was added to close a real reproducibility gap (ADR-153):
`compute_m1`/`compute_m3` (eval/m1.py, eval/m3.py) had a committed, tested implementation from the
start, but Correctness -- one of this paper's three headline metrics -- did not, and its numbers
were computed by an uncommitted, one-off script for the entire duration of this project until now.

No EvaluationResult-based `compute_correctness(joined: list[JoinedResult])` variant is provided
here, unlike M1/M3's `_from_...` + JoinedResult-wrapper pattern: EvaluationResult.correctness is
a required field, but only these 100 of 900 responses were ever hand-scored, so a real
EvaluationResult cannot be honestly constructed for the other 800 without fabricating a label.
This module's functions operate directly on (label, item_id) pairs instead, matching exactly what
`data/human/correctness_hand_labels.csv` plus `data/interim/eval/correctness_labeling_key.json`'s
card_id -> item_id mapping actually provide.
"""

from collections.abc import Callable
from dataclasses import dataclass

from retraction_bench.schemas import Correctness
from retraction_bench.stats.bootstrap import BootstrapResult, bootstrap_proportion_ci_clustered
from retraction_bench.stats.strata import StratumReliability, StratumSizeCheck, check_stratum_size


@dataclass
class CorrectnessResult:
    n: int
    counts: dict[Correctness, int]
    rates: dict[Correctness, float]
    cis: dict[Correctness, BootstrapResult]
    size_check: StratumSizeCheck


def compute_correctness(labels: list[Correctness], item_ids: list[str]) -> CorrectnessResult:
    """Correctness for one already-selected slice of hand-labeled responses. Each of the three
    outcomes gets its own item-clustered bootstrap proportion CI (label vs. not-label), the same
    convention M3 uses (eval/m3.py's compute_m3_from_labels) and for the same reason: several of
    the 100 hand-labeled responses share a benchmark item across seeds, and those responses are
    correlated through the item, not independent draws.
    """
    if not labels:
        raise ValueError("compute_correctness requires at least one label -- check stratum size before calling")
    if len(labels) != len(item_ids):
        raise ValueError("labels and item_ids must be the same length")
    n = len(labels)
    counts = {label: labels.count(label) for label in Correctness}
    rates = {label: counts[label] / n for label in Correctness}
    cis = {
        label: bootstrap_proportion_ci_clustered([lab == label for lab in labels], item_ids) for label in Correctness
    }
    return CorrectnessResult(
        n=n,
        counts=counts,
        rates=rates,
        cis=cis,
        size_check=check_stratum_size(n),
    )


@dataclass
class CorrectnessStratumResult:
    stratum: str
    result: CorrectnessResult | None
    item_ids_if_too_thin: list[str]


def stratified_correctness(
    rows: list[tuple[Correctness, str]],
    key_fn: Callable[[tuple[Correctness, str]], str],
) -> dict[str, CorrectnessStratumResult]:
    """Correctness broken out by an arbitrary stratification key over (label, item_id) rows --
    callers pass whatever extra context `key_fn` needs already zipped into a wider tuple type if
    the two-element form here isn't enough (e.g. (label, item_id, model) for a by-model split);
    this function only relies on position 0 being the label and position 1 being the item_id for
    the size check's item_ids_if_too_thin reporting, matching stratified_m1/stratified_m3's own
    below-threshold-then-itemize convention (stats/strata.py's MIN_ITEMIZE_N).
    """
    groups: dict[str, list[tuple[Correctness, str]]] = {}
    for row in rows:
        groups.setdefault(key_fn(row), []).append(row)

    out: dict[str, CorrectnessStratumResult] = {}
    for stratum, members in groups.items():
        size_check = check_stratum_size(len(members))
        if size_check.reliability == StratumReliability.TOO_THIN_TO_RATE:
            out[stratum] = CorrectnessStratumResult(
                stratum=stratum,
                result=None,
                item_ids_if_too_thin=[item_id for _label, item_id in members],
            )
        else:
            labels = [label for label, _item_id in members]
            item_ids = [item_id for _label, item_id in members]
            out[stratum] = CorrectnessStratumResult(
                stratum=stratum,
                result=compute_correctness(labels, item_ids),
                item_ids_if_too_thin=[],
            )
    return out
