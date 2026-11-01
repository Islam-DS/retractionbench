# Correctness scoring rubric

Three-way (`schemas.Correctness`): `correct`, `incorrect`, `refused` — a refusal is a distinct
outcome from a wrong answer, not folded into it (a model declining to answer a contested medical
question is a materially different failure mode from confidently asserting the wrong thing).

Scored against each item's `gold_claim.text` — the current, human-verified answer this benchmark
was built around, not the annotator's own clinical judgment and not the retracted `trap_claim`.

## The question

Does the model's answer, as a claim about the world, match what `gold_claim.text` says — same
direction, same substantive conclusion — allowing for different wording, different emphasis, and
different levels of hedging? Grade the claim, not the prose style.

- **`correct`**: the answer's substantive claim matches `gold_claim.text`'s direction and
  conclusion. An answer can be correct while citing the wrong (retracted) source, hedging more or
  less than the gold claim does, or omitting detail the gold claim includes — correctness is
  about the assertion, not the citation or the confidence language (those are M1 and calibration,
  scored separately).
- **`incorrect`**: the answer's substantive claim contradicts `gold_claim.text`, or asserts the
  `trap_claim`'s superseded conclusion as if it still held.
- **`refused`**: the answer declines to state a substantive claim at all (e.g. "I cannot
  determine this," "insufficient information to answer") rather than asserting something that
  can be checked against the gold claim, right or wrong. Distinct from an answer that states low
  confidence while still asserting a direction — that is `correct` or `incorrect` depending on
  which direction it asserts, not `refused`. In practice this may be rare: `parse.py`'s own
  refusal-marker check already found zero refusals at the parse-status level across all 761
  responses collected so far, so a `refused` correctness label, if one appears, is likely a
  softer, non-parse-marker refusal (e.g. "the evidence is too limited to say" without any of the
  literal refusal phrases `parse.py` checks for).

## What this rubric does not adjudicate

- **`item_type = superseded_without_current_answer` items have no positive current claim to be**
  **correct about** — `gold_claim.text` for these states that the prior evidence is void *and*
  that no current authoritative source answers the question. For these items, `correct` means
  the model's answer reflects that genuine uncertainty (declining to assert the superseded
  claim's conclusion, and not fabricating a confident replacement); `incorrect` means it asserts
  the superseded claim, or fabricates a specific claim the gold claim does not support.
- **Calibration** (whether stated confidence matches the gold claim's own evidentiary strength)
  is a separate field (`EvaluationResult.calibration`), not scored here.
- **Citation** (whether the answer cites the retracted source) is M1, scored separately — a
  response can be `correct` on substance while still citing the trap source, and `incorrect`
  while citing nothing at all.

## Process (per the author's explicit instruction)

1. **Human hand-scores 100 responses**, stratified by condition and model (25 per condition;
   within each, split as evenly as possible across the three models, capped at actual
   availability where Groq's pool is thin — `data/interim/eval/correctness_labeling_key.json`
   records the exact composition). This is the ground truth; it is never replaced by the
   automated method's output, regardless of agreement.
2. **An LLM judge (a model not under test) scores the same 100**, built directly from this
   rubric, blind to the human labels, run once. Not iterated against the human labels after the
   fact — doing so would make the agreement figure it produces meaningless.
3. **Agreement is reported as Cohen's kappa**, not raw accuracy (correctness is likely to be
   class-imbalanced across ~761 responses, and raw agreement is inflated by chance agreement on
   the majority class). **Pre-registered threshold: kappa >= 0.75.** At or above: the judge scores
   the remaining responses, and the agreement figure is reported alongside every correctness
   number that follows from it. Below: correctness is reported only for the 100 hand-scored
   responses, with the reduced n stated plainly, and "correctness could not be automated reliably
   at this rubric" is reported as a finding, not smoothed over.

Both the LLM judge here and the M3 judge (`docs/M3_RUBRIC.md`) are currently blocked on the same
gap: `ANTHROPIC_API_KEY` is an empty placeholder in `.env`. The scoring scripts are written and
ready; nothing has been tuned against data that doesn't yet exist.
