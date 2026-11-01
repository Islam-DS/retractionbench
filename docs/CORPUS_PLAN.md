# Corpus Construction Plan

> **Status: Built and frozen (ADR-048), 2026-08-09.** 400,542 documents (400,538 background
> + 4 benchmark documents), ~27-fold domain imbalance (Rehabilitation 330,753 vs.
> Obstetrics/Gynecology 12,107 -- larger than every earlier estimate in this file; see
> ADR-048 for why). Retrieval-ceiling infrastructure (section 6) is validated against the
> real index but not yet statistically meaningful with only one annotated item -- re-run as
> annotation adds items across all three domains.

## 1. The problem this exists to solve

A corpus containing only the benchmark's own ~90 retracted sources plus their superseding
evidence makes retrieval trivially easy: every document in the corpus is relevant to some
benchmark question, and there are no distractors. Any model would look better at retrieval
than it deserves, and the gap between "retrieval found the right document" and "the model
used it correctly" would be invisible -- exactly the ambiguity the project protocol's standards exist to
prevent (every reported number needs to mean what it claims to mean).

## 2. Corpus composition and size

**Derived, not targeted (ADR-046): 325,043 PubMed records**, drawn from the three final
domains (Pharmacology, Obstetrics/Gynecology, Rehabilitation/Therapy -- ADR-018/021/027) by
MeSH heading (section 3), 2000-present, restricted to records with abstract text present.
This is a background/distractor pool, not meant to mirror the benchmark's own domain
proportions -- its job is to supply plausible neighbors a retriever could confuse with the
real answer, not to represent the benchmark's composition. Rehabilitation dominates the
total (287,885 of 325,043 pre-abstract-filter) because its MeSH heading is genuinely broad --
the same breadth ADR-025 already found in Retraction Watch's own Rehabilitation/Therapy tag,
so this is a consistent, expected property of the domain, not a query-design artifact.

No subsampling to a round number, per instruction -- if the fetch proceeds, it proceeds
against the full derived scope, or a further-narrowed scope decided on a principled basis
(not an arbitrary cutoff) if index build time turns out to bind in practice.

Every corpus document carries a `corpus_role` tag, one of:
- `benchmark_source` -- the retracted paper itself (`SupersededSource`)
- `supersession_notice` -- the notice text, embedded as its own retrievable unit, linked to
  its source (see section 4; this is what makes `notice_retrieved` in `EvaluationResult`
  actually measurable rather than assumed)
- `superseding_evidence` -- a `post_supersession_evidence` entry
- `background` -- everything else, the general PubMed sample

## 3. Background sampling method

PubMed ESearch, MeSH-derived per domain (ADR-046), not hand-tuned keywords -- each domain's
top-level MeSH heading, letting PubMed's automatic tree expansion pull in narrower/child
terms rather than an enumerated keyword list. Verified live, 2026-08-07:

| Domain | Query | Count (pre-abstract-filter) |
|---|---|---|
| Pharmacology | `"Pharmacology"[MeSH Terms]` | 63,224 |
| Obstetrics/Gynecology | `"Obstetrics"[MeSH Terms] OR "Gynecology"[MeSH Terms]` | 17,169 |
| Rehabilitation/Therapy | `"Rehabilitation"[MeSH Terms]` | 287,885 |

Combined, `AND 2000:2026[dp] AND hasabstract[text]`: **325,043** (deduplicated union; the
three domains overlap by under 0.1% at the MeSH level). A narrower alternative was checked
for Pharmacology (`"Pharmacology, Clinical"[MeSH Terms]`, 1,877 records) and rejected as too
narrow to represent the domain's real scope; a broader alternative was checked for
Rehabilitation (adding `"Physical and Rehabilitation Medicine"[MeSH Terms]`) and rejected as
redundant (<0.5% change).

Date window: **2000 to present**, frozen at build time (section 7). Rationale: the
benchmark's own retracted sources span 2001-2017 and superseding evidence runs to 2025 --
narrowing the window at either end would clip real benchmark dates and introduce an
unquantifiable retrieval bias, where widening it only costs (cheap) index size. The corpus's
own publication-date distribution will be reported alongside the benchmark items' dates.

This reuses the rate-limited, cached-to-disk pattern already built in `ingest/pubmed.py`
rather than a new one-off script.

**Deliberately not filtered by retraction status.** Screening out retracted papers before
sampling would require trusting exactly the PubMed tag this project has already shown
(ADR-028/029) is not fully reliable -- using an unreliable filter to build the "realistic"
half of the corpus would quietly reintroduce the problem those ADRs document. Background
sampling draws from PubMed as-is.

## 4. Guaranteeing benchmark sources appear exactly once

1. Build the background sample first (section 3), independent of the benchmark.
2. Collect every benchmark-relevant PMID: `SupersededSource.external_ids.pmid` for each
   retracted source, plus PMIDs resolved from `post_supersession_evidence[].identifier`
   (mostly DOIs -- resolved via NCBI's ID Converter API, cached, not re-resolved on every
   build).
3. Deduplicate: if a benchmark PMID already landed in the background sample (plausible,
   since domain sampling could legitimately catch it), remove the background copy.
4. Insert every benchmark PMID exactly once, tagged with its `corpus_role` (`benchmark_source`
   or `superseding_evidence`), regardless of whether step 3 found it already present.
5. Embed each `SupersededSource`'s notice text as a separate document (`corpus_role =
   supersession_notice`), linked to its source's `source_registry_id` -- distinct from the
   source's own abstract, since a model can retrieve the retracted paper without retrieving
   its notice, and that distinction is exactly what `EvaluationResult.notice_retrieved` is
   for.

This is deterministic and re-buildable: steps 1-5 depend only on the current
`data/benchmark/sources.jsonl` and PubMed's own state, both of which are logged
(`as_of_date`-style, matching the pattern already used for citation lookups in ADR-035).

## 5. Retracted papers as deliberate distractors

Background sampling (section 3) is not screened for retraction status, so it will contain an
unknown number of retracted papers alongside the deliberately-included benchmark sources.
**This is the point, not a flaw to fix.** After the corpus is built, run the existing
`ingest/pubmed.py` verification against every background document (same cached, rate-limited
mechanism already used for the candidate pool) and report the background retracted-tag rate
as its own corpus statistic -- e.g. "X% of the 325,043-document background corpus carries a
`Retracted Publication` tag, entirely independent of our own benchmark items." This is a
second, corpus-level data point for the same phenomenon ADR-028/029 already measured at the
candidate-pool level, and it is nearly free to compute given the tooling already exists.

## 6. Retrieval metrics, reported separately from generation metrics

The schema already supports this without changes: `ModelResponse.retrieved_document_ids`
records what retrieval actually surfaced; `EvaluationResult.notice_retrieved` is already
required exactly under `Condition.RETRIEVAL_WITH_NOTICE`. Once the corpus exists with stable
document IDs matching `SupersededSource`/`Evidence` identifiers, retrieval quality is
computable directly by set comparison, independent of anything a model does with what it's
given:

- **Trap-source recall@k**: was the retracted source itself in the retrieved set, for
  retrieval-enabled conditions.
- **Notice recall@k**: was the notice document specifically retrieved (section 4's separate
  notice documents make this answerable).
- **Gold-evidence recall@k**: was at least one `post_supersession_evidence` entry retrieved.
- **Background contamination rate**: of the retrieved set, how many documents are
  `background`-tagged retracted papers (section 5) the model wasn't even being tested on --
  a realistic-corpus effect a trivial corpus could never surface.

Reporting this split is what lets a result be attributed to retrieval or generation
specifically, rather than staying ambiguous, per the author's stated reason for wanting it.

**Retrieval ceiling, measured before any model call (ADR-046 addition):** once the index is
built, for every benchmark item, check whether its retracted source and its notice appear in
the top-k retrieved results for the item's question, at k in {1, 5, 10, 20, 50}. This
produces a retrieval ceiling -- the best any model could do given this corpus -- and is
reported before generation results, not alongside them as an afterthought: if a notice is
never retrieved at k=10 across the corpus, a model's failure to mention it under that k is a
retrieval failure, not a generation failure, and the two must not be conflated. Cheap (no
model calls), so it isn't gated by the cost-estimate step in ADR-045.

**Broken out per domain, not just in aggregate (ADR-047).** The corpus is 17-fold imbalanced
by domain (Rehabilitation 287,885 vs. Obstetrics/Gynecology 17,169 records) -- a real threat
to the benchmark's stratified per-domain comparison (ADR-027) if retrieval competition
differs enough by domain to confound any downstream domain-level result. Per-domain ceilings
answer this with evidence rather than assumption: comparable ceilings across domains despite
the density difference mean the imbalance isn't binding; a materially lower Rehabilitation
ceiling means it is, and one of ADR-047's three recorded fixes applies (preferred: report
density as a covariate; second: a balanced secondary stratified index; rejected: narrowing
Rehabilitation's MeSH scope). Not decided until the measurement exists.

## 7. Resolved decisions (ADR-046, ADR-047)

1. **Date window: 2000-present, frozen at build time.**
2. **Domain query terms: MeSH-derived, exact queries in section 3, not hand-tuned.**
3. **Freeze policy: built once, hashed, versioned.** Frozen at construction; freeze date,
   record count, and a content hash (SHA-256 manifest, format decided at build time) recorded
   in ADR-046's follow-up entry and in the paper. A later rebuild is corpus v2, a new ADR,
   with affected results recomputed and reported against the version they used -- never a
   silent drift. Post-freeze benchmark items are inserted individually via section 4's
   exactly-once mechanism, not folded into a rebuild.
4. **Size: derived (325,043), not targeted.** No subsampling to a round number; the full
   scope is fetched and indexed as-is (ADR-047), including the 17-fold domain imbalance --
   not narrowed on the assumption that size hurts retrieval, which is measured, not assumed
   (section 6).
5. **Reproduction path reports real requirements, not optimistic ones.** Build time, peak
   memory, and on-disk index size are measured and reported from the actual run, not
   estimated in advance.
6. **The 17-fold domain imbalance is itself a reportable finding** (ADR-047), belonging in
   the paper's domain-description material, not just handled as a nuisance parameter.
