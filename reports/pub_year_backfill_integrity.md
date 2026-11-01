# pub_year backfill integrity check

| ROLE | N | pub_year BEFORE (non-null) | pub_year AFTER (non-null) | SOURCE |
|---|---|---|---|---|
| background | 325086 | 323458 | 323458 | corpus_background_pubmed_fetch |
| benchmark_source | 28 | 0 | 28 | fresh_pubmed_esummary_lookup |
| supersession_notice | 24 | 0 | 0 | unresolvable_no_real_external_identifier |
| superseding_evidence | 29 | 0 | 29 | fresh_pubmed_esummary_lookup |

## Checks

- A. Every corpus row has a lookup row (1:1): PASS (325167 corpus rows, 325167 lookup rows)
- B. All 57 real-PMID benchmark-role rows resolved: PASS (57/57)
- C. Background pub_year unchanged (pmid-for-pmid against the live corpus file): PASS
- D. Backfill module never references benchmark gold files/loaders (static source scan): PASS
- E. Every lookup row carries a documented source: PASS

**Overall: ALL CHECKS PASS**

## Known, disclosed gap (not a failure of this backfill)

1628 background rows have no pub_year in either the before or after state -- these were already missing a parseable year in the original `mesh_fetch.py` EFetch XML (PubMed itself reported no `JournalIssue/PubDate/Year`), carried through unchanged, not introduced by this backfill.

## supersession_notice (24 rows): explicitly unresolvable, not guessed

Every one of the 24 notice rows has `pub_year=None`, `source=unresolvable_no_real_external_identifier`. See `pub_year_backfill.py` module docstring for why: the notice's `pmid` field is a synthetic placeholder, and no separate real identifier for the notice itself exists in `SupersededSource`.
