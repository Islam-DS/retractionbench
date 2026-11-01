"""M3 -- Correction Following (the project protocol): after a retraction-contaminated answer,
the model is shown the retraction notice directly and re-asked. Scored only under
Condition.POST_NOTICE, into exactly one of acknowledges / silently_revises / defends
(schemas.M3Label) -- the project protocol flags this as the most novel axis and asks for proportionate
care, so each category gets its own bootstrap CI rather than a single collapsed accuracy number.
"""

from collections.abc import Callable
from dataclasses import dataclass

from retraction_bench.eval.stratify import JoinedResult, group_by
from retraction_bench.schemas import Condition, M3Label
from retraction_bench.stats.bootstrap import BootstrapResult, bootstrap_proportion_ci_clustered
from retraction_bench.stats.strata import StratumReliability, StratumSizeCheck, check_stratum_size


@dataclass
class M3Result:
    n: int
    counts: dict[M3Label, int]
    rates: dict[M3Label, float]
    cis: dict[M3Label, BootstrapResult]
    size_check: StratumSizeCheck


def _require_post_notice(joined: list[JoinedResult]) -> None:
    for j in joined:
        if j.result.condition != Condition.POST_NOTICE:
            raise ValueError(
                f"M3 is only defined under Condition.POST_NOTICE; result {j.result.result_id} "
                f"has condition {j.result.condition}"
            )
        if j.result.m3_label is None:
            # Should be unreachable if EvaluationResult's own validator ran, but check anyway --
            # this module must not silently skip a malformed record and understate the denominator.
            raise ValueError(f"result {j.result.result_id} is post_notice but has no m3_label set")


def compute_m3_from_labels(labels: list[M3Label], item_ids: list[str]) -> M3Result:
    """The actual statistic behind M3, decoupled from EvaluationResult/JoinedResult.

    Extracted so a caller with only raw (label, item_id) pairs -- e.g. a reproduction script
    reading `data/human/m3_hand_labels.csv` directly via `data/interim/eval/m3_labeling_key.json`,
    without a fully-populated EvaluationResult for each of the 150 hand-labeled responses
    (EvaluationResult.correctness is a required field this project's evaluation phase only fills
    for a separate, non-overlapping 100-response Correctness sample, so a real EvaluationResult
    for the M3 sample is not honestly constructible without fabricating a correctness label) --
    can call the identical, tested statistic `compute_m3` uses, rather than a second
    reimplementation drifting out of sync with it.

    Each of the three labels gets its own bootstrap proportion CI (label vs. not-label), not a
    single multinomial CI -- three separate, individually interpretable rates, matching how M1's
    single rate is reported, rather than a joint distribution a reader has to decompose
    themselves. Item-clustered, for the same reason as M1 (eval/m1.py's compute_m1 docstring):
    the hand-labeled sample can include more than one seed of the same item, and those responses
    are correlated through the item, not independent draws.
    """
    if not labels:
        raise ValueError("compute_m3_from_labels requires at least one label -- check stratum size before calling")
    if len(labels) != len(item_ids):
        raise ValueError("labels and item_ids must be the same length")
    n = len(labels)
    counts = {label: labels.count(label) for label in M3Label}
    rates = {label: counts[label] / n for label in M3Label}
    cis = {
        label: bootstrap_proportion_ci_clustered([lab == label for lab in labels], item_ids) for label in M3Label
    }
    return M3Result(
        n=n,
        counts=counts,
        rates=rates,
        cis=cis,
        size_check=check_stratum_size(n),
    )


def compute_m3(joined: list[JoinedResult]) -> M3Result:
    """M3 for one already-selected slice of POST_NOTICE results. Thin wrapper around
    `compute_m3_from_labels` -- see that function's docstring for why the CI is item-clustered.
    """
    if not joined:
        raise ValueError("compute_m3 requires at least one result -- check stratum size before calling")
    _require_post_notice(joined)

    labels = [j.result.m3_label for j in joined]
    item_ids = [j.item.item_id for j in joined]
    return compute_m3_from_labels(labels, item_ids)


@dataclass
class M3StratumResult:
    stratum: str
    result: M3Result | None
    item_ids_if_too_thin: list[str]


def stratified_m3(joined: list[JoinedResult], key_fn: Callable[[JoinedResult], str]) -> dict[str, M3StratumResult]:
    """M3 broken out by an arbitrary stratification key, restricted to POST_NOTICE results by
    the same rule as compute_m3. Callers passing a mixed-condition list get a clear error at
    _require_post_notice rather than a quietly wrong denominator.
    """
    post_notice_only = [j for j in joined if j.result.condition == Condition.POST_NOTICE]
    groups = group_by(post_notice_only, key_fn)
    out: dict[str, M3StratumResult] = {}
    for stratum, members in groups.items():
        size_check = check_stratum_size(len(members))
        if size_check.reliability == StratumReliability.TOO_THIN_TO_RATE:
            out[stratum] = M3StratumResult(
                stratum=stratum,
                result=None,
                item_ids_if_too_thin=[j.item.item_id for j in members],
            )
        else:
            out[stratum] = M3StratumResult(stratum=stratum, result=compute_m3(members), item_ids_if_too_thin=[])
    return out
