import pytest

from eval_fixtures import make_item, make_response, make_result
from retraction_bench.eval.m3 import compute_m3, stratified_m3
from retraction_bench.eval.stratify import by_domain, join_results
from retraction_bench.schemas import Condition, M3Label


def _post_notice_joined(labels: list[str], domain: str = "Pharm"):
    items, responses, results = [], [], []
    for idx, label in enumerate(labels, start=1):
        iid, rid = f"RB-{idx:04d}", f"resp-{idx}"
        items.append(make_item(iid, domain=domain))
        responses.append(make_response(rid, iid, condition=Condition.POST_NOTICE))
        results.append(make_result(f"er-{idx}", rid, iid, condition=Condition.POST_NOTICE, m3_label=label))
    return join_results(results, responses, items)


def test_compute_m3_counts_each_label() -> None:
    joined = _post_notice_joined(["acknowledges", "acknowledges", "defends", "silently_revises"])
    m3 = compute_m3(joined)
    assert m3.n == 4
    assert m3.counts[M3Label.ACKNOWLEDGES] == 2
    assert m3.counts[M3Label.DEFENDS] == 1
    assert m3.counts[M3Label.SILENTLY_REVISES] == 1


def test_compute_m3_rates_sum_to_one() -> None:
    joined = _post_notice_joined(["acknowledges", "defends", "silently_revises", "defends"])
    m3 = compute_m3(joined)
    total = sum(m3.rates.values())
    assert total == pytest.approx(1.0)


def test_compute_m3_each_label_has_a_ci() -> None:
    joined = _post_notice_joined(["acknowledges"] * 5 + ["defends"] * 5)
    m3 = compute_m3(joined)
    for label in M3Label:
        ci = m3.cis[label]
        assert ci.ci_low <= m3.rates[label] <= ci.ci_high


def test_compute_m3_rejects_empty() -> None:
    with pytest.raises(ValueError, match="at least one result"):
        compute_m3([])


def test_compute_m3_rejects_non_post_notice_condition() -> None:
    item = make_item("RB-0001")
    response = make_response("resp-1", "RB-0001", condition=Condition.NO_RETRIEVAL)
    result = make_result("er-1", "resp-1", "RB-0001", condition=Condition.NO_RETRIEVAL)
    joined = join_results([result], [response], [item])

    with pytest.raises(ValueError, match="only defined under Condition.POST_NOTICE"):
        compute_m3(joined)


def test_stratified_m3_filters_to_post_notice_only() -> None:
    post_item = make_item("RB-0001")
    post_response = make_response("resp-1", "RB-0001", condition=Condition.POST_NOTICE)
    post_result = make_result("er-1", "resp-1", "RB-0001", condition=Condition.POST_NOTICE, m3_label="acknowledges")

    other_item = make_item("RB-0002")
    other_response = make_response("resp-2", "RB-0002", condition=Condition.NO_RETRIEVAL)
    other_result = make_result("er-2", "resp-2", "RB-0002", condition=Condition.NO_RETRIEVAL)

    joined = join_results([post_result, other_result], [post_response, other_response], [post_item, other_item])
    strata = stratified_m3(joined, by_domain)

    # Both items share the default domain. Only the post_notice one should survive the filter --
    # a single surviving item is correctly too-thin-to-rate (stats/strata.py), which is itself
    # the evidence the NO_RETRIEVAL item was excluded rather than counted (else n would be 2 and
    # this domain would report a rate rather than fall through to the item-id path).
    domain = post_item.domain
    assert strata[domain].result is None
    assert strata[domain].item_ids_if_too_thin == ["RB-0001"]


def test_stratified_m3_too_thin_reports_item_ids() -> None:
    joined = _post_notice_joined(["acknowledges", "defends"], domain="ThinDomain")
    strata = stratified_m3(joined, by_domain)
    stratum = strata["ThinDomain"]
    assert stratum.result is None
    assert len(stratum.item_ids_if_too_thin) == 2
