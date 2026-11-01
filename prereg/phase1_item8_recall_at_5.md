# Prereg: Phase 1 item 8 — report recall@5 wherever recall@10 is reported

**Status: additional reporting of already-computed, cached results — not a new computation, not
a pre-registration.**

- **Timestamp:** 2026-10-03
- **Git commit at time of writing:** `88309ed802fa074547589613f87f682c55f68c5c`
- **Motivation:** The deployed pipeline's actual retrieved-document count is `RETRIEVAL_K=5`
  (`rag/prompts.py`), not 10 — recall@10 numbers currently reported describe a larger window than
  any model ever actually saw in its own context. `scripts/replacement_retrieval_ceiling.py`
  already computes `K_VALUES = (1, 3, 5, 10, 20)`, so recall@5 already exists in the cached output
  (`results/replacement_retrieval_ceiling.json`) and has simply never been pulled into the
  manuscript prose/table alongside recall@10.
- **Hypothesis:** None.
- **Primary endpoint:** recall@5 for the 15-item replacement-evidence ceiling, read directly from
  the existing JSON — no new computation.
- **No new model/embedding calls.**
