# Claim-type hand-labeling: instructions

`claim_type_hand_labels.csv` is a fixed-seed random sample of 100 tier-1 candidates
(Retraction, post-2015, PMID-resolvable, `tier_1_clean`), drawn across all 39 `(HSC)`
subjects, shuffled so labeling order doesn't track any subject grouping.

For each row, fill in `human_label` with exactly one of:

- `clinical_intervention` -- named drug, device, procedure, or behavioural
  intervention, with a human clinical or economic outcome.
- `clinical_observational` -- human study, epidemiological or diagnostic
  claim, no intervention tested.
- `preclinical` -- cell line, animal model, in-vitro mechanism,
  bioinformatics-only.
- `unclear` -- genuinely can't tell from title + article type alone.

Judge from `title` and `article_type` only -- the same information the
heuristic screen sees. Do not look up the paper. This is a specificity/genre
judgment, not a clinical correctness judgment (same distinction as the
rejection-rate pilot).

The screen's own predictions are deliberately **not** in this file, to avoid
anchoring your judgment. Once `human_label` is filled in for all 100 rows,
report back and the agreement rate (with a confidence interval) will be
computed and recorded in `docs/DECISIONS.md` ADR-021.
