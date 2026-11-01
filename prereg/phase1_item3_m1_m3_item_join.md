# Prereg: Phase 1 item 3 — item-level join of M1 (retrieval_with_notice) and M3 (post_notice)

**Status: post hoc re-analysis of already-published results, prespecified before running — not a
pre-registration.**

- **Timestamp:** 2026-10-03
- **Git commit at time of writing:** `88309ed802fa074547589613f87f682c55f68c5c`
- **Motivation:** The Discussion currently infers that citation behavior under retrieval and
  acknowledgment behavior under direct confrontation reflect "an evidence-integration bottleneck...
  rather than a comprehension failure" from the *aggregate* contrast between section 4.2 and
  section 4.4's rates. This has never been tested at the item level: are the specific items where
  a model cites the trap under `retrieval_with_notice` the same items it later acknowledges under
  `post_notice`? This re-analysis joins the two at that level, per model.
- **Hypothesis:** H0: within a model, item-level `cites_superseded` under `retrieval_with_notice`
  and item-level `acknowledges` (vs. not) under `post_notice` are independent. H1: they are
  associated (in either direction).
- **Unit of analysis:** item x model. Where multiple seeds exist for the same item x model x
  condition cell, collapse to a single binary value per cell by majority vote across seeds
  (ties, if any, reported explicitly and excluded from that cell rather than broken arbitrarily).
- **Test:** A clustered association statistic appropriate to a 2x2 binary join at this n — a
  paired/matched-pairs test (McNemar's) is not applicable here since this is not a within-subject
  before/after design; instead compute Cohen's phi coefficient (equivalent to Pearson correlation
  for two binary variables) with a cluster-aware CI via `stats.bootstrap_ci` resampling at the
  item level (this is already the right resampling unit here, since item IS the unit of analysis
  — "clustered" in the sense of resampling items with replacement, matching this project's
  existing bootstrap convention, not a different library).
- **Primary endpoint:** phi coefficient per model, with bootstrap CI (10,000 resamples, seed 42,
  matching `stats/bootstrap.py`'s existing defaults).
- **Alpha:** 0.05 (CI excludes 0 as the significance criterion, consistent with this project's
  existing convention of reporting CIs rather than bare p-values for descriptive associations).
- **Scope/exclusion rule, stated before running:** This join is only computable for items that
  are both notice-eligible (have a `retrieval_with_notice` M1 score) AND have an M3 hand label
  under `post_notice` for that model — the actual n will be reported exactly, and if it is too
  small (a real possibility given M3's hand-labeled subsample, e.g. gpt-oss's n=6) the result for
  that model will be reported as descriptive only, not a tested association.
- **Explicitly prespecified interpretation rule:** The Discussion's "not a comprehension failure"
  inference will be deleted or rewritten to match exactly what this join supports — if the join
  shows no association (or is too small to test), the inference will be marked as not supported
  by item-level evidence, not retained on the strength of the aggregate contrast alone.
- **No new model calls:** uses only the existing cached M1 results and the existing M3 hand
  labels (`data/human/m3_hand_labels.csv`).
