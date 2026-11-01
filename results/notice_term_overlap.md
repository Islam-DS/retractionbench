# Term overlap vs. notice length as a predictor of notice rank (ADR-094)

## CORRECTED FINAL, TAKE TWO: n=24, not n=22 or n=27 (2026-08-20, ADR-136) — the n=22 section below is also SUPERSEDED

**The `n=22` section immediately below was itself wrong, caught before any evaluation call was**
**made (`docs/DECISIONS.md` ADR-136).** It used `notice_text_verified` as a proxy for "does a
notice document exist," which conflates two different questions: verification governs what the
gold claim may assert (ADR-042), not what a retriever can find. Two sources (`rw-7837`/RB-0003,
`rw-1471`/RB-0004) have real notice text that was never independently confirmed against a primary
source -- retrievable regardless. **The correct, final count is n=24.** Corrected correlations:
**length Pearson r=0.7219, Jaccard Pearson r=-0.7073** (magnitude 0.707) -- the comparative claim
still fails, same direction as at n=22 (length ahead). Full accounting, including a striking
exact-match consistency check against this project's own historical n=24 checkpoint: ADR-136.

---

## SUPERSEDED (ADR-136) — CORRECTED FINAL: n=22, not n=27 (2026-08-20, ADR-133/134)

**The "FINAL: n=28 checkpoint" section immediately below this one is superseded, not deleted.**
It was written in good faith against the data available at the time and is kept in full so the
correction is visible, not just asserted -- the sequence (measure at n=27, treat one item as an
outlier requiring leave-one-out, only later discover that item was never a legitimate data point)
is itself part of this project's record, per the author's explicit instruction.

**What changed:** ADR-133 found the corpus stale -- five sources (`rw-7837`/RB-0003,
`rw-1471`/RB-0004, `rw-6062`/RB-0026, `rw-21782`/RB-0027, `rw-24670`/RB-0028) are correctly
`notice_text_verified=False` under current annotation (ADR-042: their notice text could not be
independently confirmed), but the corpus that produced every number below still had a bare-notice
document for all five, built before that verification status was set and never rebuilt after.
**The real notice-bearing count is 22, not 27** (six exclusions -- RB-0005 plus these five -- not
one).

**Corrected correlations, n=22, no leave-one-out exclusion of any kind (every item below has a
genuine, verified notice document):**

| Metric | Pearson r | Spearman rho |
|---|---|---|
| Length (chars) | **0.6981** | 0.6069 |
| Jaccard | **-0.6872** | -0.7657 |
| (Cosine similarity, not part of this file's original scope: -0.7510 Pearson -- see `results/embedding_similarity_and_crowdedness.md`) | | |

**Corrected verdict on the ADR-094 pre-registered predictions:**

- **"Mechanism stabilizes" prediction:** length's Pearson (0.698) and Jaccard's Pearson magnitude
  (0.687) both **exceed the top of their predicted n=30 ranges** (0.35-0.55 and 0.45-0.65) --
  stronger than expected, not weaker, and neither the "stabilizes within range" nor the
  "regresses toward noise" scenario ADR-094 named is quite what happened.
- **Comparative claim ("Jaccard stays ahead of length"):** **fails**, length very slightly ahead
  (0.698 vs. 0.687, a 0.011 margin) -- the specific disconfirming pattern ADR-094 named in advance
  as the one outcome that would undermine the dilution account. It occurred, on the corrected,
  final sample, not narrowly-in-one-of-two-readings as the superseded n=27 verdict below reported.
- **This is now genuinely the last word.** The superseded section below treated RB-0026's
  exclusion as a leave-one-out judgement call, contingent on more data possibly changing the
  picture. It cannot -- RB-0026 (and four other items) are correctness exclusions, not
  statistical ones, and no future measurement changes that.

**What does not change:** cosine similarity (not evaluated in this file, see
`results/embedding_similarity_and_crowdedness.md`) remains the strongest of the three predictors,
exactly as ADR-122 found -- that conclusion survives the correction; only the sample it was
computed against, and the framing of RB-0026's exclusion, do not. Full accounting and the
seventh-instance self-correction narrative: `docs/DECISIONS.md` ADR-134.

---

## SUPERSEDED -- FINAL: n=28 checkpoint (2026-08-20, ADR-126/128) — the n=30 target was not reached; this is the last word

**Annotation closed at n=28 items (27 notice-bearing) before the pre-registered n=30 checkpoint**
**could be reached — the schedule moved, not the data.** Evaluated here against ADR-094's
predictions exactly as written, not re-baselined to read more favorably. **Verdict: genuinely
mixed, reported as such.**

|  | Length Pearson r | Jaccard Pearson r (magnitude) | Length Spearman | Jaccard Spearman (magnitude) |
|---|---|---|---|---|
| Bare, all 27 items | 0.0581 | 0.2525 | 0.5154 | 0.7136 |
| Excluding RB-0026 (n=26) | 0.6933 | 0.6781 | 0.5969 | 0.7407 |

- **Broad "mechanism stabilizes" prediction:** supported once RB-0026 (an independently-explained
  outlier, ADR-122's crowdedness investigation — not a broad decay) is set aside; both Pearson
  correlations land just above their predicted 0.35-0.55 / 0.45-0.65 ranges. Bare, length's
  Pearson (0.058) crosses the explicit |r|<0.2 null-signature threshold — reported, not hidden,
  but attributed to the one known outlier, not a dataset-wide trend.
- **Comparative claim ("Jaccard stays ahead of length throughout"):** holds clearly on Spearman in
  both readings. **On Pearson — the metric the prediction was phrased around — holds bare (0.253
  vs. 0.058) but fails once the outlier is excluded (0.678 vs. 0.693, length ahead by 0.015).**
  This is the specific failure mode ADR-094 named in advance as the one outcome that would
  undermine the dilution account. It occurred, narrowly, in one of two readings and one of two
  correlation measures — reported as an unresolved, single-item-sensitive split verdict, not a
  clean pass or fail either way.

**No further checkpoint is coming.** The embedding-cosine-similarity finding (ADR-122/123) is
the sharper, more complete account of the underlying mechanism and should carry more weight in
the paper's actual argument — but this original, pre-registered prediction is evaluated and
reported on its own terms first, per standing practice never to let a later measurement quietly
replace an earlier falsifiable one.

## A third predictor, embedding cosine similarity, measured directly

**`results/embedding_similarity_and_crowdedness.md` (ADR-122) — it outperforms both length and**
**Jaccard once RB-0026 is set aside, and resolves RB-0027's anomaly cleanly (Jaccard=0, but**
**cosine similarity is high). This file's own pre-registered n=30 predictions for length and**
**Jaccard specifically are unchanged and evaluated as written** — the new measurement explains
why Jaccard was a useful proxy (it tracked semantic similarity indirectly, in most items) and
where the proxy breaks (RB-0027, where lexical and semantic similarity diverge), not a
replacement for the length-vs-Jaccard test this file runs.

**n=27 checkpoint, 2026-08-18 (ADR-121): the pre-registered null signature technically fires --**
**length's Pearson r drops to 0.0581, under the |r|<0.2 threshold ADR-094 named in advance --**
**but leave-one-out shows this is one item, not the mechanism failing. Reported plainly, per**
**standing practice, not smoothed toward either reading.**

Full n=27 (RB-0026/RB-0027/RB-0028 folded in): length Pearson **0.0581** (was 0.7219 at n=24),
Spearman 0.5154 (was 0.6428). Jaccard Pearson **-0.2525** (was -0.7073), Spearman -0.7136 (was
-0.7884). Both correlations fell sharply -- length far more than Jaccard, so the *comparative*
claim (Jaccard's magnitude should exceed length's) still holds and by a wider relative margin
than before, even as both weakened in absolute terms.

**Leave-one-out, run immediately given the size of the swing (same discipline as ADR-109's**
**RB-0008 check): one item, RB-0026, accounts for nearly all of it.** Removing RB-0026 alone:
length Pearson **0.6933**, Jaccard Pearson **-0.6781** -- both snap back to within 0.03 of the
n=24 values, and the gap between them (0.0148) is essentially unchanged from n=24's 0.0146.
Removing RB-0027 or RB-0028 individually moves either correlation by at most 0.02. **RB-0026 is**
**not an ordinary outlier on the axis this file measures** -- its own Jaccard (0.20) and notice
length (144 chars) are both entirely unremarkable, sitting mid-range among all 27 items. What is
extreme is its `notice_rank`: **15th**, more than four times worse than the previous worst rank
recorded in this dataset (RB-0010's 3rd) and far outside the 1st-3rd range every other item has
landed in. **This is not the dilution mechanism this file tests failing -- it is a different**
**item hitting a different limitation this file was never designed to measure:** RB-0026's trap
source is a Lancet network meta-analysis on a common, heavily-studied topic (NSAIDs for
osteoarthritis), and its own trap-source rank (7th) is also the worst recorded for a trap source
-- consistent with a broad, well-covered topic having many more legitimately competing documents
in a 400,622-document general biomedical corpus than the benchmark's typically narrower,
more specific questions face. Term overlap and length predict *this item's own notice's rank*
about as well as always; what changed is that rank's absolute value, driven by corpus-wide
topic competition the length/Jaccard account was never a model of.

**Stated plainly, per the standard this project holds itself to: the pre-registered null**
**condition (|r|<0.2 by n=20-30) is technically met at n=27 on Pearson, and reporting only that**
**number without the leave-one-out result behind it would be a materially misleading account of**
**what happened.** The mechanism's fit on the other 26 items is, if anything, unchanged from
n=24. Whether n=30 confirms RB-0026's shape as a second data point of a genuine "broad-topic
corpus competition" phenomenon, or whether RB-0026 remains a singular case, is exactly what the
next checkpoint should watch for -- not assumed either way here. **Do not report the bare n=27
number in the paper without this qualification attached.**

**A second, independent finding at this checkpoint, in `results/notice_above_trap_source.md`**
**(ADR-121): RB-0027 is a tenth notice-above-trap-source case, and the sharpest counter-example**
**to the lexical-overlap account found so far.** Its notice's Jaccard with its own question is
**exactly 0** -- zero shared tokens at all (`HPV`/`vaccination`/`fertility` in the question vs.
`papillomavirus`/`vaccine`/`pregnancy` in the notice title -- semantically close, lexically
disjoint under this tokenizer) -- yet the notice still outranks its trap source (rank 2 vs. 6).
Whatever wins this specific competition for RB-0027, it is not lexical overlap by this
measure; the dense embedding model is picking up a semantic relationship (HPV vaccine ~
papillomavirus vaccination; fertility ~ pregnancy) no token-overlap metric can see. See the
isolating delta measurement's own update for how this affects that check specifically.

**n=24 checkpoint, 2026-08-16 (ADR-117): RB-0025 folded in, gap continues narrowing but has**
**not crossed back.** Pearson: |length|=0.7219 vs. |Jaccard|=0.7073 (gap now 0.0146, down from
0.0253 at n=23 and 0.0455 at n=19). Spearman still favors Jaccard clearly (0.7884 vs. 0.6428).
RB-0025 is itself a ninth notice-above-trap-source case -- see `results/notice_above_trap_source.md`
(ADR-117). Still no new leave-one-out run at this checkpoint; the n=30 prediction is unchanged.

**n=23 checkpoint, 2026-08-16 (ADR-115): RB-0021/22/23/24 folded in, the n=19 picture holds.**
Pearson: |length|=0.7151 vs. |Jaccard|=0.6898 (was 0.7235 vs. 0.6780 at n=19) -- length still
nominally ahead, gap narrowed slightly (0.0455 -> 0.0253). Spearman still favors Jaccard clearly
(0.7825 vs. 0.6558). No new leave-one-out investigation run at this checkpoint -- the qualitative
picture (a genuine Pearson/Spearman disagreement, not yet resolved, n=30 prediction unchanged) is
unchanged from ADR-109's finding and does not yet warrant repeating that analysis. Two of the
four new items (RB-0022, RB-0023) are themselves new notice-above-trap-source cases -- see
`results/notice_above_trap_source.md` (ADR-115).

**n=19 update, 2026-08-16 (ADR-108/109): the pre-registered falsification condition partially**
**triggered -- reported as the methodology working, not as the finding weakening.** ADR-094
stated in advance, before this data existed, exactly one outcome that would count against the
dilution account: Jaccard's advantage over length disappearing or reversing. At n=19, on
Pearson, that condition partially occurred: |length| = 0.7235 vs. |Jaccard| = 0.6780. **A**
**result meeting a falsification condition specified in advance is what makes the original**
**result credible, not what discredits it -- a prediction that can fail, tested honestly, and**
**found to be failing exactly where it was said it might, is the entire point of writing the**
**condition down first.** No hedging toward the preferred answer follows from here.

**Investigated directly rather than left as an unexplained disagreement (ADR-109): does the**
**Pearson/Spearman split trace to one or two high-leverage points, or does it survive**
**leave-one-out?** Pearson measures linear association and is sensitive to individual points;
Spearman measures monotonic rank association and is not -- when the two diverge, that is
usually diagnostic, not just noise to average away. Standardized residuals from each metric's
own fitted line were computed per item, then each item was removed in turn and both
correlations recomputed on the remaining 18.

**Result: one item, RB-0008, is the pivot -- and the flip it produces is itself razor-thin.**
Removing RB-0008 changes the ordering from |length|=0.7235>|Jaccard|=0.6780 (full n=19) to
|length|=0.7055<|Jaccard|=0.7081 (n=18) -- a swing of about 0.048 correlation points from one
item, but the post-removal gap (0.0026) is close enough to call a tie either way. No other
single removal comes close: every other leave-one-out result keeps length ahead of Jaccard by a
comfortable margin (roughly 0.02-0.15). **RB-0008 specifically is the item with the single**
**largest Jaccard residual in the dataset (standardized residual -1.59):** its notice is short
(121 characters, in the same length range as RB-0007/RB-0011/RB-0014/RB-0017/RB-0018) and ranks
1st, above its own trap source -- length's account fits it well -- but its Jaccard is only
0.2667, because its notice text shares "alone," "electroconvulsive," "schizophrenia," and
"therapy" with the question but not "antipsychotic," "monotherapy," or "treating." It is a
short notice with unusually low overlap for its length, which is exactly the shape of point that
weakens Jaccard's fit relative to length's. **This means the Pearson/Spearman divergence does**
**not survive leave-one-out as a fully structural property -- it hinges heavily on one point --**
**but that one point is not an anomaly to discard, either: it is a real, correctly-measured**
**item, and its presence in the dataset is exactly as legitimate as any other item's.**

**Stated plainly, as the author asked: the mechanism is unresolved at n=19. The pre-registered**
**condition that would undermine it has partially occurred. Whether it holds, widens, or**
**reverts depends heavily on which items land in the next several annotations -- a single**
**item's worth of leverage at this sample size is not a small effect. The n=30 checkpoint**
**stands exactly as written in ADR-094 and is not revised here or anywhere before it is reached.**

**n=14 update, 2026-08-15 (ADR-103):** RB-0014 and RB-0015 (ADR-100) folded in -- both now have
a notice document in the corpus, so this is every notice-bearing item in the benchmark (14 of
15; RB-0005 remains the sole exclusion, ADR-071), not a partial update. The author's framing
for RB-0014 going in was that a bare notice with no `notice_text` is "the limiting case of the
dilution account, where non-question vocabulary is zero." **Checked directly, and that premise**
**does not hold as stated: the indexed notice document is never truly empty.** Every notice
document embeds as `f"Notice: {source.title}"` plus the notice body (empty string here) --
RB-0014's indexed text is 129 characters, the paper's own title, not zero characters. So this is
not a new, more extreme case than RB-0007/RB-0008/RB-0011 (also `bare`, also title-only); it is
a fourth member of that same cluster. **What makes it worth reporting anyway: its title happens**
**to share unusually high vocabulary with its own question** (`Foley catheter`, `misoprostol`,
`induction`, `labor` all appear in both) -- **Jaccard = 0.5833, the highest value in the entire**
**dataset**, and its notice ranks 1, above its own trap source (rank 2). That is the dilution
account's prediction at the opposite extreme from what was anticipated: not "zero diluting
vocabulary in the limit," but "maximal overlap because there is no diluting vocabulary added at
all, and the shared title vocabulary is unusually large" -- the same mechanism, a real
data point at the strong end of the scale rather than a hypothetical limiting case. RB-0015
(Jaccard=0.2000, rank 2) sits mid-range and unremarkably confirms the trend at an ordinary point.
**Updated correlations, n=14:** length-vs-rank Pearson r = **0.7259** (was 0.7142 at n=12);
recall-vs-rank r = **-0.2557** (was -0.1882); Jaccard-vs-rank r = **-0.8018** (was -0.8312) --
essentially unchanged, still the clear leader over both alternatives. **The n=30 prediction below**
**is unchanged and stays unchanged** -- this is a checkpoint, not a revision, per the same
discipline ADR-094 itself specified and ADR-080/101 exist to enforce.

**Status: exploratory, not pre-registered, prompted directly by ADR-090's mechanism account.**
ADR-090 argued that a bare notice ranks well because it is lexically near-identical to a
question written about the same paper -- length was always a *proxy* for this, not the
hypothesized causal variable. This document tests the more specific claim directly: does
term overlap between notice and question predict rank better than length does?

## Method

For each of the 27 items with a notice document (n=12 at original write-up, RB-0014/RB-0015
folded in 2026-08-15, RB-0016 through RB-0025 folded in 2026-08-16, RB-0026/RB-0027/RB-0028
folded in 2026-08-18), both `question` and the
indexed notice text
(`f"Notice: {title}" + " " + (notice_text or "")`) are tokenized (lowercased, alphanumeric
runs of length >2, common English stopwords removed -- full list in
`results/notice_term_overlap.json`), producing a term set for each. Two overlap metrics are
computed against the notice's term set:

- **Recall**: `|question_terms ∩ notice_terms| / |question_terms|` -- what fraction of the
  question's own vocabulary appears in the notice, regardless of how much else the notice
  contains.
- **Jaccard**: `|question_terms ∩ notice_terms| / |question_terms ∪ notice_terms|` -- overlap
  normalized by the *combined* vocabulary, so a notice with many terms outside the question's
  vocabulary is penalized even if it contains every question term.

Both are correlated against `notice_rank`. **Robustness check:** the same computation repeated
with no stopword list at all (naive tokenization) to confirm the result is not an artifact of
stopword-list choices made after seeing the data.

## Result (current, n=27; n=24/n=23/n=19/n=14/n=12 values in the update notes above)

| Metric | Pearson r vs. `notice_rank` | Spearman rho |
|---|---|---|
| Length (chars) | **+0.0581** | +0.5154 |
| Recall (stopword-filtered) | -0.2360 | -0.3796 |
| **Jaccard (stopword-filtered)** | **-0.2525** | **-0.7136** |
| Jaccard (naive, no stopwords) | -0.7875 *(n=12 value, not yet recomputed)* | -- |

**Pearson: both correlations collapsed at n=27, length far more than Jaccard (0.0581 vs.**
**0.2525) -- driven almost entirely by one item, RB-0026 (see the n=27 checkpoint note above);**
**with it excluded, both correlations sit within 0.03 of the n=24 values.** Spearman still ranks
Jaccard ahead of length clearly (0.7136 vs. 0.5154), less disrupted by the single outlier than
Pearson is, as expected of a rank-based statistic. **Do not cite the bare Pearson numbers above**
**without the leave-one-out qualification in the n=27 checkpoint note.**

(Sign note: `notice_rank` is 1-indexed and lower is better, so length's *positive* correlation
means longer -> worse, and Jaccard's *negative* correlation means more overlap -> better --
both point the same direction: more shared vocabulary with the question, better rank.)

**Recall alone is a poor predictor (|r|=0.19) -- weaker than length, not stronger.** Simply
containing the question's words is not what predicts rank. **Jaccard is a substantially**
**better predictor than length (|r|=0.83 vs. 0.71), and the result is not an artifact of the**
**stopword list** -- a naive tokenization with no stopword removal at all still gives |r|=0.79,
comfortably ahead of length's 0.71.

## Why Jaccard and not recall -- what this says about the mechanism

Jaccard's denominator is the *union* of both term sets, so a notice that contains every
question term but also adds substantial vocabulary the question doesn't share is penalized --
recall alone would not penalize it, since recall only asks whether the question's own words
are present. **This is precisely ADR-090's dilution account, made quantitative:** it is not
that informative notices are missing the right words, it is that they add so many *other*
words that the relevant overlap is diluted relative to the document's total content. Jaccard
measures dilution directly; length only measures it indirectly, through the reasonable but
imperfect assumption that longer notices have proportionally more diluting content. That
Jaccard outperforms length is evidence *for* the dilution mechanism specifically, not just for
"shorter is better" as an unexplained fact.

## Worked examples (full detail in `results/notice_term_overlap.json`)

- **RB-0007** (Nigeria mortality): question terms `{rural, urban, post, neonatal, mortality,
  nigeria, rates, areas}`; notice = the bare title, which contains 7 of 8 (`recall=0.875`,
  `jaccard=0.412`, the highest Jaccard in the set) -- ranks 1 (above its trap source).
- **RB-0010** (NAC-schizophrenia): question terms `{acetylcysteine, panss, scores, improving,
  patients, placebo, schizophrenia}`; the 471-character categorical notice contains only
  `schizophrenia` (`recall=0.143`, `jaccard=0.022`, the lowest Jaccard in the set) -- ranks 3,
  the worst rank recorded. The notice is not short, but almost none of its vocabulary overlaps
  the question -- exactly the case recall would miss and Jaccard catches.
- **RB-0002** and **RB-0013** (both `bare`, both rank *below* their trap source, the two
  counterexamples to "bare wins"): `RB-0002` recall=0.333, jaccard=0.111; `RB-0013`
  recall=0.571, jaccard=0.267. Both are short, but their titles simply don't share as much
  vocabulary with their own questions as RB-0007/0008/0011's titles do with theirs -- **length**
  **was never sufficient on its own; it happened to correlate with overlap in most, not all,**
  **of this sample.**

## Pre-registered interpretation for the n=30 checkpoint, both outcomes (2026-08-16, ADR-118)

**Written now, before n=30 arrives, because the gap has closed enough (0.0146 at n=24) that
either outcome is live.** The point of writing both readings down in advance is that when the
real number lands, we report the interpretation that matches it, not the interpretation we
would have preferred -- the same discipline the numeric prediction below was written under.

**If Jaccard's Pearson advantage stays gone or reverses at n=30** (length ≥ Jaccard, both likely
still in the 0.4-0.6 range per the prediction below): what survives is that **term overlap
predicts notice rank at all, at a correlation strength (~0.6-0.7) too large to be noise.**
Something about shared vocabulary between question and notice governs retrievability. What is
lost is the *comparative* claim -- that dilution (Jaccard's union-normalized penalty for added,
off-topic vocabulary) is a **sharper** account than simple length. At that point we could no
longer say more than: retrievability tracks lexical overlap with the question, by some
reasonable measure of overlap, and this specific dataset cannot adjudicate between "overlap
matters because non-overlapping content dilutes it" (Jaccard's account) and "overlap matters
because short documents happen to have less non-overlapping content" (length's account, which
is compatible with the same correlation without invoking dilution as a mechanism). **This would
not undermine the paper's central retrieval finding** (that a bare, low-informative notice can
outrank the paper it corrects) -- it would only mean we report the *mechanism* as an open
question rather than a resolved one, which the paper should do plainly rather than picking a
side the data no longer supports. Report `results/notice_term_overlap.json`'s Spearman columns
alongside Pearson in this case, since Spearman's persistence in favoring Jaccard throughout would
still be worth stating as suggestive, not dispositive -- rank correlation and linear correlation
answer different questions and a reader should see both rather than the one that reads better.

**If Jaccard's Pearson advantage holds at n=30** (within or above the predicted 0.45-0.65 range,
still ahead of length's predicted 0.35-0.55): the specific thing dilution explains that length
does not is already visible in the current n=24 data, not hypothetical -- **RB-0002 and RB-0013**
**are exactly as short as the items that do flip (RB-0007/RB-0008/RB-0011), but do not flip,**
**because their notice titles simply don't share much vocabulary with their own questions**
(Jaccard 0.111 and 0.267 respectively, both well below the flip group's range). Length alone
predicts both should rank well, on the strength of being short; length is wrong about both.
Jaccard predicts both correctly. If this pattern holds at n=30 -- short notices with low overlap
continuing to rank poorly, at a rate length's account cannot explain -- that is the concrete
demonstration that dilution is doing real work length is only a proxy for.

**A third source of evidence that does not wait for n=30, reported this session (ADR-118,**
**`results/source_jaccard_delta.json`):** a separate, more targeted test of the same mechanism,
independent of whichever way the corpus-wide Pearson comparison lands. Rather than asking
whether a notice's own Jaccard predicts its rank against the whole corpus, this measures the
**notice's Jaccard advantage over its own trap source, on their shared question** --
`delta = notice_jaccard(question) - source_jaccard(question)`. Across all 24 notice-bearing
items, `delta` separates the notice-above-trap-source flip group from the non-flip group with
only 3 misclassifications (point-biserial r=0.68, p=0.00025; Mann-Whitney p=0.0005) -- see
`results/notice_above_trap_source.md`'s dedicated writeup. **This result does not depend on the**
**length-vs-Jaccard horse race and survives regardless of which way it resolves at n=30**,
because it is a head-to-head, within-item comparison of overlap on both sides of the competition,
not a corpus-wide correlation of one document's overlap against a numeric rank. If the
Pearson race ties or reverses at n=30, this measurement is the stronger citation for the dilution
mechanism specifically, and should be promoted accordingly in the paper's framing.

## Pre-registered prediction for n=30 (recorded here in advance, per standing practice)

**The correlation trajectory to date is declining as more data arrives (ADR-081/088/092):
Pearson r (length vs. rank) = 0.80 (n=8) -> 0.75 (n=11) -> 0.71 (n=12).** A monotonic decline
across three measurements from the same small sample is the expected signature of an effect
whose magnitude was overestimated by an unusually favorable first sample -- three anomalous
items (RB-0007, RB-0008, RB-0011) generated the hypothesis and were then included in every
subsequent test of it, biasing early estimates upward. Stated now, before more data exists, so
the eventual number cannot be quietly rationalized either way:

1. **If the underlying mechanism (lexical overlap, diluted by added text) is real**, both
   correlations should *stabilize*, not continue toward zero, as n grows toward 30: predicted
   range for length-vs-rank Pearson r at n=30 is **0.35-0.55** (continued decline from 0.71, but
   settling well above noise); predicted range for Jaccard-vs-rank Pearson r at n=30 is
   **0.45-0.65**, and **Jaccard's magnitude should remain larger than length's at every
   intermediate measurement point**, not just at n=12 -- this comparative claim, not just
   either coefficient alone, is the sharper test of the mechanism account.
2. **If instead the pattern is noise from a small, unrepresentative first sample**, both
   correlations should continue declining past this range, with r approaching or crossing zero
   (|r| < 0.2, or a bootstrap CI that includes zero) by n=20-30, and Jaccard's current advantage
   over length should not persist or should shrink toward parity.
3. **A specific failure mode to watch for:** if Jaccard's advantage over length disappears or
   reverses as more items are added, that would suggest the current result is itself an
   artifact of this specific 12-item sample's vocabulary, not a stable property of the
   mechanism -- worth flagging explicitly since it is the one outcome that would undermine the
   dilution account without simply reducing to "there is no effect."

This prediction is falsifiable and recorded before the data that will test it exists. Update
this file, not a new one, when re-tested at larger n, and report both the original prediction
and the outcome side by side -- do not silently replace the prediction with the result.
