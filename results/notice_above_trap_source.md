# Notice-above-trap-source: rate and the necessary-but-not-sufficient condition (ADR-111)

## CORRECTED, TAKE TWO: rate is 9/24 (37.5%), not 9/22 or 10/27 (2026-08-20, ADR-136) — the n=22 section below is also SUPERSEDED

**The `n=22` section immediately below was itself wrong, caught before any evaluation call fired**
**(ADR-136).** `notice_text_verified` is not the right eligibility test -- RB-0003 and RB-0004
have real, retrievable notice text despite being unverified, and belong in the comparison.
**Corrected, final: 9/24 = 37.5%, Wilson 95% CI [21.2%, 57.3%].** The count itself is unchanged
(still the same nine cases); only the denominator moved, a second time. Neither RB-0003 nor
RB-0004 is a flip case -- both collapse cleanly with their trap source ranked ahead of their
notice, ordinary additions. Full accounting: ADR-136.

---

## SUPERSEDED (ADR-136) — CORRECTED: rate is 9/22 (40.9%), not 10/27 (37.0%)

**Everything below this section is kept exactly as originally written and is superseded, not**
**deleted.** ADR-133 found the corpus underlying this file's counts was stale: five sources
(`rw-7837`/RB-0003, `rw-1471`/RB-0004, `rw-6062`/RB-0026, `rw-21782`/RB-0027, `rw-24670`/RB-0028)
are correctly `notice_text_verified=False` under current annotation, but the corpus still had a
bare-notice document for all five, built before their verification status was corrected.

**RB-0027 -- one of the original ten flip cases, and the specific case this file called out as**
**"breaking the pattern the other nine share"** (zero lexical overlap, yet outranking its trap
source by a wider-than-usual margin) -- **has no notice document under corrected data and cannot**
**flip.** It was never a real instance of a notice beating its trap source; it was a bare-notice
placeholder, built from a source whose notice text was later determined unrecoverable, outranking
a trap source that had genuine indexed content. **The count changes from 10 to 9; the correct
denominator changes from 27 (or 24) notice-bearing items to 22.**

**Corrected rate: 9/22 = 40.9%, Wilson 95% CI [23.3%, 61.3%]** (`curate/scoring.wilson_ci`, this
project's own implementation, reused for consistency with every other Wilson interval reported).
Wider than the superseded 27-item interval below, as expected at a smaller, correct n -- reported
plainly rather than the tighter-but-wrong interval quietly carried forward.

**The nine remaining cases are exactly the original ten minus RB-0027** -- RB-0007, RB-0008,
RB-0011, RB-0014, RB-0017, RB-0018, RB-0022, RB-0023, RB-0025, checked directly against the
rebuilt index, not assumed unchanged. All nine still show the same `notice_rank=1,
trap_source_rank=2` shape the original table below reports.

**"Not yet extended to RB-0026/RB-0028's rank anomalies" (below) no longer applies** — neither
item has a notice document to extend this measurement to. RB-0026's own trap-source-rank anomaly
is unaffected by this correction and is tracked separately
(`results/embedding_similarity_and_crowdedness.md`'s corrected section).

**The "necessary, not sufficient" and Jaccard-delta sections below (this file's actual analytical**
**content, not just the headline rate) were not recomputed against the corrected n=22 in this**
**pass** — they reference RB-0002/0013/0020/0026/0028 as the non-flip empty-notice control group,
and RB-0026/0028's inclusion in that specific role (not as flip candidates, but as *evidence that
bareness alone doesn't determine flipping*) is worth re-examining now that their own notice
status is corrected to nonexistent rather than merely bare. **Flagged as an open item for the
next pass, not silently carried forward as still valid.**

Full accounting, every number in this file's scope, old vs. new: `docs/DECISIONS.md` ADR-134.

---

## SUPERSEDED -- original file, kept in full below

**Status: exploratory, tracked as a running count since ADR-077, given its own analysis line**
**2026-08-16 per the author's instruction** — not to be treated as background noise around the
Jaccard-vs-length correlation (`results/notice_term_overlap.md`), which is a related but
distinct measurement (rank *position* relative to the trap source, not rank *value* against
notice-text overlap).

## What this measures

For each benchmark item with a separate notice document in the corpus, the retrieval ceiling
(`corpus/retrieval_ceiling.py`) records both `trap_source_rank` and `notice_rank`. Most items
show `notice_rank > trap_source_rank` (the notice ranks worse than the paper it corrects — the
premise failure mode this benchmark exists to measure). A minority show the reverse:
`notice_rank < trap_source_rank`, the notice actually outranking its own trap source. This file
tracks that minority.

## Rate

**10 of 28 items overall (35.7%); 10 of 27 notice-bearing items (37.0%), Wilson 95% CI**
**[0.215, 0.558]** — RB-0005 is excluded, no separate notice document exists for it at all
(ADR-071). History of this count, for the record: n=2 (ADR-077) → "stable" at n=3 (ADR-092,
later shown wrong) → n=4 (ADR-100) → n=6 (ADR-108) → n=8 (ADR-115) → n=9 (ADR-117) →
**n=10 (ADR-121).** Every batch annotated so far has added at least one case; this has never yet
been a stable number at the point it was measured, and should not be described as one again
until a batch passes without adding to it. The rate itself has held close to 35-38% across the
last four checkpoints (n=6 through n=10) even as the count keeps climbing — the *proportion*, as
opposed to the raw count, may be closer to stabilizing than the "always growing" framing alone
suggests; worth watching directly at the next checkpoint rather than assumed.

## The ten cases

| Item | Domain | Notice length (chars) | Jaccard | `notice_rank` | `trap_source_rank` |
|---|---|---|---|---|---|
| RB-0007 | Ob/Gyn | 159 | 0.4118 | 1 | 2 |
| RB-0008 | Pharmacology | 121 | 0.2667 | 1 | 2 |
| RB-0011 | Pharmacology | 142 | 0.3333 | 1 | 2 |
| RB-0014 | Ob/Gyn | 129 | 0.5833 | 1 | 2 |
| RB-0017 | Ob/Gyn | 133 | 0.6923 | 1 | 2 |
| RB-0018 | Ob/Gyn | 219 | 0.3333 | 1 | 2 |
| RB-0022 | Ob/Gyn | 131 | 0.3333 | 1 | 2 |
| RB-0023 | Pharmacology | 182 | 0.4286 | 1 | 2 |
| RB-0025 | Pharmacology | 157 | 0.4737 | 1 | 2 |
| RB-0027 | Ob/Gyn | 129 | **0.0** | 2 | 6 |

**RB-0027 breaks the pattern the other nine share, and is worth reading as its own case, not**
**folded silently into the table:** its notice has *zero* lexical overlap with its own question
(`HPV`/`vaccination`/`fertility` vs. the notice title's `papillomavirus`/`vaccine`/`pregnancy` --
semantically close, lexically disjoint under this project's tokenizer) yet still outranks its
trap source, and by a wider margin than usual (rank 2 vs. rank 6, not the usual 1-vs-2). Whatever
wins this specific competition, it is not lexical overlap by any measure this file or
`results/notice_term_overlap.md` computes -- see the delta measurement update below.

## Necessary, not sufficient

**All ten have `SupersededSource.notice_specificity = bare` (or `unverifiable`, RB-0026/27/28's**
**actual annotated value) and `notice_text = None`** — the "verified-empty" case (confirmed via
PubMed EFetch or, for the three newest, an exhausted four-route access attempt that itself
resulted in no recoverable notice text; ADR-042/081/103/120), not merely a short notice. **This
holds without exception: an effectively-empty notice is necessary for this pattern in every case**
**observed so far.**

**It is not sufficient.** Five other notice-bearing items share the identical property
(no recoverable notice text) and do **not** outrank their trap source:

| Item | Jaccard | `notice_rank` | `trap_source_rank` | Outcome |
|---|---|---|---|---|
| RB-0002 | 0.1111 | 2 | 1 | does not flip |
| RB-0013 | 0.2667 | 2 | 1 | does not flip |
| RB-0020 | 0.5385 | 2 | 1 | does not flip |
| RB-0026 | 0.2000 | 15 | 7 | does not flip (both ranks are outliers -- see `notice_term_overlap.md`'s n=27 checkpoint) |
| RB-0028 | 0.0952 | 2 | 1 | does not flip |

Of the 15 empty-notice items in the benchmark, 10/15 (67%) outrank their trap source and 5/15 do
not. **Jaccard does not cleanly separate the two groups:** RB-0013 (0.2667) and RB-0008 (0.2667)
have identical Jaccard values and opposite outcomes; RB-0020 (0.5385) has a higher Jaccard than
eight of the ten flip cases yet does not flip either; RB-0027 flips with Jaccard exactly **0**,
lower than every non-flip case except RB-0002. Two more bare-notice items (RB-0021, RB-0024)
have real, if minimal, added notice text (not `None`) and also do not flip — consistent with
bareness-with-truly-zero-added-text being the relevant necessary condition, not merely "short."

## Measured, 2026-08-16 (ADR-114): the flip trap sources are not generally weak retrievers

The natural next measurement, flagged above and now run: is a trap source's loss to its own
notice explained by the trap source itself being a poor retriever in general (so *any*
reasonably on-topic notice could beat it), or does it hold up fine against unrelated queries and
lose specifically to its own notice? Measured directly, not inferred: for each of the 6 flip
trap sources and the 3 non-flip verified-bare trap sources (RB-0002, RB-0013, RB-0020, the
control group), its rank was computed against **every one of the other 19 items' questions**
(19 full-corpus searches, 400,597 documents each; each trap source's rank extracted from every
other query's full ranking, not just a small-k check).

| Group | n | Mean of per-item median rank (other 19 questions) | Range of each item's *best* rank on any other question |
|---|---|---|---|
| Flip (loses to own notice) | 6 | 237,467 | 208 – 7,013 |
| Non-flip bare (beats own notice) | 3 | 232,337 | 2,042 – 19,873 |

**The two groups are statistically indistinguishable on general retrievability, and if anything**
**point the opposite way from the "weak source" hypothesis.** Both groups' typical (median)
rank against an unrelated question sits deep in the corpus (roughly the 55-60th percentile of
400,597 documents) — expected for any specific document against a random unrelated query, and
nearly identical between groups (237,467 vs. 232,337). The flip group's *best-case* rank
against some other question is, if anything, slightly better (208–7,013) than the non-flip
group's (2,042–19,873) — the flip trap sources are not systematically harder to retrieve in
general. **Conclusion: this pattern is not explained by weak trap sources.** Whatever makes a
notice outrank its trap source is specific to the competition between that notice and that trap
source on their shared, specific question — consistent with the dilution/Jaccard account
(`results/notice_term_overlap.md`) rather than an alternative "these are just bad source
documents" explanation, which would have been a considerably less interesting finding. Full
per-item data: `results/trap_source_retrievability.json`.

**Still open, not computed here:** the trap source's own Jaccard overlap with its *own* question
specifically (as opposed to its rank against 19 unrelated questions) — whether the
notice-minus-trap-source Jaccard *difference* on the shared question separates the flip and
non-flip groups better than either side's Jaccard alone. Flagged as a further refinement, not
assumed to resolve anything on its own.

**Not yet extended to RB-0022/RB-0023/RB-0025/RB-0027 (the four newest flip cases, ADR-115/117/121)**
**or to RB-0026/RB-0028's rank anomalies:** the retrievability measurement above covers the
original 6 flip and 3 non-flip trap sources only. Extending it to the now-10-item flip group is
a natural next step, not assumed to change the conclusion -- and RB-0026's own trap-source rank
(7th, the worst recorded) makes it a specifically interesting case for this exact measurement,
since it directly tests whether RB-0026's trap source is a weak retriever in general (consistent
with the "broad topic, more corpus competition" account in `notice_term_overlap.md`) rather than
weak specifically against its own notice.

## Rate, with a confidence interval (2026-08-16, ADR-118)

**9/24 = 0.375, Wilson 95% CI [0.212, 0.573].** (Of all 25 items including RB-0005, which has no
notice document at all: 9/25 = 0.36, Wilson 95% CI [0.202, 0.555] -- reported for completeness,
but 24 is the correct denominator since RB-0005 cannot show this pattern by construction, not
because it fails to.) The interval is wide, as expected at this n, but it excludes both "this is
a rare edge case" (the lower bound alone rules out anything under ~1 in 5) and "this is nearly
universal" (the upper bound stays under 3 in 5). **Calling this "the single most robust pattern
in the project" needs a qualifier: robust in that it has never gone down and has appeared in
every batch so far (a directional, monotonic property, 9 consecutive-or-growing observations),
not robust in the sense of a tight interval -- the interval is still wide enough that n=30-40
could plausibly land anywhere from about 1-in-4 to 1-in-2.** Both things are true at once and
the paper should say both: the trend has been one-directional every time it has been checked,
and the point estimate still carries real uncertainty.

## What the nine have in common, beyond bare notices (2026-08-16, ADR-118)

**Domain, item_type, and claim_type do not separate the flip group from the non-flip group --**
**checked directly, ruled out as explanations, not merely unexamined:**

| | Flip (n=9) | Non-flip bare + rest (n=15) |
|---|---|---|
| Domain | 5 Ob/Gyn, 4 Pharmacology | 8 Pharmacology, 6 Ob/Gyn, 1 Rehab |
| `item_type` | 5 with-answer, 4 without-answer | 8 with-answer, 7 without-answer |
| `claim_type` | 8 intervention, 1 observational | 11 intervention, 4 observational |

Each split is close to the group's overall proportion -- none of these fields carries the signal.
Jaccard alone doesn't separate the groups either (established already: RB-0013 and RB-0008 share
an identical Jaccard value, 0.2667, and opposite outcomes). **What does separate them, isolated**
**directly rather than inferred, is below.**

## Measured, 2026-08-16 (ADR-118): the notice's Jaccard *advantage over its own trap source*, on their shared question, isolates the mechanism

ADR-114 ruled out "the trap source is a weak retriever in general" -- flip and non-flip trap
sources are statistically indistinguishable on retrievability against 19 *unrelated* questions.
That leaves the specific, targeted hypothesis: on **the item's own question**, is the source
diluted *relative to the notice*, not relative to the corpus at large? This is a different,
sharper test than either side's Jaccard alone -- it is the head-to-head comparison the
competition actually runs.

**Method:** for each of the 27 notice-bearing items, `source_jaccard` = Jaccard overlap between
the question's term set and the trap source's own indexed text (`f"{title} {summary}"`, the
identical convention `corpus/embed_index.py` uses to build the document actually embedded),
computed with the same tokenizer and stopword list as `notice_jaccard` (already measured, in
`results/notice_term_overlap.json`). `delta = notice_jaccard - source_jaccard`. Full data and
code output: `results/source_jaccard_delta.json`.

**Result at n=27 (was n=24, ADR-118): `delta` still separates the flip group from the non-flip**
**group clearly, though slightly less cleanly than before -- reported at both checkpoints,**
**not just the more favorable one.**

| | n | mean `delta` | median `delta` |
|---|---|---|---|
| Flip (notice outranks source) | 10 | **+0.1761** (was +0.2002 at n=24) | +0.1866 |
| Non-flip | 17 | **-0.0051** (was -0.0068) | +0.0088 |

Mann-Whitney one-sided p = 0.00119 (was 0.00052). Point-biserial r(delta, flip) = **0.6177**
(was 0.6806), p = 0.00060. A single threshold on `delta` (0.1524-0.1568, unchanged) now sorts
all 27 items with **4 misclassifications** (up from 3/24), the new one being **RB-0027 itself**:
its `delta` is *negative* (-0.0408, a false negative under this model) because neither its
notice (Jaccard 0.0) nor its source (Jaccard 0.0408) has meaningful lexical overlap with the
question at all -- the delta account, built entirely on lexical overlap, has nothing to work
with for an item where the competition is won on semantic rather than lexical grounds. The other
three misclassifications carry over from n=24 (RB-0020 false positive; RB-0018 and RB-0023
false negatives, both with an unusually well-matched trap source, `source_jaccard` = 0.282 and
0.400 respectively). **RB-0026 (a non-flip case) fits the delta account fine** (delta=+0.0462,
correctly below threshold) despite its own retrieval anomaly (`notice_term_overlap.md`'s n=27
checkpoint) -- its rank-15 outlier status is orthogonal to this head-to-head measurement, which
only compares notice against source, not either against the rest of the corpus.

**RB-0027's shape is worth naming precisely: this is the first flip case this delta measurement**
**cannot explain, and it points to a real limit of the lexical-overlap account rather than a**
**flaw in the measurement.** Every prior flip case had *some* lexical signal favoring the notice
over its source; RB-0027 has none on either side, and still flips, on the strength of embedding
similarity the token-overlap metric structurally cannot detect (`HPV vaccination` ~
`papillomavirus vaccine`, `fertility` ~ `pregnancy`). The delta account remains the best
available explanation for 26 of 27 items; it is not a complete account of the mechanism, and this
is the item that shows why.

**Resolved directly in `results/embedding_similarity_and_crowdedness.md` (ADR-122): measured in**
**the space retrieval actually uses (embedding cosine similarity, not lexical overlap), RB-0027**
**is not anomalous at all** -- its notice's cosine similarity to the question (0.7818) is
ordinary, its standardized residual under a cosine-vs-rank fit is well within normal range
(-0.924, nothing flagged), and `notice_cosine - trap_source_cosine` is positive, directly
confirming the notice legitimately outscores its trap source on this question. The lexical delta
measurement's miss on RB-0027 was a limit of measuring lexical overlap specifically, not evidence
against the dilution/competition account generally -- see that file for the full comparison
against length and Jaccard, and for why cosine-based delta is not treated as an independent
confirmation the way the lexical delta was (it is close to definitional, not a second signal).

**This is the isolating result the retrievability check (ADR-114) was a precondition for, not a**
**repeat of it.** ADR-114 showed the source isn't weak in general; this shows that on its own
question specifically, the source *is* the weaker of the two competitors, by a margin that
predicts the outcome directly -- the notice doesn't win because the source is a bad document, it
wins because the source's own relevant vocabulary is diluted by everything else in its abstract
that isn't about this specific question, while the notice (bare, title-only) has almost nothing
but the on-topic vocabulary. **This is a stronger, more specific statement of the dilution**
**mechanism than the corpus-wide Jaccard/length correlation can produce on its own**, because it
is a within-item, two-sided measurement rather than a one-sided correlation against a numeric
rank -- and it holds regardless of how the Jaccard-vs-length Pearson race resolves at n=30 (see
`results/notice_term_overlap.md`'s pre-registered dual-outcome interpretation, ADR-118).

## On whether this should become the paper's primary retrieval finding

The author asked for a view before either of us commits. Mine: **not yet, but it is close, and**
**the `delta` result above is what would tip it.** Three considerations:

1. **The Jaccard/length correlation is a *global* claim** (overlap predicts rank across the whole
   corpus) **and this pattern is a *specific, binary* claim** (does the notice beat its own
   source). A binary claim with a clean, mechanistically-isolated cause (delta, 21/24 correct on
   a single threshold) is easier for a reader to hold in their head and easier to defend against
   the obvious objection ("maybe it's just noise") than a correlation with an unresolved
   Pearson/Spearman disagreement.
2. **But the CI is still wide (0.212-0.573 at n=24)**, and the paper's headline retrieval finding
   should be the one whose *rate*, not just its mechanism, is stated with confidence. Right now
   that argues for keeping notice-above-trap-source as the sharper, better-explained finding
   while the Jaccard/length correlation (whichever way it lands) supplies the corpus-wide
   context around it -- roughly the current ordering, not yet reversed.
3. **If n=30-40 narrows the CI without the rate collapsing, and the `delta` separation holds up**
   **on the new items, that is exactly the condition under which I'd recommend the swap** --
   at that point notice-above-trap-source would have both a tighter interval and a cleaner,
   directly-tested mechanism, and Jaccard/length would properly become the supporting corpus-wide
   evidence for the same underlying account rather than competing for top billing. **Worth
   deciding once, at that point, not now and not by default** -- I'd flag it again when the CI
   narrows rather than assume today's answer still holds then.

## Relationship to the Jaccard/length correlation

This is a distinct measurement from `results/notice_term_overlap.md`'s length/Jaccard-vs-rank
correlations, though mechanistically related: that file asks what predicts a notice's *rank*
among all corpus documents; this file asks specifically whether the notice beats its own trap
source. A notice can have a middling Jaccard and still win this specific two-way comparison if
its trap source is an even weaker match to the question — which is consistent with why Jaccard
alone does not cleanly separate the flip and non-flip groups above.
