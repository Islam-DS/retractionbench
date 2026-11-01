# Phase 1 Exploration Report

Generated: 2026-08-05. Source: raw Retraction Watch table (see docs/DATA_NOTES.md for exact source URL and access date). **215 completely blank rows** (every field null -- a source CSV export artifact, not real records) were found and are excluded from every count and table below; the raw DuckDB table itself is untouched and still contains them. See docs/DATA_NOTES.md for the full exclusion accounting. No filtering or domain-selection decisions are made in this report -- see docs/DECISIONS.md ADR-013 for why the benchmark's domain count is small (3-4) and chosen only after this report is read.

## 1. Overview by notice type

Total raw records (all notice types): **71325**.

| Notice type | Count | % of all records |
| --- | --- | --- |
| Retraction (paper-1 scope) | 66081 | 92.6% |
| Correction | 1499 | 2.1% |
| Expression of Concern | 0 | 0.0% |
| Reinstatement | 160 | 0.2% |
| Expression of concern | 3585 | 5.0% |
| **Total** | 71325 | 100.0% |

## 2. Records with a resolvable DOI

"Resolvable DOI" here means `OriginalPaperDOI` -- the superseded paper's own identifier, not the retraction notice's DOI (which is reported separately under data quality).

| Notice type | Total records | Resolvable OriginalPaperDOI | % |
| --- | --- | --- | --- |
| Retraction (paper-1 scope) | 66081 | 60198 | 91.1% |
| Correction | 1499 | 1468 | 97.9% |
| Expression of Concern | 0 | 0 | n/a |
| Reinstatement | 160 | 155 | 96.9% |
| Expression of concern | 3585 | 3556 | 99.2% |

## 3. Distribution by year

Summary by notice type:

| Notice type | Total | Post-2015 (year >= 2016) | Post-2020 (year >= 2021) |
| --- | --- | --- | --- |
| Retraction (paper-1 scope) | 66081 | 47622 | 35707 |
| Correction | 1499 | 1028 | 372 |
| Expression of Concern | 0 | 0 | 0 |
| Reinstatement | 160 | 150 | 60 |
| Expression of concern | 3585 | 3428 | 2553 |

Full year-by-year breakdown, Retraction only (paper-1 scope):

| Retraction year | Count (paper-1 scope: Retraction only) |
| --- | --- |
| 1927 | 1 |
| 1960 | 1 |
| 1966 | 1 |
| 1967 | 2 |
| 1968 | 1 |
| 1970 | 7 |
| 1971 | 1 |
| 1975 | 2 |
| 1977 | 31 |
| 1979 | 5 |
| 1980 | 14 |
| 1981 | 3 |
| 1982 | 5 |
| 1983 | 13 |
| 1984 | 8 |
| 1985 | 14 |
| 1986 | 28 |
| 1987 | 12 |
| 1988 | 6 |
| 1989 | 15 |
| 1990 | 19 |
| 1991 | 23 |
| 1992 | 25 |
| 1993 | 28 |
| 1994 | 22 |
| 1995 | 25 |
| 1996 | 26 |
| 1997 | 46 |
| 1998 | 71 |
| 1999 | 51 |
| 2000 | 41 |
| 2001 | 37 |
| 2002 | 124 |
| 2003 | 89 |
| 2004 | 127 |
| 2005 | 139 |
| 2006 | 212 |
| 2007 | 330 |
| 2008 | 450 |
| 2009 | 1186 |
| 2010 | 5012 |
| 2011 | 4937 |
| 2012 | 1159 |
| 2013 | 1450 |
| 2014 | 1114 |
| 2015 | 1545 |
| 2016 | 1683 |
| 2017 | 1711 |
| 2018 | 2535 |
| 2019 | 2907 |
| 2020 | 3079 |
| 2021 | 3905 |
| 2022 | 5570 |
| 2023 | 13210 |
| 2024 | 6155 |
| 2025 | 5728 |
| 2026 | 1139 |

## 4. Subject category distribution

Counted per-label: a record listing multiple subjects is counted once for each. Top 25 by Retraction count (paper-1 scope).

| Subject | Retraction (paper-1 scope) | Correction | Expression of Concern | Reinstatement | Expression of concern | Total |
| --- | --- | --- | --- | --- | --- | --- |
| (B/T) Technology | 12230 | 48 | 0 | 5 | 302 | 12585 |
| (BLS) Biology - Cellular | 11116 | 674 | 0 | 22 | 952 | 12764 |
| (B/T) Computer Science | 9255 | 29 | 0 | 3 | 120 | 9407 |
| (BLS) Genetics | 8366 | 412 | 0 | 11 | 533 | 9322 |
| (BLS) Biochemistry | 7631 | 399 | 0 | 13 | 559 | 8602 |
| (BLS) Biology - Cancer | 6342 | 317 | 0 | 8 | 422 | 7089 |
| (B/T) Data Science | 5632 | 18 | 0 | 0 | 55 | 5705 |
| (SOC) Education | 5205 | 21 | 0 | 4 | 171 | 5401 |
| (BLS) Biology - Molecular | 4453 | 283 | 0 | 7 | 343 | 5086 |
| (B/T) Business - Economics | 4130 | 13 | 0 | 2 | 33 | 4178 |
| (PHY) Mathematics | 4077 | 15 | 0 | 1 | 41 | 4134 |
| (HSC) Medicine - Oncology | 3822 | 124 | 0 | 15 | 148 | 4109 |
| (ENV) Environmental Sciences | 3213 | 26 | 0 | 5 | 167 | 3411 |
| (PHY) Materials Science | 3083 | 61 | 0 | 0 | 101 | 3245 |
| (B/T) Business - Management | 3039 | 15 | 0 | 2 | 30 | 3086 |
| (HSC) Medicine - Pharmacology | 2982 | 75 | 0 | 17 | 275 | 3349 |
| (HSC) Medicine - Surgery | 2539 | 45 | 0 | 6 | 98 | 2688 |
| (HSC) Medicine - Cardiovascular | 2475 | 46 | 0 | 10 | 83 | 2614 |
| (HSC) Medicine - Neurology | 2359 | 63 | 0 | 10 | 102 | 2534 |
| (BLS) Toxicology | 2298 | 111 | 0 | 9 | 190 | 2608 |
| (PHY) Chemistry | 2264 | 60 | 0 | 0 | 101 | 2425 |
| (PHY) Engineering - Electrical | 2155 | 14 | 0 | 4 | 67 | 2240 |
| (SOC) Psychology | 2088 | 53 | 0 | 4 | 140 | 2285 |
| (B/T) Business - General | 2073 | 4 | 0 | 1 | 21 | 2099 |
| (HSC) Medicine - Obstetrics/Gynecology | 1866 | 46 | 0 | 15 | 186 | 2113 |

## 5. Retraction reason distribution

Counted per-label, same convention as subjects. Top 20 by Retraction count (paper-1 scope).

| Reason | Retraction (paper-1 scope) | Correction | Expression of Concern | Reinstatement | Expression of concern | Total |
| --- | --- | --- | --- | --- | --- | --- |
| Investigation by Journal/Publisher | 29601 | 81 | 0 | 7 | 1752 | 31441 |
| Unreliable Results and/or Conclusions | 21490 | 18 | 0 | 5 | 37 | 21550 |
| Investigation by Third Party | 17289 | 39 | 0 | 2 | 279 | 17609 |
| Concerns/Issues about Referencing/Attributions | 14828 | 93 | 0 | 3 | 179 | 15103 |
| Concerns/Issues about Data | 14229 | 70 | 0 | 14 | 1511 | 15824 |
| Notice - Limited or No Information | 11973 | 7 | 0 | 92 | 34 | 12106 |
| Paper Mill | 11710 | 0 | 0 | 0 | 86 | 11796 |
| Concerns/Issues about Peer Review | 11287 | 0 | 0 | 0 | 289 | 11576 |
| Compromised Peer Review | 10866 | 0 | 0 | 1 | 580 | 11447 |
| Concerns/Issues about Results and/or Conclusions | 9172 | 18 | 0 | 3 | 761 | 9954 |
| Computer-Aided Content or Computer-Generated Content | 9165 | 0 | 0 | 0 | 1 | 9166 |
| Date of Article and/or Notice Unknown | 6881 | 9 | 0 | 99 | 15 | 7004 |
| Duplication of/in Image | 5156 | 175 | 0 | 1 | 186 | 5518 |
| Breach of Policy by Author | 4791 | 2 | 0 | 2 | 2 | 4797 |
| Removed | 3968 | 10 | 0 | 70 | 5 | 4053 |
| Euphemisms for Plagiarism | 3740 | 15 | 0 | 1 | 15 | 3771 |
| Duplication of/in Article | 3641 | 9 | 0 | 1 | 48 | 3699 |
| Objections by Author(s) | 3450 | 7 | 0 | 1 | 32 | 3490 |
| Investigation by Company/Institution | 3262 | 114 | 0 | 1 | 452 | 3829 |
| Author Unresponsive | 2997 | 3 | 0 | 1 | 163 | 3164 |

## 6. Records with more than one reason

| Notice type | Total records | Records with >1 reason | % |
| --- | --- | --- | --- |
| Retraction (paper-1 scope) | 66081 | 54558 | 82.6% |
| Correction | 1499 | 1086 | 72.4% |
| Expression of Concern | 0 | 0 | n/a |
| Reinstatement | 160 | 152 | 95.0% |
| Expression of concern | 3585 | 3280 | 91.5% |

## 7. Top 15 subject categories: post-2015 retractions with a DOI

Retraction-only, year >= 2016. Subject ranking taken from section 4's overall top 15.

| Subject (top 15 overall, from section 4) | Post-2015 retractions | ...with resolvable DOI | % |
| --- | --- | --- | --- |
| (B/T) Technology | 9685 | 9413 | 97.2% |
| (BLS) Biology - Cellular | 9033 | 8814 | 97.6% |
| (B/T) Computer Science | 7513 | 7452 | 99.2% |
| (BLS) Genetics | 7219 | 7111 | 98.5% |
| (BLS) Biochemistry | 6332 | 6192 | 97.8% |
| (BLS) Biology - Cancer | 5761 | 5625 | 97.6% |
| (B/T) Data Science | 5536 | 5536 | 100.0% |
| (SOC) Education | 3621 | 3100 | 85.6% |
| (BLS) Biology - Molecular | 2795 | 2748 | 98.3% |
| (B/T) Business - Economics | 2175 | 1823 | 83.8% |
| (PHY) Mathematics | 1099 | 1026 | 93.4% |
| (HSC) Medicine - Oncology | 3280 | 3202 | 97.6% |
| (ENV) Environmental Sciences | 2202 | 2119 | 96.2% |
| (PHY) Materials Science | 2361 | 2297 | 97.3% |
| (B/T) Business - Management | 1261 | 1019 | 80.8% |

## 8. Reason co-occurrence (top 25 pairs)

Retraction only (paper-1 scope) -- this is candidate stratification-variable analysis for domain selection, which is a paper-1-scoped decision. Restricted to pairs where both reasons are in the top 20 most frequent reasons (section 5), to keep the pair space bounded.

| Reason A | Reason B | Co-occurrence count |
| --- | --- | --- |
| Investigation by Journal/Publisher | Unreliable Results and/or Conclusions | 18230 |
| Investigation by Journal/Publisher | Investigation by Third Party | 15417 |
| Concerns/Issues about Referencing/Attributions | Investigation by Journal/Publisher | 13726 |
| Investigation by Third Party | Unreliable Results and/or Conclusions | 13186 |
| Concerns/Issues about Referencing/Attributions | Unreliable Results and/or Conclusions | 12406 |
| Concerns/Issues about Peer Review | Investigation by Journal/Publisher | 11058 |
| Concerns/Issues about Data | Investigation by Journal/Publisher | 10975 |
| Concerns/Issues about Data | Unreliable Results and/or Conclusions | 10616 |
| Investigation by Third Party | Paper Mill | 10498 |
| Investigation by Journal/Publisher | Paper Mill | 10345 |
| Concerns/Issues about Peer Review | Unreliable Results and/or Conclusions | 10269 |
| Concerns/Issues about Data | Investigation by Third Party | 10149 |
| Concerns/Issues about Referencing/Attributions | Investigation by Third Party | 10118 |
| Concerns/Issues about Peer Review | Concerns/Issues about Referencing/Attributions | 9986 |
| Compromised Peer Review | Investigation by Journal/Publisher | 9742 |
| Paper Mill | Unreliable Results and/or Conclusions | 9493 |
| Computer-Aided Content or Computer-Generated Content | Investigation by Journal/Publisher | 8949 |
| Concerns/Issues about Data | Concerns/Issues about Referencing/Attributions | 8905 |
| Concerns/Issues about Data | Concerns/Issues about Peer Review | 8701 |
| Concerns/Issues about Peer Review | Investigation by Third Party | 8464 |
| Computer-Aided Content or Computer-Generated Content | Concerns/Issues about Referencing/Attributions | 8271 |
| Computer-Aided Content or Computer-Generated Content | Investigation by Third Party | 8242 |
| Concerns/Issues about Data | Concerns/Issues about Results and/or Conclusions | 8124 |
| Concerns/Issues about Results and/or Conclusions | Investigation by Journal/Publisher | 8113 |
| Concerns/Issues about Results and/or Conclusions | Unreliable Results and/or Conclusions | 8002 |

## 9. Time-to-supersession (gap between OriginalPaperDate and notice date)

By notice type (negative gaps excluded from the stats and counted separately -- see section 10 for why they're a data quality issue, not a real value):

| Notice type | N (valid, non-negative gap) | Mean days | Median days | Min | Max | Negative gaps |
| --- | --- | --- | --- | --- | --- | --- |
| Retraction (paper-1 scope) | 66080 | 889 | 489 | 0 | 29622 | 0 |
| Correction | 1499 | 1198 | 669 | 0 | 19297 | 0 |
| Expression of Concern | 0 | n/a | n/a | n/a | n/a | 0 |
| Reinstatement | 160 | 569 | 0 | 0 | 25954 | 0 |
| Expression of concern | 3585 | 2173 | 1122 | 0 | 28191 | 0 |

Gaps longer than 40 years are flagged as implausible but *not* excluded from the stats above (unusual isn't the same as impossible): **71** records.

By subject, Retraction only (paper-1 scope), top 15 subjects from section 4:

| Subject (top 15, from section 4) | N | Mean days | Median days |
| --- | --- | --- | --- |
| (B/T) Technology | 12230 | 542 | 454 |
| (BLS) Biology - Cellular | 11116 | 1531 | 1096 |
| (B/T) Computer Science | 9255 | 648 | 505 |
| (BLS) Genetics | 8366 | 1346 | 958 |
| (BLS) Biochemistry | 7631 | 1565 | 1036 |
| (BLS) Biology - Cancer | 6342 | 1478 | 1128 |
| (B/T) Data Science | 5632 | 666 | 517 |
| (SOC) Education | 5205 | 453 | 352 |
| (BLS) Biology - Molecular | 4453 | 1332 | 772 |
| (B/T) Business - Economics | 4130 | 442 | 188 |
| (PHY) Mathematics | 4077 | 305 | 60 |
| (HSC) Medicine - Oncology | 3822 | 1012 | 586 |
| (ENV) Environmental Sciences | 3213 | 525 | 364 |
| (PHY) Materials Science | 3083 | 881 | 517 |
| (B/T) Business - Management | 3039 | 344 | 61 |

## 10. Subject x reason cross-tabulation (top 10 subjects x top 10 reasons)

Retraction only (paper-1 scope). A record with multiple subjects and/or reasons contributes to every (subject, reason) cell it's tagged with -- cells are not mutually exclusive counts.

| Subject \ Reason | Investigation by Journal | Unreliable Results and/o | Investigation by Third P | Concerns/Issues about Re | Concerns/Issues about Da | Notice - Limited or No I | Paper Mill | Concerns/Issues about Pe | Compromised Peer Review | Concerns/Issues about Re |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| (B/T) Technology | 8760 | 6572 | 5181 | 5395 | 3460 | 2420 | 4594 | 4176 | 4273 | 3153 |
| (BLS) Biology - Cellular | 3685 | 3230 | 3227 | 669 | 3179 | 476 | 2332 | 608 | 466 | 884 |
| (B/T) Computer Science | 7082 | 4781 | 3664 | 4168 | 2076 | 1589 | 3062 | 2763 | 4090 | 1980 |
| (BLS) Genetics | 3701 | 2918 | 3246 | 906 | 2735 | 314 | 2352 | 863 | 751 | 974 |
| (BLS) Biochemistry | 2971 | 2542 | 1891 | 553 | 1887 | 560 | 1310 | 423 | 580 | 724 |
| (BLS) Biology - Cancer | 2607 | 2082 | 2279 | 372 | 2072 | 143 | 1852 | 348 | 443 | 579 |
| (B/T) Data Science | 5332 | 4638 | 4015 | 4084 | 2468 | 59 | 2744 | 3183 | 2237 | 2106 |
| (SOC) Education | 2912 | 1960 | 1645 | 1842 | 1439 | 1588 | 1279 | 1548 | 996 | 1246 |
| (BLS) Biology - Molecular | 1621 | 1428 | 1208 | 516 | 982 | 261 | 806 | 460 | 510 | 498 |
| (B/T) Business - Economics | 1586 | 1175 | 615 | 1051 | 492 | 1871 | 464 | 788 | 700 | 549 |

## 11. PubMed ID availability by subject

Retraction only -- this is scoped to the the project protocol verification rule, which only applies to retractions. A subject rich in retraction counts but poor in PMIDs is a weak domain candidate regardless of raw volume, since the PubMed tag can't be checked without a PMID.

| Subject (top 15, from section 4) | Retractions | ...with resolvable OriginalPaperPubMedID | % |
| --- | --- | --- | --- |
| (B/T) Technology | 12230 | 1915 | 15.7% |
| (BLS) Biology - Cellular | 11116 | 10464 | 94.1% |
| (B/T) Computer Science | 9255 | 1094 | 11.8% |
| (BLS) Genetics | 8366 | 7784 | 93.0% |
| (BLS) Biochemistry | 7631 | 6476 | 84.9% |
| (BLS) Biology - Cancer | 6342 | 6088 | 96.0% |
| (B/T) Data Science | 5632 | 1577 | 28.0% |
| (SOC) Education | 5205 | 743 | 14.3% |
| (BLS) Biology - Molecular | 4453 | 4042 | 90.8% |
| (B/T) Business - Economics | 4130 | 576 | 13.9% |
| (PHY) Mathematics | 4077 | 111 | 2.7% |
| (HSC) Medicine - Oncology | 3822 | 3366 | 88.1% |
| (ENV) Environmental Sciences | 3213 | 997 | 31.0% |
| (PHY) Materials Science | 3083 | 568 | 18.4% |
| (B/T) Business - Management | 3039 | 224 | 7.4% |

## 12. Clinical domain candidates: (HSC) subjects + (BLS) Toxicology, tiered

Retraction only, post-2015, PubMed-ID-resolvable -- the same population used throughout domain selection. DOI %/PMID % are computed over the post-2015 subset, matching section 7's convention. tier_1_clean / tier_2_duplication / tier_3_other_ambiguous are defined in `src/retraction_bench/curate/reason_screen.py`; see docs/DECISIONS.md ADR-016 through ADR-018 for the methodology and the domain-selection reasoning built on these numbers.

| Subject | Total retractions | Post-2015 | Resolvable DOI % | Resolvable PMID % | tier_1_clean | tier_2_duplication | tier_3_other_ambiguous | tier_1 median days |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| (BLS) Toxicology | 2298 | 2004 | 97.3% | 90.2% | 219 | 211 | 414 | 934 |
| (HSC) Medicine - Oncology | 3822 | 3280 | 97.6% | 88.4% | 216 | 127 | 219 | 782 |
| (HSC) Medicine - Pharmacology | 2982 | 2223 | 97.9% | 91.3% | 179 | 95 | 316 | 1174 |
| (HSC) Medicine - Obstetrics/Gynecology | 1866 | 1521 | 97.1% | 88.6% | 136 | 46 | 208 | 1320 |
| (HSC) Medicine - Neurology | 2359 | 2017 | 97.9% | 79.0% | 110 | 55 | 184 | 722 |
| (HSC) Medicine - Surgery | 2539 | 1918 | 97.0% | 90.8% | 107 | 10 | 181 | 1043 |
| (HSC) Medicine - Rehabilitation/Therapy | 1661 | 1342 | 95.8% | 81.6% | 100 | 22 | 95 | 762 |
| (HSC) Medicine - Cardiovascular | 2475 | 1957 | 97.4% | 84.9% | 95 | 22 | 136 | 996 |
| (HSC) Medicine - Gastroenterology | 1528 | 1284 | 97.4% | 92.1% | 80 | 63 | 100 | 636 |
| (HSC) Medicine - Infectious Disease | 1537 | 1284 | 98.4% | 77.6% | 80 | 16 | 123 | 360 |
| (HSC) Public Health and Safety | 1538 | 1231 | 95.9% | 63.8% | 80 | 1 | 71 | 380 |
| (HSC) Biostatistics/Epidemiology | 949 | 831 | 97.7% | 84.8% | 79 | 0 | 62 | 356 |
| (HSC) Medicine - Orthopedics | 1480 | 1271 | 97.2% | 87.7% | 74 | 31 | 103 | 679 |
| (HSC) Medicine - Immunology | 1259 | 789 | 95.1% | 84.7% | 55 | 22 | 81 | 540 |
| (HSC) Medicine - Pulmonology | 1227 | 1007 | 98.3% | 89.9% | 54 | 23 | 79 | 680 |
| (HSC) Medicine - Anesthesia/Anaesthesia | 953 | 610 | 97.0% | 93.4% | 50 | 3 | 122 | 4104 |
| (HSC) Medicine - Pediatrics | 1031 | 813 | 95.0% | 79.0% | 49 | 2 | 55 | 331 |
| (HSC) Medicine - Urology/Nephrology | 937 | 761 | 98.3% | 90.5% | 43 | 24 | 59 | 1063 |
| (HSC) Medicine - Cardiology | 822 | 516 | 94.0% | 81.0% | 40 | 9 | 77 | 2434 |
| (HSC) Radiology/Imaging | 1622 | 1467 | 98.6% | 75.5% | 40 | 28 | 52 | 638 |
| (HSC) Medicine - Psychiatry | 512 | 407 | 96.3% | 77.9% | 36 | 2 | 55 | 498 |
| (HSC) Medicine - General | 1163 | 932 | 93.1% | 55.9% | 34 | 9 | 35 | 374 |
| (HSC) Medicine - Drug Design | 671 | 470 | 97.4% | 81.1% | 31 | 46 | 69 | 991 |
| (HSC) Medicine - Diabetes | 679 | 557 | 96.2% | 84.2% | 29 | 27 | 60 | 766 |
| (HSC) Medicine - Alternative | 775 | 682 | 98.5% | 88.7% | 26 | 11 | 54 | 916 |
| (HSC) Medicine - Endocrinology | 630 | 438 | 95.2% | 87.2% | 22 | 18 | 33 | 1136 |
| (HSC) Medicine - Otorhinolaryngology | 561 | 443 | 97.3% | 84.9% | 22 | 10 | 35 | 730 |
| (HSC) Medicine - Dentistry | 498 | 377 | 91.5% | 77.7% | 21 | 17 | 26 | 525 |
| (HSC) Nutrition | 263 | 229 | 97.4% | 84.3% | 17 | 1 | 44 | 1043 |
| (HSC) Medicine - Pathology | 1021 | 826 | 98.2% | 94.9% | 16 | 46 | 46 | 1288 |
| (HSC) Medicine - Sports | 241 | 196 | 97.4% | 76.5% | 16 | 0 | 11 | 774 |
| (HSC) Veterinary Science | 266 | 177 | 95.5% | 77.4% | 16 | 21 | 23 | 1602 |
| (HSC) Medicine - Dermatology | 492 | 410 | 97.8% | 86.3% | 15 | 15 | 16 | 301 |
| (HSC) Medicine - Ophthalmology | 434 | 356 | 95.2% | 77.8% | 15 | 5 | 21 | 301 |
| (HSC) Occupational Health and Safety | 357 | 271 | 92.6% | 53.9% | 14 | 0 | 14 | 541 |
| (HSC) Medicine - Internal | 357 | 284 | 94.0% | 81.0% | 10 | 3 | 10 | 502 |
| (HSC) Medicine - Geriatric | 412 | 336 | 96.7% | 79.5% | 9 | 1 | 21 | 205 |
| (HSC) Medicine - Nursing | 588 | 544 | 99.4% | 93.0% | 7 | 0 | 5 | 460 |
| (HSC) Sports Science | 338 | 321 | 98.8% | 50.8% | 7 | 2 | 6 | 494 |
| (HSC) Medicine - Transplantation | 105 | 101 | 100.0% | 93.1% | 2 | 2 | 15 | 300 |

## 13. Claim-type-filtered ranking (PROVISIONAL -- screen not yet validated)

**The claim_type column comes from a heuristic keyword screen (`config/vocabularies/claim_type_screen.yaml`) that has not yet been scored against hand labels.** Treat this table as provisional until docs/DECISIONS.md ADR-021 records a measured agreement rate. `tier_1 AND clinical claim type` = tier_1_clean records whose title/ArticleType were classified `clinical_intervention` or `clinical_observational` (not `preclinical` or `unclear`). The `tier_1+clinical median days` figure is computed over that same narrow, doubly-filtered subset, and is partly an artifact of which reason tags and which title keywords happen to survive both screens -- not a clean estimate of the subject's true evidence-turnover speed. The broad median (unfiltered, all retractions in the subject) is the more stable number and the one comparable across subjects; report both in the paper, never the narrow one alone.

| Subject | tier_1 (unfiltered) | tier_1 AND clinical claim type | broad median days (unfiltered) | tier_1+clinical median days |
| --- | --- | --- | --- | --- |
| (HSC) Medicine - Pharmacology | 179 | 156 | 765 | 1293 |
| (HSC) Medicine - Oncology | 216 | 124 | 586 | 814 |
| (HSC) Medicine - Obstetrics/Gynecology | 136 | 119 | 679 | 1461 |
| (HSC) Medicine - Surgery | 107 | 103 | 548 | 1045 |
| (HSC) Medicine - Rehabilitation/Therapy | 100 | 89 | 514 | 625 |
| (HSC) Medicine - Cardiovascular | 95 | 83 | 560 | 996 |
| (HSC) Medicine - Neurology | 110 | 77 | 540 | 525 |
| (HSC) Public Health and Safety | 80 | 77 | 432 | 406 |
| (HSC) Biostatistics/Epidemiology | 79 | 75 | 476 | 355 |
| (HSC) Medicine - Infectious Disease | 80 | 66 | 464 | 343 |
| (HSC) Medicine - Gastroenterology | 80 | 57 | 656 | 561 |
| (HSC) Medicine - Orthopedics | 74 | 56 | 578 | 656 |
| (HSC) Medicine - Immunology | 55 | 47 | 567 | 540 |
| (HSC) Medicine - Anesthesia/Anaesthesia | 50 | 46 | 1556 | 4680 |
| (HSC) Medicine - Pediatrics | 49 | 45 | 523 | 331 |
| (HSC) Medicine - Pulmonology | 54 | 38 | 561 | 587 |
| (HSC) Medicine - Psychiatry | 36 | 35 | 602 | 490 |
| (HSC) Medicine - Cardiology | 40 | 34 | 676 | 3172 |
| (HSC) Medicine - General | 34 | 34 | 498 | 374 |
| (HSC) Radiology/Imaging | 40 | 33 | 540 | 603 |
| (HSC) Medicine - Urology/Nephrology | 43 | 30 | 560 | 1070 |
| (HSC) Medicine - Diabetes | 29 | 24 | 580 | 440 |
| (HSC) Medicine - Alternative | 26 | 20 | 561 | 663 |
| (HSC) Medicine - Endocrinology | 22 | 20 | 601 | 1086 |
| (HSC) Medicine - Otorhinolaryngology | 22 | 18 | 704 | 916 |
| (HSC) Medicine - Dentistry | 21 | 17 | 608 | 404 |
| (HSC) Nutrition | 17 | 17 | 615 | 1043 |
| (HSC) Medicine - Sports | 16 | 16 | 473 | 774 |
| (HSC) Medicine - Ophthalmology | 15 | 14 | 490 | 308 |
| (HSC) Medicine - Dermatology | 15 | 12 | 536 | 270 |
| (HSC) Medicine - Drug Design | 31 | 12 | 730 | 1505 |
| (HSC) Occupational Health and Safety | 14 | 12 | 427 | 541 |
| (HSC) Medicine - Pathology | 16 | 11 | 881 | 741 |
| (HSC) Medicine - Geriatric | 9 | 8 | 522 | 264 |
| (HSC) Medicine - Nursing | 7 | 7 | 454 | 460 |
| (HSC) Sports Science | 7 | 7 | 508 | 494 |
| (HSC) Veterinary Science | 16 | 7 | 914 | 1736 |
| (HSC) Medicine - Internal | 10 | 5 | 552 | 551 |
| (HSC) Medicine - Transplantation | 2 | 2 | 1295 | 300 |

## 14. Data quality problems

- **Unexpected RetractionNature values** (not in the documented set): ['Expression of concern']

### Dates

| Notice type | RetractionDate missing | RetractionDate malformed | OriginalPaperDate missing | OriginalPaperDate malformed |
| --- | --- | --- | --- | --- |
| Retraction (paper-1 scope) | 0 | 1 | 0 | 1 |
| Correction | 0 | 0 | 0 | 0 |
| Expression of Concern | 0 | 0 | 0 | 0 |
| Reinstatement | 0 | 0 | 0 | 0 |
| Expression of concern | 0 | 0 | 0 | 0 |

### Malformed DOIs (present but not valid DOI syntax)

| Notice type | RetractionDOI malformed (present, bad syntax) | OriginalPaperDOI malformed |
| --- | --- | --- |
| Retraction (paper-1 scope) | 2 | 0 |
| Correction | 0 | 0 |
| Expression of Concern | 0 | 0 |
| Reinstatement | 0 | 0 |
| Expression of concern | 0 | 0 |

### Duplicate records

- Record IDs appearing more than once: **0** distinct IDs, **0** rows total.
- Distinct OriginalPaperDOI values appearing on more than one record: **2354** (this can legitimately mean multiple notices for the same paper, e.g. a Correction followed later by a Retraction -- not necessarily an error; reported separately from true Record ID duplicates).

### Inconsistent subject category labels (case/whitespace variants of the same label)

- None found.

### Trailing unnamed column (from the source header's trailing comma)

- Non-empty values: **0** (expected: 0).
