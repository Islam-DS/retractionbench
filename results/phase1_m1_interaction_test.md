# Phase 1 item 2: condition x model interaction test for M1

Prereg: `prereg/phase1_item2_m1_interaction_test.md`.

n=422 responses, 24 items, 3 models.

## GLMM attempt (prespecified primary model) -- completed, but flagged as unreliable, not trusted as primary

`BinomialBayesMixedGLM` with crossed random effects `(1|item_id) + (1|seed)` ran without an
exception, but its results are **not treated as the primary, trustworthy result**, for a reason
caught by comparing it against the GEE fallback rather than assumed in advance:

| Interaction term | GLMM mean (log-odds) | GLMM SD | Implied z | GEE raw p |
|---|---|---|---|---|
| condition x gpt-oss-120b | -1.882 | 0.464 | -4.06 (nominally significant) | **0.1548 (not significant)** |
| condition x qwen2.5:7b | -3.528 | 0.334 | -10.56 (significant) | **0.0058 (significant)** |

The two methods **disagree on the gpt-oss interaction** -- the GLMM's variational-Bayes posterior
implies it is significant; the asymptotically-justified GEE says it is not. This is consistent
with a known property of variational Bayes fits (posterior variance underestimation), compounded
by the `(1|seed)` random effect having only 3 levels -- too few to estimate a variance component
reliably, exactly the concern flagged in the prereg before running. **The GLMM result is reported
for transparency, not relied on**; the GEE result below is treated as primary.

## GEE fallback (fixed effects: condition * model, clustered on item_id) -- primary result

No separate `seed` random effect (GEE has no crossed-random-effects analog) -- a named deviation
from the original model spec, reported rather than silently substituted.

| Interaction term | Raw p | Holm-adjusted p |
|---|---|---|
| condition[T.retrieval_with_notice]:model[T.openai/gpt-oss-120b] | 0.1548 | 0.1548 |
| condition[T.retrieval_with_notice]:model[T.qwen2.5:7b-instruct-q4_K_M] | 0.0058 | 0.0115 |

**Interpretation (prespecified rule applied):** the qwen interaction term survives Holm
correction (0.0115 < 0.05); the gpt-oss interaction term does not (0.1548). This is a **partial**
confirmation of the "three distinct patterns" framing, not a full one: it formally supports that
**qwen's response to the notice differs significantly from llama's** (the reference level), but
does **not** formally support that **gpt-oss's response differs significantly from llama's** --
consistent with the paper's own existing characterization of gpt-oss as "inconclusive" rather than
a third clearly distinct pattern. The manuscript's three-patterns language should be read, and
ideally reworded, as: two of the three pairwise model comparisons are statistically distinguishable
from each other (qwen vs. llama), the third (gpt-oss vs. llama) is not — not three independently
confirmed distinct effects.
