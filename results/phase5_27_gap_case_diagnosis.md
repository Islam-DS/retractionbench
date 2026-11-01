# Phase 5 Part A: diagnosis of the 27 RW-vs-PubMed gap rows (24 distinct PMIDs)

Prereg: `prereg/phase5_record_level_audit.md`. Full enumeration of an already-identified
set, not a sample.

**27 gap rows map to 24 distinct PMIDs** -- 3 PMIDs (37940041, 19959915, 30267080) each appear twice as duplicate candidate-pool rows, not duplicate retractions. Diagnosing the 24 distinct cases below.

## Classification summary (corrected after manual follow-up on the 2 initially-uncorroborated cases)

| Classification | n |
|---|---|
| true_pubmed_gap_corroborated (by OpenAlex and/or Crossref) | 22 |
| true_pubmed_gap_corroborated_by_pubmed_own_text (PMID 31563928) | 1 |
| corroboration_impossible_no_public_notice_anywhere (PMID 26955437) | 1 |

**Both of the two initial "uncorroborated" cases needed a closer manual look, and resolved**
**differently -- neither should be left as a flat "uncorroborated" line item:**

- **PMID 31563928 (NZ Medical Journal fish-oil-supplements paper):** RW's own `original_paper_doi`
  field holds the literal placeholder string `"unavailable"`, not a real DOI -- so the Crossref/
  OpenAlex 404s above are a **script artifact**, not genuine non-corroboration (both lookups were
  attempted against the literal string "unavailable" as if it were a DOI path). Checking PubMed's
  own record directly resolves this cleanly: the title itself is **"RETRACTED Are over-the-counter
  fish oil supplements safe, effective and accurate with labelling?..."** and the abstract field is
  literally **"RETRACTED."** -- unambiguous confirmation in PubMed's own unstructured text, exactly
  the same pattern already documented for PMID 37940041's "WITHDRAWN:"-prefixed title elsewhere in
  this project. The structured `Retracted Publication` tag omits it regardless of how plainly the
  plain text states it.
- **PMID 26955437 (Malawi Medical Journal semen-profile study):** this one is genuinely
  unresolved, not a script bug. RW's own `reason` field reads **"Error in Data;Notice - Lack**
  **of;"** -- RW itself discloses that no public retraction notice could be located for this
  record. Consistent with that: PubMed's title/abstract show no retraction language at all,
  OpenAlex explicitly returns `is_retracted: false`, and Crossref shows no retraction-relation
  metadata. **No source checked -- PubMed's tag, PubMed's own text, OpenAlex, or Crossref --**
  **corroborates this retraction at all.** This is a genuine example of RW's own stated limitation
  (a retraction claim resting on something other than a locatable public notice), not evidence RW
  is wrong, but also not independently verifiable through any channel available to this audit.

## Full per-case detail

| PMID | RW journal | RW publisher | RW date | RW nature | PubMed tag now | OpenAlex retracted | Crossref relation present | Classification |
|---|---|---|---|---|---|---|---|---|
| 14583953 | Cochrane Database of Systematic Reviews | Wiley | 9/1/2016 0:00 | Retraction | False | True | False | true_pubmed_gap_corroborated |
| 16856030 | Cochrane Database of Systematic Reviews | Wiley | 7/17/2017 0:00 | Retraction | False | True | True | true_pubmed_gap_corroborated |
| 19959915 | Aging Clinical and Experimental Research | Springer | 6/5/2018 0:00 | Retraction | False | True | False | true_pubmed_gap_corroborated |
| 22696330 | Cochrane Database of Systematic Reviews | Wiley | 9/1/2016 0:00 | Retraction | False | True | False | true_pubmed_gap_corroborated |
| 25069726 | Cochrane Database of Systematic Reviews | Wiley | 9/1/2016 0:00 | Retraction | False | True | False | true_pubmed_gap_corroborated |
| 26658572 | Knee Surgery, Sports Traumatology, Arthroscopy: Official Journal of the ESSKA | Springer | 10/1/2016 0:00 | Retraction | False | True | False | true_pubmed_gap_corroborated |
| 26955437 | Malawi Medical Journal: the Journal of Medical Association of Malawi | Montfort Press for the Medical Association of Malawi | 10/23/2019 0:00 | Retraction | False | False | False | **corroboration_impossible_no_public_notice_anywhere** |
| 27098397 | Cell Biology International | Wiley | 7/24/2017 0:00 | Retraction | False | True | False | true_pubmed_gap_corroborated |
| 27140910 | Cochrane Database of Systematic Reviews | Wiley | 9/1/2016 0:00 | Retraction | False | True | False | true_pubmed_gap_corroborated |
| 27294218 | International Journal of Reproductive Biomedicine | Shahid Sdoughi University of Medical Sciences | 1/9/2023 0:00 | Retraction | False | True | False | true_pubmed_gap_corroborated |
| 27552401 | Cochrane Database of Systematic Reviews | Wiley | 9/1/2016 0:00 | Retraction | False | True | False | true_pubmed_gap_corroborated |
| 28226403 | Pain Practice: The Official Journal of World Institute of Pain | Wiley | 9/1/2017 0:00 | Retraction | False | True | False | true_pubmed_gap_corroborated |
| 28395637 | Modern Rheumatology | Taylor and Francis | 1/2/2020 0:00 | Retraction | False | True | False | true_pubmed_gap_corroborated |
| 28617973 | Paediatric and Perinatal Epidemiology | Wiley | 9/20/2017 0:00 | Retraction | False | True | False | true_pubmed_gap_corroborated |
| 29438490 | Journal of Biochemistry | Oxford University Press | 5/15/2018 0:00 | Retraction | False | True | False | true_pubmed_gap_corroborated |
| 30267080 | JAMA Oncology | American Medical Association | 4/25/2019 0:00 | Retraction | False | True | False | true_pubmed_gap_corroborated |
| 30688986 | JAMA Internal Medicine | American Medical Association | 1/19/2021 0:00 | Retraction | False | True | True | true_pubmed_gap_corroborated |
| 31415103 | Clinical Cardiology | Wiley | 3/17/2020 0:00 | Retraction | False | True | True | true_pubmed_gap_corroborated |
| 31563928 | The New Zealand Medical Journal | New Zealand Medical Association | 9/25/2019 0:00 | Retraction | False | None (DOI placeholder bug) | False | **true_pubmed_gap_corroborated_by_pubmed_own_text** |
| 32946583 | QJM: An International Journal of Medicine | Oxford University Press | 12/14/2020 0:00 | Retraction | False | True | False | true_pubmed_gap_corroborated |
| 37940041 | Journal of Obstetrics and Gynaecology Canada | Elsevier | 9/26/2024 0:00 | Retraction | False | True | False | true_pubmed_gap_corroborated |
| 39566682 | The American Journal of Clinical Nutrition | Elsevier | 11/19/2024 0:00 | Retraction | False | True | False | true_pubmed_gap_corroborated |
| 39906865 | Heliyon | Elsevier - Cell Press | 1/22/2026 0:00 | Retraction | False | True | False | true_pubmed_gap_corroborated |
| 6522427 | Pharmacology Biochemistry and Behavior | Elsevier | 4/23/2026 0:00 | Retraction | False | True | False | true_pubmed_gap_corroborated |
