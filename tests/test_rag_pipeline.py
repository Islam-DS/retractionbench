from datetime import datetime

import pytest

from retraction_bench.rag.pipeline import (
    build_post_notice_turn2,
    select_retrieval_naive_documents,
    select_retrieval_with_notice_documents,
)
from retraction_bench.rag.prompts import RenderedDocument
from retraction_bench.schemas import Condition, ModelResponse

QUESTION = "Does drug X reduce mortality in condition Y?"
NOTICE_DOC = RenderedDocument("doc-notice", "Notice: Trial A", "This article has been retracted.")


_DEFAULT_RAW_ANSWER = "ANSWER: Yes.\nCITED_DOCUMENT_IDS: NONE\nCONFIDENCE: high"


def _response(condition: Condition, seed: int, raw_answer_text: str = _DEFAULT_RAW_ANSWER) -> ModelResponse:
    return ModelResponse(
        response_id="resp-1",
        item_id="RB-0001",
        model_identifier="test-model",
        seed=seed,
        condition=condition,
        raw_answer_text=raw_answer_text,
        prompt_template_id="v1",
        temperature=0.0,
        max_tokens=256,
        call_timestamp=datetime(2026, 8, 20, 12, 0, 0),
    )


# --- build_post_notice_turn2's enforced constraints ---


def test_post_notice_accepts_a_matching_no_retrieval_same_seed_response() -> None:
    turn1 = _response(Condition.NO_RETRIEVAL, seed=1)
    prompt = build_post_notice_turn2(turn1, seed=1, notice_doc=NOTICE_DOC, question=QUESTION)
    assert "Yes." in prompt
    assert QUESTION in prompt


def test_post_notice_rejects_wrong_condition_source() -> None:
    turn1 = _response(Condition.RETRIEVAL_NAIVE, seed=1)
    with pytest.raises(ValueError, match="must be a no_retrieval response"):
        build_post_notice_turn2(turn1, seed=1, notice_doc=NOTICE_DOC, question=QUESTION)


def test_post_notice_rejects_retrieval_with_notice_source_too() -> None:
    turn1 = _response(Condition.RETRIEVAL_WITH_NOTICE, seed=1)
    with pytest.raises(ValueError, match="must be a no_retrieval response"):
        build_post_notice_turn2(turn1, seed=1, notice_doc=NOTICE_DOC, question=QUESTION)


def test_post_notice_rejects_mismatched_seed() -> None:
    turn1 = _response(Condition.NO_RETRIEVAL, seed=1)
    with pytest.raises(ValueError, match="identical seed"):
        build_post_notice_turn2(turn1, seed=2, notice_doc=NOTICE_DOC, question=QUESTION)


def test_post_notice_falls_back_to_raw_text_when_turn1_did_not_parse() -> None:
    turn1 = _response(Condition.NO_RETRIEVAL, seed=1, raw_answer_text="unstructured garbled text")
    prompt = build_post_notice_turn2(turn1, seed=1, notice_doc=NOTICE_DOC, question=QUESTION)
    assert "unstructured garbled text" in prompt


# --- select_retrieval_with_notice_documents' injection rule ---


def _docs(n: int) -> list[RenderedDocument]:
    return [RenderedDocument(f"doc-{i}", f"Title {i}", f"Text {i}") for i in range(1, n + 1)]


def test_notice_already_in_top_k_is_left_unchanged() -> None:
    naive = [*_docs(2), NOTICE_DOC, *_docs(2)]  # notice at position 3 of a 5-doc naive list
    result = select_retrieval_with_notice_documents(naive, NOTICE_DOC, k=5)
    assert result == naive[:5]
    assert NOTICE_DOC in result


def test_notice_outside_top_k_replaces_the_last_slot() -> None:
    naive = [*_docs(6)]  # notice not present anywhere in this naive list
    result = select_retrieval_with_notice_documents(naive, NOTICE_DOC, k=5)
    assert len(result) == 5
    assert result[:4] == naive[:4]
    assert result[4] == NOTICE_DOC


def test_notice_none_degenerates_to_plain_naive_top_k_rb0005_case() -> None:
    """RB-0005 has no separate notice document in the corpus at all (verified directly,
    ADR-071/131) -- notice_doc=None must return plain naive top-k unchanged, not raise and not
    fabricate a placeholder notice."""
    naive = _docs(7)
    result = select_retrieval_with_notice_documents(naive, None, k=5)
    assert result == naive[:5]


def test_fewer_naive_docs_than_k_appends_notice_without_evicting() -> None:
    naive = _docs(2)
    result = select_retrieval_with_notice_documents(naive, NOTICE_DOC, k=5)
    # Under capacity (2 < k=5) -- the notice is added, not swapped in place of a real document.
    assert len(result) == 3
    assert result[:2] == naive
    assert result[2] == NOTICE_DOC


# --- select_retrieval_naive_documents' active exclusion rule (ADR-135) ---


def test_notice_in_top_k_is_filtered_and_backfilled_from_beyond_k() -> None:
    ranked = [*_docs(2), NOTICE_DOC, *_docs(4)]  # notice at rank 3; 6 non-notice docs total
    result = select_retrieval_naive_documents(ranked, NOTICE_DOC, k=5)
    assert len(result) == 5
    assert NOTICE_DOC not in result
    # the two docs originally ranked 1-2, then the four ranked 4-7 (post-filter), first five kept
    assert result == [ranked[0], ranked[1], ranked[3], ranked[4], ranked[5]]


def test_notice_outside_top_k_naive_result_is_unaffected() -> None:
    ranked = [*_docs(5), NOTICE_DOC, *_docs(2)]  # notice at rank 6, already outside top-5
    result = select_retrieval_naive_documents(ranked, NOTICE_DOC, k=5)
    assert result == ranked[:5]
    assert NOTICE_DOC not in result


def test_notice_none_degenerates_to_plain_top_k_for_naive_too() -> None:
    """The six items with no verifiable notice document at all (RB-0005 and, as of ADR-133/134,
    RB-0003/RB-0004/RB-0026/RB-0027/RB-0028) have nothing to exclude -- plain top-k, unchanged."""
    ranked = _docs(7)
    result = select_retrieval_naive_documents(ranked, None, k=5)
    assert result == ranked[:5]


def test_naive_and_with_notice_produce_different_document_sets_when_notice_was_in_top_k() -> None:
    """The whole point of ADR-135's redesign: for an item where the notice is naturally in naive
    top-k (ADR-133/134: 100% of items with a genuine notice), retrieval_naive and
    retrieval_with_notice must now differ -- under the old passive definition they were identical.
    """
    ranked = [*_docs(2), NOTICE_DOC, *_docs(4)]
    naive_result = select_retrieval_naive_documents(ranked, NOTICE_DOC, k=5)
    with_notice_result = select_retrieval_with_notice_documents(ranked, NOTICE_DOC, k=5)
    assert NOTICE_DOC not in naive_result
    assert NOTICE_DOC in with_notice_result
    assert naive_result != with_notice_result
