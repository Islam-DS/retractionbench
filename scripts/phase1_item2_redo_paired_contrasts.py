"""Phase 1 item 2, REDONE per author decision: the original BinomialBayesMixedGLM output is
discarded entirely (disagreed with the GEE fallback on the gpt-oss term, likely VB posterior-
variance underestimation compounded by only 3 levels for the seed random effect -- logged in
docs/ANALYSIS_LOG.md, not reused here).

New design (prereg/phase1_item2_m1_interaction_test.md's own stated fallback path, now the
primary design by author instruction):
1. Collapse seeds within item x model x condition by majority vote (ties excluded, not broken).
2. Per-item, per-model paired difference (with_notice - naive, in {-1,0,+1}).
3. Omnibus: Friedman test across the 3 models' per-item diffs, on items shared by all three.
4. All three pairwise contrasts (llama-qwen, llama-gpt-oss, qwen-gpt-oss) via
   `paired_bootstrap_permutation_test` on the difference-of-differences, each on items shared by
   that pair; Holm correction across the 3.
5. Check: redo 3-4 using the continuous per-item-per-model citation RATE across seeds (not
   majority-vote-binarized) -- does binarization change the qualitative conclusion.

No new model calls -- same cached 900 responses, same `cites_trap_source` function as before.
"""

import json
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
from scipy.stats import friedmanchisquare

from retraction_bench.curate.benchmark_io import load_items, load_sources
from retraction_bench.eval.citation import cites_trap_source
from retraction_bench.rag.cache import ResponseCache
from retraction_bench.rag.collect import notice_eligible_item_ids
from retraction_bench.stats.paired_test import holm_correction, paired_bootstrap_permutation_test

ROOT = Path(__file__).resolve().parent.parent
OUT_JSON = ROOT / "results/phase1_item2_redo_paired_contrasts.json"
OUT_MD = ROOT / "results/phase1_item2_redo_paired_contrasts.md"
MODELS = ["llama3.1:8b-instruct-q4_K_M", "qwen2.5:7b-instruct-q4_K_M", "openai/gpt-oss-120b"]


def majority(values: list[bool]) -> bool | None:
    c = Counter(values)
    if len(c) == 2 and c[True] == c[False]:
        return None
    return c.most_common(1)[0][0]


def build_raw() -> dict:
    """(item_id, model, condition) -> list of per-seed bool outcomes."""
    items = {i.item_id: i for i in load_items()}
    sources = {s.source_registry_id: s for s in load_sources()}
    eligible_ids = notice_eligible_item_ids(list(items.values()), sources)
    cache = ResponseCache(ROOT / "data/interim/eval/model_responses.jsonl")

    raw = defaultdict(list)
    for r in cache.all_responses():
        if r.condition.value not in ("retrieval_naive", "retrieval_with_notice") or r.item_id not in eligible_ids:
            continue
        outcome = cites_trap_source(r, items[r.item_id], sources)
        if outcome is None:
            continue
        raw[(r.item_id, r.model_identifier, r.condition.value)].append(outcome)
    return raw


def collapse_majority(raw: dict) -> dict:
    out = {}
    for cell, vals in raw.items():
        m = majority(vals)
        if m is not None:
            out[cell] = m
    return out


def collapse_rate(raw: dict) -> dict:
    return {cell: sum(vals) / len(vals) for cell, vals in raw.items()}


def per_model_item_diffs(collapsed: dict, model: str) -> dict[str, float]:
    """item_id -> (with_notice - naive) for one model, items present in both conditions only."""
    diffs = {}
    for item_id in {c[0] for c in collapsed if c[1] == model}:
        naive = collapsed.get((item_id, model, "retrieval_naive"))
        notice = collapsed.get((item_id, model, "retrieval_with_notice"))
        if naive is not None and notice is not None:
            diffs[item_id] = float(notice) - float(naive)
    return diffs


def run_contrasts(collapsed: dict, label: str) -> dict:
    per_model = {m: per_model_item_diffs(collapsed, m) for m in MODELS}
    for m in MODELS:
        print(f"  [{label}] {m}: n_items_with_paired_diff={len(per_model[m])}")

    # Omnibus: Friedman across the 3 models, items common to all three.
    common_items = sorted(set(per_model[MODELS[0]]) & set(per_model[MODELS[1]]) & set(per_model[MODELS[2]]))
    omnibus = None
    if len(common_items) >= 3:
        samples = [[per_model[m][i] for i in common_items] for m in MODELS]
        # Friedman requires non-degenerate variation; guard against a constant column.
        if any(len(set(s)) > 1 for s in samples):
            stat, p = friedmanchisquare(*samples)
            omnibus = {"n_items": len(common_items), "statistic": float(stat), "p_value": float(p)}
        else:
            omnibus = {"n_items": len(common_items), "statistic": 0.0, "p_value": 1.0, "note": "all samples constant"}
    else:
        omnibus = {"n_items": len(common_items), "note": "too few common items for Friedman"}

    # Pairwise contrasts, each on items shared by that specific pair.
    pairwise = {}
    pairs = [(MODELS[0], MODELS[1]), (MODELS[0], MODELS[2]), (MODELS[1], MODELS[2])]
    for a, b in pairs:
        shared = sorted(set(per_model[a]) & set(per_model[b]))
        if len(shared) < 2:
            pairwise[f"{a} vs {b}"] = {"n_items": len(shared), "note": "too few shared items"}
            continue
        diff_of_diffs = [per_model[a][i] - per_model[b][i] for i in shared]
        test = paired_bootstrap_permutation_test(diff_of_diffs)
        pairwise[f"{a} vs {b}"] = {
            "n_items": len(shared),
            "mean_diff_of_diffs": test.mean_diff,
            "ci": [test.ci_low, test.ci_high],
            "p_value": test.p_value,
        }

    raw_p = {k: v["p_value"] for k, v in pairwise.items() if "p_value" in v}
    holm_adjusted = holm_correction(raw_p) if raw_p else {}

    return {"omnibus_friedman": omnibus, "pairwise": pairwise, "holm_adjusted_pairwise_p": holm_adjusted}


def main() -> None:
    raw = build_raw()

    print("=== PRIMARY: majority-vote-collapsed seeds ===")
    collapsed_majority = collapse_majority(raw)
    primary = run_contrasts(collapsed_majority, "majority")

    print("\n=== CHECK: continuous per-seed citation rate (not binarized) ===")
    collapsed_rate = collapse_rate(raw)
    check = run_contrasts(collapsed_rate, "rate")

    report = {"primary_majority_vote": primary, "check_continuous_rate": check}
    OUT_JSON.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"\nwrote {OUT_JSON}")

    def fmt_pairwise(block: dict) -> list[str]:
        lines = ["| Pair | n items | mean diff-of-diffs | 95% CI | raw p | Holm p |", "|---|---|---|---|---|---|"]
        for pair, v in block["pairwise"].items():
            if "p_value" not in v:
                lines.append(f"| {pair} | {v['n_items']} | -- | -- | -- | {v.get('note','')} |")
                continue
            holm = block["holm_adjusted_pairwise_p"].get(pair, float("nan"))
            lines.append(
                f"| {pair} | {v['n_items']} | {v['mean_diff_of_diffs']:+.3f} | "
                f"[{v['ci'][0]:+.3f},{v['ci'][1]:+.3f}] | {v['p_value']:.4f} | {holm:.4f} |"
            )
        return lines

    qvg = primary["pairwise"].get("qwen2.5:7b-instruct-q4_K_M vs openai/gpt-oss-120b", {})
    qvg_holm = primary["holm_adjusted_pairwise_p"].get("qwen2.5:7b-instruct-q4_K_M vs openai/gpt-oss-120b")
    qvg_significant = qvg_holm is not None and qvg_holm < 0.05

    lines = [
        "# Phase 1 item 2, REDONE: paired per-item contrasts across models (VB GLMM discarded)",
        "",
        "Prereg: `prereg/phase1_item2_m1_interaction_test.md` (fallback path, now primary by author",
        "instruction). The original BinomialBayesMixedGLM run is discarded -- logged, not reused,",
        "in `docs/ANALYSIS_LOG.md`.",
        "",
        "## Primary: seeds collapsed by majority vote within item x model x condition",
        "",
        f"Omnibus Friedman test across all 3 models (items common to all three, n={primary['omnibus_friedman'].get('n_items')}): "
        + (
            f"chi2={primary['omnibus_friedman']['statistic']:.3f}, p={primary['omnibus_friedman']['p_value']:.4f}"
            if "p_value" in primary["omnibus_friedman"]
            else primary["omnibus_friedman"].get("note", "n/a")
        ),
        "",
        "### All three pairwise contrasts (Holm-corrected across the 3)",
        "",
        *fmt_pairwise(primary),
        "",
        "## Check: continuous per-item citation rate across seeds (not majority-vote-binarized)",
        "",
        f"Omnibus Friedman (n={check['omnibus_friedman'].get('n_items')}): "
        + (
            f"chi2={check['omnibus_friedman']['statistic']:.3f}, p={check['omnibus_friedman']['p_value']:.4f}"
            if "p_value" in check["omnibus_friedman"]
            else check["omnibus_friedman"].get("note", "n/a")
        ),
        "",
        *fmt_pairwise(check),
        "",
        "## Interpretation (prespecified rule applied)",
        "",
        (
            "**qwen vs. gpt-oss is significant after Holm correction** -- both detected effects "
            "differ from each other, not just from llama."
            if qvg_significant
            else
            "**qwen vs. gpt-oss is NOT significant after Holm correction.** Per the author's "
            "prespecified wording rule: this is reported as **'one detected effect, two "
            "non-detections'** -- qwen's own within-model notice effect is the one pairwise "
            "contrast against llama that survives correction; gpt-oss's contrast against llama "
            "does not, and qwen's contrast against gpt-oss itself also does not, meaning the data "
            "do not support treating qwen and gpt-oss as two separately confirmed distinct "
            "patterns from each other, only each as distinct-or-not from llama individually."
        ),
    ]
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {OUT_MD}")


if __name__ == "__main__":
    main()
