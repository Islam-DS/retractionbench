# Prereg: Phase 1 item 7 — domain-matched retrieval ranks alongside full-corpus ranks

**Status: post hoc re-analysis/additional reporting of already-published results, prespecified
before running — not a pre-registration.**

- **Timestamp:** 2026-10-03
- **Git commit at time of writing:** `88309ed802fa074547589613f87f682c55f68c5c`
- **Motivation:** Every rank reported in §4.5/§4.6 (trap source, notice, replacement evidence) is
  computed against the full, cross-domain 325,167-document corpus. Given Phase 0's finding that
  Rehabilitation/Therapy alone is 79.37% of the background pool, a document's full-corpus rank is
  partly a function of how crowded its own domain's share of the corpus is, not purely how
  retrievable it is relative to clinically relevant competitors. Domain-matched rank (rank within
  only same-domain candidates) is a natural, cheap additional report.
- **Hypothesis:** None — descriptive, additional reporting alongside the existing figures, not a
  hypothesis test.
- **Primary endpoint:** For every item already scored in §4.5 (trap/notice rank) and §4.6
  (replacement-evidence rank), the same rank computed restricted to candidates sharing the item's
  own `domain` field (filtering the existing full ranking, no new FAISS search required).
- **Test:** N/A (descriptive).
- **Exclusion rules:** Identical item sets as the original measurements (24 notice-eligible items
  for trap/notice rank; 15 `superseded_with_current_answer` items for replacement rank).
- **No new model/embedding calls:** reuses the existing frozen FAISS index and the already-computed
  full ranking for each item; domain-matched rank is obtained by filtering that same ranking, not
  by re-querying the index.
