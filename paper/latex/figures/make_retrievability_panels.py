"""Main-text retrieval figure: full-corpus rank of each item's supersession notice, its trap
(retracted) source, and its replacement evidence, one row per benchmark item, log-scale rank axis.

Replaces the earlier two-panel figure (a "24/24" callout plus a jittered scatter of three distinct
points), which showed only the notice side of the asymmetry section @sec:retrievability reports.
One plot now shows both sides: notices sit at ranks 1-3, replacement evidence spreads to 253,313.

Data, read directly (never transcribed):
  results/retrieval_ceiling_report.json      -- trap-source and notice rank per item
  results/replacement_retrieval_ceiling.json -- replacement-evidence rank per item (15 items)
"""

import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _style import BLUE, GREEN, INK, LIGHT, VERMILLION, save, set_rcparams

ROOT = Path(__file__).resolve().parent.parent.parent.parent
CEILING = ROOT / "results/retrieval_ceiling_report.json"
REPLACEMENT = ROOT / "results/replacement_retrieval_ceiling.json"
RETRIEVAL_K = 5  # the pipeline's own top-k (rag/prompts.py)

set_rcparams()


def main() -> None:
    ceiling = {r["item_id"]: r for r in json.loads(CEILING.read_text(encoding="utf-8"))["per_item"]}
    replacement = {
        r["item_id"]: r["rank"]
        for r in json.loads(REPLACEMENT.read_text(encoding="utf-8"))["per_item"]
        if r.get("status") == "indexed"
    }
    items = sorted(set(ceiling) | set(replacement))

    def sort_key(item):
        # items with replacement evidence first, ordered by its rank; then the rest by item id
        rep = replacement.get(item)
        return (rep is None, rep if rep is not None else 0, item)

    items.sort(key=sort_key)
    n = len(items)

    fig, ax = plt.subplots(figsize=(4.6, 0.118 * n + 0.75))
    for row, item in enumerate(items):
        y = n - 1 - row
        c = ceiling.get(item, {})
        ranks = [r for r in (c.get("trap_source_rank"), c.get("notice_rank"), replacement.get(item)) if r]
        if len(ranks) > 1:
            ax.plot([min(ranks), max(ranks)], [y, y], color=LIGHT, linewidth=0.6, zorder=1)
        if c.get("trap_source_rank"):
            ax.scatter(c["trap_source_rank"], y, marker="s", s=14, color=VERMILLION, zorder=3, linewidths=0)
        if c.get("notice_rank"):
            ax.scatter(c["notice_rank"], y, marker="o", s=16, color=BLUE, zorder=4, linewidths=0)
        if item in replacement:
            ax.scatter(replacement[item], y, marker="^", s=18, color=GREEN, zorder=5, linewidths=0)

    ax.axvline(RETRIEVAL_K + 0.5, color=INK, linewidth=0.6, linestyle=(0, (3, 2)), zorder=0)
    ax.text(RETRIEVAL_K * 1.18, n - 0.3, f"top {RETRIEVAL_K} shown to models", fontsize=6.5, va="bottom", ha="left")

    ax.set_xscale("log")
    ax.set_xlim(0.7, 1e6)
    ax.xaxis.set_major_locator(mticker.LogLocator(base=10, numticks=7))
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{v:,.0f}"))
    ax.xaxis.set_minor_locator(mticker.NullLocator())
    ax.set_ylim(-0.8, n - 0.2 + 0.9)
    ax.set_yticks(range(n))
    ax.set_yticklabels(list(reversed(items)), fontsize=6)
    ax.tick_params(axis="y", length=0)
    ax.spines["left"].set_visible(False)
    ax.set_xlabel("Rank in the full corpus for the item's own question (log scale)")

    handles = [
        ax.scatter([], [], marker="o", s=16, color=BLUE, linewidths=0),
        ax.scatter([], [], marker="s", s=14, color=VERMILLION, linewidths=0),
        ax.scatter([], [], marker="^", s=18, color=GREEN, linewidths=0),
    ]
    ax.legend(
        handles,
        ["Retraction notice", "Retracted (trap) source", "Replacement evidence"],
        loc="lower right",
        handletextpad=0.3,
        borderaxespad=0.2,
    )
    fig.tight_layout(pad=0.3)
    save(fig, "fig_retrievability_panels")


if __name__ == "__main__":
    main()
