# A conditional remedy: enrichment helps low-overlap notices and is predicted to hurt near-maximal ones (ADR-096, sharpened ADR-098)

**Status: exploratory, n=12, a diagnosed candidate mechanism (ADR-090/094) tested with a**
**candidate remedy that has a stated, testable condition -- not a validated intervention, and**
**not "mostly doesn't work."** ADR-094's Jaccard-overlap result implies a falsifiable
prediction: if a notice's poor rank is caused by dilution of shared vocabulary with the
question, restoring that vocabulary (by indexing the notice jointly with its own paper's title
and abstract) should improve its rank -- **but only where there is diluted vocabulary to
restore.** For a notice already at near-maximal overlap (a bare notice whose entire text is
already the paper's own title), there is nothing to restore, and adding more text can only add
competing signal. **The remedy's predicted failures are not noise -- they are the same account
that predicts its successes, applied to the opposite case.** That is what makes this evidence
for the mechanism, not just an intervention with mixed results.

## Method

**The production frozen corpus and index are untouched.** The existing index's 400,576 vectors
were reconstructed directly (no re-embedding of background documents), and only the ~12 notice
documents' vectors were recomputed, using enriched text:
`f"{notice_title} {notice_body} {trap_source_title} {trap_source_abstract}"`. A fresh
in-memory `IndexFlatIP` was built from this modified vector set (background and trap-source
vectors identical to production) and searched with each item's real question, using the same
`retrieval_ceiling.measure_item` function the production ceiling measurement uses. Nothing is
written back to `data/interim/corpus/index`; the raw comparison is
`results/notice_enrichment_intervention_test.json`.

## The condition, stated explicitly as a prediction someone else can test

**Enrichment should help a notice whose baseline Jaccard overlap with its question is low, and**
**is expected to hurt (or not help) a notice whose overlap is already near-maximal**, because in
the latter case enrichment does not add missing relevant vocabulary -- it adds vocabulary that
makes the notice compete more directly with its own trap source's richer, more specific text,
which the mechanism predicts the trap source usually wins.

## Result, read against that condition

| Item | Baseline Jaccard | Baseline notice rank | Enriched notice rank | Outcome |
|---|---|---|---|---|
| RB-0010 | 0.022 (lowest) | 3 | 3 | unchanged |
| RB-0004 | 0.098 | 3 | **1** | **improved** |
| RB-0002 | 0.111 | 2 | 2 | unchanged |
| RB-0009 | 0.123 | 2 | 2 | unchanged |
| RB-0012 | 0.135 | 2 | 2 | unchanged |
| RB-0006 | 0.143 | 3 | 3 | unchanged |
| RB-0003 | 0.167 | 2 | 2 | unchanged |
| RB-0001 | 0.214 | 2 | 2 | unchanged |
| RB-0008 | 0.267 | 1 | 2 | **worsened** |
| RB-0013 | 0.267 | 2 | 2 | unchanged |
| RB-0011 | 0.333 | 1 | 1 | unchanged |
| RB-0007 | 0.412 (highest) | 1 | 2 | **worsened** |
| RB-0005 | -- | none (no notice document, ADR-071) | -- | excluded |

**The two worsened cases are the two highest-Jaccard items in the entire set. The one improved**
**case sits in the low-Jaccard half.** Correlating baseline Jaccard against the rank change
(baseline rank minus enriched rank, positive = improved) directly: **Pearson r = -0.535 (n=12)**
-- a real, moderate, correctly-signed relationship (higher starting overlap, less benefit or
more harm from enrichment), computed once, not tuned. This is consistent with the stated
condition and is the sharper evidence for the mechanism: **a remedy whose failures are predicted**
**by the same account that predicts its successes is stronger evidence for that account than a**
**uniform improvement would have been** -- a uniform win would be equally consistent with many
mechanisms (more text always retrieves better, for instance); a *conditional* win, matching a
specific, stated, falsifiable condition, is not.

**Two honest exceptions, not smoothed over.** RB-0010 has the single lowest Jaccard overlap in
the set (0.022) and did *not* improve -- it stayed at rank 3. RB-0011 has the third-highest
Jaccard (0.333, comparable to the two worsened cases) and did *not* worsen -- it stayed at rank
1. r=-0.535 is a real, moderate correlation at n=12, not a deterministic threshold rule, and
these two items are the reason it is r=-0.535 and not something closer to -1. A more refined
test -- e.g. the *change* in Jaccard overlap caused by enrichment, rather than only the
baseline value, since how much vocabulary enrichment actually adds varies by item -- was not
run in this pass and is a natural next step, not assumed to resolve these exceptions.

**RB-0004's improvement, mechanistically:** a 747-character `unverifiable`-specificity notice,
heavily diluted by retraction-notice boilerplate unrelated to the clinical question (low
baseline Jaccard, 0.098). Restoring the trap source's own title and abstract reintroduced the
diluted vocabulary and moved the notice from rank 3 to rank 1 -- past the trap source itself.

**RB-0007 and RB-0008's worsening, mechanistically:** both `bare` notices already at maximal
lexical overlap -- their entire notice text *is* the paper's title. Enriching them adds the
paper's own abstract on top of a notice that was already, in effect, a compressed pointer to
that exact content. **A rank is a position in an ordering, not an absolute score** -- note that
`enriched_trap_rank` changed too (2->1 for both), even though the trap source's own vector was
never touched. Making the notice more similar to the trap source shifts their *relative* order;
neither document individually became less relevant.

## What this does and does not show

**It shows the diagnosed mechanism supports a concrete, conditional, testable remedy, with the**
**condition itself falsifiable at scale: enrichment should help low-Jaccard notices and should**
**not help (or should hurt) near-maximal ones.** That is a sharper, more useful contribution
than "we tried enrichment and it sometimes worked" -- someone building a medical RAG system, or
extending this benchmark, has a specific, testable rule to check, not just an anecdote.

**This is n=12, generated by testing a hypothesis on the same items that produced it -- the**
**same post-hoc status as ADR-090's mechanism account and ADR-094's correlation.** The r=-0.535
correlation and the stated condition are not claimed as validated. They are reported because
they are the most specific, falsifiable form this project can currently give the finding, and
the two honest exceptions are reported alongside them rather than omitted.

## What this does not touch

**ADR-094's pre-registered n=30 predictions (length r in 0.35-0.55, Jaccard r in 0.45-0.65) are**
**unchanged by this result and must stay unchanged.** This intervention test does not bear on
those numbers directly, and even if it did, revising a pre-registered prediction in response to
a new, favorable-looking result is exactly the discipline lapse ADR-080 already named and
corrected once. The numbers stand as originally recorded.
