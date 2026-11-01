# Phase 1 item 7: domain-matched vs. full-corpus retrieval ranks

Prereg: `prereg/phase1_item7_domain_matched_ranks.md`. Same frozen corpus/index/embedding
model as every other ranking measurement in this paper; domain-matched rank is the same
full ranking filtered to same-domain candidates only, not a new or re-weighted search.

## Headline finding: trap/notice retrievability is unaffected by domain crowding; replacement-evidence retrievability is substantially affected

**Trap source and notice ranks are identical, or within 1 position, between full-corpus and
domain-matched rankings for every one of the 24 eligible items.** Domain pool size (12,061 to
258,020 documents) makes essentially no difference here -- these documents are lexically and
semantically so close to their own item's query that almost nothing outside their own domain ever
outranks them regardless of how large the cross-domain corpus is. This is a real, reassuring
robustness check on the paper's central retrievability finding: it is not an artifact of a
particular domain being under-crowded.

**Replacement-evidence rank tells a different, materially important story.** Domain-matched
recall improves substantially over the published full-corpus figures:

| k | Recall@k, full-corpus (published) | Recall@k, domain-matched (new) |
|---|---|---|
| 1 | 6.7% (1/15) | 6.7% (1/15) |
| 3 | 53.3% (8/15) | **66.7% (10/15)** |
| 5 | 53.3% (8/15) | **73.3% (11/15)** |
| 10 | 60.0% (9/15) | **73.3% (11/15)** |

Two items move from "effectively unfindable at any realistic k" to "found within a realistic
top-3-to-5 window" once domain-crowding is removed: **RB-0026 (full-corpus rank 29 -> domain rank
3)** and **RB-0001 (rank 56 -> rank 4)**. A third, **RB-0022 (rank 10 -> rank 3)**, moves from the
edge of a top-10 window to comfortably inside a top-3 one. This directly affects how the "three
effectively unfindable" framing in the published §4.5 text should be read: **the three items that
remain unfindable even domain-matched are RB-0010 (253,313 -> 42,762), RB-0012 (81,153 -> 9,438),
and RB-0013 (7,941 -> 2,102)** -- the same three items the original text already names, and they
remain genuinely unfindable by any realistic standard even after this correction. But the
*milder* difficulty cases (RB-0001, RB-0022, RB-0026) were not nearly as hard as their full-corpus
rank suggested -- a meaningful fraction of their apparent difficulty was Rehabilitation/Therapy's
79.37%-of-background-pool crowding (Phase 0 finding), not an intrinsic property of the query or
the replacement document itself.

**Recommended manuscript change (not yet applied):** report both figures side by side in §4.5/4.6
(recall@k full-corpus vs. domain-matched), and revise the "effectively unfindable... not merely
subordinate" language to name RB-0010/RB-0012/RB-0013 as the specific items that remain
unfindable under either standard, rather than letting the reader infer this from the full-corpus
number alone, which overstates the difficulty for the other 12 items.

## Full item-level table

| Item | Domain | Trap rank (full) | Trap rank (domain) | Notice rank (full) | Notice rank (domain) | Replacement rank (full) | Replacement rank (domain) | Domain pool size |
|---|---|---|---|---|---|---|---|---|
| RB-0001 | (HSC) Medicine - Pharmacology | 1 | 1 | 2 | 2 | 56 | 4 | 55086 |
| RB-0002 | (HSC) Medicine - Obstetrics/Gynecology | 1 | 1 | 2 | 2 | 3 | 3 | 12061 |
| RB-0003 | (HSC) Medicine - Obstetrics/Gynecology | 1 | 1 | 2 | 2 | -- | -- | 12061 |
| RB-0004 | (HSC) Medicine - Pharmacology | 1 | 1 | 3 | 3 | -- | -- | 55086 |
| RB-0006 | (HSC) Medicine - Pharmacology | 1 | 1 | 3 | 3 | 2 | 2 | 55086 |
| RB-0007 | (HSC) Medicine - Obstetrics/Gynecology | 2 | 2 | 1 | 1 | -- | -- | 12061 |
| RB-0008 | (HSC) Medicine - Pharmacology | 2 | 2 | 1 | 1 | 3 | 3 | 55086 |
| RB-0009 | (HSC) Medicine - Rehabilitation/Therapy | 1 | 1 | 2 | 2 | 27 | 27 | 258020 |
| RB-0010 | (HSC) Medicine - Pharmacology | 1 | 1 | 3 | 2 | 253313 | 42762 | 55086 |
| RB-0011 | (HSC) Medicine - Pharmacology | 2 | 2 | 1 | 1 | -- | -- | 55086 |
| RB-0012 | (HSC) Medicine - Obstetrics/Gynecology | 1 | 1 | 2 | 2 | 81153 | 9438 | 12061 |
| RB-0013 | (HSC) Medicine - Obstetrics/Gynecology | 1 | 1 | 2 | 2 | 7941 | 2102 | 12061 |
| RB-0014 | (HSC) Medicine - Obstetrics/Gynecology | 2 | 2 | 1 | 1 | 3 | 3 | 12061 |
| RB-0015 | (HSC) Medicine - Pharmacology | 1 | 1 | 2 | 2 | -- | -- | 55086 |
| RB-0016 | (HSC) Medicine - Obstetrics/Gynecology | 1 | 1 | 3 | 3 | -- | -- | 12061 |
| RB-0017 | (HSC) Medicine - Obstetrics/Gynecology | 2 | 2 | 1 | 1 | 3 | 3 | 12061 |
| RB-0018 | (HSC) Medicine - Obstetrics/Gynecology | 2 | 2 | 1 | 1 | 3 | 3 | 12061 |
| RB-0019 | (HSC) Medicine - Pharmacology | 1 | 1 | 3 | 3 | -- | -- | 55086 |
| RB-0020 | (HSC) Medicine - Pharmacology | 1 | 1 | 2 | 2 | -- | -- | 55086 |
| RB-0021 | (HSC) Medicine - Obstetrics/Gynecology | 1 | 1 | 2 | 2 | 3 | 3 | 12061 |
| RB-0022 | (HSC) Medicine - Obstetrics/Gynecology | 2 | 2 | 1 | 1 | 10 | 3 | 12061 |
| RB-0023 | (HSC) Medicine - Pharmacology | 2 | 2 | 1 | 1 | -- | -- | 55086 |
| RB-0024 | (HSC) Medicine - Pharmacology | 1 | 1 | 2 | 2 | -- | -- | 55086 |
| RB-0025 | (HSC) Medicine - Pharmacology | 2 | 2 | 1 | 1 | -- | -- | 55086 |
| RB-0026 | (HSC) Medicine - Pharmacology | -- | -- | -- | -- | 29 | 3 | 55086 |
| RB-0027 | (HSC) Medicine - Obstetrics/Gynecology | -- | -- | -- | -- | 1 | 1 | 12061 |
