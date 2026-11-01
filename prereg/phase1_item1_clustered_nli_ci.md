# Prereg: Phase 1 item 1 — item-clustered CIs for the NLI faithfulness check (§4.11)

**Status: post hoc re-analysis of already-published results, prespecified before running — not a
pre-registration (no OSF/AsPredicted record exists).**

- **Timestamp:** 2026-10-03
- **Git commit at time of writing:** `88309ed802fa074547589613f87f682c55f68c5c`
- **Motivation:** `eval/faithfulness_check.py`'s `report()` calls plain `bootstrap_proportion_ci`
  (not `_clustered`) on a list of per-response NLI labels. Every other evaluation-phase CI in this
  project (M1, M3, Correctness) already uses `bootstrap_proportion_ci_clustered`. This is the one
  remaining inconsistency identified in Phase 0's audit.
- **Hypothesis:** None — this is a methods-consistency recomputation, not a hypothesis test.
- **Primary endpoint:** The "not-contradiction" rate (overall, by condition, by model) from the
  cached `data/interim/eval/faithfulness_check_nli.json`, recomputed with
  `bootstrap_proportion_ci_clustered` (cluster = `item_id`, recovered by joining `response_id`
  back to `data/interim/eval/model_responses.jsonl`) instead of the current unclustered call.
- **Test:** No hypothesis test — CI recomputation only. Both the original (unclustered) and new
  (clustered) point estimates and intervals will be reported side by side; the point estimate is
  identical between methods by construction (clustering changes the resampling unit, not the
  statistic), only CI width can differ.
- **Degenerate-interval rule:** If a stratum collapses to a single cluster, report the point
  estimate and state explicitly that the interval is degenerate (collapses to the point) rather
  than report a zero-width interval as if it reflected real certainty.
- **Alpha:** N/A (no hypothesis test).
- **Exclusion rules:** Unchanged from the original check — only parsed `retrieval_naive`/
  `retrieval_with_notice` responses that cite the trap source enter the NLI pairs set; no new
  exclusion introduced.
- **No new model/NLI calls:** reuses the existing cached scoring output in full.
