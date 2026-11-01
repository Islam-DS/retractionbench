"""Outcome-share figures, drawn as dot-and-interval small multiples (one panel per outcome, one
row per group) instead of stacked or grouped bars, so every share is shown with its item-clustered
95% CI (Phase 6 figure redesign):

  fig_m3_by_model           -- main text: M3 label shares under post_notice, by model
  fig_correctness_by_domain -- supplement: Correctness shares, by domain

Data, read directly (never transcribed):
  results/reproduced_paper_numbers.json  -- M3 by model
  results/phase6_recomputed_numbers.json -- Correctness by domain
"""

import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _style import FULL_WIDTH, INK, LIGHT, save, set_rcparams

ROOT = Path(__file__).resolve().parent.parent.parent.parent
REPRO = ROOT / "results/reproduced_paper_numbers.json"
RECOMPUTED = ROOT / "results/phase6_recomputed_numbers.json"

set_rcparams()


def dot_panels(rows, outcomes, titles, name, descriptive_only=()):
    """rows: list of (label, {outcome: (rate, lo, hi)}). Rows in descriptive_only are drawn with
    hollow markers (shown for completeness, too small to interpret)."""
    n = len(rows)
    fig, axes = plt.subplots(1, len(outcomes), figsize=(FULL_WIDTH, 0.28 * n + 0.75), sharey=True)
    for ax, outcome, title in zip(axes, outcomes, titles, strict=True):
        for i, (label, vals) in enumerate(rows):
            y = n - 1 - i
            rate, lo, hi = vals[outcome]
            hollow = label in descriptive_only
            ax.plot([lo, hi], [y, y], color=INK, linewidth=1.0, solid_capstyle="butt")
            ax.plot(rate, y, marker="o", markersize=4.5, linestyle="none",
                    markerfacecolor="white" if hollow else INK, markeredgecolor=INK, markeredgewidth=0.9)
        ax.set_xlim(-0.04, 1.04)
        ax.set_xticks([0, 0.25, 0.5, 0.75, 1.0])
        ax.set_xticklabels(["0", "25", "50", "75", "100"])
        ax.set_xlabel(f"{title} (%)")
        for x in (0.25, 0.5, 0.75):
            ax.axvline(x, color=LIGHT, linewidth=0.4, zorder=0)
        ax.tick_params(axis="y", length=0)
        ax.spines["left"].set_visible(False)
    axes[0].set_yticks(range(n))
    axes[0].set_yticklabels([r[0] for r in reversed(rows)])
    axes[0].set_ylim(-0.6, n - 0.4)
    fig.tight_layout(pad=0.3, w_pad=1.2)
    save(fig, name)


def m3_by_model() -> None:
    by_model = json.loads(REPRO.read_text(encoding="utf-8"))["m3"]["by_model"]
    order = [("qwen2.5:7b-instruct-q4_K_M", "Qwen 2.5 7B"), ("llama3.1:8b-instruct-q4_K_M", "Llama 3.1 8B"),
             ("openai/gpt-oss-120b", "GPT-OSS 120B")]
    outcomes = ["acknowledges", "silently_revises", "defends"]
    rows, small = [], []
    for key, short in order:
        d = by_model[key]
        label = f"{short} (n={d['n']})"
        if d["n"] < 10:
            small.append(label)
        rows.append((label, {o: (d["rates"][o], d["cis"][o]["ci_low"], d["cis"][o]["ci_high"]) for o in outcomes}))
    dot_panels(rows, outcomes, ["Acknowledges", "Silently revises", "Defends"], "fig_m3_by_model", small)


def correctness_by_domain() -> None:
    dom = json.loads(RECOMPUTED.read_text(encoding="utf-8"))["domain_correctness"]
    order = [("(HSC) Medicine - Obstetrics/Gynecology", "Obstetrics/Gynecology"), ("(HSC) Medicine - Pharmacology", "Pharmacology")]
    outcomes = ["correct", "incorrect", "refused"]
    rows = []
    for key, short in order:
        d = dom[key]
        rows.append((f"{short} (n={d['n']})", {o: (d["rates"][o], d["ci"][o][0], d["ci"][o][1]) for o in outcomes}))
    dot_panels(rows, outcomes, ["Correct", "Incorrect", "Refused"], "fig_correctness_by_domain")


if __name__ == "__main__":
    m3_by_model()
    correctness_by_domain()
