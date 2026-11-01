# Prereg: Phase 1 item 2 — condition x model interaction test for M1

**Status: post hoc re-analysis of already-published results, prespecified before running — not a
pre-registration.**

- **Timestamp:** 2026-10-03
- **Git commit at time of writing:** `88309ed802fa074547589613f87f682c55f68c5c`
- **Motivation:** The paper's current claim ("three distinct empirical patterns") rests on three
  separate per-model paired tests (Table 3), not a single joint test of whether model identity
  actually moderates the notice's effect on citation. This re-analysis asks that directly.
- **Hypothesis:** H0: the effect of `condition` (`retrieval_naive` vs `retrieval_with_notice`) on
  `cites_superseded` (M1) does not differ by `model`. H1: it does (a condition x model
  interaction).
- **Model specification (fixed before fitting, not adjusted after seeing results):**
  `cites_superseded ~ condition * model + (1|item_id) + (1|seed)`, binomial family, logit link —
  a mixed-effects logistic regression (GLMM), fit via `statsmodels` (`BinomialBayesMixedGLM` or
  the closest converging equivalent available; if a crossed-random-effects GLMM fails to converge,
  fall back to a GEE with an exchangeable working correlation clustered on `item_id`, reported as
  a named deviation, not substituted silently).
- **Primary endpoint:** The condition x model interaction term(s) — Wald test (or LRT against the
  no-interaction model, whichever the fitting routine supports) p-value, plus the per-model
  simple-effect estimates (log-odds and percentage-point marginal effects) with CIs.
- **Multiple-comparison correction:** Holm correction across the per-model simple-effect tests
  that follow from the interaction (3 comparisons), matching this project's existing convention
  (`stats/paired_test.py`'s `holm_correction`).
- **Alpha:** 0.05, two-sided.
- **Exclusion rules:** Identical to the existing M1 paired test (section 4.2) — only items shared
  across the relevant model pair for condition, seed-level responses as recorded, no new
  filtering introduced.
- **Explicitly prespecified interpretation rule:** If the interaction term is not significant at
  alpha=0.05, this will be reported plainly as "no significant model x condition interaction
  detected at this sample size" and the "three distinct empirical patterns" language will be
  reworded accordingly — not defended by re-running a different specification until one is found.
  A random-effect variance estimate at or near zero for `(1|seed)` (only 3 levels) will be
  reported as a named limitation of this specific model, not hidden.
- **No new model calls:** uses only the existing 900 cached responses.
