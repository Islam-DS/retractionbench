"""Orchestration glue between corpus retrieval, prompts.py's rendering, and rag/cache.py's
resume-safe storage. Owns the constraints the author flagged as load-bearing:
post_notice's turn 1 must come from a same-seed no_retrieval response, retrieval_with_notice's
notice-injection degenerates cleanly (not silently) when an item has no separate notice document
at all (RB-0005-shaped items, ADR-071), and -- as of ADR-135 -- retrieval_naive is an active
notice-exclusion control, not a passive observation, because ADR-134 measured that a passive
no-notice condition does not occur naturally on this corpus: the notice was already present in
naive top-k for 22/22 items that have one at all (100%, ADR-133/134's corrected count).
"""

from retraction_bench.rag.parse import parse_response
from retraction_bench.rag.prompts import RenderedDocument, render_post_notice_turn2_prompt
from retraction_bench.schemas import Condition, ModelResponse


def select_retrieval_naive_documents(
    ranked_docs: list[RenderedDocument],
    notice_doc: RenderedDocument | None,
    k: int = 5,
) -> list[RenderedDocument]:
    """retrieval_naive's document-selection rule (ADR-135, redefined from ADR-131's original
    passive top-k): the item's own supersession notice is actively filtered out of the ranked
    results before taking the top k, so this condition is a genuine no-notice control rather than
    an observation that happens to lack one.

    This redefinition exists because ADR-134's corrected retrieval-ceiling measurement found the
    notice already present in naive top-5 for every one of the 22 items that have a genuine,
    verified notice document (100%, not "usually") -- meaning retrieval_naive and
    retrieval_with_notice, defined the original passive way, were identical prompts for every
    such item, and the "notice absent from retrieval" condition this benchmark's design intended
    to compare against never occurred on its own. `ranked_docs` must be the *full* ranked list
    (not pre-truncated to k), so a filtered-out notice can be backfilled from beyond the original
    top-k rather than shrinking the document count.

    `notice_doc=None` (no verifiable notice document exists for this item at all -- RB-0005 and,
    as of ADR-133/134, RB-0003/RB-0004/RB-0026/RB-0027/RB-0028) means there is nothing to
    exclude: this condition degenerates to plain top-k, identical to what it always was for these
    six items, and callers must not treat that as an error -- excluding a document that was never
    in the corpus is not a meaningful intervention, so these items should be excluded from any
    retrieval_naive-vs-retrieval_with_notice comparison entirely, not silently included as a
    no-op case (see `select_retrieval_with_notice_documents` below and ADR-134's `n=22` framing).
    """
    if notice_doc is None:
        return ranked_docs[:k]
    filtered = [d for d in ranked_docs if d.doc_id != notice_doc.doc_id]
    return filtered[:k]


def select_retrieval_with_notice_documents(
    naive_ranked_docs: list[RenderedDocument],
    notice_doc: RenderedDocument | None,
    k: int = 5,
) -> list[RenderedDocument]:
    """retrieval_with_notice's document-selection rule: take the top-k naive results (the
    *unfiltered* ranking -- this is the one condition that still reflects what a real RAG system
    would retrieve on its own), and guarantee the notice is among them -- if it's already in the
    naive top-k (the common case, ADR-133/134: 100% of the time for items with a genuine notice),
    no change; if not, it replaces the lowest-ranked (k-th) slot so the count stays fixed at k.

    `notice_doc=None` is the RB-0005-shaped case: no separate notice document exists in the
    corpus for this item at all (verified directly against the corpus, ADR-071/131/133/134 -- not
    a retrieval failure at any k). The condition degenerates to plain naive top-k for these items,
    returned unchanged -- callers must not treat this as an error; it is the correct, honest
    behavior for an item with no notice to inject. As of ADR-134, these items should be excluded
    from the retrieval_naive/retrieval_with_notice comparison entirely (n=22), not included as a
    no-op case in either condition.
    """
    top_k = naive_ranked_docs[:k]
    if notice_doc is None:
        return top_k
    if any(d.doc_id == notice_doc.doc_id for d in top_k):
        return top_k
    if len(top_k) < k:
        # Under capacity -- room to add the notice without evicting anything.
        return [*top_k, notice_doc]
    return [*top_k[:-1], notice_doc]


def build_post_notice_turn2(
    turn1_response: ModelResponse,
    seed: int,
    notice_doc: RenderedDocument,
    question: str,
) -> str:
    """Renders post_notice's turn 2, reusing turn1_response (a cached no_retrieval response) as
    the "prior answer" rather than making an independent call.

    Raises if turn1_response isn't a no_retrieval response for the identical seed -- reusing a
    retrieval-condition response would let retrieval quality confound what M3 is trying to
    isolate; reusing a different seed's response would silently mix randomness sources within
    what is supposed to be one seeded run (stats/seeds.py's variance reporting depends on that
    not happening). Both are the author's explicit, load-bearing constraints (ADR-131), enforced
    here rather than left to caller discipline.
    """
    if turn1_response.condition != Condition.NO_RETRIEVAL:
        raise ValueError(
            f"post_notice's turn 1 must be a no_retrieval response; got condition="
            f"{turn1_response.condition!r} for response_id={turn1_response.response_id!r}"
        )
    if turn1_response.seed != seed:
        raise ValueError(
            f"post_notice's turn 1 must use the identical seed ({seed}); got seed="
            f"{turn1_response.seed!r} for response_id={turn1_response.response_id!r}"
        )

    parsed = parse_response(turn1_response.raw_answer_text)
    prior_answer = parsed.answer if parsed.answer is not None else turn1_response.raw_answer_text
    return render_post_notice_turn2_prompt(notice_doc, prior_answer, question)
