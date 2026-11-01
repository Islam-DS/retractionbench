import pytest

from eval_fixtures import make_item, make_response, make_result
from retraction_bench.eval.stratify import by_condition, by_domain, by_model, group_by, join_results
from retraction_bench.schemas import Condition, ItemType


def test_join_results_links_all_three_records() -> None:
    item = make_item("RB-0001")
    response = make_response("resp-1", "RB-0001")
    result = make_result("er-1", "resp-1", "RB-0001")

    joined = join_results([result], [response], [item])

    assert len(joined) == 1
    assert joined[0].item.item_id == "RB-0001"
    assert joined[0].response.response_id == "resp-1"
    assert joined[0].result.result_id == "er-1"


def test_join_results_raises_on_unknown_response_id() -> None:
    item = make_item("RB-0001")
    result = make_result("er-1", "resp-missing", "RB-0001")

    with pytest.raises(ValueError, match="unknown response_id"):
        join_results([result], [], [item])


def test_join_results_raises_on_unknown_item_id() -> None:
    response = make_response("resp-1", "RB-9999")
    result = make_result("er-1", "resp-1", "RB-9999")

    with pytest.raises(ValueError, match="unknown item_id"):
        join_results([result], [response], [])


def test_group_by_domain() -> None:
    items = [make_item("RB-0001", domain="Pharm"), make_item("RB-0002", domain="ObGyn")]
    responses = [make_response("resp-1", "RB-0001"), make_response("resp-2", "RB-0002")]
    results = [make_result("er-1", "resp-1", "RB-0001"), make_result("er-2", "resp-2", "RB-0002")]

    joined = join_results(results, responses, items)
    groups = group_by(joined, by_domain)

    assert set(groups.keys()) == {"Pharm", "ObGyn"}
    assert len(groups["Pharm"]) == 1


def test_group_by_condition() -> None:
    item = make_item("RB-0001")
    responses = [
        make_response("resp-1", "RB-0001", condition=Condition.NO_RETRIEVAL),
        make_response("resp-2", "RB-0001", condition=Condition.POST_NOTICE),
    ]
    results = [
        make_result("er-1", "resp-1", "RB-0001", condition=Condition.NO_RETRIEVAL),
        make_result("er-2", "resp-2", "RB-0001", condition=Condition.POST_NOTICE, m3_label="acknowledges"),
    ]

    joined = join_results(results, responses, [item])
    groups = group_by(joined, by_condition)

    assert len(groups["no_retrieval"]) == 1
    assert len(groups["post_notice"]) == 1


def test_group_by_model() -> None:
    item = make_item("RB-0001")
    responses = [
        make_response("resp-1", "RB-0001", model_identifier="gpt"),
        make_response("resp-2", "RB-0001", model_identifier="claude"),
    ]
    results = [make_result("er-1", "resp-1", "RB-0001"), make_result("er-2", "resp-2", "RB-0001")]

    joined = join_results(results, responses, [item])
    groups = group_by(joined, by_model)

    assert set(groups.keys()) == {"gpt", "claude"}


def test_make_item_without_current_answer_variant_is_valid() -> None:
    item = make_item("RB-0003", item_type=ItemType.SUPERSEDED_WITHOUT_CURRENT_ANSWER)
    assert item.item_type == ItemType.SUPERSEDED_WITHOUT_CURRENT_ANSWER
