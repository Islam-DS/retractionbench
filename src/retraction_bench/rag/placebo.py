"""The gold-label-free placebo condition (Phase 8 of the PE1 infrastructure build).

Rejects the previously-proposed "lowest-ranked non-notice, non-trap document" placebo: "non-
trap" requires knowing which document IS the trap source for a given item -- that is
`corpus_role`/`linked_source_registry_id` knowledge (`corpus/assemble.py`), exactly the gold-
label leakage this project's reranker discipline forbids. A real retriever never knows this.

**Why the design below is gold-label-free:** `select_retrieval_naive_documents`
(`rag/pipeline.py`) has no notice-specific logic at all -- it excludes whatever
`RenderedDocument` is passed as its `notice_doc` argument from the ranked list, then backfills
from beyond the original top-k. The placebo below calls that exact, unmodified, already-tested
function, but targets **a fixed position in the baseline ranking** (the natural rank-k slot)
instead of the real notice. Choosing "rank k" uses only information the baseline retriever
already produced for every query, for every item, with no concept of trap/notice/replacement
anywhere in the selection rule -- it is a pure positional rule, not a judgment about document
identity. The one-slot fallback (if rank k happens to coincide with the real notice's own
position) is itself positional (move to rank k-1), not identity-based: it does not ask "is
this the trap source" or read `corpus_role`, only "is this the same object as `notice_doc`",
the one piece of information the pipeline already legitimately has (which document it is about
to inject as the notice) and that is not benchmark-item-specific bookkeeping.

Not run against any outcome in this round -- see module docstring in
`scripts/pe1_replacement_retrieval_rerank.py` and the Phase 10 report.
"""

from retraction_bench.rag.pipeline import select_retrieval_naive_documents
from retraction_bench.rag.prompts import RenderedDocument


def select_placebo_documents(
    ranked_docs: list[RenderedDocument],
    notice_doc: RenderedDocument | None,
    k: int = 5,
) -> list[RenderedDocument]:
    """Excludes the document naturally occupying rank k in the unfiltered baseline ranking
    (backfilling from beyond k, via `select_retrieval_naive_documents`'s existing mechanism)
    instead of excluding the real notice. If that slot happens to be the notice itself, falls
    back to rank k-1 -- a positional tie-break, not a judgment about which document is "safe"
    to exclude. Degenerates to plain top-k, unchanged, when the ranked list has fewer than k
    documents at all (nothing to exclude or backfill), matching `rag/pipeline.py`'s own
    degenerate-case convention.
    """
    if len(ranked_docs) < k:
        return ranked_docs[:k]

    target = ranked_docs[k - 1]
    if notice_doc is not None and target.doc_id == notice_doc.doc_id:
        if k - 2 >= 0:
            target = ranked_docs[k - 2]
        else:
            return ranked_docs[:k]  # no neighboring fallback available; degenerate to plain top-k

    return select_retrieval_naive_documents(ranked_docs, notice_doc=target, k=k)
