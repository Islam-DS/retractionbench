"""Main-text Figure 1 (Phase 6 redesign): study design in two panels, plain line art.

a: the five measurements RetractionBench separates, in evidence-lifecycle order, each with the
   unit it is measured on -- replaces the earlier colored-box conceptual figure.
b: what the model is given under each of the four conditions -- replaces the earlier four-row
   box-and-arrow conditions figure.

Schematic only: no data values are drawn, so nothing here can drift from a results file.
"""

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, Rectangle

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _style import FULL_WIDTH, GRAY, INK, LINE, save, set_rcparams

set_rcparams()

MEASURES = [
    ("$R_c$", "Correction\nretrieved", "per item"),
    ("$R_r$", "Replacement\nretrieved", "per item"),
    ("$U_s$", "Retracted source\ncited", "per response"),
    ("$U_r$", "Replacement\ncited", "per response"),
    ("$C$", "Answer\ncorrect", "hand-labeled\nsubsample"),
]

COLUMNS = ["Question", "Top-5 retrieved\ndocuments", "Retraction notice", "Model's own\nprior answer"]
CONDITIONS = [
    ("no_retrieval", ["yes", "no", "no", "no"]),
    ("retrieval_naive", ["yes", "yes", "removed", "no"]),
    ("retrieval_with_notice", ["yes", "yes", "guaranteed", "no"]),
    ("post_notice", ["yes", "no", "shown directly", "yes"]),
]
SYMBOL = {"yes": "●", "no": "–"}


def panel_a(ax) -> None:
    ax.set_xlim(-0.05, 10.05)
    ax.set_ylim(0, 1.6)
    ax.axis("off")
    w, h, gap = 1.62, 0.78, (10 - 5 * 1.62) / 4
    for i, (sym, name, unit) in enumerate(MEASURES):
        x0 = i * (w + gap)
        ax.add_patch(Rectangle((x0, 0.62), w, h, fill=False, edgecolor=INK, linewidth=LINE))
        ax.text(x0 + w / 2, 0.62 + h - 0.13, sym, ha="center", va="top", fontsize=8)
        ax.text(x0 + w / 2, 0.62 + 0.26, name, ha="center", va="center", linespacing=1.15)
        ax.text(x0 + w / 2, 0.46, unit, ha="center", va="top", color=GRAY, linespacing=1.1)
        if i < len(MEASURES) - 1:
            ax.add_patch(FancyArrowPatch((x0 + w + 0.05, 1.01), (x0 + w + gap - 0.05, 1.01),
                                         arrowstyle="-|>", mutation_scale=7, linewidth=LINE, color=INK))


def panel_b(ax) -> None:
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 5.2)
    ax.axis("off")
    col_x = [3.55, 5.15, 6.95, 8.75]
    header_y, row_h = 4.55, 0.88
    ax.plot([0, 10], [5.15, 5.15], color=INK, linewidth=LINE)
    ax.text(0.05, header_y, "Condition", va="center", fontweight="bold")
    for x, col in zip(col_x, COLUMNS, strict=True):
        ax.text(x, header_y, col, ha="center", va="center", fontweight="bold", linespacing=1.1)
    ax.plot([0, 10], [3.95, 3.95], color=INK, linewidth=0.5)
    for r, (cond, cells) in enumerate(CONDITIONS):
        y = 3.5 - r * row_h
        ax.text(0.05, y, cond, va="center", family="monospace")
        for x, cell in zip(col_x, cells, strict=True):
            text = SYMBOL.get(cell, cell)
            ax.text(x, y, text, ha="center", va="center", fontsize=8 if cell in SYMBOL else 7,
                    style="normal" if cell in SYMBOL else "italic")
    ax.plot([0, 10], [3.5 - 3 * row_h - 0.45, 3.5 - 3 * row_h - 0.45], color=INK, linewidth=LINE)


def main() -> None:
    fig = plt.figure(figsize=(FULL_WIDTH, 3.05))
    ax_a = fig.add_axes([0.02, 0.60, 0.96, 0.36])
    ax_b = fig.add_axes([0.02, 0.02, 0.96, 0.50])
    panel_a(ax_a)
    panel_b(ax_b)
    fig.text(0.005, 0.965, "a", fontsize=8, fontweight="bold", va="top")
    fig.text(0.005, 0.53, "b", fontsize=8, fontweight="bold", va="top")
    save(fig, "fig_conceptual_framework")


if __name__ == "__main__":
    main()
