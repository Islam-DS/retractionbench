# Pool-wide notice-length distribution (ADR-084, corrected by ADR-087)

**Status: exploratory, prompted by ADR-081, not itself a test of ADR-081's correlation.**
This measures how much of the 296-candidate pool has short, title-dominant notices versus
substantive ones. It does not test whether length predicts retrieval rank -- that would
require running the retrieval ceiling against all 296, which this measurement does not do.

**This file was corrected 2026-08-11 (ADR-087).** The original run joined candidates to
Retraction Watch rows by `OriginalPaperPubMedID`; 37 of the 296 candidate PMIDs have more than
one raw Retraction Watch row (mostly Expression-of-Concern-then-Retraction pairs), and the
PMID-based join sometimes grabbed the wrong row. Corrected below by joining on `record_id`,
the same field the candidate pool itself was built from. See ADR-087 for the full root-cause
account and a before/after table.

## Method

For each of the 296 unique candidates (`data/interim/tier1_candidates_final3_verified.csv`,
deduplicated by PMID per ADR-066), the retraction notice PMID is read from Retraction Watch's
own raw data (`RetractionPubMedID`, `data/raw/retraction_watch_2026-08-05.csv`), **joined by**
**`record_id` (the field the candidate pool itself was selected on), not by PMID** -- PMID-based
joins are unreliable here because 37 candidate PMIDs have more than one raw Retraction Watch
row. A candidate is excluded from the length measurement (no separate notice document to
measure) if `RetractionPubMedID` is blank/zero, or equals the candidate's own
`OriginalPaperPubMedID` (ADR-071's exact criterion). For every remaining candidate, the notice
PMID's own title and abstract are fetched via a batched PubMed EFetch call and concatenated
(`f"{title} {abstract}".strip()`), and the character length of that string is recorded.

**Methodological note, stated plainly:** this uses each notice PMID's own raw PubMed
title/abstract fields, not the hand-verified `notice_text` field used for the 9 benchmark
items in `results/notice_length_correlation.md` (ADR-081). The two are a similar but not
identical text source -- this measurement trades hand-verification for pool-wide coverage.

## Reconciled against ADR-071's "5 of 296" figure -- ADR-071 was correct

ADR-071's original figure, re-derived here with the corrected `record_id` join: **same-PMID-as-
original = 5, exactly matching ADR-071.** The two extra cases the original (buggy) run of this
measurement counted were both candidates whose specific `record_id` has a distinct, real notice
PMID, but whose *original paper's PMID* happens to also appear on an unrelated Retraction Watch
row (a different `record_id`, a different correction event) that does have `RetractionPubMedID
== OriginalPaperPubMedID` -- the PMID-based join grabbed that unrelated row instead of the
correct one. See ADR-087 for the two specific record_ids and the full root-cause account.

## Result (corrected)

| | n | % of 296 |
|---|---|---|
| No separate notice document (blank/zero `RetractionPubMedID`) | 23 | 7.8% |
| No separate notice document (same PMID as original, matches ADR-071) | 5 | 1.7% |
| **No separate notice document, total** | **28** | **9.5%** |
| Notice length measured | 268 | 90.5% |

**Length distribution, n=268 (characters):**

| Statistic | Value |
|---|---|
| Min | 11 |
| P25 | 128 |
| Median | 161 |
| Mean | 333.7 |
| P75 | 242 |
| Max | 2814 |
| Stdev | 480.5 |

| Range (chars) | n | % |
|---|---|---|
| 0-50 | 18 | 6.7% |
| 50-100 | 17 | 6.3% |
| 100-200 | 143 | 53.4% |
| 200-300 | 39 | 14.6% |
| 300-500 | 13 | 4.9% |
| 500-1000 | 11 | 4.1% |
| 1000-2000 | 22 | 8.2% |
| 2000-10000 | 5 | 1.9% |

**66.4% of notices with any content at all are under 200 characters** -- squarely in the
range occupied by RB-0007 (159 chars) and RB-0008 (121 chars), the two `bare` notices ADR-077
found ranking above their trap source. Only 10.1% exceed 1000 characters. The mean (333.7)
sits well above the median (161) -- a right-skewed distribution, a small number of long,
detailed notices pulling the mean up while the typical notice is short. **The correction did
not change the substantive conclusion** -- the corrected figures are marginally stronger in
the same direction as the original (wrong) ones, not a reversal.

Items 18-21 (the batch pre-screened in ADR-085) were checked directly against this correction
and are unaffected: none of their four original PMIDs has a duplicate Retraction Watch row,
and their notice PMIDs match exactly what `results/item18-21_raw_material.md` already used.

## Interpretation -- held at the hypothesis level, exactly as ADR-081 was

This does not test ADR-081's correlation. It does establish the premise the author's
hypothesis needs to be worth pursuing: **most of the pool's notices are short.** If notice
length does predict retrieval rank the way the n=8 benchmark-item correlation suggests
(ADR-081), then most notices in this pool would be expected to retrieve *well* --
**precisely because they say nothing.** Combined with ADR-083's finding that item 17's
notice, one of the few in this pool actually sought out for its explanatory content, turned
out to be paywalled and unreadable rather than short-but-present, the pattern this project
has now observed twice, from two different angles, both point the same way: **the more a
correction actually says, the harder it is for anyone -- human or machine -- to reach it.**
Stated explicitly as a hypothesis for a future pass with the statistical power to test it
(ideally with a measured open-access/paywall rate alongside length, using Retraction Watch's
own `Paywalled` field, not used in this measurement), not claimed here.
