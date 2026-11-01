"""M1 reliability check, part A: compare the LLM-judge's labels (eval/run_llm_judge.py output)
against the author's own hand labels and report Cohen's kappa via curate/scoring.py -- reusing
the exact scoring function already validated for the claim-type screen (ADR-021), not a new
metric implementation.

Pre-registered threshold (docs/CORRECTNESS_RUBRIC.md): kappa >= 0.75 for Correctness. M3 has no
formally pre-registered threshold in docs/M3_RUBRIC.md; this script applies the same 0.75 bar for
consistency and says so explicitly in the report, rather than silently reusing it as if it had
been pre-registered too.

Usage: python scripts/validate_llm_judge_agreement.py <m3|correctness|both>
"""

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from retraction_bench.curate.scoring import score  # noqa: E402

TASKS = {
    "m3": {
        "hand_labels": ROOT / "data/human/m3_hand_labels.csv",
        "judge_output": ROOT / "data/interim/eval/m3_llm_judge_results.jsonl",
        "labels": ["acknowledges", "silently_revises", "defends", "unclear"],
    },
    "correctness": {
        "hand_labels": ROOT / "data/human/correctness_hand_labels.csv",
        "judge_output": ROOT / "data/interim/eval/correctness_llm_judge_results.jsonl",
        "labels": ["correct", "incorrect", "refused"],
    },
}
KAPPA_THRESHOLD = 0.75


def load_hand_labels(path: Path) -> dict[str, str]:
    with path.open(encoding="utf-8", newline="") as f:
        return {row["response_id"]: row["human_label"] for row in csv.DictReader(f)}


def load_judge_labels(path: Path) -> dict[str, str | None]:
    out: dict[str, str | None] = {}
    if not path.exists():
        return out
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                row = json.loads(line)
                out[row["response_id"]] = row["judge_label"]
    return out


def run_task(name: str) -> None:
    cfg = TASKS[name]
    hand = load_hand_labels(cfg["hand_labels"])
    judge = load_judge_labels(cfg["judge_output"])

    if not judge:
        print(f"[{name}] No judge output found at {cfg['judge_output']} -- run "
              f"`python -m retraction_bench.eval.run_llm_judge {name}` first.")
        return

    missing = [rid for rid in hand if rid not in judge]
    unparsed = [rid for rid in hand if judge.get(rid) is None and rid in judge]
    scored_ids = [rid for rid in hand if judge.get(rid) is not None]

    y_true = [hand[rid] for rid in scored_ids]
    y_pred = [judge[rid] for rid in scored_ids]
    result = score(y_true, y_pred, cfg["labels"])

    print(f"\n=== {name} ===")
    print(f"Hand-labeled: {len(hand)} | Judge output present: {len(judge)} | "
          f"Missing from judge output: {len(missing)} | Unparsed (judge_label=None): {len(unparsed)}")
    print(f"Scored (both labels present): n={result.n}")
    print(f"Raw agreement: {result.agreement}/{result.n} = {result.agreement_rate:.3f} "
          f"(95% CI [{result.agreement_ci[0]:.3f}, {result.agreement_ci[1]:.3f}])")
    print(f"Cohen's kappa: {result.cohens_kappa:.3f}")
    threshold_note = " (pre-registered)" if name == "correctness" else " (applied for consistency, not pre-registered in M3_RUBRIC.md)"
    verdict = "MEETS" if result.cohens_kappa >= KAPPA_THRESHOLD else "BELOW"
    print(f"Threshold: kappa >= {KAPPA_THRESHOLD}{threshold_note} -> {verdict}")
    print("Per-class:")
    for cm in result.per_class:
        print(f"  {cm.label:<18} precision={cm.precision:.3f} recall={cm.recall:.3f} support={cm.support}")
    print("Confusion (true, pred) -> count, off-diagonal only:")
    for (t, p), c in result.confusion.items():
        if t != p and c:
            print(f"  ({t} -> {p}): {c}")
    if missing:
        print(f"NOTE: {len(missing)} hand-labeled response_ids have no judge output at all -- rerun the judge to cover them before trusting this kappa as final.")


def main() -> None:
    if len(sys.argv) != 2 or sys.argv[1] not in (*TASKS, "both"):
        print(f"Usage: python {sys.argv[0]} <m3|correctness|both>")
        raise SystemExit(1)
    names = TASKS.keys() if sys.argv[1] == "both" else [sys.argv[1]]
    for name in names:
        run_task(name)


if __name__ == "__main__":
    main()
