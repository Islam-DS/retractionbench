"""Supplementary flow diagram of candidate screening (Phase 6 redesign), PRISMA-style: one main
column of retained counts, with the number excluded at each step in a side box.

Replaces the earlier four-box funnel, which showed "n varies" for the reason-screen step. Every
count is read from results/phase6_funnel_counts.json (scripts/phase6_funnel_counts.py), whose
final screening step is asserted to reproduce the committed 364-row / 296-paper candidate pool;
exclusion counts are the differences between consecutive retained counts.
"""

import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, Rectangle

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _style import FULL_WIDTH, INK, LINE, save, set_rcparams

ROOT = Path(__file__).resolve().parent.parent.parent.parent
DATA = ROOT / "results/phase6_funnel_counts.json"

set_rcparams()

EXCLUSION_LABEL = [
    "Blank rows",
    "Other notice type (not a retraction)",
    "Retracted before 2016",
    "Original paper has no resolvable PubMed ID",
    "Reason screen: not tier_1_clean",
    "Claim-type screen: not a clinical claim",
]


def box(ax, x, y, w, h, text, bold=False):
    ax.add_patch(Rectangle((x - w / 2, y - h / 2), w, h, fill=False, edgecolor=INK, linewidth=LINE))
    ax.text(x, y, text, ha="center", va="center", fontweight="bold" if bold else "normal", linespacing=1.2)


def arrow(ax, p0, p1):
    ax.add_patch(FancyArrowPatch(p0, p1, arrowstyle="-|>", mutation_scale=6, linewidth=LINE, color=INK, shrinkA=0, shrinkB=0))


def main() -> None:
    d = json.loads(DATA.read_text(encoding="utf-8"))
    steps = d["screening_steps"]
    pool = d["three_domain_pool"]
    ann = d["annotation"]

    main_boxes = [f"{s['step']}\nn = {s['n_records']:,}" for s in steps]
    exclusions = [f"{lab}\nn = {steps[i]['n_records'] - steps[i + 1]['n_records']:,}" for i, lab in enumerate(EXCLUSION_LABEL)]
    main_boxes.append(f"Candidate pool in the three domains\nn = {pool['distinct_papers']:,} papers ({pool['rows']:,} domain rows)")
    exclusions.append(f"Not in the three domains\nn = {steps[-1]['n_records'] - pool['distinct_papers']:,}")
    main_boxes.append(f"Evaluated by hand for eligibility\nn = {ann['candidates_evaluated']}")
    exclusions.append(f"Not reached before annotation closed\nn = {pool['distinct_papers'] - ann['candidates_evaluated']:,}")
    main_boxes.append(f"Included in RetractionBench\nn = {ann['included']}")
    exclusions.append(f"Rejected, n = {ann['rejected']}\nDeferred, n = {ann['deferred']}")

    n = len(main_boxes)
    step_h = 0.5
    fig, ax = plt.subplots(figsize=(FULL_WIDTH, step_h * n + 0.1))
    ax.set_xlim(0, 10)
    ax.set_ylim(-0.4, n * 1.0 - 0.6)
    ax.axis("off")
    mx, mw, mh = 2.85, 5.3, 0.66
    ex, ew, eh = 8.15, 3.6, 0.56
    for i, text in enumerate(main_boxes):
        y = n - 1 - i
        box(ax, mx, y, mw, mh, text, bold=(i == n - 1))
        if i < n - 1:
            arrow(ax, (mx, y - mh / 2), (mx, y - 1 + mh / 2))
            ey = y - 0.5
            box(ax, ex, ey, ew, eh, exclusions[i])
            arrow(ax, (mx, ey), (ex - ew / 2, ey))
    fig.subplots_adjust(left=0.0, right=1.0, top=0.995, bottom=0.005)
    save(fig, "fig_funnel")


if __name__ == "__main__":
    main()
