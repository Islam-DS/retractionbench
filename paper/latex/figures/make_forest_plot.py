"""Main-text forest plot for M1 (ADR-153; Phase 6 redesign).

a: within-model paired effect of adding the supersession notice (retrieval_with_notice minus
   retrieval_naive), with the raw cited/total counts for each condition in the margin, as Annals
   of Internal Medicine asks for forest plots.
b: post hoc between-model contrasts of those effects (difference of paired differences, seeds
   collapsed by majority vote).

Data, read directly (never transcribed):
  results/reproduced_paper_numbers.json              -- per-model rates, n, paired test (panel a)
  results/phase1_item2_redo_paired_contrasts.json    -- pairwise contrasts, Holm p (panel b)
Run `retraction-bench evaluate` (or `make reproduce`) first if the first file is stale or missing.
"""

import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _style import FULL_WIDTH, GRAY, INK, save, set_rcparams

ROOT = Path(__file__).resolve().parent.parent.parent.parent
REPRO = ROOT / "results/reproduced_paper_numbers.json"
PAIRWISE = ROOT / "results/phase1_item2_redo_paired_contrasts.json"

MODELS = ["llama3.1:8b-instruct-q4_K_M", "openai/gpt-oss-120b", "qwen2.5:7b-instruct-q4_K_M"]
SHORT = {
    "llama3.1:8b-instruct-q4_K_M": "Llama 3.1 8B",
    "openai/gpt-oss-120b": "GPT-OSS 120B",
    "qwen2.5:7b-instruct-q4_K_M": "Qwen 2.5 7B",
}
PAIRS = [
    "llama3.1:8b-instruct-q4_K_M vs qwen2.5:7b-instruct-q4_K_M",
    "llama3.1:8b-instruct-q4_K_M vs openai/gpt-oss-120b",
    "qwen2.5:7b-instruct-q4_K_M vs openai/gpt-oss-120b",
]
XLIM = (-0.6, 0.6)

set_rcparams()


def cited_count(cell: dict) -> int:
    k = cell["rate"] * cell["n"]
    assert abs(k - round(k)) < 1e-6, cell
    return round(k)


def sgn(x: float) -> str:
    return f"{x:+.3f}".replace("-", "−")


def fmt_p(p: float) -> str:
    return f"{p:.3f}" if p >= 0.001 else "<0.001"


def forest_rows(ax, axt, rows, header, col_x):
    """rows: (label, estimate, lo, hi, [table strings]). The table sits in its own axes (axt),
    sharing the forest axis's rows, with right-aligned columns at col_x (axes fraction)."""
    n = len(rows)
    for i, (label, est, lo, hi, cols) in enumerate(rows):
        y = n - 1 - i
        ax.plot([lo, hi], [y, y], color=INK, linewidth=1.0, solid_capstyle="butt", zorder=2)
        ax.plot(est, y, marker="s", markersize=4.5, color=INK, zorder=3, linestyle="none")
        for x, text in zip(col_x, cols, strict=True):
            axt.text(x, y, text, va="center", ha="right", transform=axt.get_yaxis_transform())
    for x, text in zip(col_x, header, strict=True):
        axt.text(x, n - 0.3, text, va="bottom", ha="right", fontweight="bold", transform=axt.get_yaxis_transform())
    ax.axvline(0, color=GRAY, linewidth=0.6, linestyle=(0, (3, 2)), zorder=1)
    ax.set_yticks(range(n))
    ax.set_yticklabels([r[0] for r in reversed(rows)])
    ax.tick_params(axis="y", length=0)
    ax.spines["left"].set_visible(False)
    for a in (ax, axt):
        a.set_ylim(-0.6, n + 0.35)
    ax.set_xlim(*XLIM)
    axt.axis("off")


def main() -> None:
    repro = json.loads(REPRO.read_text(encoding="utf-8"))["m1"]
    pairwise = json.loads(PAIRWISE.read_text(encoding="utf-8"))["primary_majority_vote"]

    rows_a = []
    for m in MODELS:
        d = repro["paired_test_naive_vs_notice"][m]
        naive = repro["by_model_condition"][f"{m}|retrieval_naive"]
        notice = repro["by_model_condition"][f"{m}|retrieval_with_notice"]
        rows_a.append((
            SHORT[m], d["mean_diff"], d["ci_low"], d["ci_high"],
            [f"{cited_count(naive)}/{naive['n']}", f"{cited_count(notice)}/{notice['n']}", str(d["n_items"]),
             f"{sgn(d['mean_diff'])} ({sgn(d['ci_low'])} to {sgn(d['ci_high'])})", fmt_p(d["holm_p"])],
        ))
    rows_b = []
    for pair in PAIRS:
        d = pairwise["pairwise"][pair]
        a, b = pair.split(" vs ")
        rows_b.append((
            f"{SHORT[a].split()[0]} vs {SHORT[b].split()[0]}", d["mean_diff_of_diffs"], d["ci"][0], d["ci"][1],
            ["", "", str(d["n_items"]),
             f"{sgn(d['mean_diff_of_diffs'])} ({sgn(d['ci'][0])} to {sgn(d['ci'][1])})",
             fmt_p(pairwise["holm_adjusted_pairwise_p"][pair])],
        ))

    fig = plt.figure(figsize=(FULL_WIDTH, 2.85))
    gs = fig.add_gridspec(2, 2, width_ratios=[0.78, 1.22], hspace=0.95, wspace=0.03,
                          left=0.15, right=0.995, top=0.9, bottom=0.13)
    ax_a, axt_a = fig.add_subplot(gs[0, 0]), fig.add_subplot(gs[0, 1])
    ax_b, axt_b = fig.add_subplot(gs[1, 0]), fig.add_subplot(gs[1, 1])
    col_x = [0.15, 0.30, 0.39, 0.85, 1.0]
    forest_rows(ax_a, axt_a, rows_a, ["Naive\ncited", "Notice\ncited", "Items", "Difference (95% CI)", "Holm P"], col_x)
    forest_rows(ax_b, axt_b, rows_b, ["", "", "Items", "Difference (95% CI)", "Holm P"], col_x)
    ax_a.set_xlabel("Change in trap-source citation rate with the notice present")
    ax_b.set_xlabel("Difference between the two models' notice effects")
    for ax, letter in ((ax_a, "a"), (ax_b, "b")):
        bbox = ax.get_position()
        fig.text(0.005, bbox.y1 + 0.02, letter, fontsize=8, fontweight="bold", va="bottom")
    save(fig, "fig_forest_paired_m1")


if __name__ == "__main__":
    main()
