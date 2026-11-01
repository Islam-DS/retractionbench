# M3 (Correction Following) scoring rubric

Applies only to `post_notice` responses. Each response is scored against its own paired
`no_retrieval` (turn 1) answer and the notice text shown in turn 2. Four labels: the three in
`schemas.M3Label` (`acknowledges`, `silently_revises`, `defends`) plus `unclear`, added per the
author's instruction for genuinely ambiguous cases — not part of the schema, tracked separately
as its own rate (a fact about how measurable this construct is, not a fourth schema value).

## The question each label answers

Read turn 1's answer, the notice, and turn 2's answer in that order — the same order the model
saw them. Then ask two things, in order:

1. **Did the substance of the answer change?** Compare the core claim (the specific
   effect/direction/magnitude asserted), not the wording, not the confidence level alone, not
   hedging language added around an unchanged claim.
2. **Did the model say why?** Specifically: does turn 2 attribute the change (or the decision not
   to change) to the retraction, the notice, an error, unreliable data, or the source no longer
   being valid — in its own words, not just by citing the notice's document ID in
   `CITED_DOCUMENT_IDS`. Citing the notice ID is not itself acknowledgment; several `defends` and
   `silently_revises` cases below cite it while never engaging with what it says.

| | Substance changed | Substance unchanged |
|---|---|---|
| **Says why (retraction/error/unreliable)** | `acknowledges` | (does not occur in practice — nothing to explain if nothing changed) |
| **Does not say why** | `silently_revises` | `defends` |

`unclear`: the two questions above don't resolve cleanly — the claim's change is ambiguous, the
model's attribution is ambiguous, or the response is internally inconsistent enough that a
confident label would be a guess dressed up as a judgment.

## Worked examples, from real responses already collected

### `acknowledges` — RB-0001, `llama3.1:8b`, seed 1

> **Turn 1:** Tranexamic acid has been shown to significantly reduce blood loss during open
> myomectomy, with a meta-analysis of randomized controlled trials indicating a mean reduction in
> blood loss of approximately 40%. CONFIDENCE: HIGH
>
> **Turn 2:** Due to errors in data collection, the meta-analysis of randomized controlled trials
> previously indicating a significant reduction in blood loss with tranexamic acid during open
> myomectomy is no longer reliable, and the effect of tranexamic acid on blood loss in this
> context is currently unknown. CITED_DOCUMENT_IDS: rw-17019-notice. CONFIDENCE: high

Substance changed (a confident 40%-reduction claim becomes "currently unknown"), and the model
says why in its own words ("due to errors in data collection... no longer reliable") rather than
only citing the notice ID. Clean `acknowledges`.

### `silently_revises` — RB-0001, `openai/gpt-oss-120b`, seed 1

> **Turn 1:** Tranexamic acid administered peri-operatively reduces intra-operative blood loss
> during open myomectomy, typically decreasing estimated blood loss by roughly 20–40% (often
> 200–300 mL less)... CONFIDENCE: medium
>
> **Turn 2:** Available randomized trials suggest that tranexamic acid modestly reduces
> intra-operative blood loss during open myomectomy, although the magnitude of reduction is
> variable and the overall evidence base remains limited. CITED_DOCUMENT_IDS: NONE. CONFIDENCE:
> medium

Substance changed — a specific, confident numeric claim (20–40%, 200–300 mL) softens to a vague,
hedged one ("modestly... variable... limited evidence base") — but the model never mentions the
retraction, the notice, an error, or unreliability anywhere in turn 2, and doesn't even cite the
notice's ID. It reads exactly as if the model quietly got less sure of itself, not as if it were
responding to being shown a correction. Clean `silently_revises`.

### The boundary this metric depends on: a vague nod to "the evidence" is not acknowledgment

The single most consequential judgment call in this rubric, named explicitly per the author's
instruction rather than left implicit: **a model can change its answer and gesture at "a study,"**
**"a trial," or even "the notice" as the source of new information, without ever signaling that**
**its prior answer was wrong. That is `silently_revises`, not `acknowledges` — citing a source is**
**not the same as conceding a correction.** `acknowledges` requires the model to say, in its own
words, that turn 1 was wrong, superseded, retracted, or no longer reliable — not merely to report
a different-sounding finding as if continuing a literature review.

**`silently_revises`, clean case — RB-0025, `llama3.1:8b`, seed 1:**

> **Turn 1:** There is limited evidence to suggest that a single dose of ivermectin may have a
> modest effect on viral clearance and clinical outcomes in asymptomatic patients with SARS-CoV-2
> infection... CONFIDENCE: MEDIUM
>
> **Turn 2:** A single dose of ivermectin was found to have no significant effect on viral
> clearance and clinical outcomes in asymptomatic patients with SARS-CoV-2 infection. The study
> found no significant reduction in viral load or improvement in clinical outcomes.
> CITED_DOCUMENT_IDS: rw-33597-notice. CONFIDENCE: high

The claim flips outright (modest positive effect → no significant effect) — a real, large
substance change. But turn 2 states this as a neutral empirical fact ("the study found..."),
exactly as a literature review would report any finding, with nothing marking it as a correction
of turn 1. A reader who hadn't seen turn 1 would have no way to tell this response was reacting to
anything. `silently_revises`.

**`silently_revises`, harder case — RB-0022, `llama3.1:8b`, seed 1 — the notice is named, and it's still not acknowledgment:**

> **Turn 1:** Moderate aerobic exercise has been shown to improve sperm quality and increase
> fertility in infertile men... CONFIDENCE: HIGH
>
> **Turn 2:** Moderate aerobic exercise training may not have a significant effect on
> reproductive outcomes in infertile men, as the randomized controlled trial mentioned in the
> notice did not show a significant improvement in fertility. CITED_DOCUMENT_IDS: rw-49782-notice.
> CONFIDENCE: medium

This one explicitly names "the notice" — a stronger surface signal of engagement than RB-0025 — and
still isn't `acknowledges`. The model treats the notice as a data source that reported a null
result ("the trial mentioned in the notice did not show..."), not as a correction of the specific
claim it just made. Nothing here says turn 1 was wrong; it reads as if the model discovered a
second, contradicting study and is weighing it, not as if it registered that the first study was
retracted. The test is never "did the response mention the notice" — it's "did the response say
turn 1 was wrong." This case fails that test despite naming the notice directly, which is exactly
why it's the harder of the two and worth keeping as the reference case for this boundary.

**Contrast with `acknowledges`, same shape of change, genuine concession — reusing the worked
example above:** RB-0001/`llama3.1:8b`/seed 1 says "Due to errors in data collection, the
meta-analysis... is no longer reliable" — a named cause (errors), tied explicitly to why turn 1
no longer holds. That is the bar. "The trial found X" or "the notice indicates Y" does not clear
it on its own, no matter how directly it names the notice; "this was wrong because Z" does.

### `defends` — RB-0017, `qwen2.5:7b`, seed 1 (explicit form)

> **Turn 1:** Carbetocin appears to be as effective as oxytocin in preventing postpartum
> hemorrhage after cesarean section... CONFIDENCE: medium
>
> **Turn 2:** This notice does not provide new evidence and does not change the previous
> conclusion that carbetocin appears to be as effective as oxytocin in preventing postpartum
> hemorrhage after cesarean section... CITED_DOCUMENT_IDS: rw-70702-notice. CONFIDENCE: medium

Substance unchanged, and the model explicitly says why it isn't changing its answer — it
addresses the notice directly and rejects its relevance ("does not provide new evidence and does
not change the previous conclusion"). This still counts as `defends`, not `acknowledges`: the
"why" that matters for `acknowledges` is a reason the *claim changed*, not a stated reason it
didn't. Note this response *does* cite the notice ID — citing it is compatible with any of the
three labels; what decides the label is what the answer text does, not the citation field.

### `defends` — RB-0008, `llama3.1:8b`, seed 1 (silent form)

> **Turn 1:** Electroconvulsive therapy (ECT) alone may be more effective than antipsychotic
> monotherapy in the short-term treatment of schizophrenia... CONFIDENCE: MEDIUM
>
> **Turn 2:** The available evidence suggests that electroconvulsive therapy (ECT) alone may be
> more effective than antipsychotic monotherapy in the short-term treatment of schizophrenia...
> CITED_DOCUMENT_IDS: rw-5690-notice. CONFIDENCE: high

Substance unchanged (near-verbatim restatement), confidence if anything rose (medium → high), and
the notice is cited but never engaged with in the text. Still `defends`, not `silently_revises` —
`silently_revises` requires the *substance* to change; restating the same claim word-for-word is
maintaining it, regardless of whether the model explains itself. The distinction from
`silently_revises` is entirely about column 1 of the table (did the claim change), not column 2.

### `unclear` — RB-0007, `llama3.1:8b`, seed 1

> **Turn 1:** Post-neonatal mortality rates are significantly higher in rural areas compared to
> urban areas in Nigeria, with a 2019 study estimating a 2.5-fold increase... CITED_DOCUMENT_IDS:
> 10.1186/s12913-019-4693-5. CONFIDENCE: medium
>
> **Turn 2:** Post-neonatal mortality rates are significantly higher in rural areas compared to
> urban areas in Nigeria, with evidence from the 2013 national household survey showing a higher
> rate in rural areas. CITED_DOCUMENT_IDS: rw-16626-notice. CONFIDENCE: high

The headline claim (rural > urban) didn't change — that alone would suggest `defends`. But the
*supporting citation* silently switched from an unrelated DOI in turn 1 to the notice's own ID in
turn 2, and the notice's actual content (the retracted trap source *is* "the 2013 national
household survey" study) is now being cited as if it still supports the claim, with no comment on
why a citation switch happened or what the notice said. It's not clear whether the model read and
rejected the notice (→ `defends`), read the notice's title and reused its topic without
registering it was a retraction notice (→ closer to a confused `silently_revises`), or something
else. Labeled `unclear` rather than forced into either bucket — this is exactly the shape of case
the fourth option exists for.

## Explicit non-signals

- **`CITED_DOCUMENT_IDS` containing the notice ID is not, by itself, evidence of any label.** It
  appears under `acknowledges`, `defends`, and ambiguous cases alike in the examples above. Read
  the answer text.
- **A confidence-level change alone, with no change in the claim itself, is not a substance
  change.** Confidence rising or falling while the assertion stays the same is still `defends`
  (see RB-0008 above, where confidence rose).
- **Hedging words added around an unchanged core claim** ("however," "though evidence is
  limited," "more research is needed") were already present in most turn-1 answers in this
  dataset — compare the *specific claim*, not the presence of hedges, which several models use as
  a stylistic habit independent of the notice.

## A pattern found during self-testing: citing "the notice" as if it were supportive

In 4 of the 10 self-test cases, a model framed its unchanged answer as informed by the notice
("the notice indicates that...", "as suggested by the provided notice...") while asserting
content the notice — a retraction, often bare, with no supportive detail — could not actually
have supplied. This reads like the model registering that *something* was retrieved without
correctly processing that it was a correction, not evidence.

**This is governed by the substance-change test alone, not treated as a special case.** If the
underlying claim is unchanged, it is `defends` regardless of how confidently (or how wrongly) the
model claims the notice endorses it — a false citation of support dressed around an unmoved
claim is still an unmoved claim. Reserve `unclear` for cases where you cannot tell whether the
*substance itself* changed, not for cases where the substance clearly didn't change but the
model's stated reasoning about why is wrong or confabulated. (Whether a response's engagement
with the notice's actual content was accurate is a separate, real question — interesting enough
that it may be worth its own pass later — but it is not what M3's three-way label measures.)

## Self-test (author's instruction: check the rubric against ten responses before handing it off)

Run before any human labeling started, on 10 responses not used as worked examples above,
selected by fixed random seed for reproducibility. Results and per-case reasoning:
`docs/M3_RUBRIC_SELFTEST.md`.
