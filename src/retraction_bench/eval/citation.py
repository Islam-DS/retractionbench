"""Whether a model's response cites the trap source -- M1's actual input signal (ADR-153).

Extracted into committed, tested code because this logic previously existed only inside an
uncommitted scratch script used to compute every M1 number reported in the paper: parsing
`raw_answer_text` and checking whether the trap source's PMID appears among the cited document
IDs is exactly what an `EvaluationResult.cited_superseded_ids` field is supposed to hold, but
nothing in this repository ever populated that field for the real 900-response run (there is no
production code path that turns a raw `ModelResponse` into an `EvaluationResult`), so `eval/m1.py`
's `compute_m1` was, until this module existed, tested against synthetic fixtures only, and never
actually run end-to-end against `data/interim/eval/model_responses.jsonl`.
"""

from retraction_bench.rag.parse import ParseStatus, parse_response
from retraction_bench.schemas import BenchmarkItem, ModelResponse, SupersededSource


def trap_source_pmid(item: BenchmarkItem, sources_by_id: dict[str, SupersededSource]) -> str | None:
    """The PMID of the item's primary trap source (its first `supporting_sources` entry) --
    matching this benchmark's construction convention (`docs/CORPUS_PLAN.md`) that a benchmark
    item's trap source is the retracted study a candidate answer would cite if it relied on the
    superseded finding. Returns None if that source has no PMID recorded in `external_ids`
    (rare, but not assumed impossible -- a caller checking `is None` should exclude that item
    from citation scoring rather than crash).
    """
    if not item.supporting_sources:
        return None
    source = sources_by_id.get(item.supporting_sources[0])
    if source is None:
        return None
    return source.external_ids.get("pmid")


def cites_trap_source(
    response: ModelResponse, item: BenchmarkItem, sources_by_id: dict[str, SupersededSource]
) -> bool | None:
    """M1's per-response outcome, computed directly from the raw cached response: did the parsed
    answer cite the item's trap-source PMID. Returns None (not False) when the response did not
    parse (`ParseStatus.PARSED` required) -- matching `eval/m1.py`'s own documented refusal to
    fold "did not parse" into either a citation or a non-citation outcome, so a caller must
    explicitly decide how to handle None rather than have it silently count as a non-citation.
    """
    parsed = parse_response(response.raw_answer_text)
    if parsed.parse_status != ParseStatus.PARSED:
        return None
    pmid = trap_source_pmid(item, sources_by_id)
    if pmid is None:
        return None
    return pmid in (parsed.cited_document_ids or [])
