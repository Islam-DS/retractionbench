# Author-Cluster Analysis of the Candidate Pool

**Corrected 2026-08-10 (ADR-066): the pool is 296 unique candidates, not 364.** 68 of the
364 rows in `tier1_candidates_final3_verified.csv` are the same `record_id` exported twice
(or, in 4 cases, three times) because it matched more than one domain's MeSH query --
21.6% cross-domain overlap among unique candidates, far higher than the <0.1% overlap in
the full background corpus. This is a property of this project's own per-domain export, not
a Retraction Watch data error. See ADR-066 for the full investigation. The record counts
below (87 records touched, 31 names) were already computed per-`record_id` and are
unchanged; only the percentages, which divided by 364, are corrected here.

Prompted by picking Yoshitaka Fujii as the very first item-1 candidate (RW record 1471) --
a reminder that a benchmark drawn from retracted literature risks oversampling a small
number of famous fabrication scandals rather than measuring evidence-currency tracking in
general. See `docs/DECISIONS.md` ADR-031 for the cap decision this feeds and
`ANNOTATION.md` section 3.1.2 for the resulting inclusion criterion.

## Method

Retraction Watch's `Author` field is a semicolon-separated list of full names per record
(confirmed against real data, e.g. record 1471: `"Yoshitaka Fujii;Hiroyoshi Tanaka;Mutsuko
Ito"`). Every candidate's author list was split into individual names
(`curate/author_clusters.py`, tested) and counted across the full 364-candidate pool for
the three final domains. A name counts once per distinct record regardless of author
position (first, last, or middle).

## Result

**1,631 distinct individual author names appear across the pool. 31 of them appear
on 3 or more distinct records. Those 31 names collectively touch 87/296 unique candidates
(29.4%)** (was reported as 87/364 = 23.9% before the duplicate-record correction, ADR-066 --
the record count was always correct, only the denominator was wrong).

**2026-10-05 independent re-verification (author-requested, item 3):** re-ran
`author_clusters.py`'s `clusters()`/`author_record_map()` directly against a fresh load of
`data/interim/tier1_candidates_final3_verified.csv` to confirm 87/31/296 were genuinely
recomputed on distinct papers, not the row-based 87/364 figure relabeled with a new
denominator. Confirmed independently: `df['record_id'].nunique()` = 296; `clusters(df,
min_size=3)` returns exactly 31 authors; the union of their `record` sets has exactly 87
members. This is not a coincidence of the correction -- `author_record_map` keys each author's
tally on a `set()` of `record_id` values (not rows), so a duplicated row (same `record_id`
exported under two domains) was never double-counted in the numerator to begin with; only the
364->296 unique-paper denominator used for the percentage needed fixing. The script's own test
suite (`tests/test_author_clusters.py`) already exercises this set-based dedup logic on
synthetic data; this round's check additionally confirms it against the real, live candidate
file, not just a synthetic fixture.

**Domain sub-counts corrected 2026-08-10 (ADR-066)** -- previously each domain a record was
cross-listed under added to that author's domain sub-count independently, so e.g. Boldt's
sub-counts summed to 15 against a reported total of 13. Using the same first-listed-domain
convention as the per-domain table above, sub-counts now sum exactly to the record total:

| Author | Records | Domains |
|---|---|---|
| Joachim Boldt | 13 | Pharmacology 11, Rehab/Therapy 2 |
| Gunter G Hempelmann | 11 | Pharmacology 9, Rehab/Therapy 2 |
| Ahmed Badawy | 10 | Ob/Gyn 10 |
| Ahmed M Maged | 9 | Ob/Gyn 9 |
| Jun Iwamoto | 7 | Pharmacology 3, Ob/Gyn 2, Rehab/Therapy 2 |
| Tsuyoshi Takeda | 6 | Ob/Gyn 2, Rehab/Therapy 2, Pharmacology 2 |
| Ahmed Mohamed Abbas | 6 | Ob/Gyn 6 |
| Zatollah Asemi | 5 | Ob/Gyn 3, Pharmacology 2 |
| Yoshitaka Fujii | 5 | Pharmacology 5 |
| Hideo Matsumoto | 5 | Pharmacology 3, Rehab/Therapy 2 |
| Donal P O'Mathuna | 5 | Rehab/Therapy 5 |
| ... 20 more, each 3-4 records | -- | -- |

(Record counts per author were always correct -- `author_record_map` keys on unique
`record_id`, so no author's total was ever double-counted, only the domain sub-breakdown
was, before this correction. Full 31-row table is reproducible via
`curate/author_clusters.clusters()` against the deduplicated candidate CSV.)

**Per-domain concentration is uneven** (corrected 2026-08-10, ADR-066 -- domain assignment
for the 64 cross-domain-listed records uses "first-listed domain in the original per-domain
export" as one documented convention, not a claimed-correct partition; a different
convention would shift these, especially Pharmacology and Rehabilitation/Therapy):

| Domain | Records touched by a cluster | Pool size | Share |
|---|---|---|---|
| Obstetrics/Gynecology | 48 | 119 | 40.3% |
| Rehabilitation/Therapy | 15 | 57 | 26.3% |
| Pharmacology | 24 | 120 | 20.0% |

(Previously reported, before the duplicate-record correction: Ob/Gyn 48/119=40.3%
unchanged; Pharmacology 44/156=28.2%; Rehabilitation/Therapy 19/89=21.3%.)

Obstetrics/Gynecology is worst affected, driven by three overlapping author names (Ahmed
Badawy 10, Ahmed M Maged 9, Ahmed Mohamed Abbas 6) whose retraction reasons are
`Concerns/Issues about Data`, `Unreliable Results and/or Conclusions`, and
`Investigation by Journal/Publisher` or `Investigation by Third Party` -- checked directly,
not assumed. This is a materially different reason profile from Boldt and Fujii, whose RW
reason tags explicitly say `Falsification/Fabrication of Data/Image/Results`. The
Ob/Gyn cluster's reason profile (data/results concerns triggering third-party
investigation, no explicit fabrication tag) is consistent with the "implausible trial"
pattern documented elsewhere in the literature for small RCTs from a handful of prolific
groups, though this analysis does not independently confirm that specific characterization
-- it only reports what Retraction Watch's own reason tags say for these records.

## Why this matters for the benchmark

Whatever drove any individual cluster -- proven fabrication (Boldt, Fujii) or an
unresolved data-integrity investigation (the Ob/Gyn cluster) -- including many items tied
to one author is a sampling-independence problem for this benchmark specifically: a model
that has simply seen a famous retraction wave in training data could answer correctly by
pattern-matching the scandal, not by tracking evidence currency in general. Both failure
modes look the same from the benchmark's perspective and both are addressed by the same
fix.

## Decision

A cap of **2 items per author** applies during final selection of the 90-item benchmark
(`curate/author_clusters.authors_over_cap`, checked against every individual author name,
not just first/last author). See ADR-031. Even in the worst-affected domain
(Obstetrics/Gynecology, 40.3% of its pool touched by a cluster), 71/119 candidates are
untouched by any 3+ cluster, leaving ample room to reach 30 items without relying on
capped-out authors.
