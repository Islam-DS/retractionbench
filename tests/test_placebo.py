from retraction_bench.rag.placebo import select_placebo_documents
from retraction_bench.rag.prompts import RenderedDocument

NOTICE_DOC = RenderedDocument("doc-notice", "Notice: Trial A", "This article has been retracted.")


def _docs(n: int, start: int = 1) -> list[RenderedDocument]:
    """Unique doc_ids across the whole fixture -- real retrieved documents (real pmids) are
    never duplicated, and `select_retrieval_naive_documents` filters by doc_id *value*, not
    list position, so a fixture with colliding ids (e.g. two independently-restarting calls
    both producing "doc-1") would make both copies vanish on exclusion and produce a
    confusing, unrealistic result. Each call here takes an explicit `start` to guarantee
    uniqueness across concatenated segments.
    """
    return [RenderedDocument(f"doc-{i}", f"Title {i}", f"Text {i}") for i in range(start, start + n)]


def test_excludes_the_natural_rank_k_document_not_the_notice() -> None:
    ranked = [*_docs(2), NOTICE_DOC, *_docs(4, start=3)]  # notice at rank 3; 7 unique docs total
    result = select_placebo_documents(ranked, NOTICE_DOC, k=5)
    assert len(result) == 5
    assert NOTICE_DOC in result  # unlike retrieval_naive, the placebo must NOT exclude the notice
    assert ranked[4] not in result  # the doc naturally at rank 5 (index 4) was excluded instead
    assert result == [ranked[0], ranked[1], ranked[2], ranked[3], ranked[5]]


def test_falls_back_to_rank_k_minus_1_when_rank_k_is_the_notice_itself() -> None:
    ranked = [*_docs(4), NOTICE_DOC, *_docs(2, start=5)]  # notice lands exactly at rank 5 == k
    result = select_placebo_documents(ranked, NOTICE_DOC, k=5)
    assert NOTICE_DOC in result  # still not excluded
    assert ranked[3] not in result  # rank 4 (index 3) was excluded instead, via the fallback
    assert len(result) == 5


def test_degenerates_to_plain_top_k_when_fewer_than_k_documents_exist() -> None:
    ranked = _docs(3)
    result = select_placebo_documents(ranked, None, k=5)
    assert result == ranked[:5]


def test_degenerates_to_plain_top_k_when_no_fallback_slot_available_at_k_equals_1() -> None:
    ranked = [NOTICE_DOC, *_docs(3)]  # notice at rank 1 == k, no rank-0 fallback exists
    result = select_placebo_documents(ranked, NOTICE_DOC, k=1)
    assert result == ranked[:1]


def test_placebo_and_naive_exclude_different_documents_for_the_same_input() -> None:
    """The whole point: naive excludes the notice, placebo excludes a fixed position and
    explicitly preserves the notice."""
    from retraction_bench.rag.pipeline import select_retrieval_naive_documents

    ranked = [*_docs(2), NOTICE_DOC, *_docs(4, start=3)]
    naive_result = select_retrieval_naive_documents(ranked, NOTICE_DOC, k=5)
    placebo_result = select_placebo_documents(ranked, NOTICE_DOC, k=5)
    assert NOTICE_DOC not in naive_result
    assert NOTICE_DOC in placebo_result
    assert naive_result != placebo_result


def test_placebo_is_deterministic() -> None:
    ranked = [*_docs(2), NOTICE_DOC, *_docs(4, start=3)]
    first = select_placebo_documents(ranked, NOTICE_DOC, k=5)
    second = select_placebo_documents(ranked, NOTICE_DOC, k=5)
    assert first == second


def test_placebo_selection_reads_no_benchmark_identity_only_position() -> None:
    """Structural check: the function's only inputs are RenderedDocument (doc_id/title/text)
    and an integer k -- there is no corpus_role, linked_source_registry_id, or item_id
    anywhere in its signature or in RenderedDocument itself for it to read."""
    import inspect

    sig = inspect.signature(select_placebo_documents)
    assert set(sig.parameters) == {"ranked_docs", "notice_doc", "k"}
    doc_fields = {f for f in RenderedDocument.__dataclass_fields__}
    assert doc_fields == {"doc_id", "title", "text"}
