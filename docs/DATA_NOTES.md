# Data Notes

> Skeleton only. Every anomaly, edge case, and judgement call encountered
> during ingestion, curation, or annotation gets an entry here — this is
> the record the project protocol's verification rule points to for any
> retraction-status discrepancy that isn't a clean Retraction Watch + PubMed
> tag match.

## Format

Each entry: date, affected record(s) (by `source_registry_id` / `item_id`), what was anomalous, what decision was made, and why.

## Entries

### 2026-08-05 -- Retraction Watch source acquisition

- Source URL: https://gitlab.com/crossref/retraction-watch-data/-/raw/main/retraction_watch.csv
- Access date: 2026-08-05
- Cached to: data\raw\retraction_watch_2026-08-05.csv
- Access method: anonymous HTTPS GET (see docs/DECISIONS.md ADR-015 for why, not `git clone`).

### 2026-08-05 -- Phase 1 exploration: data quality findings

- Completely blank source rows (every field null -- a CSV export artifact): 215 records out of 71540 total rows. Excluded from every count below and from the exploration report; the raw DuckDB table is unmodified and still contains them.
- RetractionDate unparseable (present but malformed, strict M/D/YYYY H:MM): 1 records.
- OriginalPaperDate unparseable: 1 records.
- RetractionDate missing (blank): 0 records.
- OriginalPaperDate missing (blank): 0 records.
- OriginalPaperDOI present but not valid DOI syntax: 0 records.
- RetractionDOI present but not valid DOI syntax: 2 records.
- Duplicate Record IDs (among non-blank rows only): 0 rows across 0 distinct IDs -- not deduplicated at this stage; Stage 1B decides how to handle these.
- Negative RetractionDate-OriginalPaperDate gaps (retraction predates the paper it retracts -- always a data error, excluded from section 9's distribution): 0 records.
- Implausibly long gaps (> 40 years, flagged but included in section 9's distribution): 71 records.

### 2026-08-06 -- PubMed tag verification (the project protocol) run against the 3 final-domain candidate pool

Ran `retraction-bench ingest verify-pubmed` against the 364-candidate export for
the three confirmed domains (Pharmacology 156, Ob/Gyn 119, Rehab/Therapy 89 --
see ADR-021, ADR-026, ADR-027). Every PMID was queried live against NCBI's
ESummary endpoint, not inferred. Result:

- **336/364 (92.3%) confirmed**: PubMed's own record carries the `Retracted
  Publication` publication-type tag, matching Retraction Watch.
- **27/364 (7.4%) discrepancy -- lookup succeeded, tag absent.** These are
  real ESummary responses (verified live, not a code bug -- see below) whose
  `pubtype` list does not include `Retracted Publication`, despite the paper
  being a `Retraction`-nature entry in Retraction Watch. One example checked
  directly: PMID 37940041's PubMed title has been edited to
  `"WITHDRAWN: The Effect of Preoperative Intravenous Tranexamic Acid..."` --
  PubMed acknowledges the withdrawal in the citation text itself, but the
  `pubtype` field was never updated to carry the tag. This indicates PubMed's
  own tagging is sometimes incomplete or lagged relative to the retraction
  notice, not that Retraction Watch is wrong. Per section 4's rule ("or the
  discrepancy is documented in `docs/DATA_NOTES.md`"), these 27 are treated
  as retracted on the strength of Retraction Watch plus this documented
  PubMed gap, not silently dropped and not silently included without a flag.
  Every one of the 27 is individually listed in
  `data/interim/tier1_candidates_final3_verified.csv`
  (`pubmed_retracted_tag_confirmed=False`, `pubmed_lookup_error=""` --
  empty error is exactly what distinguishes this case from a genuine lookup
  failure). Full list and per-domain counts kept in that file rather than
  duplicated here since it is a regenerable pipeline artifact.
  Sub-pattern noted, not yet explained: 5 of the 27 are different PMIDs for
  what appears to be the same underlying Cochrane review ("Therapeutic touch
  for healing acute wounds", record_ids 31158-31162) -- multiple republished
  versions, none carrying the tag. Not yet investigated further; worth a
  second look if this review is a live annotation candidate.
- **1/364 (0.3%) genuine lookup error**: PMID 38355237 returned
  `"cannot get document summary"` from ESummary -- an actual unresolvable-ID
  response, not a missing tag. Verified live.

Initial ad hoc analysis of the "unconfirmed" set mis-classified 27 of the 28
as lookup errors, because it read the cache/output CSV with pandas' default
NA handling, which silently turns an intentionally-empty `pubmed_lookup_error`
string into `NaN` and breaks an `!= ''` comparison. Re-run with
`keep_default_na=False` gave the correct split above. No code in
`src/retraction_bench/ingest/pubmed.py` was wrong -- the bug was in a
throwaway analysis script, not the pipeline -- but worth noting since it
nearly produced a false "these are all just bad PMIDs" conclusion in this
file.

### 2026-08-06 -- PubMed/Retraction Watch completeness checked in both directions (paper finding, not just a data note)

The 27-record gap above turned out to be a real, standalone result, not a
footnote: characterised by year, journal, publisher, and reason, and checked
in the inverse direction (PubMed-tagged retractions RW does not list). Full
writeup, tables, and the drafted methods-subsection prose are in
`results/pubmed_rw_completeness_check.md`; the decision this feeds is
`docs/DECISIONS.md` ADR-029. Headline: **7.4% [Wilson 95% CI 5.15%, 10.58%]**
of RW-listed retractions in the candidate pool lack PubMed's own tag despite
resolving cleanly (not indexing lag alone -- the gap persists in decade-old
records), and within a bounded 19-journal check, **11.3%** of PubMed-tagged
retractions have no matching RW entry at all. Neither source is
independently complete.
