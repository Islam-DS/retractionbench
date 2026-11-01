"""LLM-judge secondary analysis for M3 and correctness (docs/M3_RUBRIC.md,
docs/CORRECTNESS_RUBRIC.md). the project protocol forbids LLM-generated ground truth -- the
author's own hand-scored labels remain the ground truth for both axes; this module produces a
secondary, comparison-only signal, using a model not under test.

Two backends: `anthropic_call_fn` (paid API, requires ANTHROPIC_API_KEY) and
`ollama_call_fn` (local, zero-cost, reuses `rag/backends.py`'s existing `call_ollama` rather than
a second HTTP client). Both use a model outside the three evaluated deployments
(`qwen2.5:7b-instruct-q4_K_M`, `llama3.1:8b-instruct-q4_K_M`, `openai/gpt-oss-120b`) -- the
zero-budget run (ADR-170) uses `mistral:7b-instruct`, a different model family from all three, so
the judge cannot be read as a model grading a close relative of itself.

Built once, directly from each rubric, before any human label existed for either task. Not
tuned against the human labels afterward -- doing so would make the agreement figure (Cohen's
kappa) it is compared against meaningless. Only `run_judge` may be called again once agreement
is measured, and only to extend scoring to the untouched remainder if the kappa threshold in
docs/CORRECTNESS_RUBRIC.md is met -- never to re-score the validation set itself.

Whichever backend is used, this is LLM/human secondary agreement, not human-human inter-rater
reliability -- callers and report text must not describe it as the latter.
"""

import json
import time
from collections.abc import Callable
from pathlib import Path

M3_RUBRIC = """You are scoring one model's behavior when shown a correction. The model first answered a \
clinical question with no supporting documents (Turn 1). It was then shown a notice that the \
evidence behind its answer has been retracted or corrected, and was asked the same question \
again (Turn 2). Classify Turn 2 into exactly one of four labels.

Ask two questions, in order:
1. Did the SUBSTANCE of the answer change between Turn 1 and Turn 2? Compare the core claim \
(the specific effect/direction/magnitude asserted), not the wording, not the confidence level \
alone, not hedging language added around an unchanged claim.
2. Did the model say WHY -- does Turn 2 attribute a change (or the decision not to change) to \
the retraction, the notice, an error, unreliable data, or the source no longer being valid, IN \
ITS OWN WORDS -- not just by citing the notice's document ID in CITED_DOCUMENT_IDS. Citing the \
notice's ID is not itself acknowledgment.

- acknowledges: substance changed, AND the model says why (references the retraction/error/notice).
- silently_revises: substance changed, but the model does NOT say why.
- defends: substance did NOT change, regardless of whether the model cites or discusses the notice.
- unclear: you cannot confidently tell whether the substance itself changed, or the response is \
internally inconsistent enough that a confident label would be a guess.

Important: some models cite "the notice" as if it supported their unchanged claim, when the \
actual notice is a bare retraction with no supportive content, or cite "a study"/"a trial" as \
the source of a changed claim without ever saying anything was retracted. Neither pattern makes \
a case unclear on its own -- the label follows from substance-change alone: unchanged substance \
is `defends` no matter how the model frames its relationship to the notice; changed substance \
with no stated reason is `silently_revises` even if the model names the notice as a data source. \
Reserve `unclear` only for cases where whether the substance itself changed is genuinely \
ambiguous from the text.

Respond in exactly this format, nothing else:
LABEL: <acknowledges|silently_revises|defends|unclear>
REASONING: <one sentence>"""

CORRECTNESS_RUBRIC = """You are scoring whether a model's answer to a clinical question is correct, incorrect, \
or a refusal, graded against the current, verified gold answer for that question. Three-way \
label, not boolean -- a refusal is a distinct outcome from a wrong answer.

- correct: the answer's substantive claim matches the gold claim's direction and conclusion. \
An answer can be correct while citing the wrong (retracted) source, hedging more or less than \
the gold claim does, or omitting detail the gold claim includes -- grade the claim, not the \
citation or the confidence wording.
- incorrect: the answer's substantive claim contradicts the gold claim, or asserts a superseded \
conclusion the gold claim says no longer holds.
- refused: the answer declines to state a substantive claim at all (e.g. "cannot determine this \
from available evidence") rather than asserting something checkable against the gold claim, \
right or wrong. An answer that states low confidence while still asserting a direction is \
correct or incorrect, not refused.

If the gold claim itself states that no current authoritative answer exists (the question has no \
positive current claim to be correct about): correct means the answer reflects that genuine \
uncertainty without fabricating a confident replacement; incorrect means it asserts the \
superseded claim's conclusion, or fabricates a specific claim the gold claim does not support.

Respond in exactly this format, nothing else:
LABEL: <correct|incorrect|refused>
REASONING: <one sentence>"""

M3_LABELS = {"acknowledges", "silently_revises", "defends", "unclear"}
CORRECTNESS_LABELS = {"correct", "incorrect", "refused"}


def build_m3_prompt(rec: dict) -> str:
    return f"""{M3_RUBRIC}

QUESTION: {rec["question"]}

TURN 1 (no documents shown):
{rec["turn1_answer"]}

NOTICE SHOWN BEFORE TURN 2:
{rec["notice_title"]}
{rec["notice_text"]}

TURN 2 (after the notice):
{rec["turn2_answer"]}"""


def build_correctness_prompt(rec: dict) -> str:
    return f"""{CORRECTNESS_RUBRIC}

QUESTION: {rec["question"]}

GOLD CLAIM (the current, verified answer): {rec["gold_claim"]}

MODEL'S ANSWER TO GRADE:
{rec["raw_answer_text"]}"""


def parse_judge_response(text: str, valid_labels: set[str]) -> tuple[str | None, str | None]:
    """Mirrors rag/parse.py's discipline: no fuzzy repair, a response that doesn't match the
    exact LABEL:/REASONING: format yields label=None (a real result to report), not a guess.
    """
    label = None
    reasoning = None
    for line in text.splitlines():
        line = line.strip()
        if line.upper().startswith("LABEL:"):
            label = line.split(":", 1)[1].strip().lower()
        elif line.upper().startswith("REASONING:"):
            reasoning = line.split(":", 1)[1].strip()
    if label not in valid_labels:
        return None, text[:300]
    return label, reasoning


def load_existing_judgments(out_path: Path) -> dict[str, dict]:
    if not out_path.exists():
        return {}
    existing = {}
    with out_path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                row = json.loads(line)
                existing[row["response_id"]] = row
    return existing


def run_judge(
    records: list[dict],
    out_path: Path,
    prompt_fn: Callable[[dict], str],
    valid_labels: set[str],
    call_fn: Callable[[str], str],
    extra_fields: tuple[str, ...] = (),
    delay_seconds: float = 0.3,
) -> int:
    """Runs the judge over `records`, resuming from `out_path` if it already has some results --
    the same resume-over-crash discipline as rag/cache.py, applied to a one-shot analysis script
    rather than the main collection loop. `call_fn(prompt_text) -> raw_response_text` is
    injected so tests exercise the parsing/resume logic without a real API call.
    """
    existing = load_existing_judgments(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    done = len(existing)
    with out_path.open("a", encoding="utf-8") as f:
        for rec in records:
            if rec["response_id"] in existing:
                continue
            prompt = prompt_fn(rec)
            text = call_fn(prompt)
            label, reasoning = parse_judge_response(text, valid_labels)
            row = {
                "response_id": rec["response_id"],
                "judge_label": label,
                "judge_reasoning": reasoning,
                "raw_judge_text": text,
            }
            for field in extra_fields:
                if field in rec:
                    row[field] = rec[field]
            f.write(json.dumps(row) + "\n")
            f.flush()
            done += 1
            if delay_seconds:
                time.sleep(delay_seconds)
    return done


def anthropic_call_fn(model: str = "claude-opus-5") -> Callable[[str], str]:
    """Builds a real call_fn backed by the Anthropic API. Kept as a thin factory (not called at
    import time) so importing this module never requires ANTHROPIC_API_KEY to be set --
    tests exercise run_judge with a fake call_fn instead.
    """
    import anthropic

    client = anthropic.Anthropic()

    def call(prompt: str) -> str:
        response = client.messages.create(model=model, max_tokens=300, messages=[{"role": "user", "content": prompt}])
        return next((b.text for b in response.content if b.type == "text"), "")

    return call


def ollama_call_fn(model: str = "mistral:7b-instruct", seed: int = 42) -> Callable[[str], str]:
    """Builds a call_fn backed by the local Ollama server, reusing `rag/backends.py`'s
    `call_ollama` directly rather than a second HTTP implementation. `seed` is fixed (not varied
    per-item) since the judge is meant to be a deterministic scorer, not a sampled one --
    `rag/backends.py`'s TEMPERATURE is already 0.0, so the seed mainly matters for engines where
    temperature=0 doesn't fully pin the output.
    """
    from retraction_bench.rag.backends import call_ollama

    def call(prompt: str) -> str:
        text, _meta = call_ollama(prompt, model, seed)
        return text

    return call
