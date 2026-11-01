# Retraction Status Is Not Reliably Machine-Readable at the Source

Standalone result, not a data-quality footnote. This documents a completeness gap
in the two authoritative sources RetractionBench itself is built on -- Retraction
Watch (RW) and PubMed's structured `Retracted Publication` publication-type tag --
checked in both directions. See `docs/DECISIONS.md` ADR-028 and ADR-029, and
`docs/DATA_NOTES.md`'s 2026-08-06 entries, for the decisions this feeds.

## 1. Forward direction: RW-listed retractions PubMed does not tag

Every PMID in the 364-candidate pool for the three final domains (Pharmacology,
Obstetrics/Gynecology, Rehabilitation/Therapy -- ADR-027) was queried live against
NCBI's ESummary endpoint (`src/retraction_bench/ingest/pubmed.py`).

**27/364 = 7.42%, Wilson 95% CI [5.15%, 10.58%]** are RW `Retraction`-nature entries
whose PubMed record resolves successfully but whose `pubtype` list does not include
`Retracted Publication`. This is not a lookup failure -- the record is real and
complete in every other respect. (A 28th, unrelated case, PMID 38355237, is a
genuine unresolvable-PMID error and is excluded from this count and from the
candidate pool pending manual check.)

**Concrete example:** PMID 37940041's PubMed title is itself
`"WITHDRAWN: The Effect of Preoperative Intravenous Tranexamic Acid Versus Rectal
Misoprostol..."` -- PubMed's own citation text acknowledges the withdrawal, but the
structured `pubtype` field was never updated to carry the tag. A system filtering
on the structured field alone would treat this paper as current.

### 1a. Temporal pattern -- not simple indexing lag

If the gap were purely "PubMed hasn't caught up yet," the rate should fall
monotonically as records age. It does not. Excluding a 6-record cluster that is
five republished PMIDs of one Cochrane review plus its original ("Therapeutic
touch for healing acute wounds", RW record IDs 31158-31162 and 30918 -- a single
editorial event, not six independent cases):

| Retraction year | n (all 3 domains) | gap n | gap rate |
|---|---|---|---|
| 2016 | 6 | 1 | 16.7% |
| 2017 | 23 | 3 | 13.0% |
| 2018 | 23 | 3 | 13.0% |
| 2019 | 39 | 4 | 10.3% |
| 2020 | 28 | 3 | 10.7% |
| 2021 | 47 | 1 | 2.1% |
| 2022 | 35 | 0 | 0.0% |
| 2023 | 57 | 1 | 1.8% |
| 2024 | 47 | 3 | 6.4% |
| 2025 | 25 | 0 | 0.0% |
| 2026 | 28 | 2 | 7.1% |

Per-year n is small enough that individual cells are noisy, but the qualitative
pattern survives: retractions from 2016-2020 (6-10 years old at time of check)
still show a materially higher gap rate (10-17%) than 2021-2023 (0-2%), which is
the opposite of what a clearing backlog predicts -- those older records had years
to be backfilled and were not. The 2024/2026 uptick is consistent with lag for
genuinely recent retractions. Read together: part of the gap looks like ordinary
lag (recent records), but the persistent gap in decade-old records is a structural
tagging failure, not a queue that resolves with time.

### 1b. Publisher and reason -- no single confound

Excluding the Cochrane cluster, publisher-level gap rates are unremarkable and
don't concentrate in one venue (Wiley 8.2% [4/49], Elsevier ~5%, single-record
publishers excluded as uninformative at n=1). RW's `Reason` field for the 27 is
heterogeneous -- data/results reliability categories dominate generally, as they
do across the whole candidate pool, with no single reason code overrepresented.

## 2. Inverse direction: PubMed-tagged retractions RW does not list

Checking every PubMed retraction against RW is out of scope for this project (RW
covers 71,540 raw records across every discipline and subject; a full census is a
project of its own). This check is deliberately bounded: the 19 journals
implicated by the 27-record gap set above, PubMed ESearch for
`"<journal>"[Journal] AND "Retracted Publication"[Publication Type]` restricted to
2016-2026, then every returned PMID checked against the *full* 71,540-row RW table
(both `OriginalPaperPubMedID` and `RetractionPubMedID` columns, any subject --
not just our three domains). This answers "within the journal universe our pool
already touches, is RW's side also incomplete?", not "how complete is RW overall?"

**443 PubMed-tagged-retracted PMIDs found across the 19 journals. 50/443 (11.3%)
have no matching PMID anywhere in RW.**

46 of the 50 are in a single journal, Heliyon. This is not one concentrated
retraction event: the 46 span 2019-2024 and cover unrelated fields (chemistry,
engineering, economics, sports science, agriculture, IT security, a handful of
biomedical/pharmacology titles) -- checked directly against ESummary titles and
dates, not assumed. That spread argues against a single paper-mill incident and
for a general RW ingestion gap on a high-volume, all-disciplines mega-journal.
Only our forward-direction 364-pool happens to include exactly one Heliyon record
(RW ID 70654), so this cluster has essentially no overlap with, and does not
threaten, our actual candidate pool -- it's evidence about database completeness
in general, not about this benchmark's items specifically.

The remaining 4 unmatched PMIDs are single cases each, in journals already
represented in the candidate pool:

- **PMID 30285533 (Modern Rheumatology)** shares its exact title with RW record
  16851 / PMID 28395637, already counted among the 27 forward-direction gaps.
  This is very likely the *same article under two PMIDs* -- an epub-ahead-of-print
  PMID versus a final-issue PMID, a known PubMed behavior -- with the retraction
  tag applied to one and RW's record pointing at the other. This is a distinct
  failure mode from a missing tag: identifier fragmentation across the same
  article, not the article's retraction status being untagged anywhere.
- **PMID 28213740 (Aging Clinical and Experimental Research)**, **PMID 41818766
  (New Zealand Medical Journal)**, and **PMID 36468208 (Cell Biology
  International, titled "Withdrawn: Ticagrelor reduces myocardial cell injury...")**
  are genuinely separate retracted articles with no RW entry at all, in journals
  RW otherwise covers -- titles and pubtypes checked live, not inferred.

## 3. What this means for the benchmark

Both directions show a real, measured gap, of comparable order of magnitude
(7.4% RW-not-tagged-by-PubMed; 11.3% PubMed-tagged-not-in-RW within the bounded
journal check), via different mechanisms: PubMed's failure looks like inconsistent
or lagged application of a structured field to an otherwise-complete record (plus
at least one case of identifier fragmentation across duplicate PMIDs for the same
article); RW's failure looks like curation/ingestion lag, concentrated on a
high-volume multidisciplinary journal.

**Neither source is independently complete.** A hypothetical AI system that did
everything right -- retrieved the correct paper, checked PubMed's own structured
retraction tag before answering -- would still get roughly one in fourteen
genuinely-retracted papers wrong in our candidate pool, not because it reasoned
badly, but because the authoritative index it checked against does not reliably
encode the fact. This reframes RetractionBench's central failure mode as partly
infrastructural rather than purely a model-behavior problem: the propagation
failure this benchmark measures in AI systems is already present one layer
earlier, in the sources those systems would need to check.

## Reproducing this check

`uv run python -m retraction_bench.ingest.pubmed_rw_completeness` regenerates the
inverse-direction numbers in section 2 (raw ESearch results cached to
`data/interim/inverse_check_pubmed_pmids.json`). Not wired into the CLI and not
covered by tests -- a single investigative analysis feeding one paper finding
(ADR-029), not a repeated pipeline stage; see the module docstring for that
tradeoff. Section 1's forward-direction numbers come from
`retraction-bench ingest verify-pubmed`'s existing output
(`data/interim/tier1_candidates_final3_verified.csv`).
