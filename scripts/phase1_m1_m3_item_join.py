"""Phase 1 item 3 (prereg/phase1_item3_m1_m3_item_join.md): item x model join of M1 under
`retrieval_with_notice` and M3 (`acknowledges` vs. not) under `post_notice`.

No new model calls -- M1 from the existing cached responses (same `cites_trap_source` function
used by phase1_m1_interaction_test.py), M3 from the existing hand labels
(`data/human/m3_hand_labels.csv`). Multiple seeds per item x model cell are collapsed to one
binary value by majority vote; ties are reported and excluded from that cell, not broken
arbitrarily.
"""

import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

from retraction_bench.curate.benchmark_io import load_items, load_sources
from retraction_bench.eval.citation import cites_trap_source
from retraction_bench.rag.cache import ResponseCache
from retraction_bench.stats.bootstrap import DEFAULT_N_RESAMPLES, DEFAULT_SEED

ROOT = Path(__file__).resolve().parent.parent
OUT_JSON = ROOT / "results/phase1_m1_m3_item_join.json"
OUT_MD = ROOT / "results/phase1_m1_m3_item_join.md"


def majority(values: list[bool]) -> bool | None:
    """Returns None (not an arbitrary break) on an exact tie."""
    c = Counter(values)
    if len(c) == 2 and c[True] == c[False]:
        return None
    return c.most_common(1)[0][0]


def collapsed_m1(cache: ResponseCache, items: dict, sources: dict) -> dict[tuple[str, str], bool]:
    """(item_id, model) -> majority-vote cites_trap under retrieval_with_notice."""
    by_cell: dict[tuple[str, str], list[bool]] = defaultdict(list)
    for r in cache.all_responses():
        if r.condition.value != "retrieval_with_notice":
            continue
        outcome = cites_trap_source(r, items[r.item_id], sources)
        if outcome is None:
            continue
        by_cell[(r.item_id, r.model_identifier)].append(outcome)
    out = {}
    for cell, vals in by_cell.items():
        m = majority(vals)
        if m is not None:
            out[cell] = m
    return out


def collapsed_m3(cache: ResponseCache) -> dict[tuple[str, str], bool]:
    """(item_id, model) -> majority-vote acknowledges under post_notice, from hand labels."""
    response_by_id = {r.response_id: r for r in cache.all_responses()}
    by_cell: dict[tuple[str, str], list[bool]] = defaultdict(list)
    with open(ROOT / "data/human/m3_hand_labels.csv", encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            resp = response_by_id.get(row["response_id"])
            if resp is None:
                continue
            by_cell[(row["item_id"], resp.model_identifier)].append(row["human_label"] == "acknowledges")
    out = {}
    for cell, vals in by_cell.items():
        m = majority(vals)
        if m is not None:
            out[cell] = m
    return out


def phi_coefficient(x: list[bool], y: list[bool]) -> float:
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    if x.std() == 0 or y.std() == 0:
        return float("nan")  # no variance in one variable -- phi undefined, not zero
    return float(np.corrcoef(x, y)[0, 1])


def bootstrap_phi_ci(x: list[bool], y: list[bool], seed: int = DEFAULT_SEED, n_resamples: int = DEFAULT_N_RESAMPLES):
    rng = np.random.default_rng(seed)
    n = len(x)
    x_arr, y_arr = np.asarray(x), np.asarray(y)
    point = phi_coefficient(x, y)
    if n < 2:
        return point, point, point
    vals = []
    for _ in range(n_resamples):
        idx = rng.integers(0, n, size=n)
        v = phi_coefficient(list(x_arr[idx]), list(y_arr[idx]))
        if not np.isnan(v):
            vals.append(v)
    if len(vals) < 2:
        return point, float("nan"), float("nan")
    return point, float(np.percentile(vals, 2.5)), float(np.percentile(vals, 97.5))


def main() -> None:
    items = {i.item_id: i for i in load_items()}
    sources = {s.source_registry_id: s for s in load_sources()}
    cache = ResponseCache(ROOT / "data/interim/eval/model_responses.jsonl")

    m1_cells = collapsed_m1(cache, items, sources)
    m3_cells = collapsed_m3(cache)

    shared_cells = set(m1_cells) & set(m3_cells)
    print(f"M1 cells (item,model) with a majority vote: {len(m1_cells)}")
    print(f"M3 cells (item,model) with a hand-labeled majority vote: {len(m3_cells)}")
    print(f"Shared cells (joinable): {len(shared_cells)}")

    by_model: dict[str, list[tuple[str, bool, bool]]] = defaultdict(list)
    for item_id, model in sorted(shared_cells):
        by_model[model].append((item_id, m1_cells[(item_id, model)], m3_cells[(item_id, model)]))

    report = {"n_shared_cells_total": len(shared_cells), "by_model": {}}
    lines = [
        "# Phase 1 item 3: item-level M1 (retrieval_with_notice) x M3 (post_notice, acknowledges) join",
        "",
        "Prereg: `prereg/phase1_item3_m1_m3_item_join.md`.",
        "",
        f"Total joinable (item, model) cells (both M1 and hand-labeled M3 available): {len(shared_cells)}.",
        "",
        "| Model | n items | phi | 95% CI | 2x2 breakdown (cites_trap x acknowledges) |",
        "|---|---|---|---|---|",
    ]
    for model, rows in sorted(by_model.items()):
        items_m, cites_vals, ack_vals = zip(*rows)
        n = len(rows)
        tt = sum(1 for c, a in zip(cites_vals, ack_vals) if c and a)
        tf = sum(1 for c, a in zip(cites_vals, ack_vals) if c and not a)
        ft = sum(1 for c, a in zip(cites_vals, ack_vals) if not c and a)
        ff = sum(1 for c, a in zip(cites_vals, ack_vals) if not c and not a)
        point, lo, hi = bootstrap_phi_ci(list(cites_vals), list(ack_vals))
        too_small = n < 5
        report["by_model"][model] = {
            "n_items": n,
            "phi": point,
            "ci": [lo, hi],
            "confusion": {"cites_and_acknowledges": tt, "cites_not_acknowledge": tf, "not_cites_acknowledges": ft, "neither": ff},
            "too_small_for_inference": too_small,
            "item_ids": list(items_m),
        }
        phi_str = f"{point:.3f}" if not np.isnan(point) else "undefined (no variance)"
        ci_str = f"[{lo:.3f},{hi:.3f}]" if not (np.isnan(lo) or np.isnan(hi)) else "n/a"
        flag = " **(n<5, descriptive only, not tested)**" if too_small else ""
        lines.append(f"| {model} | {n}{flag} | {phi_str} | {ci_str} | TT={tt} TF={tf} FT={ft} FF={ff} |")
        print(f"{model}: n={n}, phi={phi_str}, CI={ci_str}, confusion TT={tt} TF={tf} FT={ft} FF={ff}")

    OUT_JSON.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"\nwrote {OUT_JSON}")

    any_adequate = any(not v["too_small_for_inference"] for v in report["by_model"].values())
    lines += [
        "",
        "**Interpretation (prespecified rule applied):** "
        + (
            "At least one model has an adequately-sized joined sample; see its phi/CI above for "
            "whether citing the trap source under retrieval_with_notice is associated with later "
            "acknowledging the correction under post_notice, at the item level."
            if any_adequate
            else
            "**Every model's joinable sample is n<5 items.** This join cannot support a tested "
            "association for any model at this sample size -- a direct consequence of M3's hand-"
            "labeled subsample being small and only partially overlapping with the "
            "retrieval_with_notice-eligible item set per model. The Discussion's inference that "
            "this pattern is 'not a comprehension failure' is **not supported by item-level "
            "evidence** and should be deleted or explicitly rewritten as resting only on the "
            "aggregate (not item-joined) contrast between sections 4.2 and 4.4."
        ),
    ]
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {OUT_MD}")


if __name__ == "__main__":
    main()
