# Abstract-overwrite measurement across the candidate pool

**Corrected 2026-08-10 (ADR-066): the pool is 296 unique candidates, not 364** -- 68 rows in
`tier1_candidates_final3_verified.csv` are the same `record_id` exported once per matching
domain (a property of this project's own per-domain MeSH export, not a Retraction Watch
data error; full investigation in ADR-066). The headline figure below is now the
unique-PMID count; the original by-row figure is kept for comparison, not deleted.

Measured 2026-08-10, prompted by item 6 (record 5685, Boldt et al.): its original 1991
abstract is not merely hard to find -- it has been overwritten in PubMed's own structured
record, with the `<Abstract>` field now containing only the retraction statement. That
raised a broader question: how common is this specific failure mode across the whole
364-candidate pool, distinct from a *bare* notice (status not machine-readable) or a
genuinely *absent* abstract?

## Method

For every candidate's own PMID (the retracted paper's PMID, not its separate retraction
notice's PMID), fetched the current PubMed record via EFetch and classified its
`<Abstract>` field into exactly one of three states:

- **`no_abstract`** -- no `<AbstractText>` element present at all.
- **`replaced_by_retraction_text`** -- the field is present but contains retraction
  boilerplate instead of the original scientific content: either the text starts with a
  known retraction-notice opening phrase ("This article has been retracted...", "This paper
  has been retracted...", "The publisher regrets...", etc.), or it is short (<=120 words),
  contains a "retract" root word, and lacks any structured-abstract section marker
  (Background/Methods/Results/Conclusions/Objective/etc.).
- **`original_retained`** -- everything else.

**Classifier validated against 5 known cases before trusting it at scale**: the four
sources already verbatim-confirmed for RB-0001 through RB-0004 (all `original_retained`,
correctly classified) and record 5685/PMID 2025077 (known `replaced_by_retraction_text` from
item 6's raw material, correctly classified once the word-count threshold was widened to
accommodate its longer-than-typical retraction statement -- an early version of the
classifier missed this exact case, caught by the validation step before running at scale).
Also spot-checked 8 of the 23 row-level `replaced_by_retraction_text` results and the 10
shortest `original_retained` abstracts by hand; all matched their assigned category.

## A finding along the way, now investigated and corrected (ADR-066)

Checking PMIDs before fetching found **296 unique PMIDs across the 364 candidate rows** --
68 rows share a PMID with another row in the same pool. **Investigated 2026-08-10: every
one of the 64 duplicate-PMID groups is the same single `record_id` exported once per
domain it matched** (32 Ob/Gyn+Pharmacology, 26 Pharmacology+Rehabilitation/Therapy, 2
Ob/Gyn+Rehabilitation/Therapy, 4 all three) -- this project's own per-domain MeSH export
concatenated without deduplicating on `record_id`, not a Retraction Watch data-quality
issue and not two distinct RW records pointing at one paper. Full investigation in
ADR-066, which also recomputes every other pool-wide figure affected by this (author-cluster
shares, PubMed-tag verification rates).

## Result

**The unique-PMID row is now the headline figure (296, not 364).**

| | n | proportion | Wilson 95% CI | 95% bootstrap CI |
|---|---|---|---|---|
| `replaced_by_retraction_text` (n=296, unique) | 17 | 5.74% | **[3.62%, 9.00%]** | [3.04%, 8.45%] |
| `no_abstract` (n=296, unique) | 22 | 7.43% | -- | -- |
| `original_retained` (n=296, unique) | 257 | 86.82% | -- | -- |
| *`replaced_by_retraction_text` (n=364, by row, superseded)* | *23* | *6.32%* | *[4.25%, 9.30%]* | *[3.85%, 8.79%]* |
| *`no_abstract` (n=364, by row, superseded)* | *26* | *7.14%* | *--* | *--* |
| *`original_retained` (n=364, by row, superseded)* | *315* | *86.54%* | *--* | *--* |

**2026-10-05 post hoc addendum: a Wilson score interval column was added** (every other
binomial proportion in this paper is reported with a Wilson CI, not a bootstrap CI; this row
was the one exception, caught during an author-requested audit of every "Wilson"-labeled CI in
the manuscript -- this specific cell was never mislabeled "Wilson" in the paper text, but was
inconsistent with the paper's own convention). The Wilson interval is now the headline CI cited
in `paper.md`; the original percentile-bootstrap CI (10,000 resamples, seed 20260810) is kept,
not deleted, for comparison -- the two methods agree closely (both roughly [3-3.6%, 8.5-9.0%]),
so this is a labeling/convention fix, not a substantive change to the finding.

## Why this matters for the paper

This completes a three-way pattern worth stating plainly in the methods/discussion: a
retracted paper's original content can fail to reach a reader in at least three distinct
ways, and they are not interchangeable:

1. **Notice not machine-readable** -- the retraction *notice* itself carries no verifiable
   text (`notice_specificity = unverifiable`/`bare`, ADR-033/042). The source paper's own
   content is intact; what's missing is the explanation for why it shouldn't be trusted.
2. **Content uninformative** -- the notice exists and is verifiable, but says nothing
   substantive about the mechanism (`notice_specificity = bare`, confirmed empty via two
   independent sources).
3. **Claim erased** -- measured here: the retracted paper's *own* abstract, in the record
   that would normally preserve it, has been overwritten by retraction boilerplate. Roughly
   1 in 17 candidates in this pool (5.74% of 296 unique candidates). A RAG system that retrieves this record
   would not retrieve the trap claim at all -- it would retrieve a paper-shaped document that
   says nothing but "this was retracted," which is a different (arguably better) outcome
   than retrieving the original claim, but also means this specific failure mode cannot be
   used to build a benchmark item (item 6/record 5685 was rejected for exactly this reason).

Machine-readable code and full classification per record_id: `abstract_overwrite_measurement.json`.
