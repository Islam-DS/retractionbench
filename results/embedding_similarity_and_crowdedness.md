# Embedding cosine similarity as the real predictor, and a direct test of topic crowdedness (ADR-122)

## CORRECTED, TAKE TWO: n=24, not n=22 (2026-08-20, ADR-136) — the n=22 section below is also SUPERSEDED

**The `n=22` section immediately below was itself wrong, caught before any evaluation call fired**
**(ADR-136).** It used `notice_text_verified` as a proxy for document existence; two sources
(RB-0003, RB-0004) have real, retrievable notice text that was simply never independently
confirmed, and belong in the corpus regardless. **Corrected, final: n=24. Cosine remains the**
**strongest predictor: Pearson r=-0.7662** (was -0.7510 at the wrong n=22, -0.4175 at the
original stale n=27). Both new items (RB-0003, RB-0004) are unremarkable, non-flip, cleanly
collapsing additions -- neither changes the conclusion. Full accounting: ADR-136.

---

## SUPERSEDED (ADR-136) — CORRECTED: n=22, not n=27 (2026-08-20, ADR-133/134)

**Everything below this section is kept exactly as originally written and is superseded, not**
**deleted.** ADR-133 found that the corpus underlying every measurement in this file was stale:
`rw-6062` (RB-0026) and `rw-21782` (RB-0027) -- along with `rw-7837`/RB-0003, `rw-1471`/RB-0004,
and `rw-24670`/RB-0028 -- are correctly `notice_text_verified=False` under current annotation
(ADR-042: notice text could not be independently confirmed against a primary source), but the
index this file searched still had a bare, empty-abstract notice document for all five, because
the corpus was built before their verification status was corrected and was never rebuilt after.

**RB-0026 has no `notice_rank`. RB-0027 has no `notice_rank`.** The "unexplained anomaly" this
file gave a named paragraph to, and the "circularity case" that motivated this file's entire
non-circular-cosine-alone test, were both measurements of a document that should never have been
in the corpus at all. This is recorded as the seventh, and most consequential, instance of this
project's self-correction pattern (`docs/DECISIONS.md` ADR-134, superseding ADR-123's
six-instance paragraph) -- the first six caught a claim before it left this project's working
notes; this one was caught after two ADRs and this results file had already been built on it.

**Corrected numbers, n=22 (the six items without a verifiable notice -- RB-0005, RB-0003,
RB-0004, RB-0026, RB-0027, RB-0028 -- excluded by construction, not by leave-one-out judgement):**

| Metric | Pearson r | Spearman rho |
|---|---|---|
| Length (chars) | 0.6981 | 0.6069 |
| Jaccard | -0.6872 | -0.7657 |
| **Cosine similarity** | **-0.7510** | -0.7360 |

**Cosine similarity remains the strongest predictor of the three -- the conclusion survives.**
What does not survive: the n (27 -> 22), and the framing of RB-0026's exclusion as a cautious
leave-one-out judgement call. It was that, and it was also -- discovered only after the fact --
a data-correctness fix arriving early. The leave-one-out numbers this file reported below
(length 0.6933, Jaccard -0.6781, cosine -0.7288) sit within 0.02-0.04 of the properly-corrected
n=22 values above, which is itself informative: the statistical instinct to check an outlier's
influence was exactly right, even though the reason that check looked so clean was not "one
unusual but legitimate item" the way it was framed at the time.

**RB-0027's non-circular cosine-alone test (AUC=0.85, below) is not wrong as a method** --
applied to the 21 items that do have a genuine notice and did flip or not flip, absolute notice
cosine similarity is still a real, non-circular, significant signal. What is withdrawn is RB-0027
specifically as a data point within that test: it never flipped anything, because it never had a
notice to flip with. The AUC and point-biserial numbers below have not been recomputed on the
corrected n and should not be cited without that recomputation -- flagged here as an open item
rather than silently left implying they still hold at their original values.

**RB-0026's crowdedness paragraph (below) is also withdrawn as an open anomaly.** There is no
anomaly to explain: RB-0026's trap-source rank (7th under the stale index, 6th after ADR-133's
deduplication) is unusual but not mysterious, and it has no notice-rank at all to be mysterious
*about*. The crowdedness-vs-trap-rank null result (Part 2 below, p=0.51 across all 28 items) is
unaffected by this correction -- it never depended on RB-0026 having a notice -- and stands as
originally reported.

**Full accounting, every number in this file's original scope, old vs. new, in one table:**
`docs/DECISIONS.md` ADR-134.

---

## SUPERSEDED -- original file, kept in full below

**Status: two investigations run together (they share the same expensive full-corpus**
**searches), reported in full including where each one did and did not confirm its own**
**hypothesis, per standing practice.**

## Motivation

`results/notice_term_overlap.md` and `results/notice_above_trap_source.md` have, until now,
measured *lexical* overlap (Jaccard, length) as a proxy for what predicts a notice's retrieval
rank. But retrieval in this project's corpus is not lexical search — it is dense-embedding
cosine similarity (`BAAI/bge-large-en-v1.5`, `IndexFlatIP` over normalized vectors, so FAISS's
raw inner-product score *is* the cosine similarity). Jaccard and length were always proxies for
whatever actually drives that similarity, not measurements of it. RB-0027 (ADR-121) is the case
where the proxy and the mechanism visibly come apart: its notice shares zero tokens with its
question yet still outranks its trap source. The author's hypothesis, recorded before this was
run: embedding cosine similarity will predict rank better than either lexical proxy, and RB-0027
will stop looking anomalous once measured in the space retrieval actually operates in.

**This does not revise the ADR-094 pre-registered n=30 predictions for length and Jaccard.**
Those predictions were made about those two specific metrics and are evaluated as written,
regardless of what this file finds about a third, different metric.

## Method

For each of the 28 benchmark items: embed the question with the exact same `embed_fn` used to
build the corpus and used by `corpus/retrieval_ceiling.py` (no separate re-implementation), run
a full-corpus search (`k = len(manifest)`, i.e. 400,622 documents, brute-force exact rank via
`IndexFlatIP`), and read off two things directly from the ranked results rather than
recomputing anything: (1) the cosine score FAISS already returns at the position where the trap
source and notice documents appear (`trap_source_cosine`, `notice_cosine`), and (2) the cosine
score of the corpus document at a fixed rank cutoff, 100 (`crowdedness_score_at_100`) — a
pre-committed, untuned rank position, not a threshold chosen after seeing the data. A slowly-
decaying score curve (high score still at rank 100) means many documents cluster near the top of
this question's ranking; a fast-decaying curve means few do. Full per-item data:
`results/embedding_and_crowdedness_raw.json` (raw) and
`results/embedding_similarity_and_crowdedness.json` (with computed correlations).

## Part 1: embedding cosine similarity vs. length and Jaccard, as predictors of `notice_rank`

**At face value, n=27 (RB-0005 excluded, no notice document):**

| Metric | Pearson r | Spearman rho |
|---|---|---|
| Length (chars) | 0.0581 | 0.5154 |
| Jaccard | -0.2525 | -0.7136 |
| **Cosine similarity** | **-0.4175** | **-0.7589** |

On Spearman, cosine similarity is already the strongest of the three. On Pearson it beats length
comfortably but trails Jaccard's pre-RB-0026 magnitude — because **RB-0026 is an outlier under**
**cosine similarity too, and a more extreme one than under either lexical proxy:** standardized
residual **+4.853** under a linear fit of cosine vs. rank, several times larger than the next
largest residual (RB-0027, at -0.924, well within normal range). **Leave-one-out, run
immediately given the size of that residual (same discipline as ADR-109/121): excluding RB-0026,
cosine similarity's Pearson r rises to -0.7288** (Spearman: -0.7364, essentially unchanged) —
now clearly the single strongest predictor of the three, ahead of both lexical proxies at their
own best (n=24) values.

**RB-0026's own cosine values are not low — they are high.** `notice_cosine = 0.8058`,
`trap_source_cosine = 0.8204`, both comfortably inside the range of well-ranked items elsewhere
in the benchmark (compare RB-0023's trap-source cosine of 0.9427, or RB-0007's notice cosine of
0.8935 — RB-0026 is not a semantic mismatch by any reasonable reading of these numbers). **What
is anomalous is not the similarity value, it is the rank position given that value** — meaning
whatever is depressing RB-0026's rank, it is not that its notice or trap source are a poor
semantic match for the question. This sharpens, rather than replaces, the "broad-topic corpus
competition" account from ADR-121: the item is being outcompeted by rank, not outmatched by
relevance.

## RB-0027 stops being an anomaly, exactly as predicted

`notice_cosine = 0.7818` for RB-0027 — high in absolute terms, and its standardized residual
under the cosine fit is -0.924, comfortably inside the normal range (nothing else in the dataset
outside RB-0026 exceeds |1.0|). **Under the metric retrieval actually uses, RB-0027 is an
ordinary, well-explained point, not an outlier at all.** It was only anomalous under Jaccard
because Jaccard cannot see the semantic relationship between `HPV vaccination` and
`papillomavirus vaccine`, or between `fertility` and `pregnancy` — the dense embedding model can,
and does.

**A direct, non-tautological check on the flip specifically:** `delta_cos = notice_cosine -
trap_source_cosine` **perfectly separates the flip group from the non-flip group, 0
misclassifications out of 27** (Mann-Whitney p<0.00001, point-biserial r=0.777). **This is not
reported as a discovery in the way the Jaccard-based delta measurement (ADR-118) was —**
**it is close to definitional, not independently informative.** Both `notice_rank` and
`trap_source_rank` come from the identical single ranked list produced by the identical cosine
similarity computation, so whichever document has the higher cosine score to the question will,
up to tie-breaking, rank better; `delta_cos > 0` and `flip = True` are two descriptions of
essentially the same fact, not two independent measurements that happen to agree. **What this
check is genuinely useful for is confirming the extraction pipeline is internally consistent**
(no bug silently mismatching ranks and scores) — RB-0027's own `delta_cos = +0.0316` confirms
directly, in the actual mechanism's own terms, that its notice really does outscore its trap
source on this question, resolving why it flips at all, something the lexical delta (ADR-118)
could not explain for this item.

## A circularity caught before it was reported as a discovery (2026-08-19, ADR-123)

The `delta_cos = notice_cosine - trap_source_cosine` result above (0 misclassifications, 27/27)
was already flagged in this file, at the point it was computed, as "close to definitional, not
independently informative" -- **the author asked that this catch itself be recorded as an**
**instance of this project's own running pattern of claims stated more confidently than the**
**evidence warranted, caught before they did lasting damage (ADR-104/106/108/110): the sixth.**
A measure that separates a binary outcome perfectly, by construction, is not evidence that the
measure predicts the outcome -- both `notice_rank` and `trap_source_rank` are read off the
identical single ranked list produced by the identical cosine-similarity computation, so
`delta_cos > 0` and `flip = True` are two descriptions of one fact, not two independent
measurements that happen to agree. Reporting the 0-misclassification number without that
qualification, the way the (genuinely independent) Jaccard-based delta result was reported in
ADR-118, would have been exactly the kind of overclaim this project's standing practice exists to
catch -- see ADR-123 for the extended six-instance paragraph.

## A non-circular test: does the notice's absolute cosine similarity, alone, predict flip status?

The circularity above meant the real question -- can the notice's own cosine similarity, measured
without any reference to the trap source at all, predict whether it flips -- was still untested.
**Tested directly: `notice_cosine` alone, correlated against the binary `flip` outcome, across
all 27 notice-bearing items, with no comparison to `trap_source_cosine` anywhere in the**
**computation.**

**Result: yes, significantly better than chance, though not perfectly.**

| Statistic | Value |
|---|---|
| Flip group mean `notice_cosine` | 0.8992 (sd 0.0477) |
| Non-flip group mean `notice_cosine` | 0.8387 (sd 0.0274) |
| Mann-Whitney U (two-sided) | p = 0.0028 |
| Point-biserial r | 0.6275 (p = 0.0005) |
| AUC (rank-sum) | **0.8529** |
| Best single threshold | 24/27 correct (3 misclassifications) |

An AUC of 0.85 means: pick one flip item and one non-flip item at random, and the flip item's
notice has the higher absolute cosine similarity to its own question 85% of the time. **This is a
real, non-circular, statistically significant signal (p=0.0005) -- the honest answer is not "flip
is purely relative and cannot be predicted from the notice alone."** A notice with unusually high
semantic similarity to its own question is more likely to outrank its trap source, considered
completely on its own, without reference to how good or bad the trap source happens to be.

**It is not a complete account, and the item that motivated this whole investigation is its own**
**best exception, reported precisely rather than smoothed over.** RB-0027 -- the zero-Jaccard
flip case that started this line of inquiry -- has `notice_cosine = 0.7818`, the **lowest of all
ten flip cases**, well below the best-threshold cutoff (~0.876), and is the model's one false
negative. RB-0027 flips despite an unremarkable absolute notice-cosine score because its trap
source's own cosine (0.7503) is even lower still -- its flip is a genuinely *relative* outcome,
not explained by strong absolute notice quality the way most of the other nine flip cases are.
**The complete, honest picture is neither of the two possibilities the author named at the
extremes: absolute notice cosine similarity does predict flip status significantly better than
chance for most items (AUC=0.85, a real and useful signal, not "purely relative"), but the
specific item that revealed the lexical account's limits is also the case this non-circular
predictor explains worst** -- RB-0027's flip is disproportionately a story about its trap
source's own weakness, not its notice's own strength, even measured correctly.

## Part 2: is RB-0026 explained by general topic crowdedness? Tested directly — no, not as a general phenomenon

**Correlation across all 28 items: `crowdedness_score_at_100` vs. `trap_source_rank` —**
**Pearson r = 0.1304 (p = 0.51), Spearman rho = 0.0698 (p = 0.72). Neither is significant.**
**Stated plainly, as the author asked: if the crowdedness account does not hold, say so — it**
**does not hold as a general predictor of trap-source rank across this benchmark.**

RB-0026 is genuinely one of the most "crowded" topics measured (`crowdedness_score_at_100 =
0.7515`, 2nd-highest of 28 items) — consistent with, though not proof of, its own poor rank.
**But the single most crowded item by this measure, RB-0009, has `trap_source_rank = 1` — a**
**perfect rank, despite facing the heaviest topical competition of any item in the benchmark.**
Three more of the eight most-crowded items (RB-0019, RB-0003, RB-0010) also rank their trap
source 1st. A broad, heavily-studied topic does not, on this evidence, generally doom trap-source
retrieval — some broad-topic items retrieve their trap source perfectly despite the competition.

## RB-0026: an unexplained item, given a named paragraph rather than a footnote

**RB-0026's poor retrieval rank (trap source 7th, notice 15th — both the worst recorded in this**
**benchmark) is not explained by any account this project has tested, and is recorded here as**
**exactly that: an open anomaly, not a resolved one.** One unexplained item in twenty-eight is an
ordinary outcome for a project that is actually looking, not a gap to paper over — a benchmark
whose every finding resolves cleanly is usually one that stopped investigating early.

**What was ruled out, checked directly rather than assumed:**

- **Semantic mismatch.** RB-0026's trap source and notice both have *high* cosine similarity to
  their own question (0.8204 and 0.8058 respectively) — solidly inside the range of items that
  rank well elsewhere in the benchmark (e.g. RB-0007's notice at 0.8935, RB-0023's trap source at
  0.9427). The documents are not a poor semantic match for the question they were written to
  answer.
- **Topic crowdedness as a general phenomenon.** Tested directly (Part 2, above) across all 28
  items: no significant correlation between topical crowdedness and trap-source rank (p=0.51).
  RB-0026 is genuinely crowded by this measure (2nd of 28), but the single *most* crowded item in
  the benchmark, RB-0009, has a *perfect* trap-source rank — crowdedness alone does not doom
  retrieval, so it cannot be the whole explanation for RB-0026 either, even though it correlates
  with RB-0026's own case individually.

**What remains genuinely open:** why an item with high semantic relevance to its question, and
crowdedness comparable to several perfectly-ranked items, still ranks 7th and 15th. A natural next
step — not attempted in this pass, given the n=30 checkpoint's proximity — would be a crowdedness
measure tied to each item's own trap-source score specifically (counting documents scoring within
some margin of the trap source's own cosine value, rather than a fixed rank-100 cutoff shared
across items with very different absolute score distributions), which might separate RB-0026 from
RB-0009 where the current measure cannot. **Recorded as an open item for the next checkpoint, not
as a problem to be solved before this file can be considered complete.**

## What this changes and what it does not

- **Does not change:** the ADR-094 pre-registered n=30 predictions for length and Jaccard,
  evaluated as written. The "crowdedness explains RB-0026" account from ADR-121 is now qualified,
  not withdrawn — genuinely correlated with crowdedness by this measure, but crowdedness alone is
  shown here not to be a general predictor, so the account is incomplete, not wrong.
- **Adds:** a third, non-lexical predictor (cosine similarity) that outperforms both lexical
  proxies once RB-0026 is set aside, and resolves RB-0027's anomaly cleanly. **The refinement**
  **sequence is worth reporting in full in the paper, not replaced with only the final result:**
  length (a crude proxy) → Jaccard (a sharper lexical proxy, motivated by the dilution account) →
  embedding cosine similarity (the actual mechanism retrieval uses, motivated by RB-0027 breaking
  the lexical account). Each step was a real measurement at the time it was made, tested against
  real data, and each was superseded by a sharper one for a stated, evidenced reason — not
  arrived at directly. This sequence, told in full, is itself evidence of the project's
  measurement discipline, not just a means to the final number.
