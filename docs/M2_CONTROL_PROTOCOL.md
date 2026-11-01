# M2: Matched Non-Retracted Control Protocol

**Status: Phases 1-2 (audit, protocol design) complete. Phases 3-11 blocked — see section 9.**

Prespecified, before any control candidate is sourced, per the same discipline `docs/ANNOTATION.md`
already applies to the 28-item benchmark: define the rule, then follow it, not the reverse. This
document is the frozen protocol against which every control candidate will later be judged: to
change it once real candidates exist would make the matching-quality report meaningless.

---

## 1. Repository and data audit (Phase 1)

### 1.1 Existing item schema (`data/benchmark/items.jsonl`, 28 rows)

| Field | Values found | Use for M2 |
|---|---|---|
| `item_id` | `RB-0001`..`RB-0028` | Controls get a parallel `RC-0001`..`RC-00NN` ID space, cross-referenced 1:1 to the `item_id` they're matched against. |
| `domain` | 3 values: `(HSC) Medicine - Pharmacology` (13), `(HSC) Medicine - Obstetrics/Gynecology` (14), `(HSC) Medicine - Rehabilitation/Therapy` (1) | **Hard matching constraint** (exact match required). |
| `claim_type` | `clinical_intervention` (20), `clinical_observational` (8) | **Hard matching constraint** (exact match required). |
| `item_type` | `superseded_with_current_answer` (15), `superseded_without_current_answer` (13) | No direct control analog — a control has no supersession event at all. See 2.3 for the substitute dimension. |
| `claim_polarity` | `positive` (24), `negative` (4) | Soft matching preference (2.2, tier 2). |
| `evidence_tier_match` | `same_tier` (15), `None` (13, only populated for `superseded_with_current_answer` items) | No direct analog; substitute is the control's own supporting-evidence tier (2.3). |
| `question` | free text, quantitative form by convention (`docs/ANNOTATION.md` section 4, ADR-039) | Controls must follow the same question-generation convention — see 2.2. |
| `trap_claim`, `gold_claim` | `{text, valid_from, valid_until}` | No `trap_claim` for a control (nothing to trap on) — a control has only a `current_claim` analogous to `gold_claim`. |
| `post_supersession_evidence` | list of `Evidence` objects (`evidence_type`, `identifier`, `independence_verified`, `note`, `publication_date`, `source_authority`) | Direct analog: `supporting_evidence`, same object shape, same verification bar (2.4). |
| `supporting_sources` | list of `source_registry_id` (the *retracted* source) | No analog — a control's underlying source is, by definition, never retracted. |
| `provenance`, `annotations` | `verified` / dated annotator notes | Same discipline required for controls (2.7). |

### 1.2 The source registry (`data/benchmark/sources.jsonl`, 28 rows)

One row per *retracted* source: `doi`, `source_registry_id`, `notice_specificity`, `notice_text_verified`, `supersession_type`, `supersession_date`, `verification_method`, `verification_confirmed`. **A control has no row here by definition** — its whole qualifying property is the absence of a supersession event. Section 2.4 defines how that absence itself gets verified and logged (a control needs its own, differently-shaped provenance record, not a `sources.jsonl` row with empty supersession fields).

### 1.3 Rejected / deferred candidate logs

`data/benchmark/rejected_candidates.jsonl` (6 rows) and `deferred_candidates.jsonl` (6 rows) are **not usable as raw material for M2 controls** — checked directly, not assumed. Every row in both files is still a *retracted* paper that failed a different screen (`no_institutional_source`: 1, `other`: 5) during the original curation funnel. None of them are non-retracted candidates; they cannot be repurposed.

### 1.4 The annotation protocol's institutional-source standard (`docs/ANNOTATION.md` section 3.2)

This is the load-bearing constraint for M2. The existing standard: a gold claim must trace to a systematic review/meta-analysis, a clinical practice guideline, a Cochrane review, a regulatory agency statement, or (for epidemiological claims) a national statistics body — **never the annotator's own reasoning, never a primary study alone treated as sufficient**. Independence must be checked *before* drafting, not after. The eligibility search is capped at 30 minutes/candidate, and the project's own measured rate is **45-60 minutes per successful item including rejection overhead** (`docs/DECISIONS.md` ADR-036/037).

This same standard, applied without a weaker bar, is what section 2.4 below requires for M2 controls. Reusing it (not inventing a lighter-weight substitute) is what keeps a control comparable to a treated item in source quality, not just in domain/claim-type label — a control assembled from lower-quality sourcing would confound "supersession-specific difficulty" with "source-quality difference," undermining the whole point of M2.

### 1.5 Corpus, retrieval, and query-generation infrastructure

- Corpus: frozen, hashed, versioned (`src/retraction_bench/corpus/freeze.py`, `write_manifest`) — reused unchanged for M2 (section 5).
- Query generation: the quantitative-question convention (`docs/ANNOTATION.md` section 4, ADR-039) — reused unchanged for M2 (section 2.2).
- Retrieval conditions: `no_retrieval` / `retrieval_naive` / `retrieval_with_notice` / `post_notice` (`src/retraction_bench/rag/collect.py`) — **three of these four are structurally tied to the existence of a supersession notice**, which a control has none of. This is a real, unresolved design question, not a detail — flagged explicitly in section 6.
- Statistics: `src/retraction_bench/stats/paired_test.py` (`paired_bootstrap_permutation_test`, item-level paired bootstrap + sign-flip permutation, Holm correction) and `stats/bootstrap.py` (`bootstrap_proportion_ci_clustered`) — both reused unchanged for M2's own analysis (section 7), not reimplemented.

### 1.6 Leakage risks identified during audit

1. A control's supporting evidence could, in principle, cite or discuss the *same* retracted paper it's meant to be independent of (if the domains overlap closely) — must be checked explicitly (section 5).
2. A control could be an accidental "disguised retracted item" — e.g. a later, currently-valid paper on the *same specific claim* as one of the 28 trap claims, which would make it a same-topic *replacement* case, not an independent control (explicitly called out in the task brief; addressed in section 2.3).
3. `source_registry_id` and DOI namespaces are already used by the treated-item side (`sources.jsonl`) — a control accidentally sharing an identifier with any treated item's source or its `post_supersession_evidence` would silently corrupt both the leakage check and the corpus indexing. Checked in section 5's script.

### 1.7 Fields suitable for matching vs. fields missing

**Suitable, present now:** `domain`, `claim_type`, `claim_polarity`, question form/style, evidence type (`evidence_type` on the `Evidence` object), `source_authority`.

**Missing, needed, and not inventable from existing data:** an explicit "intervention/exposure class" taxonomy (e.g. drug class, procedure category) — the current schema has no such field; section 2.2 defines it as a *manually assessed and logged* dimension, not a controlled vocabulary lookup, since building a real taxonomy is itself a modeling choice with no existing ground truth to draw from.

---

## 2. Control construction protocol (Phase 2)

### 2.1 Unit of matching: **item-level**

Every outcome this benchmark reports ($R_c$, $R_r$, $U_s$, $U_r$, $C$) is scored at the item level (retrieval) or at the response level nested within an item (citation/correctness), and the existing statistical machinery (`bootstrap_proportion_ci_clustered`, `paired_bootstrap_permutation_test`) already clusters by `item_id`. Item-level matching is therefore not a stylistic choice — it is the only unit that lets M2 plug into the existing, tested statistical pipeline without new code. Claim-level or source-level matching would either be a no-op (each item already *is* one claim) or would conflate multiple claims sharing one source, breaking the clustering assumption the existing bootstrap code depends on.

### 2.2 Matching dimensions, in priority order

1. **`domain`** — exact match. Hard constraint.
2. **`claim_type`** — exact match. Hard constraint.
3. **Question form** — same quantitative-question convention (`docs/ANNOTATION.md` section 4). Hard constraint (a control violating the paper's own question-style convention would introduce a second confound: phrasing, not supersession status).
4. **Evidence-tier of the control's own supporting evidence**, compared against the tier of the matched item's `post_supersession_evidence` (for `superseded_with_current_answer` items) or, for `superseded_without_current_answer` items, against a stated target tier of "systematic review / guideline / Cochrane / regulatory" (the same floor `docs/ANNOTATION.md` section 3.2 sets for every item). Soft preference, tier 1.
5. **`claim_polarity`** — same-direction preference (a positive-effect control matched to a positive-effect item, etc.). Soft preference, tier 1.
6. **Intervention/exposure-class overlap** — manually assessed and logged as free text (e.g. "same drug class," "same procedure category," "unrelated but same domain"), not a controlled vocabulary score (1.7). Soft preference, tier 2.
7. **Claim shape** ("single intervention vs. multi-factor," a coarse, logged judgment, not an invented complexity index) — soft preference, tier 2.

**Explicitly excluded, per the task brief and this project's own standing discipline against outcome-dependent covariate selection:** model citation behavior, model correctness, retrieval outcome, or any property of a model's response. None of these may influence which control is selected for which item — doing so would make the "control" partially a function of the very outcome it's meant to help interpret.

### 2.3 Control definition

A candidate qualifies as a valid non-retracted control only if **all** of the following hold:

- It is built around a clinically meaningful, answerable question in the quantitative form (2.2.3).
- Its supporting evidence traces to an institutional source meeting the *same* bar as `docs/ANNOTATION.md` section 3.2 — no weaker standard for controls than for treated items (1.4).
- The underlying paper/synthesis has **never** been retracted, is **not** under an active expression of concern, and has **not** received a correction that changes the specific claim direction being asked about (a correction to an unrelated figure in the same paper does not disqualify it; a correction to the claim under test does).
- It is not, under this benchmark's own operational definition (`supersession_type` taxonomy already in `sources.jsonl`: retraction, expression of concern, major correction, guideline revision, evidence superseded by newer evidence), superseded in *any* of those five senses — not just "not formally retracted."
- **It is not a disguised version of a treated item.** A later, currently-valid paper on the *exact same specific claim* as one of the 28 trap claims is a same-topic *replacement* case (already a different, already-measured axis of this benchmark — $R_r$/$U_r$), not an independent control. A valid control tests a **different clinical question** in the same domain/claim-type stratum, not the corrected version of one of the 28 existing questions.
- Non-supersession is verified through the same channels already used for `post_supersession_evidence` independence checks: the source venue's own corrections/errata page, a direct Retraction Watch database check, and the publisher's own site — not inferred from the paper simply "seeming fine."

### 2.4 Temporal rule

Two checkpoints, both required, not one:

1. **As of the existing corpus freeze date** (`src/retraction_bench/corpus/freeze.py`'s recorded `freeze_date` — the same date already governing every treated item): the control's supporting evidence must have been current and non-retracted.
2. **As of the actual date of control construction** (i.e., now): the same check is repeated. A source that was clean at freeze time but has since been retracted, corrected, or placed under an expression of concern is **rejected outright**, not merely footnoted — a control that becomes invalid shortly after being selected defeats the purpose of a stable comparison set.

No document published after the corpus freeze date may be used to construct a control's supporting evidence, for the same reason it isn't used anywhere else in this benchmark: it would let information unavailable to the evaluated retrieval pipeline leak into how the control was built.

### 2.5 Source quality rule

Identical to `docs/ANNOTATION.md` section 3.2, reused verbatim, not restated with a lower bar: systematic review/meta-analysis, clinical practice guideline, Cochrane review, regulatory agency statement, or (epidemiological claims only) a national statistics body. Primary-study-only sourcing is treated exactly as it already is for treated items — logged as a weaker evidence tier, not excluded outright, and reported separately (mirrors the existing `evidence_tier_match` treatment).

### 2.6 Matching algorithm

**Deterministic, priority-ordered stratification — not a weighted composite score.** A composite numeric score would require assigning weights to dimensions 4-7 above with no existing data to calibrate those weights against; the task brief explicitly forbids exactly this kind of unjustified invented score, and this protocol agrees with that constraint rather than working around it.

The procedure, applied per treated item:

1. Filter the candidate pool to exact matches on `domain` and `claim_type` (2.2, tier 0 — hard constraints). Candidates failing either are dropped, not ranked.
2. Among survivors, apply tier-1 preferences (evidence tier, polarity) as a **lexicographic sort**, not a weighted sum: sort first by evidence-tier agreement (agree > disagree), then by polarity agreement (agree > disagree) among ties.
3. Among remaining ties, apply tier-2 preferences (intervention-class overlap, claim shape) the same way — as a documented, logged human judgment call each time, not a further numeric score.
4. Keep the top 2-5 ranked candidates as the retained backup pool (Phase 4), select the top-ranked as the primary match, and log the specific reason(s) every dropped or lower-ranked candidate lost (Phase 4/6) — an audit trail, not just a final answer.

### 2.7 Provenance and logging discipline

Every control candidate (selected or not) gets the same `annotations` discipline already applied to treated items (`annotator_id`, `date`, `note`, `provenance` field) — no candidate enters the frozen dataset without a dated, attributed verification note, matching `docs/ANNOTATION.md` section 5.

---

## 3. Control candidate sourcing (Phase 3) — file formats specified, not populated

The following files are **schema-specified here, not created with content** (section 9 explains why):

- `control_candidates.csv` — one row per candidate considered (selected or not): `candidate_id, matched_item_id, source_id, source_title, domain, claim_type, question_text, intervention_class, claim_polarity, publication_date, current_status_verified_date, evidence_tier, source_authority, provenance_note, status {selected|backup|rejected}, rejection_reason`.
- `matched_controls.csv` — one row per **selected** control only: same columns, `status` fixed to `selected`, plus `rank_among_candidates`.
- `control_matching_log.csv` — one row per **treated item**: `item_id, n_candidates_considered, selected_control_id, backup_control_ids (2-5), decision_notes`.
- `control_provenance.jsonl` — one JSON object per selected control, same shape as a treated item's `Evidence` object plus the two-checkpoint temporal verification (2.4) and the institutional-source citation (2.5).

## 4-8. Matching, quality audit, match-quality report, leakage audit, frozen dataset

Specified as procedures in sections 2 and 3 above; **not executed**, since execution requires real candidate content (section 9). The leakage-check script itself, however, does not require real candidate content to write — it is infrastructure, not data — and has been built now so it is ready to run the moment real candidates exist: `scripts/check_control_leakage.py` (checks: shared `source_registry_id`/DOI between any control and any treated item's source or `post_supersession_evidence`; shared/overlapping title n-grams; a control's identifier appearing anywhere in the existing corpus manifest under a treated item's own record; script exits non-zero and lists every match found — never silently passes on an empty candidate file, since an empty-input false-pass would be worse than no check at all).

---

## 5. Evaluation design (Phase 9) — what stays identical, what cannot

**Identical, reused unchanged:** query-generation convention (quantitative form), corpus and its freeze/versioning, model/deployment configurations (all three), seeds (three), prompt format, output schema, `rag/parse.py`'s parsing rules, evaluation metrics ($U_s$-analog, $C$).

**Cannot be identical, and this is the open design question this audit surfaces rather than papers over:** three of the four existing conditions (`retrieval_naive`, `retrieval_with_notice`, `post_notice`) are defined *in terms of a supersession notice's presence or absence*. A control has no notice — there is nothing to exclude, guarantee, or confront the model with. Mechanically forcing controls through all four conditions unchanged would not produce a meaningful `retrieval_naive` vs. `retrieval_with_notice` contrast; it would produce two identical conditions with different names.

Two defensible resolutions, **neither adopted here** — this is exactly the kind of methodological fork that should be decided once, explicitly, not improvised mid-implementation:

- **(A)** Run controls under `no_retrieval` and a single `retrieval` condition only (retrieval on, no notice concept applies), and skip `post_notice` entirely for controls (there is nothing to confront the model with). Cleaner, but loses any control-side comparison for the M3/`post_notice` axis.
- **(B)** Run controls under all four condition *labels* for retrieval-pipeline consistency, treating `retrieval_naive`/`retrieval_with_notice` as identical no-ops for controls and `post_notice` as a repeat of `no_retrieval`'s answer with no notice shown. Preserves a uniform data shape but produces two pairs of literally-duplicate conditions, which is worse for interpretability, not better.

This document does not pick between them. It is flagged as an unresolved risk in section 9, not resolved by default.

---

## 6. Statistical analysis plan (Phase 10)

- **Unit of inference:** item-level, matched pair (one treated item, one selected control).
- **Comparison type:** **paired**, not independent-samples — each pair is matched by construction (2.6), so the existing `paired_bootstrap_permutation_test` (`stats/paired_test.py`) is reused directly: per-model, per-outcome paired difference (treated item's outcome minus its matched control's outcome), bootstrap CI, sign-flip permutation p-value, Holm correction across the family of comparisons run together (mirrors the existing M1 three-model family exactly).
- **Outcomes analyzed:** $U_s$-analog (does the model cite/avoid the control's own would-be-superseded framing — requires care, since a control has no trap source to avoid; the literal transferable outcome is **substantive correctness, $C$**, plus retrieval-success rate for the control's own supporting evidence), and, only where condition (A) or (B) from section 5 is resolved, an M3-analog under whichever conditions remain meaningful for controls.
- **Clustering:** item-level clustering (`bootstrap_proportion_ci_clustered`), identical convention to the rest of the paper.
- **Multiple comparisons:** Holm correction across the prespecified family, not per-test uncorrected p-values.
- **Missing/malformed responses:** handled exactly as `rag/parse.py` already does — no fuzzy repair, a genuinely unparseable response is a reported rate, not silently dropped or guessed.
- **Exploratory vs. confirmatory:** at n=28 matched pairs (or fewer, if some items cannot be matched — see section 9), this is explicitly an **exploratory, small-n analysis**, reported with the same caveats the paper already applies to its other small-n axes (`docs/paper.md` section 6) — not upgraded to a confirmatory claim by virtue of having a control group.
- **No new composite score** is introduced anywhere in this plan, and no causal language beyond what a matched (not randomized) observational comparison supports — this design improves causal *interpretability* relative to the unmatched comparison it replaces; it does not license the word "causal" outright, since assignment to "retracted vs. control" is not randomized, only matched.

---

## 7. Unresolved risks (reported, not resolved)

1. **Section 5's condition-mapping question** — genuinely open, needs a decision before Phase 3 sourcing even starts, since it determines what "current-status verification" needs to check for and what a control candidate actually needs to look like.
2. **Real candidate sourcing is the same class of work as the original 28-item benchmark, at the same rigor bar** — `docs/ANNOTATION.md`'s own measured rate is 45-60 minutes per successful item including rejection overhead (1.4). At that rate, 28 matched controls is a realistic **20-28+ hours of real, human literature-verification work**, not a script that can be run. See section 9.
3. **Domain coverage risk:** the Rehabilitation/Therapy domain has exactly one treated item (`item_type` distribution, 1.1). Finding even one valid, independently-sourced control in that domain may not be possible within the 30-minute-per-candidate search cap this protocol reuses from `docs/ANNOTATION.md` — a realistic outcome is 27, not 28, matched pairs, with the Rehabilitation item's control search logged as a rejection if no institutional source is found, exactly as the original benchmark's own annotation log already treats unsuccessful searches (1.3-style logging, not silently dropping the item).

---

## 8. Files created / modified this pass

- **Created:** `docs/M2_CONTROL_PROTOCOL.md` (this file), `scripts/check_control_leakage.py` (leakage-check infrastructure, runs cleanly against zero candidates today — verified, not assumed — and is ready the moment real candidate files exist).
- **Not created:** `control_candidates.csv`, `matched_controls.csv`, `control_matching_log.csv`, `control_provenance.jsonl`, `benchmark/controls_v1/` — schemas specified (section 3), content not fabricated (section 9).
- **Not modified:** `data/benchmark/items.jsonl`, `data/benchmark/sources.jsonl`, any file under `data/human/`, the existing 900 model responses, any evaluated model configuration.

---

## 9. Why Phase 3 onward stops here

Sourcing real M2 candidates means finding real, currently-valid, institutionally-sourced clinical claims and verifying, per candidate, that they have never been retracted, corrected, or placed under an expression of concern — the identical task `docs/ANNOTATION.md` already defines for the 28 treated items, at the identical rigor bar (section 1.4), with a measured real-world cost of 45-60 minutes per successful item.

This project's own standing rule (the project protocol, already enforced throughout M1: "No LLM-generated ground truth") exists for exactly this situation. Fabricating 28 "verified" institutional sources — plausible-sounding guideline citations, DOIs, and verification notes I have not actually confirmed against a real source — would not satisfy this protocol; it would silently violate the same principle this entire benchmark is built to hold other systems to. I am not going to do that, and no version of "efficiently completing M2" is worth that trade.

**What I can respons­ibly do next, if you want it:** use real web search to propose a *draft* candidate pool — real papers/guidelines/reviews, with real URLs and DOIs, one plausible set per domain/claim-type stratum — for **your own review and verification**, exactly mirroring the annotator role `docs/ANNOTATION.md` already assigns to you for the treated items. That turns 20-28 hours of your own from-scratch searching into a shorter verification pass over a pre-filtered draft list, without ever presenting anything as "verified" until you've actually verified it.
