"""The frozen, rule-based "current-evidence-preferring" reranker (recency-only).

Explicitly NOT "supersession-aware": it reads one real, inference-time-available field
(`pub_year`, year-granularity, from `corpus/pub_year_backfill.py`'s lookup) and nothing else.
See the adversarial-flagship-audit and forensic-repository-audit rounds preceding this module
for why the originally-proposed lexical retraction-keyword boost and a document-type signal
were both rejected (the first for targeting the wrong stage; the second because no genuine
document-type field exists anywhere in this corpus, for any document).

--------------------------------------------------------------------------------------------
DESIGN DECISION (frozen before any outcome is examined -- reasoned from the rule's own
structure, never from how it performs on the 15 replacement items):

Four forms were on the table:
  A. strict publication-year descending sort over the WHOLE candidate pool
  B. lexicographic: semantic rank first, publication year second (year as tie-break only)
  C. a fixed additive recency bonus blended into the semantic score
  D. a fixed exponential/linear recency decay blended into the semantic score

A is rejected: applied globally it would discard semantic relevance entirely, surfacing the
single newest document in the pool regardless of topical fit -- scientifically indefensible
on its face, a structural property of the rule, not a result.

B is rejected in its literal form: continuous cosine-similarity scores essentially never tie
exactly, so "year as tie-break" would almost never fire and the rule would degenerate to
plain baseline ranking with no real effect -- also a structural property, not a result.

C and D are rejected: both require picking a bonus magnitude or a decay rate with no
principled way to set it without implicitly tuning against an outcome -- exactly what this
project's standing discipline forbids (no arbitrary hyperparameters, ADR-152's own family-wise
discipline extended here).

**Adopted: a bounded variant of B with the two keys swapped, scoped to the fixed candidate
pool already selected by baseline semantic retrieval.** The candidate pool handed to this
reranker (`RETRIEVAL_POOL_K` documents) is itself already a massive relevance filter (10 out
of 325,167) -- reordering *within* that pool can never admit a document baseline retrieval did
not already consider relevant enough to surface. Within the pool, publication year is used as
the PRIMARY sort key (descending; missing years sort last, see `_SORT_KEY`), with the
document's original semantic rank as the tie-break. This has zero tunable parameters -- no
bonus, no decay rate, nothing to set -- and its effect is real (not a near-null B-style
tie-break) by construction. It cannot be tuned on the 15 replacement items because there is
nothing left to choose once "primary key = year desc, secondary = original rank" is fixed.

A direct, disclosed consequence of this design, stated here rather than discovered after a run:
reordering a fixed pool can only move a document to an earlier OR later position within that
pool -- it can never pull in a document that was not already in the pool, and it therefore
cannot change hit@RETRIEVAL_POOL_K (hit@10, at the current pool size) at all. It can only move
the mass of hits among hit@1 / hit@3 / hit@5. This is a property of the frozen rule, not a
finding from running it.
--------------------------------------------------------------------------------------------

CANDIDATE-POOL DECISION (Phase 4, frozen before any run): RETRIEVAL_POOL_K stays at its
existing value (10, `rag/collect.py`). This reorder-only rule has no mechanism that benefits
from a wider pool -- it cannot surface a document beyond what baseline retrieval already
fetched -- so widening the pool would add a real, disclosed protocol change (more compute, a
different frozen artifact) with no principled benefit tied to this specific rule. Not widened
because results might look better; widened only if a future, different (non-reorder-only)
design specifically needed the extra depth, which would then need its own explicit freeze.

LEAKAGE DISCIPLINE: `CandidateDocument` below carries exactly four fields -- pmid, its semantic
rank and score from baseline retrieval, and its pub_year. It is constructed by
`build_candidate_documents`, the ONLY function in this module that ever touches a raw FAISS
hit dict (which also carries `corpus_role`/`linked_source_registry_id`/`domain` --
`corpus/embed_index.py`'s manifest schema). That function copies across only `pmid`/`score`
and discards everything else; `rerank_by_recency` itself never receives a hit dict at all, by
type, so there is no field to accidentally read even if someone tried -- not merely a
"don't look" convention. `build_candidate_documents` reads `pub_year_lookup`, a plain
pmid -> int|None mapping built entirely from real PubMed data
(`corpus/pub_year_backfill.py`) -- never a `BenchmarkItem`/`SupersededSource`/`Evidence` field.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class CandidateDocument:
    """Everything this reranker is allowed to know about one retrieved document. No
    `corpus_role`, no `linked_source_registry_id`, no title/text, no benchmark-item
    identifiers -- those fields simply do not exist on this type.
    """

    pmid: str
    semantic_rank: int  # 1-indexed position in the baseline FAISS ranking
    semantic_score: float
    pub_year: int | None


def build_candidate_documents(
    hits: list[dict], pub_year_lookup: dict[str, int | None]
) -> list[CandidateDocument]:
    """Adapter boundary: the only place in this module that reads a raw FAISS hit dict
    (as returned by `corpus/embed_index.search`). `hits` must already be in baseline
    semantic-rank order (rank is assigned positionally, not read off the hit). Only `pmid`
    and `score` are copied across; `corpus_role`/`linked_source_registry_id`/`domain`, even
    though present on the input dict, are never read here or anywhere downstream.
    """
    return [
        CandidateDocument(
            pmid=hit["pmid"],
            semantic_rank=rank,
            semantic_score=hit["score"],
            pub_year=pub_year_lookup.get(hit["pmid"]),
        )
        for rank, hit in enumerate(hits, start=1)
    ]


def _sort_key(candidate: CandidateDocument) -> tuple[bool, int, int]:
    """Present years sort before missing ones; among present years, descending; ties broken
    by the original semantic rank, ascending. Pure function of the candidate's own four
    fields -- no external state, no randomness, no hyperparameter.
    """
    has_year = candidate.pub_year is not None
    return (not has_year, -(candidate.pub_year or 0), candidate.semantic_rank)


def rerank_by_recency(candidates: list[CandidateDocument]) -> list[CandidateDocument]:
    """Deterministic lexicographic reorder of a fixed candidate pool. Never changes the set
    of documents, only their order -- see module docstring for why hit@len(candidates) is
    therefore invariant under this rule by construction.
    """
    return sorted(candidates, key=_sort_key)
