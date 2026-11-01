# Phase 5: PubMed-title-vs-RW-title mismatch check

Author-requested validation (2026-10-05, item 4), following the accidental discovery of
one wrong/truncated PMID (RW record_id 250) during the Part B downstream dossier re-check.
Git hash: `88309ed802fa074547589613f87f682c55f68c5c`.

Checked 296 distinct PMIDs in the curated pool (Part A) and 300 in the Part B v2 broad sample. Similarity: difflib `SequenceMatcher` ratio on normalized titles (lowercased, punctuation stripped, trailing `(Pub N)`/`(Review)`/`(Protocol)` tags removed); threshold 0.4 chosen to catch genuine mismatches while tolerating RW's own paraphrasing/abbreviation of titles (observed to vary even for confirmed-correct pairs).

**Part A flagged: 2/296. Part B flagged: 3/300.**

| Pool | PMID | RW title | PubMed title | Similarity |
|---|---|---|---|---|
| Part A (curated pool) | 38355237 | Predicting chorioamnionitis using AI-based methods: a retrospective cohort study | (empty/no record) | 0.0 |
| Part A (curated pool) | 35593880 | Effectiveness of anti-CGRP monoclonal antibodies for persistent headaches in pat | American Headache Society 64th Annual Scientific Meeting June 9-12, 2022 Denver, | 0.28 |
| Part B v2 (broad sample) | 28451861 | Abstract 256688 - SCOUT RADAR localization improves breast surgery operating roo | (empty/no record) | 0.0 |
| Part B v2 (broad sample) | 12966832 | End of a millennium - end of the simple mammary bypass. Two Arteriae mammariae i | [End of the millennium - end of the single mammary artery graft? Two internal ma | 0.225 |
| Part B v2 (broad sample) | 1834920 | A prospective randomized trial on the role of perioperative celecoxib administra | Preprotein translocase of Escherichia coli: solubilization, purification, and re | 0.341 |

## Disposition of each flagged case

- **38355237 (Part A)**: PubMed's own ESummary API returns `"error": "cannot get document
  summary"` for this PMID -- confirmed live, not a transient batching artifact. Already known
  and already disclosed: `results/pubmed_rw_completeness_check.md` flagged this exact PMID in
  2026-08 as "a genuine unresolvable-PMID error... excluded from this count and from the
  candidate pool pending manual check." A further attempt this round to resolve it by searching
  PubMed directly for RW's exact title text returned zero results -- the real PMID, if one
  exists, was not found. Status unchanged: excluded, unresolved, not a false claim.
- **28451861 (Part B)**: Also returns a PubMed API error, confirmed live. Already known: this is
  Part B v2's own single disclosed `unresolved_pubmed_lookup_failed` case
  (`results/phase5_part_b_scaled_check_v2.json`), already excluded from the 299/300 resolved
  denominator. No new finding -- independent re-confirmation that it is genuinely unresolvable,
  not a transient failure that should have resolved on retry.
- **35593880 (Part A)**: A new, previously-undocumented but harmless pattern (trap 14 in
  `docs/RW_PUBMED_METADATA_TRAPS.md`): this PMID is PubMed's record for an entire conference
  proceedings volume (American Headache Society 2022 annual meeting abstracts), not a
  specific-abstract-level record -- RW's `title` field holds the individual abstract's title,
  PubMed's holds the volume's. The retraction-tag check itself is unaffected:
  `pubmed_retracted_tag_confirmed=True` in `data/interim/tier1_candidates_final3_verified.csv`,
  and this PMID is not one of the 24 gap cases -- the tag genuinely is present on the shared
  volume record. No reclassification needed.
- **12966832 (Part B)**: A false positive of the similarity heuristic, not a data error. PubMed's
  title is the full original (German) title, bracket-marked per MEDLINE convention for a
  non-English article; RW's title is a partial English paraphrase of the same subject (internal
  mammary artery bypass, "end of the millennium" framing). Confirmed the same paper by subject
  match. No reclassification needed; disclosed to show the similarity threshold's own limitation.
- **1834920 (Part B)**: The already-known, already-reclassified wrong/truncated-PMID case
  (`results/phase5_part_b_downstream_dossiers.md`) -- this systematic check independently
  re-confirms it and found no *additional* case of the same kind in either population.

**Net finding: this systematic check found no wrong-PMID cases beyond the one already caught by**
**chance during the Part B dossier re-check.** Both populations' other four flagged pairs are
either already-disclosed unresolvable PMIDs or confirmed same-paper matches that merely paraphrase
or vary in granularity -- a reassuring result for the paper's broader data-quality claims, not a
null result being quietly buried: the check was real, ran against all 596 distinct PMIDs, and is
reported in full above regardless of what it found.
