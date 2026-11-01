# Phase 1 item 1: item-clustered NLI CIs vs. the originally published (unclustered) ones

Prereg: `prereg/phase1_item1_clustered_nli_ci.md`. Post hoc re-analysis — same cached NLI scores
(`data/interim/eval/faithfulness_check_nli.json`, 362 scored pairs across 24 items), only the CI
method changes. Point estimates are identical by construction; only interval width can differ.

## Headline number (Abstract, §4.11)

| | Point estimate | Original (unclustered) 95% CI | Clustered 95% CI (n=24 items) |
|---|---|---|---|
| Not-contradiction rate | 97.2% (352/362) | [95.3%, 98.9%] | **[93.7%, 99.7%]** |

**The clustered interval is ~67% wider** (5.99 points vs. 3.59 points) and comes materially closer
to the 95% boundary on its lower edge, but the qualitative finding is unchanged: even under the
more conservative, correctly-clustered interval, the rate is not meaningfully lower than the
original claim. The original 97.2% point estimate itself does not change.

## Full breakdown

| Stratum | n (responses) | n (items) | Point est. | Unclustered CI | Clustered CI |
|---|---|---|---|---|---|
| Overall: ENTAILMENT | 362 | 24 | 60.5% | [55.5%, 65.5%] | [46.7%, 72.9%] |
| Overall: NEUTRAL | 362 | 24 | 36.7% | [31.8%, 41.7%] | [25.2%, 49.9%] |
| Overall: CONTRADICTION | 362 | 24 | 2.8% | [1.1%, 4.7%] | [0.3%, 6.3%] |
| By condition: `retrieval_naive` | 196 | 24 | 100.0% | [100.0%, 100.0%] | [100.0%, 100.0%]* |
| By condition: `retrieval_with_notice` | 166 | 23 | 94.0% | [90.3%, 97.6%] | [86.7%, 99.4%] |
| By model: gpt-oss-120b | 130 | 24 | 96.2% | [92.3%, 99.2%] | [90.6%, 100.0%] |
| By model: qwen2.5:7b | 112 | 23 | 97.3% | [93.8%, 100.0%] | [91.6%, 100.0%] |
| By model: llama3.1:8b | 120 | 21 | 98.3% | [95.8%, 100.0%] | [94.6%, 100.0%] |

\* `retrieval_naive`'s [100.0%, 100.0%] is not a computation artifact from a degenerate single
cluster — there are 24 real item-clusters here, but zero of the 196 scored responses under this
condition were labeled CONTRADICTION, so the bootstrap resampling distribution has genuinely zero
variance to report either way. Reported as the true result, not suppressed.

## Code change made
`src/retraction_bench/eval/faithfulness_check.py`'s `report()` function still computes the
original, unclustered values (left unchanged so the original published numbers remain
independently reproducible from the same module). This new, separate script
(`scripts/phase1_clustered_nli_ci.py`) recomputes the clustered comparison without modifying or
replacing the original function.

## Recommendation (not yet applied to the manuscript)
Replace §4.11's reported CI for the 97.2% headline number with the clustered interval
[93.7%, 99.7%], and note explicitly that this is the one evaluation-phase CI in the paper that
was not already item-clustered before this pass (every M1/M3/Correctness CI already used
`bootstrap_proportion_ci_clustered`).
