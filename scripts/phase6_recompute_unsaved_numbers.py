"""Phase 6 (2026-10-12): recompute every main-text number the number-trace gate found with no saved
output, from the raw data, through the same code paths that originally produced them, and save
the results -- so each printed number has a committed source and any drift is caught.

Numbers covered (paper.md section, printed value):
  1. background-corpus retracted-tag rate (3.9.1): 335/325,086 = 0.103%, Wilson CI [0.093%, 0.115%]
  2. no-current-answer share of items (4.1): 13/28 = 46.4%, Wilson CI [29.5%, 64.2%]
  3. seed cells behind the majority-vote collapse (4.2): 140/141 cells had all 3 seeds
  4. Correctness by item type (4.3): gold-answer 0.571/0.302/0.127, CI [0.362, 0.750] (n=63, 14
     items); no-answer 0.108/0.757/0.135, CI [0.000, 0.242] (n=37, 12 items)
  5. LLM-judge vs human Correctness labels (4.3): Cohen's kappa = 0.148
  6. domain-stratified M1 / M3 / Correctness (4.10)

Writes results/phase6_recomputed_numbers.{json,md}. Read-only on all inputs; no model calls.
"""

from __future__ import annotations

import csv
import importlib.util
import json
from collections import Counter, defaultdict
from pathlib import Path

from statsmodels.stats.proportion import proportion_confint

from retraction_bench.curate.benchmark_io import load_items
from retraction_bench.eval.correctness import Correctness, compute_correctness
from retraction_bench.stats.bootstrap import bootstrap_proportion_ci_clustered

ROOT = Path(__file__).resolve().parent.parent
OUT_JSON = ROOT / "results" / "phase6_recomputed_numbers.json"
OUT_MD = ROOT / "results" / "phase6_recomputed_numbers.md"


def _load_script(name: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def wilson(k: int, n: int) -> list[float]:
    lo, hi = proportion_confint(k, n, method="wilson")
    return [lo, hi]


def background_tag_rate() -> dict:
    rows = list(csv.DictReader((ROOT / "data/interim/eval/background_pubmed_verification_cache.csv").open(encoding="utf-8")))
    errors = [r for r in rows if r["error"].strip()]
    ok = [r for r in rows if not r["error"].strip()]
    tagged = sum(1 for r in ok if r["is_retracted_tagged"] == "True")
    return {
        "n_rows": len(rows), "n_lookup_errors": len(errors), "n_resolved": len(ok), "n_tagged": tagged,
        "rate_over_resolved": tagged / len(ok), "wilson_over_resolved": wilson(tagged, len(ok)),
        "rate_over_all_rows": tagged / len(rows), "wilson_over_all_rows": wilson(tagged, len(rows)),
    }


def no_answer_share(items) -> dict:
    n = len(items)
    k = sum(1 for i in items if str(getattr(i.item_type, "value", i.item_type)) == "superseded_without_current_answer")
    return {"k": k, "n": n, "rate": k / n, "wilson": wilson(k, n)}


def seed_cells() -> dict:
    raw = _load_script("phase1_item2_redo_paired_contrasts").build_raw()
    sizes = Counter(len(v) for v in raw.values())
    ties = sum(1 for v in raw.values() if len(v) == 2 and sum(v) == 1)
    return {"n_cells": len(raw), "cells_by_seed_count": {str(k): v for k, v in sorted(sizes.items())},
            "cells_with_all_3_seeds": f"{sizes.get(3, 0)}/{len(raw)}",
            "two_seed_ties_dropped": ties}


def _labels(path: str) -> list[dict]:
    return list(csv.DictReader((ROOT / path).open(encoding="utf-8")))


def _ci(res) -> list[float]:
    return [res.ci_low, res.ci_high]


def correctness_by(items_by_id, key: str) -> dict:
    out = {}
    rows = _labels("data/human/correctness_hand_labels.csv")
    groups = defaultdict(list)
    for r in rows:
        item = items_by_id[r["item_id"]]
        val = getattr(item, key)
        groups[str(getattr(val, "value", val))].append((Correctness(r["human_label"]), r["item_id"]))
    for g, members in sorted(groups.items()):
        res = compute_correctness([m[0] for m in members], [m[1] for m in members])
        out[g] = {
            "n": res.n, "n_items": len({m[1] for m in members}),
            "rates": {str(k.value): v for k, v in res.rates.items()},
            "ci": {str(k.value): _ci(v) for k, v in res.cis.items()},
        }
    return out


def correctness_by_key_field(field_name: str) -> dict:
    """Correctness by a field of the labeling key (condition, model) -- the per-condition and
    per-model rows of the section 4.3 Correctness table, which reproduce.py never saved."""
    key = json.loads((ROOT / "data/interim/eval/correctness_labeling_key.json").read_text(encoding="utf-8"))
    kd = {k["card_id"]: k for k in key} if isinstance(key, list) else key
    groups = defaultdict(list)
    for r in _labels("data/human/correctness_hand_labels.csv"):
        groups[kd[r["card_id"]][field_name]].append((Correctness(r["human_label"]), r["item_id"]))
    out = {}
    for g, members in sorted(groups.items()):
        res = compute_correctness([m[0] for m in members], [m[1] for m in members])
        out[g] = {"n": res.n, "rates": {str(k.value): v for k, v in res.rates.items()},
                  "ci_correct": _ci(res.cis[Correctness("correct")])}
    return out


def malformed_by_model() -> dict:
    from retraction_bench.rag.cache import ResponseCache
    from retraction_bench.rag.parse import parse_response
    cache = ResponseCache(ROOT / "data/interim/eval/model_responses.jsonl")
    counts: dict[str, Counter] = defaultdict(Counter)
    for r in cache.all_responses():
        counts[r.model_identifier][str(parse_response(r.raw_answer_text).parse_status.value)] += 1
    return {m: {"n": sum(c.values()), "by_status": dict(c),
                "parsed_share": c.get("parsed", 0) / sum(c.values())} for m, c in sorted(counts.items())}


def notice_specificity_counts() -> dict:
    from retraction_bench.curate.benchmark_io import load_sources
    sources = load_sources()
    c = Counter(str(getattr(s.notice_specificity, "value", s.notice_specificity)) for s in sources)
    n = len(sources)
    return {"n_sources": n, "counts": dict(c),
            "bare": f"{c.get('bare', 0)}/{n}", "bare_share": c.get("bare", 0) / n,
            "bare_or_unverifiable_share": (c.get("bare", 0) + c.get("unverifiable", 0)) / n}


def gpt_oss_truncation() -> dict:
    from retraction_bench.rag.cache import ResponseCache
    from retraction_bench.rag.parse import parse_response
    cache = ResponseCache(ROOT / "data/interim/eval/model_responses.jsonl")
    rows = []
    for r in cache.all_responses():
        if r.model_identifier == "openai/gpt-oss-120b" and parse_response(r.raw_answer_text).parse_status.value == "malformed":
            u = r.raw_call_metadata.get("usage", {})
            rows.append({"finish_reason": r.raw_call_metadata.get("finish_reason"),
                         "completion_tokens": u.get("completion_tokens"),
                         "reasoning_tokens": (u.get("completion_tokens_details") or {}).get("reasoning_tokens")})
    rt = [x["reasoning_tokens"] for x in rows if x["reasoning_tokens"] is not None]
    return {"n_malformed": len(rows), "finish_reasons": dict(Counter(x["finish_reason"] for x in rows)),
            "completion_tokens": sorted({x["completion_tokens"] for x in rows}),
            "reasoning_tokens_min": min(rt) if rt else None, "reasoning_tokens_max": max(rt) if rt else None}


def correctness_lenient_and_cross(items_by_id) -> dict:
    rows = _labels("data/human/correctness_hand_labels.csv")
    def it(i):
        v = items_by_id[i].item_type
        return str(getattr(v, "value", v))
    na = [r for r in rows if it(r["item_id"]) == "superseded_without_current_answer"]
    ok = [r["human_label"] in ("correct", "refused") for r in na]
    lenient = bootstrap_proportion_ci_clustered(ok, [r["item_id"] for r in na])
    cross = {}
    for r in rows:
        cross.setdefault((items_by_id[r["item_id"]].domain, it(r["item_id"])), []).append(r)
    cross_out = {}
    for (dom, typ), members in sorted(cross.items()):
        res = bootstrap_proportion_ci_clustered([m["human_label"] == "correct" for m in members],
                                                [m["item_id"] for m in members])
        cross_out[f"{dom} | {typ}"] = {"n": len(members), "n_items": len({m['item_id'] for m in members}),
                                       "correct": res.point_estimate, "ci": _ci(res)}
    return {"no_answer_lenient": {"k": sum(ok), "n": len(na), "fraction": f"{sum(ok)}/{len(na)}",
                                  "rate": lenient.point_estimate, "ci": _ci(lenient)},
            "domain_x_item_type_correct": cross_out}


def retrieval_ordering() -> dict:
    import statistics
    rep = json.loads((ROOT / "results/retrieval_ceiling_report.json").read_text(encoding="utf-8"))
    rows = [r for r in rep["per_item"] if r.get("notice_rank") is not None]
    worse = sum(1 for r in rows if r["notice_rank"] > r["trap_source_rank"])
    better = sum(1 for r in rows if r["notice_rank"] < r["trap_source_rank"])
    gaps = [r["notice_rank"] - r["trap_source_rank"] for r in rows]
    n = len(rows)
    return {"n_items_with_notice": n, "notice_worse": f"{worse}/{n}", "notice_worse_wilson": wilson(worse, n),
            "notice_better": f"{better}/{n}", "notice_better_wilson": wilson(better, n),
            "mean_rank_gap": statistics.mean(gaps), "median_rank_gap": statistics.median(gaps)}


def correctness_by_source_evidence_level(items_by_id) -> dict:
    """Section 4.8: Correctness split by whether the retracted source is a synthesis or a primary
    study (the item's single supporting source's evidence_level)."""
    from retraction_bench.curate.benchmark_io import load_sources
    level = {s.source_registry_id: str(getattr(s.evidence_level, "value", s.evidence_level)) for s in load_sources()}
    groups = defaultdict(list)
    for r in _labels("data/human/correctness_hand_labels.csv"):
        srcs = items_by_id[r["item_id"]].supporting_sources
        groups[level[srcs[0]]].append((Correctness(r["human_label"]), r["item_id"]))
    out = {}
    for g, members in sorted(groups.items()):
        res = compute_correctness([m[0] for m in members], [m[1] for m in members])
        out[g] = {"n": res.n, "rates": {str(k.value): v for k, v in res.rates.items()},
                  "ci": {str(k.value): _ci(v) for k, v in res.cis.items()}}
    return out


def m3_by_domain(items_by_id) -> dict:
    rows = _labels("data/human/m3_hand_labels.csv")
    groups = defaultdict(list)
    for r in rows:
        groups[items_by_id[r["item_id"]].domain].append((r["human_label"] == "acknowledges", r["item_id"]))
    out = {}
    for g, members in sorted(groups.items()):
        res = bootstrap_proportion_ci_clustered([m[0] for m in members], [m[1] for m in members])
        out[g] = {"n": len(members), "n_items": len({m[1] for m in members}),
                  "acknowledges": res.point_estimate, "ci": _ci(res)}
    return out


def m1_by_domain(items_by_id) -> dict:
    raw = _load_script("phase1_item2_redo_paired_contrasts").build_raw()
    groups = defaultdict(list)
    for (item_id, _model, cond), outcomes in raw.items():
        for o in outcomes:
            groups[(items_by_id[item_id].domain, cond)].append((o, item_id))
    out = {}
    for (dom, cond), members in sorted(groups.items()):
        res = bootstrap_proportion_ci_clustered([m[0] for m in members], [m[1] for m in members])
        out[f"{dom} | {cond}"] = {"n": len(members), "n_items": len({m[1] for m in members}),
                                  "rate": res.point_estimate, "ci": _ci(res)}
    return out


def judge_kappa() -> dict:
    v = _load_script("validate_llm_judge_agreement")
    cfg = v.TASKS["correctness"]
    hand = v.load_hand_labels(cfg["hand_labels"])
    judge = v.load_judge_labels(cfg["judge_output"])
    ids = [rid for rid in hand if judge.get(rid) is not None]
    res = v.score([hand[r] for r in ids], [judge[r] for r in ids], cfg["labels"])
    return {"n": res.n, "cohens_kappa": res.cohens_kappa, "agreement_rate": res.agreement_rate}


def main() -> None:
    items = load_items()
    by_id = {i.item_id: i for i in items}
    out = {
        "background_tag_rate": background_tag_rate(),
        "no_answer_share": no_answer_share(items),
        "seed_cells": seed_cells(),
        "correctness_by_item_type": correctness_by(by_id, "item_type"),
        "correctness_by_condition": correctness_by_key_field("condition"),
        "correctness_by_model": correctness_by_key_field("model"),
        "malformed_by_model": malformed_by_model(),
        "notice_specificity": notice_specificity_counts(),
        "gpt_oss_truncation": gpt_oss_truncation(),
        "correctness_lenient_and_cross": correctness_lenient_and_cross(by_id),
        "retrieval_ordering": retrieval_ordering(),
        "correctness_by_source_evidence_level": correctness_by_source_evidence_level(by_id),
        "correctness_judge_kappa": judge_kappa(),
        "domain_m1": m1_by_domain(by_id),
        "domain_m3_acknowledges": m3_by_domain(by_id),
        "domain_correctness": correctness_by(by_id, "domain"),
    }
    OUT_JSON.write_text(json.dumps(out, indent=2), encoding="utf-8")
    lines = ["# Phase 6: recomputed numbers that previously had no saved output", "",
             "Generated by `scripts/phase6_recompute_unsaved_numbers.py` (no model calls; same loaders,",
             "scorers, and item-clustered bootstrap as the original analyses). Raw values below; the",
             "comparison against paper.md's printed values is in docs/ANALYSIS_LOG.md (Phase 6).", "",
             "```json", json.dumps(out, indent=2), "```"]
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
