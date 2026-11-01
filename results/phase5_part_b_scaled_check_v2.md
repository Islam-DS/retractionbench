# Phase 5 Part B, v2: scaled PubMed-tag-vs-RW check, Retraction-nature-only, PMID-deduped

Prereg: `prereg/phase5_record_level_audit.md` + both 2026-10-04 addenda. Git hash this
ran under: `88309ed802fa074547589613f87f682c55f68c5c`.

## Sampling-frame counts

- Population with a real PubMed ID, before nature filter: 33,359
- Excluded as non-Retraction-nature (Correction/Expression of concern/Reinstatement): 3,837
- Excluded as PMID-level duplicates (deduped, lowest record_id kept): 22
- **Final population (Retraction-nature, real PMID, distinct, dated): 29,500**
- Sample drawn (stratified by year, seed 42, proportional allocation, max exact-vs-realized fraction deviation: 0.00425 -- negligible, naive pooled rate below is not meaningfully biased by rounding): 300
- Excluded at query time (no PubMed ID after all): 0
- Checked: 300
- Unresolved (PubMed lookup failed after retries): 1
- **Flagged as suspected notice/original PMID mix-up** (PubMed itself classifies this ID
  as a retraction notice, `"Retraction of Publication"`, not the original paper) -- 
  excluded from the gap-rate denominator, not counted as a gap or a non-gap: 0
- Resolved and classified (gap rate denominator): 299

## Overall miss rate: 17/299 = 5.69%, Wilson 95% CI [3.58%, 8.92%]

## By retraction year (Wilson 95% CI -- primary)

| Year | n | Gap n | Gap rate | Wilson 95% CI |
|---|---|---|---|---|
| 1998 | 1 | 0 | 0.0% | [0.0%, 79.3%] |
| 2002 | 1 | 0 | 0.0% | [0.0%, 79.3%] |
| 2003 | 1 | 0 | 0.0% | [0.0%, 79.3%] |
| 2004 | 1 | 0 | 0.0% | [0.0%, 79.3%] |
| 2005 | 1 | 0 | 0.0% | [0.0%, 79.3%] |
| 2006 | 2 | 0 | 0.0% | [0.0%, 65.8%] |
| 2007 | 2 | 0 | 0.0% | [0.0%, 65.8%] |
| 2008 | 3 | 0 | 0.0% | [0.0%, 56.1%] |
| 2009 | 4 | 2 | 50.0% | [15.0%, 85.0%] |
| 2010 | 4 | 0 | 0.0% | [0.0%, 49.0%] |
| 2011 | 5 | 1 | 20.0% | [3.6%, 62.4%] |
| 2012 | 6 | 0 | 0.0% | [0.0%, 39.0%] |
| 2013 | 7 | 3 | 42.9% | [15.8%, 75.0%] |
| 2014 | 6 | 0 | 0.0% | [0.0%, 39.0%] |
| 2015 | 8 | 3 | 37.5% | [13.7%, 69.4%] |
| 2016 | 10 | 2 | 20.0% | [5.7%, 51.0%] |
| 2017 | 8 | 1 | 12.5% | [2.2%, 47.1%] |
| 2018 | 8 | 1 | 12.5% | [2.2%, 47.1%] |
| 2019 | 10 | 1 | 10.0% | [1.8%, 40.4%] |
| 2020 | 16 | 1 | 6.2% | [1.1%, 28.3%] |
| 2021 | 21 | 1 | 4.8% | [0.8%, 22.7%] |
| 2022 | 24 | 0 | 0.0% | [0.0%, 13.8%] |
| 2023 | 79 | 1 | 1.3% | [0.2%, 6.8%] |
| 2024 | 36 | 0 | 0.0% | [0.0%, 9.6%] |
| 2025 | 28 | 0 | 0.0% | [0.0%, 12.1%] |
| 2026 | 7 | 0 | 0.0% | [0.0%, 35.4%] |

## By publisher (descriptive only -- no CI, most publishers have very few sampled records)

| Publisher | n | Gap n | Gap rate |
|---|---|---|---|
| Hindawi | 62 | 0 | 0.0% |
| Elsevier | 42 | 3 | 7.1% |
| Wiley | 31 | 8 | 25.8% |
| Springer | 21 | 0 | 0.0% |
| Springer - Nature Publishing Group | 13 | 0 | 0.0% |
| Spandidos | 12 | 0 | 0.0% |
| Springer - Biomed Central (BMC) | 12 | 0 | 0.0% |
| Taylor and Francis | 11 | 1 | 9.1% |
| Elsevier - Cell Press | 10 | 0 | 0.0% |
| PLoS | 5 | 0 | 0.0% |
| SAGE Publications | 5 | 0 | 0.0% |
| Frontiers | 5 | 0 | 0.0% |
| Wolters Kluwer | 4 | 1 | 25.0% |
| Taylor and Francis - Dove Press | 4 | 0 | 0.0% |
| Mary Ann Liebert | 4 | 0 | 0.0% |
| MDPI | 4 | 0 | 0.0% |
| National Academy of Sciences (NAS) | 2 | 0 | 0.0% |
| BMJ Publishing | 2 | 1 | 50.0% |
| Wolters Kluwer - Lippincott Williams & Wilkins | 2 | 1 | 50.0% |
| Oxford University Press | 2 | 0 | 0.0% |
| American Society for Microbiology | 2 | 0 | 0.0% |
| American Chemical Society (ACS) | 2 | 0 | 0.0% |
| Verduci Editore | 2 | 0 | 0.0% |
| The Company of Biologists | 2 | 0 | 0.0% |
| Portland Press | 2 | 0 | 0.0% |
| Cellular Physiol Biochem Press | 2 | 0 | 0.0% |
| Impact Journals | 2 | 0 | 0.0% |
| Nature Publishing Group | 1 | 0 | 0.0% |
| The Japan Endocrine Society | 1 | 0 | 0.0% |
| Korean Cancer Association | 1 | 0 | 0.0% |

## Independent-vs-RW-derived breakdown (gap cases only)

| Classification | n |
|---|---|
| gap_independent_evidence | 5 |
| gap_rw_derived_only | 12 |
| gap_rw_only_uncorroborated | 0 |
