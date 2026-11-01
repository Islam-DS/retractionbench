# How often does the best-matching current-evidence source itself pool the retracted study? (ADR-125)

**Status: a retrospective measurement across this project's own annotation history, not a new**
**data collection pass.** Prompted by item39's independence catch (the second of its kind, after
item17) — the author's instruction: two is a pattern worth measuring, not just logging.

## What this measures, and why it matters more than a retrieval-ranking number

Every item in this benchmark that reaches `superseded_with_current_answer` (or is disqualified
from doing so) passes through an independence check (ADR-058): before a candidate synthesis,
meta-analysis, or systematic review is used as the item's post-supersession evidence, its own
reference list is checked for the retracted study itself. This measurement asks: **across every**
**item where that check was actually performed, how often did the best-matching, most obviously**
**on-topic candidate source turn out to have pooled the retracted study's own data?**

This is a different, and arguably more consequential, question than anything this project has
measured about retrieval ranking. A retrieval failure means a model might not find the correction.
**A synthesis-contamination failure means the correction never had a chance to reach the reader**
**in the first place — a clinician or a model consulting current best evidence, doing everything**
**right, inherits the retracted data anyway, laundered through a citation that looks authoritative**
**precisely because it is a synthesis.** This is a failure of the evidence base itself, not of any
retrieval or generation step downstream of it — squarely the kind of finding the project protocol's founding
thesis is about, one level upstream of where this project's other measurements sit.

## Method

**Scope: every item, from item17 onward, where a candidate synthesis-level source was seriously**
**evaluated and its reference list actually checked against the retracted study (ADR-058's**
**standardized practice).** item17 is the origin of this practice, not an arbitrary start point —
it is the item that prompted ADR-058 to be written in the first place, after this exact failure
was caught by chance rather than by a standing rule. Items before it (item1-item16) predate the
standardized check and are excluded, not because no synthesis was ever found for them, but
because no consistent, documented independence check was performed to include in this count.

**Retract-and-replace items are excluded from the denominator, not folded in as automatic**
**"clean" cases.** RB-0012 (item20), RB-0026 (item34), item37, and item38 all have
`independence` resolved *structurally* — the "replacement" is the retracted study's own authors'
corrected version, not a third-party synthesis that could have pooled it, so the question this
measurement asks (did a synthesis pool the retracted data) does not apply to them the same way.
Including them would understate the real rate by padding the denominator with items that were
never at risk of this specific failure.

**This yields 19 items in the denominator:** item17, 18, 19, 21, 22, 23, 24, 25, 26, 27, 28, 29,
30, 31, 32, 33, 35, 36, 39.

## Result

**3 of 19 (15.8%), Wilson 95% CI [5.5%, 37.6%].** The interval is wide, as expected at this n —
this is a retrospective count over the items actually annotated, not a designed sample, and
should be reported with that qualification attached, not as a precise population rate. **But the
point estimate itself is not small, and the lower bound alone rules out "this basically never
happens."**

| Item | Retracted study | Contaminated candidate found? | Resolution |
|---|---|---|---|
| **item17** | Choi 2019 (JAMA Oncology, entecavir/tenofovir HCC) | **Yes** — Oh et al. 2022 meta-analysis pools the retracted paper's own data directly (its Table 1, citation [7]) | Disqualified per ADR-058; item ultimately deferred on other grounds (JAMA notice unreachable) |
| **item27** (RB-0019) | Diacerein RCT | **Yes** — the topically closer candidate (diacerein vs. *placebo* specifically, matching the trap claim's own comparator) cites the retracted paper directly (citation #17 of 35) | Disqualified; a second, less topically precise candidate (diacerein vs. NSAIDs) was independent and used instead — the comparator mismatch this substitution introduces is itself flagged in the item's own gold claim |
| **item39** | Bansal & Arora 2017 (TURP/5-ARI bleeding) | **Yes** — the largest, most current candidate (Hehir et al. 2026, 30 RCTs) pools the retracted trial at reference #45 | Disqualified per ADR-058; a smaller, older (2015), genuinely independent synthesis used instead |
| item18, 19, 21, 22, 23, 24, 25, 26, 28, 29, 30, 32, 33, 35, 36 | — | No | Independence confirmed directly (Europe PMC reference-list check or, where the review predates the retraction, temporal impossibility), best-matching candidate used as found |
| **item31** (RB-0025) | Samaha 2021 (ivermectin) | **No — and positively documented as excluded, not merely absent.** The Cochrane review's own text states it screened for and excluded the retracted trial by name, citing the retraction itself as the reason | The one item in this set where the correction record shows its own working, not just a clean reference list |

## The contrast the author asked to be made explicit

**Same failure point in the evidence pipeline — whether a synthesis absorbed a study that was**
**later found unreliable — with opposite outcomes, and this project now has documented instances**
**of both.** In three cases (item17, item27, item39), the retracted study's data is sitting
inside a synthesis's pooled estimate with no visible marker that anything is wrong — a reader
citing that synthesis would never know. In one case (item31), the correction mechanism worked
exactly as it should: Cochrane's own review text names the trial, states it was excluded, and
gives the reason ("Trial did not pass research integrity check, due to published retraction
notice"). **The difference between these outcomes is not about whether a synthesis existed or**
**was thorough — all four syntheses in this comparison are large, recent, and methodologically**
**serious. It is about whether the review process checked retraction status at all before**
**pooling.** This is squarely a practice question for evidence synthesis as a field, not a
critique of any individual review team.

## What this does and does not establish

**Does establish:** among the syntheses this project's annotators seriously considered as
candidate current-evidence sources, roughly 1 in 6 (with wide uncertainty) had silently pooled
the very study the item exists because of. **Does not establish:** a population-level rate for
all systematic reviews, or that this is representative of evidence synthesis generally — the
denominator here is 19 syntheses selected because they were topically relevant to 19 specific
retracted claims this benchmark happened to annotate, not a random or systematic sample of the
review literature. **A larger, purpose-built study (auditing a random sample of systematic
reviews citing any retracted primary study, regardless of whether it made this benchmark) would**
**be needed to state a defensible population rate** — flagged as a natural follow-on study, not
attempted here.

## Consequences for this project

Recorded as a finding in its own right, not folded into the retrieval-ranking results as
supporting texture. `docs/STATUS.md` and `paper/paper.md` both updated with a pointer. The three
contamination catches (item17, item27, item39) and the one documented-clean case (item31)
should all four be reported together in the paper as the evidence for this rate, not just the
count — a reader should be able to see the actual cases, the same standard this project holds
every other rate to.
