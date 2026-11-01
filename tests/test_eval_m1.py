import pytest

from eval_fixtures import make_item, make_response, make_result
from retraction_bench.eval.m1 import cites_superseded, compute_m1, stratified_m1
from retraction_bench.eval.stratify import by_domain, join_results
from retraction_bench.stats.strata import StratumReliability


def _joined(n_cite: int, n_not_cite: int, domain: str = "Pharm"):
    items, responses, results = [], [], []
    idx = 0
    for _ in range(n_cite):
        idx += 1
        iid, rid = f"RB-{idx:04d}", f"resp-{idx}"
        items.append(make_item(iid, domain=domain))
        responses.append(make_response(rid, iid))
        results.append(make_result(f"er-{idx}", rid, iid, cited_superseded_ids=["rw-1"]))
    for _ in range(n_not_cite):
        idx += 1
        iid, rid = f"RB-{idx:04d}", f"resp-{idx}"
        items.append(make_item(iid, domain=domain))
        responses.append(make_response(rid, iid))
        results.append(make_result(f"er-{idx}", rid, iid, cited_superseded_ids=[]))
    return join_results(results, responses, items)


def test_cites_superseded_true_when_ids_present() -> None:
    item = make_item("RB-0001")
    response = make_response("resp-1", "RB-0001")
    result = make_result("er-1", "resp-1", "RB-0001", cited_superseded_ids=["rw-1"])
    joined = join_results([result], [response], [item])
    assert cites_superseded(joined[0]) is True


def test_cites_superseded_false_when_no_ids() -> None:
    item = make_item("RB-0001")
    response = make_response("resp-1", "RB-0001")
    result = make_result("er-1", "resp-1", "RB-0001", cited_superseded_ids=[])
    joined = join_results([result], [response], [item])
    assert cites_superseded(joined[0]) is False


def test_compute_m1_rate_is_fraction_citing() -> None:
    joined = _joined(n_cite=3, n_not_cite=7)
    m1 = compute_m1(joined)
    assert m1.n == 10
    assert m1.rate == pytest.approx(0.3)


def test_compute_m1_rejects_empty() -> None:
    with pytest.raises(ValueError, match="at least one result"):
        compute_m1([])


def test_compute_m1_reports_reliable_size_check_at_n10() -> None:
    joined = _joined(n_cite=5, n_not_cite=5)
    m1 = compute_m1(joined)
    assert m1.size_check.reliability == StratumReliability.RELIABLE


def test_stratified_m1_too_thin_stratum_reports_item_ids_not_a_rate() -> None:
    joined = _joined(n_cite=1, n_not_cite=2, domain="ThinDomain")
    strata = stratified_m1(joined, by_domain)
    stratum = strata["ThinDomain"]
    assert stratum.result is None
    assert len(stratum.item_ids_if_too_thin) == 3


def test_stratified_m1_reliable_stratum_reports_a_rate() -> None:
    joined = _joined(n_cite=5, n_not_cite=5, domain="BigDomain")
    strata = stratified_m1(joined, by_domain)
    stratum = strata["BigDomain"]
    assert stratum.result is not None
    assert stratum.result.rate == pytest.approx(0.5)
    assert stratum.item_ids_if_too_thin == []


def test_stratified_m1_all_cite_gives_rate_one() -> None:
    joined = _joined(n_cite=10, n_not_cite=0)
    m1 = compute_m1(joined)
    assert m1.rate == 1.0
