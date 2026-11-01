"""Regenerates every figure in the paper from committed/cached data, in one command (ADR-153).

Run with: `uv run python scripts/make_paper_figures.py`
(run `retraction-bench evaluate` / `make reproduce` first if `results/reproduced_paper_numbers.json`
is missing or stale, and `scripts/phase6_funnel_counts.py` before the flow diagram.) Every figure is
drawn at final printed size in one shared style (`paper/latex/figures/_style.py`). The older
schematic scripts (make_schematics.py, make_conceptual_figure.py, make_item_walkthrough.py) are
superseded and no longer run; the item walkthrough is now Supplementary Table s-walkthrough.

Each figure's own script documents its data source and, where relevant, why a requested panel or
data source was left out rather than filled in with an unverified number -- see
`paper/latex/figures/make_retrievability_panels.py`'s docstring for the clearest example.
"""

import subprocess
import sys
from pathlib import Path

FIGURES_DIR = Path(__file__).resolve().parent.parent / "paper" / "latex" / "figures"

SCRIPTS = [
    "make_design_figure.py",  # fig_conceptual_framework: Figure 1, study design (schematic)
    "make_retrievability_panels.py",  # fig_retrievability_panels (retrieval_ceiling_report.json, replacement_retrieval_ceiling.json)
    "make_forest_plot.py",  # fig_forest_paired_m1 (reproduced_paper_numbers.json, phase1_item2_redo_paired_contrasts.json)
    "make_figures.py",  # fig_m3_by_model, fig_correctness_by_domain (reproduced / phase6_recomputed numbers)
    "make_failure_cascade.py",  # fig_failure_cascade: supplementary summary dot plot (several results files)
    "make_funnel.py",  # fig_funnel: supplementary flow diagram (phase6_funnel_counts.json)
]


def main() -> None:
    for script in SCRIPTS:
        print(f"--- {script} ---")
        result = subprocess.run([sys.executable, script], cwd=FIGURES_DIR)
        if result.returncode != 0:
            raise SystemExit(f"{script} failed (exit {result.returncode})")
    print("All figures regenerated.")


if __name__ == "__main__":
    main()
