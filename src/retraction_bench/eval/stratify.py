"""Joining EvaluationResult/ModelResponse/BenchmarkItem records and grouping them for
stratified reporting. ANNOTATION.md and the project protocol both require every reported number
to be broken out by the fields annotated per item (domain, item_type, claim_polarity,
evidence_direction, ...) plus the experimental axes (condition, model, seed) -- this module is
the one place that join and grouping logic lives, so eval/m1.py and eval/m3.py don't each
reimplement it slightly differently.
"""

from collections.abc import Callable
from dataclasses import dataclass

from retraction_bench.schemas import BenchmarkItem, EvaluationResult, ModelResponse


@dataclass
class JoinedResult:
    """One EvaluationResult, joined with the ModelResponse and BenchmarkItem it was scored
    against -- everything a stratification key function needs in one place.
    """

    result: EvaluationResult
    response: ModelResponse
    item: BenchmarkItem


def join_results(
    results: list[EvaluationResult],
    responses: list[ModelResponse],
    items: list[BenchmarkItem],
) -> list[JoinedResult]:
    """Join by response_id/item_id. Raises on any result that can't be joined -- a dangling
    reference is a data bug worth surfacing immediately, not a row to silently drop, since a
    silent drop would understate whatever rate is computed from the survivors.
    """
    responses_by_id = {r.response_id: r for r in responses}
    items_by_id = {i.item_id: i for i in items}

    joined = []
    for result in results:
        response = responses_by_id.get(result.response_id)
        if response is None:
            raise ValueError(f"EvaluationResult {result.result_id} references unknown response_id {result.response_id}")
        item = items_by_id.get(result.item_id)
        if item is None:
            raise ValueError(f"EvaluationResult {result.result_id} references unknown item_id {result.item_id}")
        joined.append(JoinedResult(result=result, response=response, item=item))
    return joined


def group_by(joined: list[JoinedResult], key_fn: Callable[[JoinedResult], str]) -> dict[str, list[JoinedResult]]:
    """Generic single-key grouping. Compose key_fn (e.g. lambda j: f"{by_domain(j)}|{by_model(j)}")
    for multi-way strata -- this function doesn't special-case any particular stratification
    axis, per the project protocol's no-domain-hard-coding rule extended to the eval layer.
    """
    groups: dict[str, list[JoinedResult]] = {}
    for j in joined:
        groups.setdefault(key_fn(j), []).append(j)
    return groups


# Standard stratification keys, named for readability at call sites (e.g.
# group_by(joined, by_domain)) rather than requiring every caller to write the same lambdas.


def by_domain(j: JoinedResult) -> str:
    return j.item.domain


def by_item_type(j: JoinedResult) -> str:
    return str(j.item.item_type)


def by_claim_polarity(j: JoinedResult) -> str:
    return str(j.item.claim_polarity)


def by_evidence_direction(j: JoinedResult) -> str:
    return str(j.item.evidence_direction)


def by_condition(j: JoinedResult) -> str:
    return str(j.result.condition)


def by_model(j: JoinedResult) -> str:
    return j.response.model_identifier


def by_seed(j: JoinedResult) -> str:
    return str(j.response.seed)
