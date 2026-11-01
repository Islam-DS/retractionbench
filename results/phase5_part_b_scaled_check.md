# Phase 5 Part B: scaled PubMed-tag-vs-RW check (n=300 prespecified sample)

Prereg: `prereg/phase5_record_level_audit.md`. Git hash this ran under: `88309ed802fa074547589613f87f682c55f68c5c`.

## Sampling-frame counts

- Population with a real PubMed ID (RW's own "0" placeholder excluded, see prereg's second addendum): 33,359
- Sample drawn (stratified by year, seed 42): 300
- Excluded at query time (no PubMed ID after all): 0
- Checked: 300
- Unresolved (PubMed lookup failed): 1
- Resolved and classified: 299

## Overall miss rate: 47/299 = 15.72%, Wilson 95% CI [12.03%, 20.28%]

## Headline comparison against the narrow, curated 3-domain pool (Part A / section 3.8)

| | n (gap) | Denominator | Rate | Wilson 95% CI |
|---|---|---|---|---|
| Narrow, curated 3-domain candidate pool (Part A) | 24 | 296 distinct papers | 8.11% | [5.51%, 11.78%] |
| **Broad, cross-discipline random sample (Part B)** | **47** | **299 resolved** | **15.72%** | **[12.03%, 20.28%]** |

**The two intervals barely overlap -- the broad sample's rate is roughly double the curated**
**pool's.** This paper's own 8.1% headline figure should not be read as PubMed's general
tag-miss rate: it describes a pool that passed this project's own institutional-source
verification screening, which plausibly correlates with better-indexed journals. The broader,
unscreened sample suggests the real general-population rate is materially higher.

## Independent-vs-RW-derived breakdown, compared against Part A

| | n (gap) | Independent evidence | RW-derived only | Fully uncorroborated |
|---|---|---|---|---|
| Part A (curated pool, n=24) | 24 | 10 (41.7%) | 13 (54.2%) | 1 (4.2%) |
| **Part B (broad sample, n=47)** | **47** | **15 (31.9%)** | **9 (19.1%)** | **23 (48.9%)** |

**This is the sharper of the two findings.** The broad sample's retraction claims are far less
often independently corroborated: nearly half (48.9%) rest on Retraction Watch alone, with no
PubMed-text, Crossref-relation, or Crossref-publisher-update-to evidence found at all --
compared to 4.2% in the curated pool. This is direct evidence that RW's own reliability (not
just PubMed's tagging completeness) is a real, open question at scale, and that this project's
curated 3-domain pool is not representative of RW's broader gap cases on this axis.

## By retraction year (Wilson 95% CI -- primary)

| Year | n | Gap n | Gap rate | Wilson 95% CI |
|---|---|---|---|---|
| 1998 | 1 | 0 | 0.0% | [0.0%, 79.3%] |
| 2002 | 1 | 0 | 0.0% | [0.0%, 79.3%] |
| 2003 | 1 | 1 | 100.0% | [20.7%, 100.0%] |
| 2004 | 1 | 0 | 0.0% | [0.0%, 79.3%] |
| 2005 | 1 | 0 | 0.0% | [0.0%, 79.3%] |
| 2006 | 1 | 0 | 0.0% | [0.0%, 79.3%] |
| 2007 | 2 | 2 | 100.0% | [34.2%, 100.0%] |
| 2008 | 2 | 1 | 50.0% | [9.5%, 90.5%] |
| 2009 | 3 | 3 | 100.0% | [43.9%, 100.0%] |
| 2010 | 3 | 1 | 33.3% | [6.1%, 79.2%] |
| 2011 | 5 | 2 | 40.0% | [11.8%, 76.9%] |
| 2012 | 6 | 3 | 50.0% | [18.8%, 81.2%] |
| 2013 | 7 | 0 | 0.0% | [0.0%, 35.4%] |
| 2014 | 6 | 1 | 16.7% | [3.0%, 56.4%] |
| 2015 | 9 | 3 | 33.3% | [12.1%, 64.6%] |
| 2016 | 10 | 3 | 30.0% | [10.8%, 60.3%] |
| 2017 | 9 | 4 | 44.4% | [18.9%, 73.3%] |
| 2018 | 10 | 3 | 30.0% | [10.8%, 60.3%] |
| 2019 | 11 | 3 | 27.3% | [9.7%, 56.6%] |
| 2020 | 17 | 5 | 29.4% | [13.3%, 53.1%] |
| 2021 | 22 | 1 | 4.5% | [0.8%, 21.8%] |
| 2022 | 28 | 2 | 7.1% | [2.0%, 22.6%] |
| 2023 | 72 | 1 | 1.4% | [0.2%, 7.5%] |
| 2024 | 34 | 3 | 8.8% | [3.0%, 23.0%] |
| 2025 | 26 | 1 | 3.8% | [0.7%, 18.9%] |
| 2026 | 11 | 4 | 36.4% | [15.2%, 64.6%] |

## By publisher (descriptive only -- no CI, most publishers have very few sampled records)

| Publisher | n | Gap n | Gap rate |
|---|---|---|---|
| Hindawi | 54 | 1 | 1.9% |
| Elsevier | 43 | 8 | 18.6% |
| Wiley | 25 | 7 | 28.0% |
| Springer | 19 | 2 | 10.5% |
| Elsevier - Cell Press | 13 | 4 | 30.8% |
| PLoS | 12 | 0 | 0.0% |
| Taylor and Francis | 10 | 1 | 10.0% |
| Springer - Biomed Central (BMC) | 9 | 1 | 11.1% |
| Springer - Nature Publishing Group | 9 | 1 | 11.1% |
| Frontiers | 9 | 0 | 0.0% |
| Spandidos | 8 | 0 | 0.0% |
| American Association for Cancer Research | 6 | 4 | 66.7% |
| SAGE Publications | 6 | 1 | 16.7% |
| American Chemical Society (ACS) | 5 | 2 | 40.0% |
| American Society for Biochemistry and Molecular Biology (ASBMB) | 4 | 0 | 0.0% |
| MDPI | 4 | 1 | 25.0% |
| Oxford University Press | 4 | 0 | 0.0% |
| Karger | 3 | 2 | 66.7% |
| Wolters Kluwer | 3 | 2 | 66.7% |
| BioMed Central (BMC) | 3 | 1 | 33.3% |
| Portland Press | 3 | 1 | 33.3% |
| IOS Press (bought by Sage November 2023) | 3 | 0 | 0.0% |
| Wolters Kluwer - Lippincott Williams & Wilkins | 3 | 0 | 0.0% |
| Cellular Physiol Biochem Press | 3 | 0 | 0.0% |
| Microbiology Society | 2 | 0 | 0.0% |
| Nature Publishing Group | 2 | 0 | 0.0% |
| e-Century Publishing Corporation | 2 | 1 | 50.0% |
| Optica (formerly Optical Society of America -OSA-) | 2 | 0 | 0.0% |
| American Heart Association | 2 | 1 | 50.0% |
| Taylor and Francis - Dove Press | 2 | 0 | 0.0% |

## Independent-vs-RW-derived breakdown (gap cases only)

| Classification | n |
|---|---|
| gap_independent_evidence | 15 |
| gap_rw_derived_only | 9 |
| gap_rw_only_uncorroborated | 23 |
