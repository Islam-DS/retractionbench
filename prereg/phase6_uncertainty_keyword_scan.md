# Prespec: Phase 6 — reproducible explicit-uncertainty keyword scan

**Status: prespecified before running, not "pre-registered" (no OSF/AsPredicted record exists).**

- **Timestamp:** 2026-10-30, written before the script below was created or run.
- **Motivation:** The manuscript's "3/117 (2.6%) explicit uncertainty" figure (claims ledger row
  12) was produced by a 20-phrase keyword scan described in `docs/DECISIONS.md` but never
  committed; the phrase list itself was not recorded, so the figure cannot be regenerated. Under
  the project rule that every reported number must come from committed code and a cached output,
  it is replaced by a fresh scan with the phrase list fixed here, in advance. The old list is not
  reconstructed or approximated, and this list is not adjusted after seeing any result.
- **Data:** `data/interim/eval/model_responses.jsonl` (cached; never modified). Scope: every
  `no_retrieval` response on the 13 `superseded_without_current_answer` items (expected 117 =
  13 items x 3 models x 3 seeds). Text scanned: `raw_answer_text` only (what the model returned),
  lower-cased; hidden reasoning in `raw_call_metadata` is not scanned.
- **Phrase list (fixed, 20 entries, case-insensitive substring match):**
  `i don't know`, `i do not know`, `not sure`, `uncertain`, `unclear`, `insufficient evidence`,
  `limited evidence`, `evidence is limited`, `evidence is insufficient`, `lack of evidence`,
  `not enough evidence`, `no current`, `no reliable`, `no consensus`, `conflicting evidence`,
  `inconclusive`, `not been established`, `not well established`, `cannot determine`,
  `unable to determine`.
- **Primary endpoint:** responses with at least one hit / 117, with a Wilson 95% CI and an
  item-clustered bootstrap 95% CI (10,000 resamples, seed 42); per-model and per-item hit counts
  and every matched phrase in context are saved.
- **Reporting rule:** the new figure replaces 2.6% in the manuscript whatever its value; the old
  figure is reported alongside it in `docs/ANALYSIS_LOG.md` as superseded (unreproducible). No
  human labels are used or compared to choose phrases. The scan is a mechanical phrase match and
  is reported as such: it counts detectable hedging wording, not calibration or honesty.
- **No new model or embedding calls.**
