"""Exploratory M1 x Correctness contingency analysis (ADR-157).

A third external review asked whether the 100 hand-labeled Correctness responses could support a
direct cross-tabulation against M1's citation outcome, rather than only the separate marginal
rates already reported in sections 4.2 and 4.3. They can: `data/human/correctness_hand_labels.csv`
and `data/interim/eval/correctness_labeling_key.json` name the exact `response_id` for each of the
100 hand-labeled responses, and `eval.citation.cites_trap_source` (the same function
`reproduce.py` uses for every M1 number in the paper) can be computed for those same 100 responses
directly from the cached run -- no new annotation, no new model call, nothing invented.

Scope, stated up front and in the paper: `cites_trap_source` is only a real (non-structural)
measurement under `retrieval_naive`/`retrieval_with_notice`, since `no_retrieval`/`post_notice`
never show the model a document to cite (section 4.2). The contingency table below is therefore
restricted to the 50 hand-labeled responses under those two conditions (25 each, per the labeling
sample's own even split across conditions) -- pooling in the other 50 structural non-citations
would inflate the "does not cite" row with responses that were never able to cite in the first
place, exactly the "no source found" vs. "no evidence exists" conflation this project's own
standing rules prohibit elsewhere.

This is exploratory, small-n (n=50), and reported as such: it is not one of this paper's three
prespecified confirmatory hypotheses, and no claim here is treated as confirmatory evidence.

Run with: `python scripts/correctness_citation_contingency.py` (repo root, `uv run` prefix
optional). No live API call. Writes `results/correctness_citation_contingency.json` and `.md`.
"""

import csv
import json
from pathlib import Path

from scipy.stats import fisher_exact

from retraction_bench.curate.benchmark_io import load_items, load_sources
from retraction_bench.eval.citation import cites_trap_source
from retraction_bench.rag.cache import ResponseCache

ROOT = Path(__file__).resolve().parent.parent
SCORED_CONDITIONS = {"retrieval_naive", "retrieval_with_notice"}


def cramers_v(table: list[list[int]]) -> float:
    """2x2 Cramer's V, computed directly from the contingency table's own chi-square statistic
    (no scipy chi2_contingency dependency needed for a 2x2 table -- the closed form is exact)."""
    n = sum(sum(row) for row in table)
    (a, b), (c, d) = table
    row1, row2 = a + b, c + d
    col1, col2 = a + c, b + d
    if n == 0 or row1 == 0 or row2 == 0 or col1 == 0 or col2 == 0:
        return 0.0
    chi2 = n * (a * d - b * c) ** 2 / (row1 * row2 * col1 * col2)
    return (chi2 / n) ** 0.5


def main() -> None:
    items = load_items()
    sources = load_sources()
    items_by_id = {i.item_id: i for i in items}
    sources_by_id = {s.source_registry_id: s for s in sources}

    cache = ResponseCache(ROOT / "data/interim/eval/model_responses.jsonl")
    responses_by_id = {r.response_id: r for r in cache.all_responses()}

    with open(ROOT / "data/interim/eval/correctness_labeling_key.json", encoding="utf-8") as f:
        key = {e["card_id"]: e for e in json.load(f)}
    with open(ROOT / "data/human/correctness_hand_labels.csv", encoding="utf-8") as f:
        labels = {row["card_id"]: row["human_label"] for row in csv.DictReader(f)}

    rows = []
    for card_id, entry in key.items():
        if entry["condition"] not in SCORED_CONDITIONS:
            continue
        response = responses_by_id[entry["response_id"]]
        item = items_by_id[entry["item_id"]]
        cited = cites_trap_source(response, item, sources_by_id)
        if cited is None:
            continue  # did not parse; excluded from the denominator, matching M1's own convention
        rows.append({"card_id": card_id, "condition": entry["condition"], "cited": cited, "correctness": labels[card_id]})

    n = len(rows)
    counts = {"cited": {"correct": 0, "incorrect": 0, "refused": 0}, "not_cited": {"correct": 0, "incorrect": 0, "refused": 0}}
    for r in rows:
        key_row = "cited" if r["cited"] else "not_cited"
        counts[key_row][r["correctness"]] += 1

    # Fisher's exact test on the 2x2 collapse (cited vs. not-cited) x (correct vs. not-correct),
    # the simplest well-posed test this small, unbalanced 2x3 table supports.
    table_2x2 = [
        [counts["cited"]["correct"], counts["cited"]["incorrect"] + counts["cited"]["refused"]],
        [counts["not_cited"]["correct"], counts["not_cited"]["incorrect"] + counts["not_cited"]["refused"]],
    ]
    odds_ratio, p_value = fisher_exact(table_2x2)
    v = cramers_v(table_2x2)

    report = {
        "n": n,
        "scored_conditions": sorted(SCORED_CONDITIONS),
        "counts_3way": counts,
        "table_2x2_cited_vs_correct": table_2x2,
        "fisher_exact": {"odds_ratio": odds_ratio, "p_value": p_value},
        "cramers_v": v,
    }
    out_json = ROOT / "results/correctness_citation_contingency.json"
    out_json.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"wrote {out_json}")

    lines = [
        "# M1 x Correctness contingency (exploratory, n=50, retrieval_naive/retrieval_with_notice only)",
        "",
        f"n = {n}",
        "",
        "| | Correct | Incorrect | Refused |",
        "|---|---|---|---|",
        f"| Cites trap source | {counts['cited']['correct']} | {counts['cited']['incorrect']} | {counts['cited']['refused']} |",
        f"| Does not cite trap source | {counts['not_cited']['correct']} | {counts['not_cited']['incorrect']} | {counts['not_cited']['refused']} |",
        "",
        f"2x2 collapse (cited vs. not) x (correct vs. not-correct): odds ratio = {odds_ratio:.3f}, "
        f"Fisher's exact p = {p_value:.4f}, Cramer's V = {v:.3f}.",
    ]
    out_md = ROOT / "results/correctness_citation_contingency.md"
    out_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {out_md}")


if __name__ == "__main__":
    main()
