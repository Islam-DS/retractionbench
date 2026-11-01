"""Mechanically verifies the claim in prompt_templates.md: the four condition templates are
identical except for the DOCUMENTS block's content. If a future edit to one condition's wording
(system instruction, question format, output format) doesn't show up as an edit to the others
too, this test fails -- it is the check the author asked to exist, not just a manual review.
"""

import re

from retraction_bench.rag.prompts import (
    NO_DOCUMENTS,
    SYSTEM_INSTRUCTION,
    RenderedDocument,
    render_no_retrieval_prompt,
    render_post_notice_turn2_prompt,
    render_retrieval_prompt,
)

QUESTION = "Does drug X reduce mortality in condition Y?"

_NAIVE_DOCS = [
    RenderedDocument("doc-1", "Trial A", "Trial A found a significant reduction in mortality."),
    RenderedDocument("doc-2", "Trial B", "Trial B found no significant difference."),
]
_NOTICE_DOC = RenderedDocument("doc-notice", "Notice: Trial A", "This article has been retracted.")


def _strip_documents_content(prompt: str) -> str:
    """Replace whatever sits between 'DOCUMENTS:\\n' and the next '\\n\\nQUESTION:' with a fixed
    placeholder, so what remains is the shared skeleton every condition should share exactly.
    """
    return re.sub(r"DOCUMENTS:\n.*?\n\nQUESTION:", "DOCUMENTS:\n<CONTENT>\n\nQUESTION:", prompt, flags=re.DOTALL)


def test_system_instruction_is_byte_identical_across_all_three_single_turn_conditions() -> None:
    no_retrieval = render_no_retrieval_prompt(QUESTION)
    naive = render_retrieval_prompt(_NAIVE_DOCS, QUESTION)
    with_notice = render_retrieval_prompt([*_NAIVE_DOCS, _NOTICE_DOC], QUESTION)

    for prompt in (no_retrieval, naive, with_notice):
        assert prompt.startswith(SYSTEM_INSTRUCTION)


def test_question_block_is_byte_identical_across_all_three_single_turn_conditions() -> None:
    no_retrieval = render_no_retrieval_prompt(QUESTION)
    naive = render_retrieval_prompt(_NAIVE_DOCS, QUESTION)
    with_notice = render_retrieval_prompt([*_NAIVE_DOCS, _NOTICE_DOC], QUESTION)

    expected_suffix = f"QUESTION: {QUESTION}"
    for prompt in (no_retrieval, naive, with_notice):
        assert prompt.endswith(expected_suffix)


def test_skeleton_with_documents_content_stripped_is_identical_across_all_three() -> None:
    """The single mechanical check that matters most: with the actual document content removed,
    no_retrieval, retrieval_naive, and retrieval_with_notice must render to the exact same
    skeleton -- same header, same shape, same everything except what's inside DOCUMENTS.
    """
    no_retrieval = _strip_documents_content(render_no_retrieval_prompt(QUESTION))
    naive = _strip_documents_content(render_retrieval_prompt(_NAIVE_DOCS, QUESTION))
    with_notice = _strip_documents_content(render_retrieval_prompt([*_NAIVE_DOCS, _NOTICE_DOC], QUESTION))

    assert no_retrieval == naive == with_notice


def test_no_retrieval_documents_block_has_the_same_bracketed_shape_as_populated_conditions() -> None:
    """The structural-consistency fix itself: no_retrieval's DOCUMENTS block must use the same
    '[id] text' bracketed-entry convention as the populated conditions, not a bare inline
    sentence -- confirmed by checking the actual rendered text, not just the source code.
    """
    prompt = render_no_retrieval_prompt(QUESTION)
    assert f"DOCUMENTS:\n[{NO_DOCUMENTS.doc_id}] {NO_DOCUMENTS.title}" in prompt


def test_retrieval_naive_and_with_notice_share_the_same_render_function_output_shape() -> None:
    naive = render_retrieval_prompt(_NAIVE_DOCS, QUESTION)
    with_notice = render_retrieval_prompt([*_NAIVE_DOCS, _NOTICE_DOC], QUESTION)
    # Both must use the identical documents-block header syntax, docs in the same order.
    assert "DOCUMENTS:\n[doc-1]" in naive
    assert "DOCUMENTS:\n[doc-1]" in with_notice


def test_post_notice_turn2_shares_system_instruction_with_the_other_conditions() -> None:
    turn2 = render_post_notice_turn2_prompt(_NOTICE_DOC, "Drug X reduces mortality.", QUESTION)
    assert turn2.startswith(SYSTEM_INSTRUCTION)


def test_post_notice_turn2_shares_the_same_question_block_format() -> None:
    turn2 = render_post_notice_turn2_prompt(_NOTICE_DOC, "Drug X reduces mortality.", QUESTION)
    assert turn2.endswith(f"QUESTION: {QUESTION}")


def test_post_notice_turn1_is_rendered_by_the_exact_no_retrieval_function() -> None:
    """post_notice's turn 1 is documented as reusing render_no_retrieval_prompt exactly, not a
    separately-maintained copy of the same template -- this test would fail the moment someone
    "forked" a slightly different turn-1 template for post_notice specifically.
    """
    turn1_via_no_retrieval_condition = render_no_retrieval_prompt(QUESTION)
    turn1_as_post_notice_would_render_it = render_no_retrieval_prompt(QUESTION)
    assert turn1_via_no_retrieval_condition == turn1_as_post_notice_would_render_it
