# The four condition prompt templates (ADR-130/131) — settled, then wired

**Status: settled and wired.** This file records the design decisions and the mechanical check
(`tests/test_prompt_templates.py`) that verifies them, so a future edit to one condition can't
silently drift the others out of alignment.

## The three components every condition shares, verbatim, byte-for-byte identical

**SYSTEM_INSTRUCTION** (identical in all four conditions, no exceptions):

```
You are a clinical evidence assistant. Answer the clinical question below as accurately and
as currently as possible.

If documents are provided, base your answer on them and cite the specific document ID(s) you
relied on. If no documents are provided, answer from your own knowledge.

If the evidence is insufficient, contradictory, or you are not confident in an answer, say so
explicitly rather than guessing.

Respond in exactly this format:
ANSWER: <your answer, one or two sentences>
CITED_DOCUMENT_IDS: <comma-separated document IDs you relied on, or NONE>
CONFIDENCE: <low, medium, or high>
```

**QUESTION_BLOCK** (identical in all four conditions -- the item's own `question` field, verbatim,
never paraphrased or reworded per condition):

```
QUESTION: {item.question}
```

**Assembly order** (identical in all four): `SYSTEM_INSTRUCTION` → `DOCUMENTS` (the one varying
block, below) → `QUESTION_BLOCK`. The documents block always appears in the same position
relative to the question, whether it is empty, populated, or absent — condition never changes
where the question sits in the prompt, only what precedes it.

## The structural-consistency fix (resolved, was the open question in the prior draft)

**The prior draft had a real, unflagged confound: `no_retrieval`'s DOCUMENTS block was a single**
**inline sentence, while the other three conditions used a multi-line, bracketed-entry list**
**format. That is a difference in prompt *shape*, not just content, and a model could respond**
**to the shape rather than (or in addition to) the actual presence/absence of evidence — the**
**exact failure the author flagged as the single most important design detail in the pipeline.**
**Fixed: `no_retrieval` now uses the identical `DOCUMENTS:\n[id] text` syntactic shape as the**
**other three, with one placeholder entry instead of five real ones.** The manipulated variable
is now cleanly the *content* (zero real documents vs. five) and never the *format* — the same
header line, the same bracket-and-text-per-entry convention, in every condition, always.

## The one varying component: the `DOCUMENTS` block

**Condition 1 — `no_retrieval`:**

```
DOCUMENTS:
[none] No documents retrieved.
```

**Condition 2 — `retrieval_naive`:** top-k (k=5, fixed -- see "k=5, settled" below) plain
similarity search against the corpus, exactly what the retrieval ceiling's own `search()`
returns for this item's question — whatever comes back, including if the notice happens not to
be in the top 5.

```
DOCUMENTS:
[doc-1] {title of rank-1 result}
{abstract/text of rank-1 result}

[doc-2] {title of rank-2 result}
{abstract/text of rank-2 result}

... (through doc-5)
```

**Condition 3 — `retrieval_with_notice`:** the same top-k=5 naive search, but with the item's
supersession notice guaranteed present among the five — if naive retrieval already surfaced it
(common, per this project's own notice-above-trap-source findings), no injection needed; if not,
it replaces the lowest-ranked of the naive five so the count stays fixed at 5. **Format is
identical to Condition 2** — same per-document layout, same document count, the only difference
is whether the notice is guaranteed to be among the five.

```
DOCUMENTS:
[doc-1] {title}
{text}

... (through doc-5, notice guaranteed present, format unchanged from Condition 2)
```

**Condition 4 — `post_notice`:** two turns, not one — the one place these four templates are not
structurally identical, because M3 (Correction Following, the project protocol) is defined as a
two-turn test by its own nature: give an answer, then show the correction, then re-ask. **Turn 1
of `post_notice` reuses Condition 1's (`no_retrieval`'s) response exactly, cached from that
condition's own run — no independent turn-1 call is made.** This is a deliberate design choice,
not an implementation shortcut, recorded explicitly per the author's instruction ("a reader will
otherwise assume post_notice was run independently"): **it means M3 measures the model's**
**response to the notice given its own prior answer — the question M3 was defined to ask —**
**and it halves the number of live calls `post_notice` needs.** `retrieval_naive` and
`retrieval_with_notice` were deliberately not used as the turn-1 source, since either would let
retrieval quality confound what M3 is trying to isolate (does the model revise when shown the
correction directly, not does better retrieval produce a better prior answer to revise from).

**Hard constraint, enforced in code and tested, not just documented:** the turn-1 response
`post_notice` reuses must come from `no_retrieval`, **for the identical seed** — reusing a
different seed's `no_retrieval` response would silently mix randomness sources across what is
supposed to be one seeded run, undermining the seed-variance reporting the stats layer exists to
produce (`src/retraction_bench/stats/seeds.py`). `src/retraction_bench/rag/pipeline.py`'s
`build_post_notice_turn2` raises if given a turn-1 response whose `condition` is not
`no_retrieval` or whose `seed` doesn't match the requested seed — see
`tests/test_rag_pipeline.py::test_post_notice_rejects_wrong_condition_source` and
`::test_post_notice_rejects_mismatched_seed`.

```
[Turn 1 — identical to Condition 1's cached response, no new call made]
SYSTEM_INSTRUCTION
DOCUMENTS:
[none] No documents retrieved.
QUESTION: {item.question}

[Turn 2 — the notice, plus the prior answer, plus a re-ask]
SYSTEM_INSTRUCTION
DOCUMENTS:
[notice-doc] Notice: {source title}
{notice text, or empty if bare}

Your previous answer to this question was: "{turn 1 ANSWER field, verbatim}"

Given this notice, reconsider your answer.
QUESTION: {item.question}
```

## Fully rendered example, side by side (RB-0001)

`item.question` = *"How does open myomectomy blood loss with tranexamic acid compare to
placebo?"* (paraphrased length here for display; the real prompt uses the exact stored
`question` string).

| | no_retrieval | retrieval_naive | retrieval_with_notice | post_notice |
|---|---|---|---|---|
| SYSTEM_INSTRUCTION | *identical* | *identical* | *identical* | *identical* (both turns) |
| DOCUMENTS *shape* | `DOCUMENTS:\n[id] text` | *same shape* | *same shape* | *same shape* (both turns) |
| DOCUMENTS *content* | 1 placeholder entry | 5 real entries | 5 real entries, notice guaranteed in | turn 1: 1 placeholder; turn 2: notice + prior answer |
| QUESTION_BLOCK | *identical* | *identical* | *identical* | *identical* (both turns) |
| Output format | *identical* | *identical* | *identical* | *identical* |

**Format and content are now separated on purpose: every row except "DOCUMENTS content" reads**
**"identical" or "same shape" across all four columns.** `tests/test_prompt_templates.py`
enforces this mechanically (diffs the rendered templates and asserts the only difference is
inside the `DOCUMENTS` block's content, never its surrounding shape or any other section) — a
future edit that breaks this alignment fails a test, not just a manual review.

## Settled design decisions

1. **k=5 for retrieval conditions, fixed, not tuned.** Chosen because it sits inside the k=3-to-10
   range real RAG systems actually use in practice — this is what makes the paper's own
   retrieval-ceiling numbers (measured at full-corpus rank, not a fixed k) interpretable against
   a realistic deployment window, rather than an arbitrary number picked for convenience. **Not**
   **tuned to any result: if k changed the outcome, that would be its own paper, not a knob to**
   **turn until the numbers look right** (author's explicit instruction).
   **Consequence for RB-0005, corrected and verified directly against the corpus (not assumed):**
   RB-0005 has **no separate supersession-notice document in the corpus at all** — checked
   directly (`data/interim/corpus/assembled_corpus.jsonl` has exactly one row linked to
   RB-0005's source, `corpus_role=benchmark_source`, no `supersession_notice` row exists, ADR-071).
   This is not a case of the notice ranking below k=5 (there is nothing to rank at any k);
   `retrieval_with_notice`'s "guarantee the notice is present" injection has nothing to inject
   for this one item, and the condition degenerates to plain naive retrieval for RB-0005
   specifically. **Reported as a true negative built into the corpus by design (ADR-071's
   decision not to fabricate a notice document where none exists), not a pipeline failure or**
   **missing data** — `notice_retrieved=False` for RB-0005 under `retrieval_with_notice` is the
   honest, correct value, not an error state.
2. **Malformed output is recorded, never leniently repaired.** Every `ModelResponse`'s
   `raw_answer_text` is stored verbatim regardless of whether it parses. A new field,
   `parse_status` (`parsed` / `malformed` / `refused`), is set by
   `src/retraction_bench/rag/parse.py`'s strict parser: `parsed` only if all three required
   fields (`ANSWER`, `CITED_DOCUMENT_IDS`, `CONFIDENCE`) are present in the exact specified
   format; `refused` if the model's own text signals a refusal (a fixed, short list of refusal
   markers, checked directly, not inferred loosely); `malformed` otherwise — no fuzzy field
   extraction, no guessing at a missing field's likely value. **A model that cannot produce**
   **usable output is a real result, not an error to paper over** (author's instruction) —
   `malformed`/`parsed`/`refused` rates are reported per model alongside M1/M3, not folded
   silently into `Correctness.REFUSED` or discarded from the denominator.
3. **`post_notice` reuses `no_retrieval`'s cached response for turn 1** — see the Condition 4
   section above for the full reasoning and the enforced same-seed/same-source constraint.
