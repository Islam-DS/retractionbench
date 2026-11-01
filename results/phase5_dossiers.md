# Phase 5 dossiers: uncorroborated / mix-up-flagged cases

Per author instruction: a full dossier (PubMed record, notice, publisher page if fetchable, RW
row) for every case that could not be independently corroborated, classified as **retracted** /
**not-a-retraction** (correction, EoC, reinstatement) / **notice-original mix-up** / **unresolved**.
An unfetchable source is recorded as unresolved, never silently counted as a negative finding.

## Part A (curated 3-domain pool): 1 case

### PMID 26955437 — "Semen profiles of young men involved as bicycle taxi cyclists in Mangochi District, Malawi: A case-control study"

| Source | Finding |
|---|---|
| **RW row** (record_id 21551) | `retraction_nature=Retraction`, `retraction_date=10/23/2019`, `reason="Error in Data;Notice - Lack of;"`, `retraction_doi="unavailable"`, `retraction_pubmed_id="0"`, `urls=None`. RW itself records no locatable identifier for its own notice. |
| **PubMed record** (title/abstract, pubtype) | No retraction language in title or abstract. `pubtype = ["Journal Article", "Research Support, Non-U.S. Gov't"]` -- no `Retracted Publication` tag, no `Retraction of Publication` tag (not a notice/original mix-up). |
| **Notice** | Not locatable by any identifier RW itself provides (`doi`/`pmid` both placeholders). |
| **Publisher page** (fetched live this round, `https://pmc.ncbi.nlm.nih.gov/articles/PMC4761707`) | **Fetched successfully. No retraction notice, withdrawal notice, expression of concern, or editorial note present** -- confirmed directly, not inferred. |
| **Crossref** (`10.4314/mmj.v27i4.7`) | No retraction-type `relation` entry, no `update-to` entry. |
| **OpenAlex** | `is_retracted: false`. |

**Classification: unresolved.** Every independently-checkable source was reachable and came back
clean (no retraction evidence) except RW itself, which asserts a retraction but can locate
neither a notice DOI nor a notice PMID for it. This is not classified as "not-a-retraction"
(RW's own `retraction_nature` field says Retraction, and this audit has no basis to overrule
that) and not "retracted" (nothing independent confirms it) -- it sits exactly in the gap RW's
own `"Notice - Lack of"` tag already discloses.

## Part B (broad random sample): 0 cases -- not a gap in coverage, a corrected finding

The ~23 expected uncorroborated cases were an artifact of the contaminated v1 sampling frame
(see `results/phase5_part_b_scaled_check_v2.md` and `paper/supplementary.md` S1.6.2 for the
full account: 3,837 non-`Retraction`-nature rows had been mixed into the population, inflating
both the headline gap rate and the apparent uncorroboration rate). Once the frame was corrected
(Retraction-nature-only, PMID-deduped, final population 29,500) and the check rerun on a freshly
drawn 300-record sample, the independent-vs-RW-derived breakdown of the 17 real gap cases came
back **5 independent_evidence, 12 rw_derived_only, 0 rw_only_uncorroborated**. No Part B case
requires a dossier under this round's classification scheme, because none is classified
`rw_only_uncorroborated`. This is reported here explicitly, rather than the section being
silently deleted, because the original "~23 pending" estimate was stated to the author and
should not simply disappear without explanation: it was wrong, and the reason it was wrong is
itself a finding (sampling-frame contamination), documented above.
