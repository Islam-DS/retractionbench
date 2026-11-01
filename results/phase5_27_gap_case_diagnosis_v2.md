# Phase 5 Part A, REDONE: independent vs. RW-derived evidence, 24 distinct PMIDs

Rerun after fixing two real problems in v1: OpenAlex's `is_retracted` is RW-sourced, not
independent (per OpenAlex's own documentation, fetched live this session); Crossref's
`relation` field was checked too crudely (a false positive on an unrelated `has-review`
link). See the module docstring in `phase5_diagnose_27_gap_cases_v2.py` for the exact
classification rules, fixed before this rerun.

## Classification summary

| Classification | n |
|---|---|
| independent_evidence | 10 |
| rw_derived_only | 13 |
| rw_only_uncorroborated | 1 |

**Rate with all 24 cases counted as genuine gaps: 24/296 pool = 8.11%**
(unchanged from the row/PMID-level correction -- classification here doesn't change *whether*
a gap exists, only how well-corroborated each one is by a source independent of RW).

**Of the 24, 10 (41.7%) have genuinely independent
corroborating evidence; 13 are corroborated only by a
source that itself derives from RW (not independent validation); 1 rests on RW
alone with no corroboration found anywhere.**

**Rate with and without the one fully-uncorroborated case (PMID 26955437):**

| | n (gap) | Denominator | Rate | Wilson 95% CI |
|---|---|---|---|---|
| Including PMID 26955437 | 24 | 296 | 8.11% | [5.51%, 11.78%] |
| Excluding PMID 26955437 | 23 | 296 | 7.77% | [5.23%, 11.40%] |

The two intervals overlap heavily -- excluding the one fully-uncorroborated case does not
materially change the headline rate or its precision. Both figures are reported; this paper's
headline number should state which one it is (including it, since it is a real RW-listed
retraction even if unusually poorly documented, not a confirmed error).

## Full per-case detail

| PMID | Classification | Evidence |
|---|---|---|
| 14583953 | rw_derived_only | RW-derived only: OpenAlex is_retracted=True, Crossref update-to source=retraction-watch=False |
| 16856030 | independent_evidence | Crossref relation (publisher-asserted): ['withdrawal'] |
| 19959915 | rw_derived_only | RW-derived only: OpenAlex is_retracted=True, Crossref update-to source=retraction-watch=False |
| 22696330 | rw_derived_only | RW-derived only: OpenAlex is_retracted=True, Crossref update-to source=retraction-watch=False |
| 25069726 | rw_derived_only | RW-derived only: OpenAlex is_retracted=True, Crossref update-to source=retraction-watch=False |
| 26658572 | independent_evidence | PubMed title itself: 'RETRACTED ARTICLE: The benefit of arthroscopically assisted therapy for concomit'; Crossref update-to, source=publisher |
| 26955437 | rw_only_uncorroborated | (none found) |
| 27098397 | independent_evidence | PubMed title itself: 'Retracted: Exosomes secreted by human urine-derived stem cells accelerate skin w' |
| 27140910 | rw_derived_only | RW-derived only: OpenAlex is_retracted=True, Crossref update-to source=retraction-watch=False |
| 27294218 | rw_derived_only | RW-derived only: OpenAlex is_retracted=True, Crossref update-to source=retraction-watch=False |
| 27552401 | rw_derived_only | RW-derived only: OpenAlex is_retracted=True, Crossref update-to source=retraction-watch=False |
| 28226403 | rw_derived_only | RW-derived only: OpenAlex is_retracted=True, Crossref update-to source=retraction-watch=True |
| 28395637 | independent_evidence | PubMed title itself: 'RETRACTED ARTICLE: Safety and effectiveness of high-dose methotrexate (over 8\u2009mg'; Crossref update-to, source=publisher |
| 28617973 | rw_derived_only | RW-derived only: OpenAlex is_retracted=True, Crossref update-to source=retraction-watch=True |
| 29438490 | rw_derived_only | RW-derived only: OpenAlex is_retracted=True, Crossref update-to source=retraction-watch=False |
| 30267080 | rw_derived_only | RW-derived only: OpenAlex is_retracted=True, Crossref update-to source=retraction-watch=False |
| 30688986 | rw_derived_only | RW-derived only: OpenAlex is_retracted=True, Crossref update-to source=retraction-watch=False |
| 31415103 | independent_evidence | Crossref relation (publisher-asserted): ['retraction'] |
| 31563928 | independent_evidence | PubMed title itself: 'RETRACTED Are over-the-counter fish oil supplements safe, effective and accurate' |
| 32946583 | rw_derived_only | RW-derived only: OpenAlex is_retracted=True, Crossref update-to source=retraction-watch=False |
| 37940041 | independent_evidence | PubMed title itself: 'WITHDRAWN: The Effect of Preoperative Intravenous Tranexamic Acid Versus Rectal '; Crossref update-to, source=publisher |
| 39566682 | independent_evidence | Crossref update-to, source=publisher |
| 39906865 | independent_evidence | Crossref update-to, source=publisher |
| 6522427 | independent_evidence | Crossref update-to, source=publisher |
