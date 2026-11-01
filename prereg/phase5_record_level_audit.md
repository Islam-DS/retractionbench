# Prereg: Phase 5 — record-level audit (untagged-retraction diagnosis + scaled PubMed-vs-RW check)

**Status: prespecified before running, not "pre-registered" (no OSF/AsPredicted record exists).**

- **Timestamp:** 2026-10-04
- **Git commit at time of writing:** `88309ed802fa074547589613f87f682c55f68c5c` (plus this session's
  uncommitted Phase 0/1 edits, not yet committed)
- **API access confirmed before this prereg was written, no spending involved:**
  - PubMed (NCBI E-utilities): already in use throughout this project (`ingest/pubmed.py`); real
    `NCBI_EMAIL`/`NCBI_API_KEY` present in `.env`.
  - Crossref REST API: live-tested this session against a real DOI from this project's own data
    (`10.1097/MD.0000000000007072`). No key required; polite pool via `mailto` param; confirmed
    rate limit from response headers: 10 req/s, concurrency 3.
  - OpenAlex REST API: live-tested against the same real DOI, correctly returned `is_retracted:
    true`. No key required; polite pool via `mailto`; confirmed free (`x-ratelimit-cost-usd: 0`),
    generous limit (1000+ req shown remaining in the test call).
  - Retraction Watch: already downloaded as a static CSV (`data/raw/retraction_watch_2026-08-05.csv`,
    71,540 rows, 66,203 with a recorded PubMed ID), loaded into `data/interim/retraction_watch.duckdb`.
    No live RW API exists to call -- this is the only access route (ADR-015).

## Part A: diagnose the 27 untagged retractions -- full enumeration, not a sample

- **Population:** the exact 27 PMIDs already identified in `results/pubmed_rw_completeness_check.md`
  (RW `Retraction`-nature entries, PubMed's own `Retracted Publication` tag absent, within the
  364-candidate pool for this project's 3 domains). Deterministic, fully enumerable -- no sampling
  decision needed.
- **Hypothesis:** none -- a qualitative classification task, not a test.
- **For each of the 27:** record age (retraction date), publisher, RW `retraction_nature`/`reason`,
  journal; check PubMed (current tag status, re-verified live since this was first measured),
  Crossref (`relation`/`update-to` fields), OpenAlex (`is_retracted`), and the publisher's own page
  where locatable. Classify each as: **true PubMed gap** (genuinely retracted, confirmed by at
  least one other independent source, PubMed tag absent), **RW error/edge case** (e.g., reinstated,
  miscategorized, or RW's own record is itself questionable), or **unresolved** (could not be
  independently confirmed either way with the sources available).
- **No new exclusion rule** beyond what already produced this list of 27.

## Part B: scaled PubMed-tag-vs-RW check -- sampling frame fixed here, before drawing it

- **Population:** all Retraction Watch records with a recorded PubMed ID (`original_paper_pubmed_id
  IS NOT NULL AND != ''`), n=66,203 -- not restricted to this project's 3 domains, since the
  question here is about PubMed's general tagging reliability, not this benchmark's own domains.
  A `retraction_date` of `1/1/1970` is a known placeholder/default value in RW's export (not a
  real date) and such rows are excluded from year-stratification (counted separately, not dropped
  silently).
- **Sample size and design:** n=300, stratified proportionally by retraction year (post-exclusion
  of the placeholder-date rows), drawn with a fixed seed (42, this project's standing convention).
  300 is chosen to keep the live API call volume (PubMed + Crossref + OpenAlex lookups, ~900 calls
  total) comfortably inside a single session's time budget at the confirmed rate limits (minutes,
  not hours), while being large enough to report meaningful per-year and per-publisher Wilson CIs
  -- not chosen to hit a predetermined miss-rate number, and not adjusted after seeing any result.
- **Hypothesis:** none stated as a formal test -- this is a measurement (PubMed's tag-miss rate),
  reported with a Wilson CI by year and by publisher, exactly as the original task specifies, not
  a comparison against a null.
- **Primary endpoint:** for each sampled record, does PubMed's own `Retracted Publication` tag
  match RW's retraction claim (same direction as the existing 364-candidate check, scaled up);
  cross-checked against Crossref's `relation`/`update-to` fields and OpenAlex's `is_retracted` flag
  as two independent corroborating sources, not as tie-breakers that override PubMed or RW.
- **RW reliability sub-check:** for records where PubMed appears to disagree with RW, additionally
  check for evidence of a **reinstatement** (RW itself sometimes reverses a retraction entry) or a
  **notice-type mismatch** (RW's `retraction_nature` field vs. what the publisher's own notice
  actually says) -- reported as a qualitative finding, not folded into the miss-rate number itself.
- **Exclusion rules:** records with no recorded PubMed ID are out of the sampling population
  entirely (stated above); records where none of PubMed/Crossref/OpenAlex/publisher page can be
  reached or resolved are reported as "unresolved," not counted as either a hit or a miss.
- **No spending:** every data source above is free and already confirmed reachable without
  payment; this prereg does not request or require any paid API, account, or external party contact.

## Addendum (2026-10-04), after Part A's first pass surfaced a provenance problem

Part A's first pass (`phase5_diagnose_27_gap_cases.py`) treated any non-empty Crossref `relation`
and any OpenAlex `is_retracted: true` as "corroboration." Both were checked properly before Part
B runs, live, this session, not assumed:

- **OpenAlex's `is_retracted` is sourced directly from Retraction Watch** (OpenAlex's own
  documentation: *"True if the work is known to be retracted, per the Retraction Watch
  database"*) -- not independent of RW at all. Treating it as corroboration was circular.
- **Crossref's `relation` field needs its key inspected, not just non-emptiness** -- a
  `"has-review"` relation (unrelated to retraction) produced a false positive in Part A's first
  pass. A `relation` key matching `retract`/`withdraw`, asserted by the object (the notice's own
  DOI record), is genuinely independent (publisher-deposited). Separately, Crossref's `update-to`
  field carries an explicit `source` of `"publisher"` (independent) or `"retraction-watch"` (not
  independent) -- per Crossref's own documentation: *"Retractions and other updates from
  Retraction Watch are identified by a `source` field, which can have a value of `publisher` or
  `retraction-watch`."*

### Classification rules for Part B (fixed here, before Part B runs; identical to Part A's redo)

- **independent_evidence**: PubMed's own title/abstract text contains a retraction/withdrawal
  marker independent of the structured tag; OR Crossref `relation` has a retract/withdraw-matching
  key; OR Crossref `update-to` has an entry with `source: "publisher"`.
- **rw_derived_only**: none of the above, but OpenAlex `is_retracted: true` and/or Crossref
  `update-to` has an entry with `source: "retraction-watch"`.
- **rw_only_uncorroborated**: none of the above at all.

### DOI placeholder check (completed before Part B)

Scanned all 62,502 distinct `original_paper_doi` values in the full RW table for anything not
shaped like a real DOI (not matching `^10\.`): exactly 2 non-conforming values exist in the
entire dataset, `"unavailable"` and `"Unavailable"` -- both are placeholder strings, not real
DOIs, and both are caught by a case-insensitive check. No other placeholder strings exist.

### Second addendum (2026-10-04): the sampling frame itself was wrong, caught by the first Part B run

The first Part B run against the originally-drawn 300-record sample returned 144/300 (48%)
"unresolved -- PubMed lookup failed." Diagnosed before reporting anything from that run:
**Retraction Watch uses the literal string `"0"` as its own placeholder for "no PubMed ID,"**
**not a real PMID** -- confirmed directly, 32,844 of the original 66,203-row population (49.6%)
hold this placeholder. The true population with a real PubMed ID is **33,359**, not 66,203.
Checked for any other malformed value in this field while fixing it: every other distinct value
already matches a clean positive-integer pattern; `"0"` is the only placeholder present.

The sample was redrawn from the corrected 33,359-row population (same method: n=300, stratified
by retraction year, seed=42) before Part B was run again. The original, contaminated sample and
its partial results are kept on disk (`data/interim/phase5_scaled_sample_v1_contaminated.json`),
not deleted, per this project's own no-silent-discarding discipline.

### Part B additions, fixed before running

- **Script git hash at time of running:** recorded in the output file itself (via `git
  rev-parse HEAD` captured at runtime), not hand-copied here, so it can never drift from what
  actually ran.
- **Raw API response caching:** every PubMed/Crossref/OpenAlex response for the 300-record sample
  is cached verbatim (full JSON body) alongside the query timestamp, so Part B is auditable and
  re-derivable without re-querying the live APIs.
- **Sampling-frame counts, reported explicitly:** population with a PubMed ID (66,203); rows
  excluded for the placeholder retraction-date (6); valid stratification population (66,197);
  sample drawn (300); and, separately, how many of the 300 are further excluded at query time
  (no resolvable PMID, no resolvable DOI) with the reason stated per exclusion, not folded
  silently into the denominator.
- **Reporting:** miss rate by retraction year with Wilson CIs (primary, matches the original
  Phase 5 task spec). By-publisher breakdown is explicitly descriptive only -- no CI claimed,
  given many publishers will have very few sampled records.

### Third addendum (2026-10-05): the sampling frame was still wrong -- a nature-filter contamination, caught by author-requested verification before trusting the v1 Part B result

The v1 Part B run (`results/phase5_part_b_scaled_check.md`, logged as ANALYSIS_LOG 5.11)
reported 47/299 = 15.72%, read at the time as "roughly double" the curated pool's 8.11%, with a
markedly worse (48.9% fully-uncorroborated) independent-evidence breakdown. Before either number
was allowed into the manuscript, the author explicitly requested verification of the sampling
frame itself: **(a)** is RW's `Nature == Retraction` enforced? It was not. 3,837 of the
33,359-row population (11.5%) are `Correction`, `Expression of concern`, or `Reinstatement`
records -- none of which were ever expected to carry PubMed's `Retracted Publication` tag, so
checking them for it manufactures gap cases that are not real gaps. This single contamination is
sufficient to explain both of v1's headline findings, since roughly 1 in 9 sampled records could
not possibly have passed the check being applied to them.

**Fix, specified here before Part B v2 ran:**

- **Population restricted to `retraction_nature == "Retraction"`** before sampling. This is a
  change to the *population*, decided and applied before the v2 sample was drawn, not a
  post-hoc exclusion of unfavorable cases after seeing results.
- **PMID-level dedup applied to this restricted population**: 22 excess rows (20 distinct PMIDs,
  max 3 occurrences) removed, lowest `record_id` kept, before sampling.
- **Notice/original PMID mix-up check added** for every sampled case (and retroactively for Part
  A's 24): PubMed's `"Retraction of Publication"` tag (on a notice's own PMID) is distinct from
  `"Retracted Publication"` (on the original article); a case where RW's `original_paper_pubmed_id`
  actually points to a notice would otherwise look like a false gap. Any such case is excluded
  from the gap-rate denominator entirely, counted as neither a gap nor a non-gap.
- **Disclosed, not silently filtered:** while auditing the unfiltered population for the nature
  filter, PMID 35073579 was found duplicated 281x across 281 distinct Expression-of-Concern
  records, all dated identically -- a bulk RW data-entry error. It is excluded by the nature
  filter regardless of this anomaly, but is reported because the author's standing instruction is
  to disclose, not silently absorb, data-quality anomalies encountered during an audit.
- **Resulting population: 29,500** (33,359 − 3,837 non-Retraction-nature − 22 duplicates). A
  fresh stratified-by-year, proportionally-allocated sample of n=300 (seed 42) was drawn from
  this corrected population -- same method as the original prereg and the second addendum,
  applied to the newly-corrected population.

**v1's result is superseded, not deleted**, per this project's standing discipline: it remains
on disk (`results/phase5_part_b_scaled_check.{json,md}`,
`data/interim/phase5_scaled_sample_v1_contaminated.json` -- note this v1-contaminated file name
refers to the `"0"`-placeholder fix from the second addendum, not this third addendum's
nature-filter fix; the nature-filter-contaminated sample file is
`data/interim/phase5_scaled_sample.json`, also retained), and is reported in
`paper/supplementary.md` S1.6.2 alongside the v2 result with an explanation of why it was wrong.
v2's result: `results/phase5_part_b_scaled_check_v2.{json,md}`.

## Fourth addendum (2026-10-05, same day as the third): the `CommentsCorrectionsList`-chain independence rule is post hoc, disclosed here before being used for anything further

The original classification rules above (and the second addendum's rules, used for Part A's redo
and applied unchanged by the automated Part B v2 pass) define `independent_evidence` only in
terms of evidence found on the *same* PMID being checked: PubMed's own title/abstract text on
that record, or a Crossref `relation`/`update-to` entry with `source: "publisher"` on that
record. Neither rule, as originally written, considers PubMed's own `CommentsCorrectionsList`
field (`Update in`/`Update of`/`Erratum in` cross-references to a *different* PMID).

**This is a post hoc addition, not a prespecified rule.** It was introduced only after a
dossier-level manual re-check of Part B v2's 12 `rw_derived_only` cases
(`results/phase5_part_b_downstream_dossiers.md`) found that five of them happened to have exactly
this kind of chained record (four Cochrane reviews whose Cochrane-initiated withdrawal is
confirmed by a later pub-version PMID titled `"WITHDRAWN:"`, one erratum chain confirming a
duplicate-publication notice). Seeing that pattern in this specific data, then writing a rule to
capture it, is the definition of post hoc rule construction -- stated here explicitly rather
than presented as if it had been planned in advance.

**Consequence for reporting, applied in the paper and in**
**`results/phase5_part_b_downstream_dossiers.md`:** every figure derived using this rule is
reported in two tiers, not one -- **strict** (the original, same-PMID-only rule: 5/298) and
**broad** (strict plus the `CommentsCorrectionsList`-chain rule: 11/298) -- so a reader can see
how much of any revised independence figure rests on a rule designed in response to the data it
is applied to, rather than one fixed before the data was seen.

**A second disclosure from the same re-check, not a counting-rule issue:** reading each chained
notice's own stated reason (not just its title or pubtype) found that three of the four Cochrane
`"WITHDRAWN:"` cases give a purely administrative reason (timeline delay, consolidation into
another review, splitting into several reviews) with no data-integrity or misconduct language --
the `CommentsCorrectionsList` hop reliably confirms that Cochrane withdrew the review, not that
the withdrawal matches the kind of event Retraction Watch's `Retraction` classification, or this
paper's own "retraction" framing, usually implies. This is reported in the paper (section 3.8)
as a caveat on the broad-tier figure, not folded silently into the independence count.
