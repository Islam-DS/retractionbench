# Phase 1 item 8: recall@5 alongside recall@10 (post hoc addendum, no new computation)

Source: `results/replacement_retrieval_ceiling.json`'s existing `recall_at` field (already
computed by `scripts/replacement_retrieval_ceiling.py`'s `K_VALUES = (1, 3, 5, 10, 20)` — never
previously pulled into the manuscript). Full-corpus ranking, n=15 `superseded_with_current_answer`
items, unchanged scope from the original measurement.

| k | Recall@k (original, already published) |
|---|---|
| 1 | 6.7% (1/15) |
| 3 | 53.3% (8/15) |
| **5** | **53.3% (8/15) — identical to recall@3, not previously reported** |
| 10 | 60.0% (9/15) |
| 20 | 60.0% (9/15) |

**Why this matters, stated plainly:** `rag/prompts.py`'s `RETRIEVAL_K = 5` is the actual number of
documents the deployed pipeline shows any model in its context — not 10. Recall@10 describes a
window one model never actually operates in. Recall@5 is unchanged from recall@3 (no additional
item enters the ranking between position 4 and 5); the one item that separates recall@5 from
recall@10 is RB-0022, whose replacement document ranks at exactly position 10 (confirmed
independently via this session's PE1 baseline-replication check).

**Recommended manuscript change (not yet applied):** everywhere §4.5/§4.6/Abstract currently
state "60.0% recall@10," add "(53.3% at the pipeline's actual k=5)" alongside it, so the
headline number matches what the deployed system actually retrieves, not a larger window.
