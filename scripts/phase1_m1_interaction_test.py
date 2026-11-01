"""Phase 1 item 2 (prereg/phase1_item2_m1_interaction_test.md): condition x model interaction
test for M1, replacing the "three distinct empirical patterns" framing's implicit reliance on
three separate per-model paired tests with one joint test of whether model identity actually
moderates the notice's effect.

No new model calls -- uses the existing 900 cached responses, scored via eval/citation.py's
`cites_trap_source` (the same function `eval/m1.py`'s compute_m1 is built on), exactly matching
M1's own exclusion rule (unparsed responses excluded, not counted as non-citation).
"""

import json
from pathlib import Path

import numpy as np
import pandas as pd

from retraction_bench.curate.benchmark_io import load_items, load_sources
from retraction_bench.eval.citation import cites_trap_source
from retraction_bench.rag.cache import ResponseCache
from retraction_bench.rag.collect import notice_eligible_item_ids
from retraction_bench.stats.paired_test import holm_correction

ROOT = Path(__file__).resolve().parent.parent
OUT_JSON = ROOT / "results/phase1_m1_interaction_test.json"
OUT_MD = ROOT / "results/phase1_m1_interaction_test.md"
SCORED_CONDITIONS = {"retrieval_naive", "retrieval_with_notice"}


def build_dataset() -> pd.DataFrame:
    items = {i.item_id: i for i in load_items()}
    sources = {s.source_registry_id: s for s in load_sources()}
    eligible_ids = notice_eligible_item_ids(list(items.values()), sources)

    cache = ResponseCache(ROOT / "data/interim/eval/model_responses.jsonl")
    rows = []
    for r in cache.all_responses():
        if r.condition.value not in SCORED_CONDITIONS or r.item_id not in eligible_ids:
            continue
        outcome = cites_trap_source(r, items[r.item_id], sources)
        if outcome is None:
            continue  # unparsed or no trap-source pmid -- excluded, not counted as non-citation
        rows.append(
            {
                "item_id": r.item_id,
                "model": r.model_identifier,
                "seed": r.seed,
                "condition": r.condition.value,
                "cites_trap": int(outcome),
            }
        )
    return pd.DataFrame(rows)


def try_glmm(df: pd.DataFrame) -> dict:
    """Crossed random effects (1|item) + (1|seed) via BinomialBayesMixedGLM's variance-components
    interface -- statsmodels' MixedLM family does not support crossed (non-nested) random effects
    directly, so this is the documented route for that structure. Falls back to a GEE clustered on
    item_id (prespecified) if this does not converge, reported as a named deviation.
    """
    from statsmodels.genmod.bayes_mixed_glm import BinomialBayesMixedGLM

    df = df.copy()
    df["condition"] = pd.Categorical(df["condition"], categories=["retrieval_naive", "retrieval_with_notice"])
    df["model"] = pd.Categorical(df["model"])

    fixed_formula = "cites_trap ~ condition * model"
    vc_formulas = {"item": "0 + C(item_id)", "seed": "0 + C(seed)"}
    try:
        fit = BinomialBayesMixedGLM.from_formula(
            fixed_formula, vc_formulas, data=df
        ).fit_vb()
        return {
            "method": "BinomialBayesMixedGLM (variational Bayes, crossed random effects item+seed)",
            "converged": True,
            "fe_names": list(fit.model.exog_names),
            "fe_mean": [float(x) for x in fit.fe_mean],
            "fe_sd": [float(x) for x in fit.fe_sd],
            "vc_mean": [float(x) for x in fit.vc_mean],
            "vc_names": list(fit.model.vc_names),
        }
    except Exception as e:  # noqa: BLE001 -- reported, not swallowed
        return {"method": "BinomialBayesMixedGLM", "converged": False, "error": str(e)}


def gee_fallback(df: pd.DataFrame) -> dict:
    """Prespecified fallback: GEE with exchangeable working correlation, clustered on item_id,
    fixed effects condition * model. Does not model a separate seed random effect (GEE has no
    crossed-random-effects analog) -- this is the named deviation from the GLMM spec.
    """
    import statsmodels.formula.api as smf
    from statsmodels.genmod.families import Binomial
    from statsmodels.genmod.generalized_estimating_equations import GEE
    from statsmodels.genmod.cov_struct import Exchangeable

    df = df.copy()
    df["condition"] = pd.Categorical(df["condition"], categories=["retrieval_naive", "retrieval_with_notice"])
    model = smf.gee(
        "cites_trap ~ condition * model",
        groups="item_id",
        data=df,
        cov_struct=Exchangeable(),
        family=Binomial(),
    )
    result = model.fit()
    # A true interaction term has BOTH "condition[" and "model[" in its name -- a naive ":" in n
    # check misfires because the Ollama model tags themselves contain a literal colon
    # (e.g. "qwen2.5:7b-instruct-q4_K_M"), which would wrongly classify a main-effect term as an
    # interaction term. Caught by inspecting the actual GEE parameter names before trusting this.
    interaction_terms = [n for n in result.params.index if "condition[" in n and "model[" in n]
    wald = result.wald_test_terms(skip_single=False) if hasattr(result, "wald_test_terms") else None
    return {
        "method": "GEE (exchangeable, clustered on item_id) -- fallback, no seed random effect",
        "converged": True,
        "params": {k: float(v) for k, v in result.params.items()},
        "pvalues": {k: float(v) for k, v in result.pvalues.items()},
        "conf_int": {k: [float(v[0]), float(v[1])] for k, v in result.conf_int().iterrows()},
        "interaction_terms": interaction_terms,
        "interaction_pvalues_raw": {k: float(result.pvalues[k]) for k in interaction_terms},
    }


def main() -> None:
    df = build_dataset()
    print(f"n responses: {len(df)}; n items: {df['item_id'].nunique()}; n models: {df['model'].nunique()}")
    print(df.groupby(["model", "condition"])["cites_trap"].agg(["mean", "count"]))

    glmm_result = try_glmm(df)
    print("\n=== GLMM attempt ===")
    print(json.dumps(glmm_result, indent=2)[:2000])

    print("\n=== GEE fallback (prespecified) ===")
    gee_result = gee_fallback(df)
    print(json.dumps({k: v for k, v in gee_result.items() if k != "params"}, indent=2))

    interaction_p = gee_result["interaction_pvalues_raw"]
    holm_adjusted = holm_correction(interaction_p) if interaction_p else {}

    report = {
        "n_responses": len(df),
        "n_items": int(df["item_id"].nunique()),
        "glmm_attempt": glmm_result,
        "gee_fallback": gee_result,
        "interaction_pvalues_holm_adjusted": holm_adjusted,
    }
    OUT_JSON.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"\nwrote {OUT_JSON}")

    any_significant = any(p < 0.05 for p in holm_adjusted.values()) if holm_adjusted else False
    lines = [
        "# Phase 1 item 2: condition x model interaction test for M1",
        "",
        "Prereg: `prereg/phase1_item2_m1_interaction_test.md`.",
        "",
        f"n={len(df)} responses, {df['item_id'].nunique()} items, {df['model'].nunique()} models.",
        "",
        "## GLMM attempt (prespecified primary model)",
        "",
        f"`BinomialBayesMixedGLM` with crossed random effects (1|item_id) + (1|seed): "
        f"**{'converged' if glmm_result.get('converged') else 'DID NOT CONVERGE / FAILED'}**.",
    ]
    if not glmm_result.get("converged"):
        lines.append(f"Error: `{glmm_result.get('error')}`")
        lines.append("")
        lines.append(
            "Falling back to the prespecified GEE (exchangeable working correlation, clustered on "
            "`item_id`), which does not include a separate `seed` random effect -- a named "
            "deviation from the original model spec, not a silent substitution."
        )
    lines += [
        "",
        "## GEE fallback results (fixed effects: condition * model, clustered on item_id)",
        "",
        "| Interaction term | Raw p | Holm-adjusted p |",
        "|---|---|---|",
    ]
    for term, p in interaction_p.items():
        lines.append(f"| {term} | {p:.4f} | {holm_adjusted.get(term, float('nan')):.4f} |")
    lines += [
        "",
        f"**Interpretation (prespecified rule applied):** "
        + (
            "At least one condition x model interaction term is significant after Holm correction "
            "(alpha=0.05) -- consistent with model identity genuinely moderating the notice's "
            "effect, supporting (not just describing) the 'three distinct patterns' framing."
            if any_significant
            else
            "**No condition x model interaction term is significant after Holm correction "
            "(alpha=0.05).** Per the prespecified interpretation rule, this is reported plainly: "
            "a formal interaction test does not detect model identity significantly moderating "
            "the notice's effect at this sample size. The 'three distinct empirical patterns' "
            "language describes three separate per-model point estimates (Table 3) correctly on "
            "its own terms, but should not be read as implying a statistically confirmed "
            "interaction -- that claim is not supported by this joint test and should be reworded."
        ),
    ]
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {OUT_MD}")


if __name__ == "__main__":
    main()
