"""Regenerates the paper's headline M1/M3/Correctness numbers -- including the item-level paired
test and Holm correction -- entirely from cached, committed data, with no live API call (ADR-153).

Closes the reproducibility gap documented in AUDIT_REPORT.md section 3.2: previously, the paired
bootstrap + permutation test + Holm correction and the Correctness statistics existed only as
prose in the paper (computed by an uncommitted scratch script during the authoring session).
Every computation below routes through the same committed, tested modules the paper's methods
section describes (`stats/bootstrap.py`, `stats/paired_test.py`, `eval/citation.py`,
`eval/m1.py`, `eval/m3.py`, `eval/correctness.py`) -- nothing here reimplements a statistic.

Lives in the installable package (not `scripts/`) specifically so `retraction-bench evaluate`
(cli.py) can import it after installation -- a bare top-level `scripts/` directory is not on the
installed package's import path, which is exactly the packaging bug that made the first version
of this module importable only via `python scripts/reproduce_paper_numbers.py` from the repo
root, and not via the CLI entry point (caught by actually running `uv run retraction-bench
evaluate`, not just the direct script invocation).

Run with: `uv run retraction-bench evaluate`, or `make reproduce`, or directly via
`uv run python scripts/reproduce_paper_numbers.py` (a thin wrapper around `main()` below, kept at
that path for discoverability alongside any future `scripts/make_paper_figures.py`).
Writes: `results/reproduced_paper_numbers.json` (machine-readable) and
`results/reproduced_paper_numbers.md` (human-readable, mirrors the paper's own tables).

Inputs read (all committed or cached, no live call):
  data/interim/eval/model_responses.jsonl      (900 cached ModelResponse records)
  data/human/m3_hand_labels.csv                (150 hand labels, ground truth per the project protocol 5.1)
  data/human/correctness_hand_labels.csv       (100 hand labels, ground truth per the project protocol 5.1)
  data/interim/eval/m3_labeling_key.json       (card_id -> item_id/model/response_id mapping)
  data/interim/eval/correctness_labeling_key.json  (same, for the correctness sample)
  data/benchmark/ (via curate.benchmark_io.load_items/load_sources)
"""

import csv
import json
from collections import defaultdict
from pathlib import Path

from retraction_bench.curate.benchmark_io import load_items, load_sources
from retraction_bench.eval.citation import cites_trap_source
from retraction_bench.eval.correctness import compute_correctness
from retraction_bench.eval.m1 import compute_m1_from_outcomes
from retraction_bench.eval.m3 import compute_m3_from_labels
from retraction_bench.rag.cache import ResponseCache
from retraction_bench.schemas import Correctness, M3Label
from retraction_bench.stats.paired_test import holm_correction, paired_bootstrap_permutation_test

ROOT = Path(__file__).resolve().parent.parent.parent
MODELS = ("llama3.1:8b-instruct-q4_K_M", "openai/gpt-oss-120b", "qwen2.5:7b-instruct-q4_K_M")


def _load_csv_labels(path: Path) -> dict[str, str]:
    with open(path, encoding="utf-8") as f:
        return {row["card_id"]: row["human_label"] for row in csv.DictReader(f)}


def _load_key(path: Path) -> dict[str, dict]:
    with open(path, encoding="utf-8") as f:
        return {e["card_id"]: e for e in json.load(f)}


def _bootstrap_result_to_dict(ci) -> dict:
    return {
        "point_estimate": ci.point_estimate,
        "ci_low": ci.ci_low,
        "ci_high": ci.ci_high,
        "n_resamples": ci.n_resamples,
    }


def compute_m1_section(responses, items_by_id, sources_by_id) -> dict:
    """M1 overall by condition, and by model x condition for the two discriminating conditions,
    plus the item-level paired test and Holm correction. Mirrors paper.md section 4.2 exactly.

    `cites_trap_source` is called exactly once per response (not once per downstream breakdown
    that needs it) -- every table below is derived from that single pass, so the by-condition
    table, the by-model-condition table, the paired test, and the seed-agreement check can never
    silently disagree about which responses were scored or how.
    """
    scored: list[tuple[str, str, str, bool]] = []  # (model, condition, item_id, outcome)
    for r in responses:
        item = items_by_id[r.item_id]
        outcome = cites_trap_source(r, item, sources_by_id)
        if outcome is None:
            continue
        scored.append((r.model_identifier, r.condition.value, r.item_id, outcome))

    by_condition_outcomes: dict[str, list[tuple[bool, str]]] = defaultdict(list)
    by_model_condition_outcomes: dict[tuple[str, str], list[tuple[bool, str]]] = defaultdict(list)
    for model, cond, item_id, outcome in scored:
        by_condition_outcomes[cond].append((outcome, item_id))
        by_model_condition_outcomes[(model, cond)].append((outcome, item_id))

    by_condition = {}
    for cond, pairs in by_condition_outcomes.items():
        outcomes = [p[0] for p in pairs]
        item_ids = [p[1] for p in pairs]
        result = compute_m1_from_outcomes(outcomes, item_ids)
        by_condition[cond] = {"n": result.n, "rate": result.rate, "ci": _bootstrap_result_to_dict(result.ci)}

    by_model_condition = {}
    for (model, cond), pairs in by_model_condition_outcomes.items():
        outcomes = [p[0] for p in pairs]
        item_ids = [p[1] for p in pairs]
        result = compute_m1_from_outcomes(outcomes, item_ids)
        by_model_condition[f"{model}|{cond}"] = {
            "n": result.n,
            "rate": result.rate,
            "ci": _bootstrap_result_to_dict(result.ci),
        }

    # Per-item rate for each (model, condition), derived from the same outcomes already
    # collected above -- reused, not recomputed, so the paired test and the by-model-condition
    # table can never silently disagree about which responses were scored.
    def _per_item_rates(model: str, condition: str) -> dict[str, float]:
        by_item: dict[str, list[bool]] = defaultdict(list)
        for outcome, item_id in by_model_condition_outcomes[(model, condition)]:
            by_item[item_id].append(outcome)
        return {item_id: sum(v) / len(v) for item_id, v in by_item.items()}

    paired_results = {}
    raw_pvalues = {}
    for model in MODELS:
        naive_by_item = _per_item_rates(model, "retrieval_naive")
        notice_by_item = _per_item_rates(model, "retrieval_with_notice")
        common = sorted(set(naive_by_item) & set(notice_by_item))
        diffs = [notice_by_item[i] - naive_by_item[i] for i in common]
        test = paired_bootstrap_permutation_test(diffs)
        paired_results[model] = {
            "n_items": test.n_items,
            "mean_diff": test.mean_diff,
            "ci_low": test.ci_low,
            "ci_high": test.ci_high,
            "raw_p": test.p_value,
        }
        raw_pvalues[model] = test.p_value

    adjusted = holm_correction(raw_pvalues)
    for model in MODELS:
        paired_results[model]["holm_p"] = adjusted[model]

    # Within-item seed agreement (the seed-stability check reported in section 4.2).
    seed_groups: dict[tuple[str, str, str], list[bool]] = defaultdict(list)
    for model, cond, item_id, outcome in scored:
        seed_groups[(model, cond, item_id)].append(outcome)

    seed_agreement = {}
    for model in MODELS:
        groups = [v for (m, _c, _i), v in seed_groups.items() if m == model and len(v) >= 2]
        agree_3_of_3 = sum(1 for v in groups if len(v) == 3 and (sum(v) == 3 or sum(v) == 0))
        total = len(groups)
        seed_agreement[model] = {"n_groups": total, "n_3_of_3_agree": agree_3_of_3}

    return {
        "by_condition": by_condition,
        "by_model_condition": by_model_condition,
        "paired_test_naive_vs_notice": paired_results,
        "seed_agreement": seed_agreement,
    }


def compute_m3_section() -> dict:
    labels_raw = _load_csv_labels(ROOT / "data/human/m3_hand_labels.csv")
    key = _load_key(ROOT / "data/interim/eval/m3_labeling_key.json")

    labels = [M3Label(labels_raw[cid]) for cid in labels_raw]
    item_ids = [key[cid]["item_id"] for cid in labels_raw]
    overall = compute_m3_from_labels(labels, item_ids)

    by_model: dict[str, dict] = {}
    grouped: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for cid, lab in labels_raw.items():
        grouped[key[cid]["model"]].append((lab, key[cid]["item_id"]))
    for model, rows in grouped.items():
        m3_labels = [M3Label(lab) for lab, _iid in rows]
        iids = [iid for _lab, iid in rows]
        result = compute_m3_from_labels(m3_labels, iids)
        by_model[model] = {
            "n": result.n,
            "rates": {str(k): v for k, v in result.rates.items()},
            "cis": {str(k): _bootstrap_result_to_dict(v) for k, v in result.cis.items()},
        }

    return {
        "overall": {
            "n": overall.n,
            "counts": {str(k): v for k, v in overall.counts.items()},
            "rates": {str(k): v for k, v in overall.rates.items()},
            "cis": {str(k): _bootstrap_result_to_dict(v) for k, v in overall.cis.items()},
        },
        "by_model": by_model,
    }


def compute_correctness_section() -> dict:
    labels_raw = _load_csv_labels(ROOT / "data/human/correctness_hand_labels.csv")
    key = _load_key(ROOT / "data/interim/eval/correctness_labeling_key.json")

    labels = [Correctness(labels_raw[cid]) for cid in labels_raw]
    item_ids = [key[cid]["item_id"] for cid in labels_raw]
    overall = compute_correctness(labels, item_ids)

    return {
        "overall": {
            "n": overall.n,
            "counts": {str(k): v for k, v in overall.counts.items()},
            "rates": {str(k): v for k, v in overall.rates.items()},
            "cis": {str(k): _bootstrap_result_to_dict(v) for k, v in overall.cis.items()},
        }
    }


def main() -> None:
    items = load_items()
    sources = load_sources()
    items_by_id = {i.item_id: i for i in items}
    sources_by_id = {s.source_registry_id: s for s in sources}

    cache = ResponseCache(ROOT / "data/interim/eval/model_responses.jsonl")
    responses = list(cache.all_responses())
    assert len(responses) == 900, f"expected 900 cached responses, found {len(responses)}"

    report = {
        "n_responses": len(responses),
        "n_items": len(items),
        "m1": compute_m1_section(responses, items_by_id, sources_by_id),
        "m3": compute_m3_section(),
        "correctness": compute_correctness_section(),
    }

    out_json = ROOT / "results/reproduced_paper_numbers.json"
    out_json.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"wrote {out_json}")

    m1 = report["m1"]
    lines = ["# Reproduced paper numbers (retraction_bench.reproduce / `retraction-bench evaluate`)", ""]
    lines.append("## M1 by condition")
    for cond, d in m1["by_condition"].items():
        ci = d["ci"]
        lines.append(f"- `{cond}`: n={d['n']}, rate={d['rate']:.3f}, CI=[{ci['ci_low']:.3f}, {ci['ci_high']:.3f}]")
    lines.append("")
    lines.append("## M1 paired test (retrieval_with_notice - retrieval_naive)")
    lines.append("| Model | Mean diff | 95% CI | Raw p | Holm p |")
    lines.append("|---|---|---|---|---|")
    for model, d in m1["paired_test_naive_vs_notice"].items():
        ci_str = f"[{d['ci_low']:+.3f}, {d['ci_high']:+.3f}]"
        lines.append(f"| `{model}` | {d['mean_diff']:+.3f} | {ci_str} | {d['raw_p']:.4f} | {d['holm_p']:.4f} |")
    lines.append("")
    lines.append("## Seed agreement")
    for model, d in m1["seed_agreement"].items():
        lines.append(f"- `{model}`: {d['n_3_of_3_agree']}/{d['n_groups']} groups fully agree across seeds")
    lines.append("")
    lines.append("## M3 overall")
    for label, rate in report["m3"]["overall"]["rates"].items():
        ci = report["m3"]["overall"]["cis"][label]
        lines.append(f"- `{label}`: {rate:.3f} [{ci['ci_low']:.3f}, {ci['ci_high']:.3f}]")
    lines.append("")
    lines.append("## Correctness overall")
    for label, rate in report["correctness"]["overall"]["rates"].items():
        ci = report["correctness"]["overall"]["cis"][label]
        lines.append(f"- `{label}`: {rate:.3f} [{ci['ci_low']:.3f}, {ci['ci_high']:.3f}]")

    out_md = ROOT / "results/reproduced_paper_numbers.md"
    out_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {out_md}")


if __name__ == "__main__":
    main()
