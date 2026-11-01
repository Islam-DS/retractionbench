# Exact prompts, document ordering, notice labelling, and decoding settings

Phase 0 deliverable (manuscript-upgrade audit). Every string and parameter below is copied
verbatim from the real source files cited next to it -- nothing here is reconstructed from memory
or rounded into place.

## 1. System instruction (identical across all four conditions and all three models)

Source: `src/retraction_bench/rag/prompts.py`, `SYSTEM_INSTRUCTION` (lines 12-26).

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

## 2. Document block rendering (`render_documents_block`, lines 45-55)

One function, shared by every condition including `no_retrieval` (called with a single
placeholder document). For each document `d`:

```
[{d.doc_id}] {d.title}
{d.text}
```

(the body line is omitted entirely if `d.text` is empty -- true only for the `no_retrieval`
placeholder, `doc_id="none"`, `title="No documents retrieved."`). Entries are joined with a blank
line and the whole block is prefixed `"DOCUMENTS:\n"`.

**Notice labelling: none beyond its own natural title.** A supersession notice is rendered exactly
like any other retrieved document -- same `[doc_id] title` / body shape, no special marker,
header, or instruction calling it out as a retraction notice. Its only distinguishing surface
feature is its own title text, which is constructed at corpus-build time as `f"Notice: {source.title}"`
(`src/retraction_bench/corpus/assemble.py`) -- e.g. `[rw-17019-notice] Notice: The efficiency and
safety of tranexamic acid for reducing blood loss in open myomectomy...`. The model is never told
"this document is a retraction notice" in any system instruction or document header.

## 3. Full prompt assembly, per condition

Source: `render_prompt` (lines 58-64) -- `SYSTEM_INSTRUCTION -> DOCUMENTS -> QUESTION`, used
identically by every condition except `post_notice` turn 2.

- **`no_retrieval`**: `render_prompt([NO_DOCUMENTS], question)`.
- **`retrieval_naive`** / **`retrieval_with_notice`**: `render_prompt(documents, question)`, where
  `documents` is whatever `rag/pipeline.py`'s selection functions returned (naive actively
  excludes the notice and backfills; with-notice guarantees its presence) -- the prompt-assembly
  code itself cannot tell the two conditions apart; only the document list passed in differs.
- **`post_notice` turn 1**: identical to `no_retrieval` (same-seed, reused, not re-called).
- **`post_notice` turn 2** (`render_post_notice_turn2_prompt`, lines 80-91), the one structural
  exception -- `SYSTEM_INSTRUCTION -> DOCUMENTS([notice_doc]) -> RECONSIDER -> QUESTION`:

```
{SYSTEM_INSTRUCTION}

DOCUMENTS:
[{notice_doc.doc_id}] {notice_doc.title}
{notice_doc.text}

Your previous answer to this question was: "{prior_answer}"

Given this notice, reconsider your answer.

QUESTION: {question}
```

`prior_answer` is the parsed `ANSWER:` field from the same-seed `no_retrieval` response (or the
raw text if parsing failed) -- never a fresh model call for turn 1.

## 4. Document ordering

Documents are passed to the renderer in the exact order `rag/pipeline.py`'s selection functions
return them -- `retrieval_naive`: filtered dense-ranking order (highest cosine similarity first,
notice removed, backfilled from beyond the cutoff); `retrieval_with_notice`: the unfiltered dense
ranking, with the notice spliced into the final (k-th) slot only if it was not already present.
No shuffling, no randomized order, no notice-to-front promotion.

## 5. Decoding settings (identical for all three models)

Source: `src/retraction_bench/rag/backends.py`, lines 26-27.

| Parameter | Value | Where set |
|---|---|---|
| `temperature` | **0.0** | `TEMPERATURE = 0.0` (module constant) |
| `max_tokens` / `num_predict` | **512** | `MAX_TOKENS = 512` |
| `top_p` | **not set** -- provider default applies | Never passed in either `call_groq` or `call_ollama`'s request body |
| `seed` | **1, 2, or 3**, passed verbatim | Groq: JSON body `"seed": seed`; Ollama: `options.seed` |
| Retries | Groq: up to 4, exponential backoff capped at 30s, on 429/5xx only; Ollama: none (local errors surface immediately) | `MAX_RETRIES`, `_retry_delay` |
| Reasoning/chain-of-thought | Stripped before storage -- only the `message.content` (Groq) / `response` (Ollama) field is kept as `raw_text`; Groq's separate `reasoning` field is captured in metadata only, never parsed for ANSWER/CITED_DOCUMENT_IDS/CONFIDENCE | `call_groq` lines 118-123 |

## 6. Models and routes

| `model_identifier` | Route | Quantization |
|---|---|---|
| `openai/gpt-oss-120b` | Groq hosted API | Provider-managed, not disclosed by Groq |
| `qwen2.5:7b-instruct-q4_K_M` | Local Ollama | 4-bit K-quant (`q4_K_M`), explicit in the model tag |
| `llama3.1:8b-instruct-q4_K_M` | Local Ollama | 4-bit K-quant (`q4_K_M`), explicit in the model tag |

## 7. Seeds

Three fixed integer seeds, `1`, `2`, `3` (`stats/seeds.py`'s `MIN_SEEDS = 3`), run for every
item x condition x model combination, passed directly as the API-level `seed` parameter above --
no derived or re-hashed seed value anywhere in the pipeline.
