# Phase 1 item 2, REDONE: paired per-item contrasts across models (VB GLMM discarded)

Prereg: `prereg/phase1_item2_m1_interaction_test.md` (fallback path, now primary by author
instruction). The original BinomialBayesMixedGLM run is discarded -- logged, not reused,
in `docs/ANALYSIS_LOG.md`.

## Primary: seeds collapsed by majority vote within item x model x condition

Omnibus Friedman test across all 3 models (items common to all three, n=21): chi2=8.968, p=0.0113

### All three pairwise contrasts (Holm-corrected across the 3)

| Pair | n items | mean diff-of-diffs | 95% CI | raw p | Holm p |
|---|---|---|---|---|---|
| llama3.1:8b-instruct-q4_K_M vs qwen2.5:7b-instruct-q4_K_M | 21 | +0.381 | [+0.190,+0.571] | 0.0073 | 0.0219 |
| llama3.1:8b-instruct-q4_K_M vs openai/gpt-oss-120b | 21 | +0.095 | [-0.095,+0.286] | 0.6248 | 0.6248 |
| qwen2.5:7b-instruct-q4_K_M vs openai/gpt-oss-120b | 24 | -0.208 | [-0.500,+0.083] | 0.2690 | 0.5379 |

## Check: continuous per-item citation rate across seeds (not majority-vote-binarized)

Omnibus Friedman (n=21): chi2=7.824, p=0.0200

| Pair | n items | mean diff-of-diffs | 95% CI | raw p | Holm p |
|---|---|---|---|---|---|
| llama3.1:8b-instruct-q4_K_M vs qwen2.5:7b-instruct-q4_K_M | 21 | +0.381 | [+0.190,+0.571] | 0.0073 | 0.0219 |
| llama3.1:8b-instruct-q4_K_M vs openai/gpt-oss-120b | 21 | +0.111 | [-0.032,+0.270] | 0.1860 | 0.2978 |
| qwen2.5:7b-instruct-q4_K_M vs openai/gpt-oss-120b | 24 | -0.208 | [-0.472,+0.042] | 0.1489 | 0.2978 |

## Interpretation (prespecified rule applied)

**qwen vs. gpt-oss is NOT significant after Holm correction.** Per the author's prespecified wording rule: this is reported as **'one detected effect, two non-detections'** -- qwen's own within-model notice effect is the one pairwise contrast against llama that survives correction; gpt-oss's contrast against llama does not, and qwen's contrast against gpt-oss itself also does not, meaning the data do not support treating qwen and gpt-oss as two separately confirmed distinct patterns from each other, only each as distinct-or-not from llama individually.
