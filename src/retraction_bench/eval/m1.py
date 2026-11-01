"""M1 -- Retraction Citation Rate (the project protocol): strictly the proportion of answers that
explicitly cite a retracted publication's document ID, not a broader claim about the answer
relying on that source's content without naming it. Applies uniformly across item_type,
condition, model, and seed -- a model can cite a retracted source whether or not current evidence
exists to replace it, so nothing here filters by item_type the way M3 filters by condition.
"""

from collections.abc import Callable
from dataclasses import dataclass

from retraction_bench.eval.stratify import JoinedResult, group_by
from retraction_bench.stats.bootstrap import BootstrapResult, bootstrap_proportion_ci_clustered
from retraction_bench.stats.strata import StratumReliability, StratumSizeCheck, check_stratum_size


def cites_superseded(j: JoinedResult) -> bool:
    """A single response's M1 outcome: did it cite/rely on any superseded source at all."""
    return len(j.result.cited_superseded_ids) > 0


@dataclass
class M1Result:
    n: int
    rate: float
    ci: BootstrapResult
    size_check: StratumSizeCheck


def compute_m1_from_outcomes(outcomes: list[bool], item_ids: list[str]) -> M1Result:
    """The actual statistic behind M1, decoupled from EvaluationResult/JoinedResult.

    Extracted so a caller with only raw (outcome, item_id) pairs -- e.g. a reproduction script
    scoring `data/interim/eval/model_responses.jsonl` directly via `eval/citation.py`, without a
    fully-populated EvaluationResult for every one of the 900 responses (EvaluationResult.
    correctness is a required field this project's evaluation phase only fills for a 100-response
    hand-labeled subset, so building a real EvaluationResult for the other 800 is not honestly
    possible without fabricating a correctness label) -- can call the identical, tested statistic
    `compute_m1` uses, rather than a second reimplementation drifting out of sync with it.

    The CI is an item-clustered bootstrap, not a per-response one, and this is load-bearing, not
    a style choice: every slice this function scores contains up to 3 seeds of the same benchmark
    item, and those 3 responses are correlated with each other through whatever makes that
    specific item easy or hard for a model -- they are not 3 independent draws. Resampling
    individual responses (this module's original implementation, caught during external review)
    treats them as if they were, which understates the true sampling uncertainty: on this
    project's own data, item-clustered CI widths for the headline M1 numbers are roughly double
    the (wrong) per-response widths. `n` below is still the response count, since that is the
    real number of responses scored -- only the CI's resampling unit changed.

    Raises on an empty slice: an empty stratum has no rate to report, matching
    stats/bootstrap.py's own refusal to fabricate a CI for zero data.
    """
    if not outcomes:
        raise ValueError("compute_m1_from_outcomes requires at least one outcome -- check stratum size before calling")
    if len(outcomes) != len(item_ids):
        raise ValueError("outcomes and item_ids must be the same length")
    ci = bootstrap_proportion_ci_clustered(outcomes, item_ids)
    return M1Result(
        n=len(outcomes),
        rate=sum(outcomes) / len(outcomes),
        ci=ci,
        size_check=check_stratum_size(len(outcomes)),
    )


def compute_m1(joined: list[JoinedResult]) -> M1Result:
    """M1 for one already-selected slice of results (e.g. one condition, one model, one domain --
    slicing is the caller's job via eval/stratify.py's group_by, this function just scores
    whatever list it's given). Thin wrapper around `compute_m1_from_outcomes` -- see that
    function's docstring for why the CI is item-clustered.

    Callers computing a full stratified breakdown should check stratum size (stats/strata.py)
    before calling this, exactly as stratified_m1 below does.
    """
    if not joined:
        raise ValueError("compute_m1 requires at least one result -- check stratum size before calling")
    outcomes = [cites_superseded(j) for j in joined]
    item_ids = [j.item.item_id for j in joined]
    return compute_m1_from_outcomes(outcomes, item_ids)


@dataclass
class M1StratumResult:
    stratum: str
    result: M1Result | None  # None iff too_thin_to_rate -- see item_ids_if_too_thin instead
    item_ids_if_too_thin: list[str]  # populated iff result is None, for individual reporting


def stratified_m1(joined: list[JoinedResult], key_fn: Callable[[JoinedResult], str]) -> dict[str, M1StratumResult]:
    """M1 broken out by an arbitrary stratification key (eval/stratify.py's by_domain,
    by_item_type, etc., or a composed multi-way key). Strata below stats/strata.py's
    MIN_ITEMIZE_N threshold are reported as a list of item_ids instead of a rate -- the project protocol's
    own annotation-phase practice (docs/DECISIONS.md ADR-099/101/102) applied to the evaluation
    phase: below 5 items, name them, don't average them into a number nobody should trust.
    """
    groups = group_by(joined, key_fn)
    out: dict[str, M1StratumResult] = {}
    for stratum, members in groups.items():
        size_check = check_stratum_size(len(members))
        if size_check.reliability == StratumReliability.TOO_THIN_TO_RATE:
            out[stratum] = M1StratumResult(
                stratum=stratum,
                result=None,
                item_ids_if_too_thin=[j.item.item_id for j in members],
            )
        else:
            out[stratum] = M1StratumResult(stratum=stratum, result=compute_m1(members), item_ids_if_too_thin=[])
    return out
