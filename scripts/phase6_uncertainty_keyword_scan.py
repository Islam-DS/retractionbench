"""Phase 6: reproducible explicit-uncertainty keyword scan (prereg/phase6_uncertainty_keyword_scan.md).

Replaces the manuscript's unscripted "3/117 (2.6%)" figure, whose phrase list was never recorded.
The 20 phrases below are fixed by the prespecification file and were not changed after running.
Scope: `no_retrieval` responses on `superseded_without_current_answer` items; text scanned is the
model's returned answer text only, never its hidden reasoning.

Output: results/phase6_uncertainty_keyword_scan.json
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from statsmodels.stats.proportion import proportion_confint

from retraction_bench.curate.benchmark_io import load_items
from retraction_bench.stats.bootstrap import bootstrap_proportion_ci_clustered

ROOT = Path(__file__).resolve().parent.parent
RESPONSES = ROOT / "data/interim/eval/model_responses.jsonl"
OUT = ROOT / "results/phase6_uncertainty_keyword_scan.json"

PHRASES = (
    "i don't know",
    "i do not know",
    "not sure",
    "uncertain",
    "unclear",
    "insufficient evidence",
    "limited evidence",
    "evidence is limited",
    "evidence is insufficient",
    "lack of evidence",
    "not enough evidence",
    "no current",
    "no reliable",
    "no consensus",
    "conflicting evidence",
    "inconclusive",
    "not been established",
    "not well established",
    "cannot determine",
    "unable to determine",
)


def _normalize(text: str) -> str:
    # curly apostrophes and non-breaking hyphens/spaces appear in model output
    return text.lower().replace("’", "'").replace("‑", "-").replace(" ", " ")


def main() -> None:
    items = load_items()
    no_answer = {i.item_id for i in items if str(getattr(i.item_type, "value", i.item_type)) == "superseded_without_current_answer"}

    rows = []
    with RESPONSES.open(encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            if r["condition"] != "no_retrieval" or r["item_id"] not in no_answer:
                continue
            text = _normalize(r["raw_answer_text"] or "")
            hits = [p for p in PHRASES if p in text]
            rows.append({
                "response_id": r["response_id"], "item_id": r["item_id"], "model": r["model_identifier"],
                "seed": r["seed"], "hits": hits,
                "contexts": [text[max(0, text.find(p) - 80): text.find(p) + len(p) + 80] for p in hits],
            })

    n = len(rows)
    k = sum(1 for r in rows if r["hits"])
    lo, hi = proportion_confint(k, n, alpha=0.05, method="wilson")
    clustered = bootstrap_proportion_ci_clustered(
        [bool(r["hits"]) for r in rows], [r["item_id"] for r in rows], n_resamples=10_000, seed=42
    )
    result = {
        "prespecification": "prereg/phase6_uncertainty_keyword_scan.md",
        "phrases": list(PHRASES),
        "n_items": len(no_answer),
        "n_responses": n,
        "n_with_hit": k,
        "rate": k / n,
        "wilson_95ci": [lo, hi],
        "item_clustered_bootstrap_95ci": [clustered.ci_low, clustered.ci_high],
        "hits_by_model": dict(Counter(r["model"] for r in rows if r["hits"])),
        "responses_by_model": dict(Counter(r["model"] for r in rows)),
        "hits_by_item": dict(Counter(r["item_id"] for r in rows if r["hits"])),
        "hits_by_phrase": dict(Counter(p for r in rows for p in r["hits"])),
        "hit_responses": [r for r in rows if r["hits"]],
    }
    OUT.write_text(json.dumps(result, indent=1, default=str), encoding="utf-8")
    print(json.dumps({k: v for k, v in result.items() if k != "hit_responses"}, indent=1, default=str))


if __name__ == "__main__":
    main()
