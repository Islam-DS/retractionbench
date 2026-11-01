# Does a retraction-and-replacement preserve or overturn the original finding? A three-item stratum (ADR-125)

**Status: flagged as a small, explicitly-labeled stratum, not a headline result.** n=3 is far
too small to support a rate or a general claim — what it supports is naming the axis and showing
that all three shapes a reader might expect are already represented in this benchmark's first
three resolved Retraction-and-Replacement cases.

## Why this axis matters

A formal Retraction-and-Replacement (ADR-069) is a structurally distinct failure mode from an
ordinary void retraction: the correct answer isn't "the evidence is void," it's "cite the
replacement, not the original." But that framing has treated every retract-and-replace case as
one shape. **It is not one shape.** Whether the replacement preserves or overturns the original's
substantive conclusion determines how much a stale citation of the retracted version actually
costs a reader — and this benchmark's first three fully resolved cases turn out to span the full
range.

## The three cases

| Item | Original finding | Replacement finding | Substance |
|---|---|---|---|
| **RB-0026** (NSAID network meta-analysis) | Diclofenac 150mg/day and etoricoxib 60mg/day most effective; no role for paracetamol | Same conclusion, numerically almost identical (74→76 trials, 58,556→58,451 patients) | **Preserved.** A citation of the retracted version would still be substantively correct. |
| **item37** (EMF exposure/ADHD) | Clean, confident dose-response: aHR 2.01 (doubled ADHD risk), stronger for persistent/comorbid cases | Qualitative "inconsistent and nonlinear" association once the flawed exposure cutpoint is removed — no comparably clean replacement effect size stated | **Overturned**, or at minimum substantially weakened from a confident actionable claim to an equivocal one. |
| **item38** (prenatal dexamethasone/CAH) | Not independently confirmable — original abstract erased from PubMed (ADR-065's shape) | No significant behavioral differences between DEX-exposed and control children/adolescents | **Unknowable with current access.** The structure of the comparison is confirmed via the notice's own text; whether the *original* found a difference that the replacement then nullified, or whether both found the same null result, is not primary-source-confirmed. Recorded as a limitation on that item specifically (`results/item38_raw_material.md`), not guessed at. |

## What this means for the paper

**A stale citation of a retracted-and-replaced source is not a uniform harm.** RB-0026 shows the
harm can be near-zero on substance (though the citation is still formally void, and still fails
M1). item37 shows the harm can be exactly the failure this benchmark exists to measure: a
confident, actionable, wrong number persisting in the record after the correction. item38 shows
that sometimes the benchmark itself cannot determine which of these it is dealing with, because
the correction record destroyed the very thing needed to know — a distinct, third finding in its
own right about the limits of what a downstream system (human or automated) can verify from the
public record alone.

**Flagged explicitly as a stratum to report, not a rate.** Three items is enough to show the
axis is real and to name all three shapes with concrete examples; it is not enough to say how
common each shape is. If more Retraction-and-Replacement cases are annotated later, extend this
table rather than computing a premature percentage from n=3.

## Relationship to other findings

This is a different axis from `results/synthesis_contamination_rate.md`'s finding (whether
current evidence *found by search* pools the retracted study) — that measurement is about
third-party syntheses; this one is specifically about the retract-and-replace shape, where the
"replacement" is the retracted study's own corrected version, not a third party. The two
findings are complementary evidence for the same broader point: the correction record's
reliability cannot be assumed at any single layer — not the notice, not the synthesis, and not
even the formal replacement — each has to be checked on its own terms.
