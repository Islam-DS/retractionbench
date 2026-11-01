"""Supplementary summary figure (Phase 6 redesign): every headline measurement of the evidence
lifecycle as a dot with its 95% interval and its own numerator/denominator, grouped by stage.

Replaces the earlier bar chart, which showed bars without intervals (Annals of Internal Medicine
advises against bars without a measure of variability) and printed section numbers that went
stale when the manuscript was restructured. Each row has its own denominator; rows are separate
measurements on different units, not a funnel.

Data, read directly (never transcribed); Wilson intervals are computed here from the counts,
item-clustered bootstrap intervals are read from the files that computed them:
  results/phase5_27_gap_case_diagnosis_v2.json, results/phase6_funnel_counts.json -- curated pool
  results/phase5_part_b_scaled_check_v2.json  -- random sample (see EXCLUDED_WRONG_PMID)
  results/retrieval_ceiling_report.json        -- notice ranks
  results/replacement_retrieval_ceiling.json   -- replacement-evidence ranks
  results/reproduced_paper_numbers.json        -- M1, M3, Correctness
  results/replacement_citation_check.json      -- replacement citation when retrieved
"""

import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from statsmodels.stats.proportion import proportion_confint

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _style import FULL_WIDTH, INK, LIGHT, save, set_rcparams

ROOT = Path(__file__).resolve().parent.parent.parent.parent
R = ROOT / "results"
RETRIEVAL_K = 5
# Part B record whose Retraction Watch PMID is a truncation of the real one (1834920 vs 18349203);
# excluded from numerator and denominator in the case-by-case re-check (Supplementary S1.6.3).
EXCLUDED_WRONG_PMID = "1834920"

set_rcparams()


def load(name):
    return json.loads((R / name).read_text(encoding="utf-8"))


def wilson(k, n):
    lo, hi = proportion_confint(k, n, alpha=0.05, method="wilson")
    return k / n, lo, hi


def rows_by_stage():
    gaps = load("phase5_27_gap_case_diagnosis_v2.json")
    pool = load("phase6_funnel_counts.json")["three_domain_pool"]["distinct_papers"]

    part_b = load("phase5_part_b_scaled_check_v2.json")["results"]
    resolved = [r for r in part_b if r["classification"] != "unresolved_pubmed_lookup_failed"]
    assert any(r["pmid"] == EXCLUDED_WRONG_PMID and r["is_gap"] for r in resolved)
    resolved = [r for r in resolved if r["pmid"] != EXCLUDED_WRONG_PMID]
    b_gaps = sum(1 for r in resolved if r["is_gap"])

    ceiling = [r for r in load("retrieval_ceiling_report.json")["per_item"] if r.get("notice_rank")]
    top3 = sum(1 for r in ceiling if r["notice_rank"] <= 3)
    repl = [r for r in load("replacement_retrieval_ceiling.json")["per_item"] if r.get("status") == "indexed"]
    repl_hit = sum(1 for r in repl if r["rank"] <= RETRIEVAL_K)

    repro = load("reproduced_paper_numbers.json")
    m1 = repro["m1"]["by_condition"]
    m3 = repro["m3"]["overall"]
    corr = repro["correctness"]["overall"]
    cite = load("replacement_citation_check.json")
    cite_ci = cite["citation_rate_given_retrieved_item_clustered_ci"]

    def clustered(est, ci):
        return est, ci["ci_low"], ci["ci_high"]

    def m1_row(cond, label):
        d = m1[cond]
        k = round(d["rate"] * d["n"])
        return (label, (d["rate"], d["ci"]["ci_low"], d["ci"]["ci_high"]), f"{k}/{d['n']} responses")

    return [
        ("Scientific record", [
            ("Retraction not tagged in PubMed: curated pool", wilson(len(gaps), pool), f"{len(gaps)}/{pool} papers"),
            ("Retraction not tagged in PubMed: random sample", wilson(b_gaps, len(resolved)), f"{b_gaps}/{len(resolved)} records"),
        ]),
        ("Retrieval", [
            ("Notice ranks in the top 3", wilson(top3, len(ceiling)), f"{top3}/{len(ceiling)} items"),
            (f"Replacement evidence in the top {RETRIEVAL_K}", wilson(repl_hit, len(repl)), f"{repl_hit}/{len(repl)} items"),
        ]),
        ("Model behavior", [
            m1_row("retrieval_naive", "Retracted source cited, notice removed"),
            m1_row("retrieval_with_notice", "Retracted source cited, notice present"),
            ("Replacement cited when retrieved", clustered(cite["citation_rate_given_retrieved"], cite_ci),
             f"{cite['n_of_those_where_model_cited_replacement']}/{cite['n_responses_with_replacement_actually_retrieved']} responses"),
            ("Correction acknowledged when shown directly", clustered(m3["rates"]["acknowledges"], m3["cis"]["acknowledges"]),
             f"{m3['counts']['acknowledges']}/{m3['n']} hand-labeled"),
            ("Answer correct, all conditions", clustered(corr["rates"]["correct"], corr["cis"]["correct"]),
             f"{corr['counts']['correct']}/{corr['n']} hand-labeled"),
        ]),
    ]


def main() -> None:
    stages = rows_by_stage()
    lines = []  # (kind, payload)
    for stage, rows in stages:
        lines.append(("stage", stage))
        lines.extend(("row", r) for r in rows)
    n = len(lines)

    fig = plt.figure(figsize=(FULL_WIDTH, 0.21 * n + 0.55))
    ax = fig.add_axes([0.40, 0.11, 0.38, 0.87])
    ax.set_ylim(-0.6, n - 0.4)
    for i, (kind, payload) in enumerate(lines):
        y = n - 1 - i
        if kind == "stage":
            ax.annotate(payload, xy=(0.01, y), xycoords=("figure fraction", "data"), fontweight="bold", va="center")
            continue
        label, (est, lo, hi), count = payload
        ax.plot([lo, hi], [y, y], color=INK, linewidth=1.0, solid_capstyle="butt")
        ax.plot(est, y, marker="o", markersize=4, color=INK, linestyle="none")
        ax.annotate(label, xy=(-0.02, y), xycoords=("axes fraction", "data"), ha="right", va="center")
        ax.annotate(count, xy=(1.03, y), xycoords=("axes fraction", "data"), ha="left", va="center")
    ax.set_ylim(-0.6, n - 0.4)
    ax.set_xlim(-0.03, 1.03)
    ax.set_xticks([0, 0.25, 0.5, 0.75, 1.0])
    ax.set_xticklabels(["0", "25", "50", "75", "100"])
    for x in (0.25, 0.5, 0.75):
        ax.axvline(x, color=LIGHT, linewidth=0.4, zorder=0)
    ax.set_yticks([])
    ax.spines["left"].set_visible(False)
    ax.set_xlabel("Rate (%), with 95% interval")
    save(fig, "fig_failure_cascade")


if __name__ == "__main__":
    main()
