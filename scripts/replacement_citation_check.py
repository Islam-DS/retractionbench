"""Generation-side replacement-evidence citation check (ADR-164).

`scripts/replacement_retrieval_ceiling.py` (ADR-163) measures only the retrieval half of the
replacement-evidence question: is the correct current evidence findable in the corpus at all.
Two external reviews in a row (the ninth and tenth) named the generation-side half as the natural,
still-missing continuation: when the replacement evidence *is* actually retrieved into a model's
context, does the model go on to cite it?

This is answerable directly from data this project already has cached, with no new model call:
every one of the 900 cached `ModelResponse` records already stores its own actual
`retrieved_document_ids` (the specific top-5 PMIDs shown to the model for that response, not a
theoretical ceiling), and `rag/parse.py`'s `parse_response` already extracts each response's own
`cited_document_ids` from `raw_answer_text` -- the exact same parsing `eval/citation.py` uses for
M1. This script only asks a new question of already-collected answers; it does not generate any
new answer.

Scope: only `retrieval_naive`/`retrieval_with_notice` responses can possibly show a model the
replacement evidence at all (`no_retrieval`/`post_notice` never retrieve anything, matching M1's
own structural-zero scoping in section 4.2); only the 15 items with
`item_type = superseded_with_current_answer` have replacement evidence to look for. Whether the
replacement evidence is even present in a *specific* response's own top-5 retrieved set is itself
a real, disclosed sub-question -- it need not be, even when the corpus-wide ceiling rank is low,
since naive top-5 retrieval is per-query, not guaranteed.

Run with: `uv run python scripts/replacement_citation_check.py` (repo root). No live API call, no
new model generation -- reads only the existing cached response file and hand-verified items.
Writes `results/replacement_citation_check.json` and `.md`.
"""

import csv
import json
from collections import defaultdict
from pathlib import Path

from retraction_bench.curate.benchmark_io import load_items
from retraction_bench.rag.cache import ResponseCache
from retraction_bench.rag.parse import ParseStatus, parse_response
from retraction_bench.schemas import ItemType
from retraction_bench.stats.bootstrap import bootstrap_proportion_ci_clustered

ROOT = Path(__file__).resolve().parent.parent
SCORED_CONDITIONS = {"retrieval_naive", "retrieval_with_notice"}


def main() -> None:
    items = {i.item_id: i for i in load_items() if i.item_type == ItemType.SUPERSEDED_WITH_CURRENT_ANSWER}

    # Which of each item's post_supersession_evidence identifiers actually made it into the
    # corpus (some can fail DOI->PMID resolution at build time; reuse the same replacement
    # retrieval ceiling's own resolved-identifier list rather than re-deriving it, to guarantee
    # the two scripts can never silently disagree about which identifiers are "real").
    ceiling_path = ROOT / "results/replacement_retrieval_ceiling.json"
    ceiling = json.loads(ceiling_path.read_text(encoding="utf-8"))
    resolved_by_item = {
        p["item_id"]: p for p in ceiling["per_item"] if p["status"] == "indexed"
    }

    cache = ResponseCache(ROOT / "data/interim/eval/model_responses.jsonl")
    responses = [r for r in cache.all_responses() if r.condition.value in SCORED_CONDITIONS and r.item_id in items]

    # For matching a response's retrieved_document_ids / cited_document_ids (bare PMIDs) against
    # each item's post_supersession_evidence identifiers, which may be DOIs. The corpus's own
    # linking (corpus/assemble.py) resolves DOI-identifiers to a PMID before indexing, but the
    # PMID it resolved to is not stored back on the BenchmarkItem -- only recoverable from the
    # corpus manifest itself, so this script reads the manifest directly rather than assuming.
    from retraction_bench.corpus.embed_index import load_index

    _, manifest = load_index(ROOT / "data/interim/corpus/index")
    pmid_by_identifier: dict[str, str] = {
        m["linked_source_registry_id"]: m["pmid"]
        for m in manifest
        if m["corpus_role"] == "superseding_evidence"
    }

    rows = []
    for r in responses:
        item = items[r.item_id]
        target_identifiers = {ev.identifier for ev in item.post_supersession_evidence}
        target_pmids = {pmid_by_identifier[i] for i in target_identifiers if i in pmid_by_identifier}
        if not target_pmids:
            continue  # this item's replacement evidence never resolved into the corpus at all

        retrieved_pmids = set(r.retrieved_document_ids or [])
        was_retrieved = bool(target_pmids & retrieved_pmids)

        parsed = parse_response(r.raw_answer_text)
        if parsed.parse_status != ParseStatus.PARSED:
            continue  # matches M1's own convention: excluded from the denominator, not counted either way

        cited_pmids = set(parsed.cited_document_ids or [])
        was_cited = bool(target_pmids & cited_pmids)

        rows.append(
            {
                "response_id": r.response_id,
                "item_id": r.item_id,
                "model": r.model_identifier,
                "condition": r.condition.value,
                "replacement_retrieved_in_this_response": was_retrieved,
                "replacement_cited": was_cited if was_retrieved else None,
            }
        )

    n_total = len(rows)
    n_retrieved = sum(1 for x in rows if x["replacement_retrieved_in_this_response"])
    n_cited_given_retrieved = sum(1 for x in rows if x["replacement_retrieved_in_this_response"] and x["replacement_cited"])

    by_item = defaultdict(lambda: {"retrieved": 0, "cited": 0, "total": 0})
    for x in rows:
        by_item[x["item_id"]]["total"] += 1
        if x["replacement_retrieved_in_this_response"]:
            by_item[x["item_id"]]["retrieved"] += 1
            if x["replacement_cited"]:
                by_item[x["item_id"]]["cited"] += 1

    # Item-clustered CI on citation-given-retrieval, not a naive per-response bootstrap: the 126
    # "retrieved" responses are not 126 independent opportunities -- they are repeated generations
    # (3 models x 3 seeds x up to 2 conditions) over only the 7 items where replacement evidence
    # happens to rank in the naive top-5 at all, since retrieval is fixed per item and only
    # generation varies by seed/model/condition. Matches this project's own standing discipline
    # (bootstrap.py's module docstring; ADR-151) rather than treating responses as independent.
    retrieved_rows = [x for x in rows if x["replacement_retrieved_in_this_response"]]
    citation_ci = bootstrap_proportion_ci_clustered(
        successes=[bool(x["replacement_cited"]) for x in retrieved_rows],
        cluster_ids=[x["item_id"] for x in retrieved_rows],
    )
    n_items_retrieved_in = len({x["item_id"] for x in retrieved_rows})

    report = {
        "n_responses_scored": n_total,
        "n_responses_with_replacement_actually_retrieved": n_retrieved,
        "n_of_those_where_model_cited_replacement": n_cited_given_retrieved,
        "citation_rate_given_retrieved": (n_cited_given_retrieved / n_retrieved) if n_retrieved else None,
        "citation_rate_given_retrieved_item_clustered_ci": {
            "point_estimate": citation_ci.point_estimate,
            "ci_low": citation_ci.ci_low,
            "ci_high": citation_ci.ci_high,
            "n_responses": citation_ci.n,
            "n_items": n_items_retrieved_in,
        },
        "n_items_with_resolved_replacement": len(resolved_by_item),
        "per_item": {k: v for k, v in sorted(by_item.items())},
        "rows": rows,
    }
    out_json = ROOT / "results/replacement_citation_check.json"
    out_json.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"wrote {out_json}")

    lines = [
        "# Generation-side replacement-evidence citation check (exploratory, no new model calls)",
        "",
        f"Responses scored (retrieval_naive/retrieval_with_notice, parsed, items with resolved replacement evidence): {n_total}",
        f"Responses where the replacement evidence was actually present in that response's own top-5 retrieved set: {n_retrieved}",
        f"Of those, responses where the model's answer cited the replacement evidence: {n_cited_given_retrieved}",
        "",
        f"**Citation rate given retrieval: {report['citation_rate_given_retrieved']:.3f}**" if report["citation_rate_given_retrieved"] is not None else "**Citation rate given retrieval: n/a (denominator is zero)**",
        "",
        f"**Item-clustered 95% CI: [{citation_ci.ci_low:.3f}, {citation_ci.ci_high:.3f}]** (n={citation_ci.n} responses "
        f"clustered over only {n_items_retrieved_in} items, not {citation_ci.n} independent draws -- retrieval is fixed "
        f"per item, so responses sharing an item are correlated, not independent observations).",
        "",
        "## Per-item breakdown",
        "",
        "| Item | Total scored | Replacement retrieved (of total) | Replacement cited (of retrieved) |",
        "|---|---|---|---|",
    ]
    for item_id, v in sorted(by_item.items()):
        lines.append(f"| {item_id} | {v['total']} | {v['retrieved']} | {v['cited']} |")

    out_md = ROOT / "results/replacement_citation_check.md"
    out_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {out_md}")


if __name__ == "__main__":
    main()
