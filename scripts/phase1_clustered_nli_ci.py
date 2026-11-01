"""Phase 1 item 1 (prereg/phase1_item1_clustered_nli_ci.md): recompute section 4.11's NLI CIs
with item-clustered bootstrap, reported side by side with the original (unclustered) values.

No new NLI scoring -- reuses the cached `data/interim/eval/faithfulness_check_nli.json` in full.
`item_id` is recovered by joining each result's `response_id` back to
`data/interim/eval/model_responses.jsonl` (the cached NLI output itself never stored item_id).
"""

import json
from collections import defaultdict
from pathlib import Path

from retraction_bench.rag.cache import ResponseCache
from retraction_bench.stats.bootstrap import bootstrap_proportion_ci, bootstrap_proportion_ci_clustered

ROOT = Path(__file__).resolve().parent.parent
NLI_PATH = ROOT / "data/interim/eval/faithfulness_check_nli.json"
OUT_JSON = ROOT / "results/phase1_nli_clustered_cis.json"
OUT_MD = ROOT / "results/phase1_nli_clustered_cis.md"


def main() -> None:
    results = json.loads(NLI_PATH.read_text(encoding="utf-8"))
    cache = ResponseCache(ROOT / "data/interim/eval/model_responses.jsonl")
    item_by_response = {r.response_id: r.item_id for r in cache.all_responses()}

    for r in results:
        r["item_id"] = item_by_response[r["response_id"]]

    n_clusters_overall = len({r["item_id"] for r in results})
    labels = [r["label"] for r in results]
    item_ids = [r["item_id"] for r in results]
    n = len(labels)

    report = {"n_responses": n, "n_clusters_overall": n_clusters_overall, "strata": {}}

    def compare(name: str, successes: list[bool], cluster_ids: list[str]) -> dict:
        n_clusters = len(set(cluster_ids))
        old = bootstrap_proportion_ci(successes)
        if n_clusters == 1:
            new = None  # degenerate: a single cluster has no resampling variance to estimate
        else:
            new = bootstrap_proportion_ci_clustered(successes, cluster_ids)
        row = {
            "n": len(successes),
            "n_clusters": n_clusters,
            "point_estimate": old.point_estimate,
            "unclustered_ci": [old.ci_low, old.ci_high],
            "clustered_ci": [new.ci_low, new.ci_high] if new else "degenerate (1 cluster)",
            "width_unclustered": old.ci_high - old.ci_low,
            "width_clustered": (new.ci_high - new.ci_low) if new else None,
        }
        return row

    print(f"n responses (NLI-scored pairs): {n}; n distinct items overall: {n_clusters_overall}")

    print("\n=== Overall label distribution ===")
    for lbl in ("ENTAILMENT", "NEUTRAL", "CONTRADICTION"):
        row = compare(lbl, [lab == lbl for lab in labels], item_ids)
        report["strata"][f"overall_{lbl}"] = row
        print(
            f"  {lbl:15s} {row['point_estimate']:.3f}  unclustered_CI={row['unclustered_ci']}"
            f"  clustered_CI={row['clustered_ci']}  n_clusters={row['n_clusters']}"
        )

    not_contra = [r["label"] != "CONTRADICTION" for r in results]
    row = compare("NOT_CONTRADICTION", not_contra, item_ids)
    report["strata"]["overall_not_contradiction"] = row
    print(
        f"\nNOT CONTRADICTION (overall): {row['point_estimate']:.3f}  "
        f"unclustered_CI={row['unclustered_ci']}  clustered_CI={row['clustered_ci']}  "
        f"n_clusters={row['n_clusters']}"
    )

    for key in ("condition", "model"):
        print(f"\n=== By {key} ===")
        grouped_vals = defaultdict(list)
        grouped_items = defaultdict(list)
        for r in results:
            grouped_vals[r[key]].append(r["label"] != "CONTRADICTION")
            grouped_items[r[key]].append(r["item_id"])
        for k, vals in grouped_vals.items():
            row = compare(f"{key}_{k}", vals, grouped_items[k])
            report["strata"][f"{key}_{k}"] = row
            print(
                f"  {k:35s} rate={row['point_estimate']:.3f}  unclustered_CI={row['unclustered_ci']}"
                f"  clustered_CI={row['clustered_ci']}  n={row['n']} n_clusters={row['n_clusters']}"
            )

    OUT_JSON.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"\nwrote {OUT_JSON}")


if __name__ == "__main__":
    main()
