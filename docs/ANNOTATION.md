# Annotation Protocol

> **Annotation closed 2026-08-20 at 28 items (ADR-126)**, below the project protocol's originally-stated
> 50-item floor — that floor was written for a larger-scoped benchmark before the arXiv deadline
> moved from November to mid-September 2026 and the annotation window closed early as a direct
> consequence. Say so plainly in the paper; this document is the full protocol that was applied
> consistently to all 28 items, not a target that was fallen short of quietly. Items 37-39 are
> fully researched and deferred, not rejected (`data/benchmark/deferred_candidates.jsonl`).

## 1. Purpose and scope

What counts as an annotation pass, and what it certifies.

## 2. Annotator qualifications and roles

Who annotates, what background is required, how `annotator_id` values map to real people.

## 3. Item selection criteria

### 3.1 Candidate pool (reason screen)

Candidates are pre-filtered by `config/vocabularies/reason_screen.yaml` into tiers (see `src/retraction_bench/curate/reason_screen.py` and `docs/DECISIONS.md`). **The screen is a heuristic pre-filter, not a determination.** It narrows which retractions are worth an annotator's time; it never decides whether a claim was actually invalidated.

- **Tier 1 (clean):** carries at least one `claim_invalidating` reason tag, no `process_only` tag, no `ambiguous` tag. Annotated first.
- **Tier 2 (duplication):** otherwise tier 1, but the only ambiguous tag(s) present are image/data duplication (`Duplication of/in Image`, `Duplication of Data`, `Euphemisms for Duplication`). A deliberate second wave, not a discard pile — see the ADR for why this is expected to be annotation-productive.
- **Tier 3 (other ambiguous):** everything else that clears the claim_invalidating/no-process_only bar. Not currently in scope for annotation.

### 3.1.1 Claim-type screen (upstream of domain and tier)

Before domain ranking, candidates are also screened by `config/vocabularies/claim_type_screen.yaml` (see `src/retraction_bench/curate/claim_type_screen.py`) into `clinical_intervention`, `clinical_observational`, `preclinical`, or `unclear`, based on title and Retraction Watch's `ArticleType`. **Same heuristic-not-ground-truth discipline as the reason screen.** This exists because raw retraction volume in a clinical specialty is a poor proxy for how many *clinically consequential* retractions it contains — a subject can be inflated by a preclinical mechanism-paper genre (e.g. in-vitro miRNA/signaling-pathway studies) that shares subject tags with clinical research but makes no claim a guideline or systematic review would ever address. See `docs/DECISIONS.md` ADR-020 and ADR-021.

**The screen's label is never inherited into the annotated item.** `schemas.BenchmarkItem.claim_type` is a separate, human-annotated field, set during annotation from the actual paper, not copied from `curate/candidates.py`'s `claim_type_screen_label` column. The screen's own validation (`results/claim_type_screen_validation.md`) shows this pair is its weakest axis: among the 68 hand-labelled items the screen passed as clinical, it defaulted to `clinical_observational` for 13 that were actually `clinical_intervention` (head-to-head drug comparisons misread as observational — "pattern A" in the validation notes) and never made the reverse error. This does not affect eligibility (both classes pass the filter), but it means the screen's label cannot be trusted as the item's claim_type. See `docs/DECISIONS.md` ADR-030.

### 3.1.2 Author-cluster cap (sampling independence)

A large share of the candidate pool traces to a small number of repeat authors, some of them well-documented serial fabricators (Joachim Boldt, Yoshitaka Fujii) whose retraction waves are individually famous. Including many items from one author risks the benchmark measuring whether a model recognises a specific scandal rather than whether it tracks evidence currency generally. **No more than 2 items in the benchmark may share a common author** (checked against every individual name in Retraction Watch's semicolon-separated `Author` field, not just first/last authors) -- a fixed cap per author regardless of the benchmark's final size (ADR-037). See `docs/DECISIONS.md` ADR-031 for the measured cluster sizes and the reasoning for the cap value.

**Author-*group* cap (ADR-070), on top of the per-individual-author cap above.** Two candidate records that share a *majority* of their authors count as a single unit against the cap, even when the per-individual-author count alone would allow both. Operationalized as: `|A ∩ B| / min(|A|, |B|) > 0.5`, i.e. more than half of the smaller record's author list overlaps the other's. Caught in practice when two 2016 ECT-for-schizophrenia meta-analyses from the same core team (8 of 11 authors shared) would each have individually sat exactly at the per-author cap of 2 -- satisfying the letter of the rule while still concentrating two items in one research team. When this triggers, keep the more informative item (e.g. the one whose current-evidence direction is contradictory rather than merely narrowing, the harder test) and reject the other with reason "author-group concentration" (section 3.4), distinct from an eligibility-based rejection.

### 3.3 Balanced work queue (domains proceed in parallel, not sequentially)

The benchmark's size is no longer a fixed target (ADR-037) -- annotation runs until a fixed date and stops wherever it lands. `curate/work_queue.py` (tested) is the required selection mechanism: it always offers the next candidate from whichever domain currently has the fewest committed items, skipping anything already selected, already rejected (section 3.4), or over the author cap (section 3.1.2, checked against everything already committed including candidates queued earlier in the same batch). Candidates are not hand-picked per domain -- doing so risks stopping the annotation window with one domain fully represented and another barely started, which cannot support the per-domain comparison the paper needs. See `docs/DECISIONS.md` ADR-038. Batches for preparation (raw-material files, section 4) are the next N items off this queue.

**Per-batch cluster cap (ADR-041):** the author cap (section 3.1.2) allows up to 2 items per author across the whole benchmark, but a single prepared batch may contain **at most 1 item per author-cluster**, enforced independently by the same function (`max_cluster_authors_per_batch`, default 1, resets every call). Satisfying the standing cap without this stricter per-batch constraint still lets one scandal dominate a given sitting -- batch 1 originally did this (2 of 5 items were Boldt/Hempelmann) before the constraint was added.

**Re-run the retrieval ceiling every 5 annotated items (ADR-049).** `corpus/retrieval_ceiling.py` against the frozen corpus index is not a one-time step run once at the end of annotation -- re-run it after every 5 newly annotated items land, so the notice-vs-trap-source rank-gap distribution (ADR-049) and the domain-imbalance question (ADR-047) both stay measured quantities throughout the annotation window, with real statistical weight by the time either is needed for the paper, rather than a single point estimate computed under time pressure in October.

### 3.2 Eligibility: gold claim must trace to an institutional source

A candidate is eligible for annotation **only if** an institutional post-retraction source can be located that speaks to the trap claim: a systematic review or meta-analysis published after the retraction, a clinical practice guideline (e.g. NCCN, ESMO, ESC, WHO, NICE — whichever governs the domain), a Cochrane review, or a regulatory agency statement. The gold claim is never the annotator's own clinical judgment; it is what one of these sources says, transcribed and cited via `Evidence.source_authority`.

**Regulatory agency statements are the expected route, not a fallback, for adverse-event and safety-signal retractions** (e.g. a case report of a drug-associated adverse event) — a guideline or systematic review is unlikely to exist for a single safety signal, but an FDA/EMA (or equivalent) communication often does. Do not reject an item of this kind merely because no guideline covers it; check the regulatory route before rejecting. This does not relax the standard — a regulatory statement is still an institutional source, transcribed and cited the same way (`Evidence.source_authority = regulatory_agency`), never the annotator's own safety assessment.

**A national statistics body or survey programme is the expected route, not a fallback, for epidemiological claims** (prevalence, incidence, mortality rates and similar population-level descriptive statistics, ADR-073) — no guideline body issues a "guideline" on a national mortality rate, and no systematic review synthesizes a single country's household survey the way a review synthesizes RCTs. A national statistics office or a survey programme (e.g. DHS, Demographic and Health Surveys) is the authoritative source for this claim type — primary data, not a synthesis, and still eligible under this section on that basis. Cite via `Evidence.source_authority = national_statistics_body`, distinct from `primary_study` (a single research study) and `regulatory_agency` (a body regulating a product/practice). Do not reject an epidemiological candidate merely because no guideline/review covers it — check this route first.

**If no such source can be found, the candidate is rejected, not weakened.** Do not fall back to a primary study or the annotator's own reasoning to manufacture a gold claim. Log the rejection (see 3.4) and move to the next candidate.

**Independence must be checked before a source is used, not after a gold claim is drafted (ADR-058/076).** Confirm the candidate evidence source's own reference list or included-studies table does not include the retracted paper before treating it as eligible -- a source can be perfectly readable and directly on-topic and still fail this, if its own analysis has absorbed the retracted paper's data. This check belongs in the eligibility pass itself, as a required step before a source counts as "found," not deferred to drafting time: an item nearly went to draft on a source that had pooled the retracted paper's own data directly, caught only because the check happened to run before the claim was finalized. Running it this early costs real time and will lower the yield of the eligibility search below what a three-check pass would find — accepted deliberately, since the alternative is finding out at drafting time instead, which is more expensive, not less.

**For "Retract and Replace" items (`replacement_exists = true`, ADR-069), full evidential independence may be unverifiable in principle, not just in practice.** A later independent synthesis will legitimately include the corrected replacement in its own pooled analysis; from outside that synthesis's own methods, whether it drew on the original void version or the replacement cannot always be disambiguated. Treat unresolvable version-provenance the same as a failed independence check — exclude the source, do not carry it forward with an "independence uncertain" caveat. For this item class, prefer the replacement itself as the current-evidence source over searching for third-party synthesis: the item is testing whether the replacement is cited over the original, not whether independent confirmation exists.

**The eligibility search is capped at 30 minutes per candidate.** If no institutional source is found within that window, reject and move on -- do not keep searching. This is a deliberate protocol rule, not a corner cut: it makes per-item annotation cost predictable, and it makes the rejection rate a *measured* quantity (how often 30 minutes of real searching turns up nothing) rather than a function of how long any given session happened to keep looking. Realistic planning figure, measured from item 1 plus the n=30 pilot's 10-15% no-source rate: **45-60 minutes per successful item, including rejection overhead** (`docs/DECISIONS.md` ADR-036, ADR-037).

Items whose gold claim rests only on `Evidence.source_authority = primary_study` or `other` (i.e. eligibility was satisfied by a single primary study rather than a review/guideline/regulatory statement) are a **weaker evidence tier**, reported separately from the main results — see `docs/DECISIONS.md`.

### 3.4 Rejection logging

Every rejected candidate is recorded as a `RejectedCandidate` (schemas.py): DOI, source registry ID, `RejectionReason`, and free-text notes. Rejected candidates are **never discarded** — the rejection rate (how often no institutional correction exists at all) is itself a reportable finding, independent of anything the models under test do. Rejected record_ids feed back into `curate/work_queue.py`'s `rejected` set (section 3.3) so they are never re-offered.

**Distinguish the rejection reason precisely in the free-text notes -- these are separately reportable rates, not one "rejected" bucket (ADR-074).** Four distinct reasons have occurred so far: no institutional source found (section 3.2); author-group concentration (section 3.1.2); redundancy (a near-duplicate of an already-kept item -- same author cluster, same intervention class, same population shape, same structural type -- rejected because it would add repetition, not coverage); and not-a-clinical-claim (a claim-type-screen false positive, e.g. an in-vitro or preclinical study that was never eligible regardless of domain tag). Each says something different about the candidate pool and should be counted separately in the paper.

## 4. Step-by-step annotation procedure

The sequence: reading the original paper, the retraction/supersession notice, and the post-retraction evidence; drafting `trap_claim` and `gold_claim`; recording `post_supersession_evidence`.

**Question style (default, set from item 1; ADR-039): quantitative form.** "How much does X reduce/increase Y?" rather than yes/no ("Is X effective for Y?") or patient-context framing ("A patient presents with... what do you recommend?"). A request for a number pulls retrieval directly toward the specific pooled estimate at risk, and the answer is short enough to score unambiguously. Patient-context questions were tried against item 1's material and rejected as the default: they produce answers too hedged and multi-part to score cleanly. This is the default, not an exclusive rule -- a candidate item may still call for a different form if the quantitative phrasing doesn't fit the claim; departures should be noted.

**Question neutrality (ADR-061/062) -- the operative test.** "Presupposes something" is too broad to apply consistently: nearly every well-formed question presupposes *some* framing (asking about efficacy presupposes the question is about efficacy). The test that actually distinguishes a leading question from a normal one: **does the question presuppose a *specific direction or magnitude* of the finding, or only the *topic* the finding is about?** "How much does X reduce Y?" presupposes a direction (a reduction) -- if the trap claim also asserts a reduction, the question already agrees with it before any evidence is retrieved, and the model is being pushed toward the trap claim's own conclusion. "How effective is X?" presupposes only that the question concerns X's effectiveness -- not which way the answer points, and it is how the question would actually be asked in practice (a clinician does not know in advance whether a treatment helps, only that they want to know whether it does). The first is leading; the second is normal and does not need revision.

Prefer directionless framing where a magnitude is being asked about: "How does X compare with Y for Z?" / "What effect does X have on Y?" / "How did Z change after W?" -- specific and quantitative in the sense ADR-039 wants (a request for a number or a comparison, not vague), but without embedding which way the number points. **This qualifies ADR-039's own worked example**, which is itself phrased in the presupposing form ("How much does X reduce/increase Y?") -- that example predates this rule and should not be copied verbatim into new items; use the neutral pattern above instead.

Caught while drafting item 5/RB-0004: a first-draft question ("how much more effective is ramosetron") baked in the trap claim's own conclusion before any evidence was cited; the revised, neutral form ("how does ramosetron compare with granisetron") does not. RB-0001 and RB-0003 were later revised for the same reason ("reduce"/"decline" -> "what effect does... have"/"how did... change"); RB-0002's "how effective is..." was left as-is under the operative test above -- it presupposes only the topic, not a direction.

**A revised question invalidates the item's stored retrieval-ceiling rank.** The retrieval-ceiling measurement (`corpus/retrieval_ceiling.py`) embeds the question text itself as the query -- changing the question changes what gets retrieved and re-ranked, so any prior `trap_source_rank`/`notice_rank` recorded for that item in `results/retrieval_ceiling_report.json` is stale the moment the question changes, even if nothing else about the item was touched. **Re-run the retrieval-ceiling measurement for any item whose question is revised, not just for newly annotated items** -- a future session that revises a question and moves on without re-measuring will leave a stale, silently-wrong rank sitting in the report.

**Raw-material preparation (per item, batches of `curate/work_queue.py`'s next N):** each item gets one markdown file, prepared exactly like `results/item1_raw_material.md` -- the retracted source's abstract, the notice text verbatim, and the eligibility search results (or a logged rejection). Everything through that point is prepared without the annotator; `trap_claim`, `gold_claim`, and the question are the three things only the annotator writes, timed (ADR-036).

**Hard rule (ADR-040): claim text is authored by the annotator directly, never reconstructed.** `trap_claim.text` and `gold_claim.text` must be written by the annotator, in their own words, from the raw-material file -- not drafted by an assistant from conversation and handed over for light editing, even when every fact in that draft is correctly sourced. A claim assembled from discussion is machine-drafted in substance regardless of factual accuracy, because the wording and judgment of what to include is not the annotator's. Raw-material files never contain draft claim text; they stop at source material and eligibility results. An item cannot move from `provenance: draft` to `verified` until the annotator has written `trap_claim` and `gold_claim` themselves.

**Notice verification standard (ADR-042):** `notice_specificity` may only be annotated from notice text confirmed against a primary or authoritative source -- the publisher directly, PubMed's own record, or a full-text repository. A secondhand quote (e.g. a third party's blog reporting what a notice says) does not qualify, no matter how reliable that third party generally is. If the primary text cannot be reached, set `notice_text_verified = false` and `notice_specificity = unverifiable` -- schema-enforced to always agree with each other. This is a fourth, informative outcome for ADR-033's eventual distribution, not a gap to paper over by guessing a level from an unconfirmed quote.

**Categorical-vs-specific boundary rule (ADR-072):** a notice is `specific` only if it names *which* data, analysis, or study was the problem; a notice that names *what kind* of problem occurred (data inconsistency, image manipulation, analytical error) without saying which specific data/analysis/study is `categorical`, even if the category is named precisely and even if it includes qualifying detail (e.g. that the concern is about magnitude of effect rather than direction). This is the operative test, not a case-by-case judgment call.

**Check for a separate notice document before assuming one exists (ADR-071).** Some Retraction Watch records have `retraction_pubmed_id`/`retraction_doi` identical to the *original* paper's -- there is no separate PubMed record for the notice at all, only (sometimes) a retitled original record visible to Crossref but not to PubMed's own metadata. Measured at ~1.7% of the candidate pool. When this is the case, the item cannot support the `retrieval_with_notice` experimental condition -- note this explicitly in the raw-material file and the item's annotation notes; it is a different, fourth variant of ADR-065's "content unreachable" pattern (notice unreadable / notice uninformative / claim erased / no separate notice document at all).

**Fields annotated by hand per item, independent of any upstream screen or registry tag:**
- `claim_type` (`clinical_intervention` / `clinical_observational`) -- never inherited from `curate/candidates.py`'s `claim_type_screen_label` (ADR-030).
- `evidence_level` (`primary_study` / `synthesis`) -- was the superseded source itself a primary study or a synthesis of other studies; stratification variable for the pre-registered prediction in ADR-032.
- `notice_specificity` (`specific` / `categorical` / `bare` / `unverifiable`) -- how informative the notice text itself is about the mechanism, read from the notice directly, not from Retraction Watch's `supersession_reasons` tags, which may be more specific than the notice they were derived from (ADR-033). Once 20 items are annotated, report the distribution and how often RW's tags outrun the notice's own specificity.
- `notice_text_verified` -- paired with `notice_specificity`, per the verification standard above.
- `item_type` (`superseded_with_current_answer` / `superseded_without_current_answer`, ADR-043) -- see below.
- `no_answer_reason` (`no_adjacent_evidence` / `adjacent_evidence_exists`, ADR-060/063) -- required iff `item_type = superseded_without_current_answer`, `None` otherwise (schema-enforced). Two different capabilities a model can fail at: `no_adjacent_evidence` means nothing authoritative addresses the topic at all (the Fujii-type case, RB-0004); `adjacent_evidence_exists` means authoritative evidence exists and addresses the underlying clinical decision but not the specific question asked (RB-0003: NCCN addresses the treatment decision, not the retracted paper's practice-pattern question). Start with these two values; add a new one only when an item genuinely doesn't fit either, not speculatively.
- `claim_polarity` (`positive` / `negative`, ADR-057) -- does the trap claim assert an effect, or assert *no* effect beyond placebo/no difference? Read from the retracted source's own conclusion, not inferred from the notice or from what current evidence says. A retracted negative finding relied on by a model wrongly discourages a treatment -- a distinct clinical harm from a retracted positive finding wrongly recommending one, not a variant of the same failure. Results are stratified by this, never pooled across it.
- `replacement_exists` (bool, ADR-069) -- does a formal, citable corrected replacement of the superseded source exist (a publisher "Retraction and Replacement," not a plain void retraction)? Check the notice/publisher record directly, don't infer from `supersession_reasons` alone. This marks a distinct failure shape from an ordinary retraction: the correct answer isn't "the evidence is void," it's "cite the replacement, not the original" -- a model that cites the withdrawn version when a corrected one exists fails differently than one citing a retraction with nothing to replace it. If `true`, identify the replacement citation directly from the notice text itself where possible, not by inference from author-list matching alone (item 17/RB-0005's raw material found a plausible replacement this way but flagged it as not yet primary-source-confirmed).

**Gold-claim scoping rule (ADR-034):** the gold claim documents what the notice states and what current evidence says. It never reconstructs an error mechanism the notice doesn't state -- doing so would fabricate provenance on the error-mechanism side the same way inferring retraction status without checking would fabricate it on the status side (the project protocol). This restriction applies to items with a `categorical`, `bare`, or `unverifiable` notice; a `specific`, verified notice's stated mechanism may be cited directly, since it is then documented.

**The operative boundary (ADR-091, sharpened ADR-093): gold claims may describe properties of**
**the evidence, including its independence from prior work, but must never describe how this**
**project established those properties.** "Independence from the retracted paper" is a property
of the evidence, exactly like its publication date, its sample size, or its study design --
ordinary evidence-based-medicine writing describes a synthesis as "an independent
meta-analysis" or "an independent replication" the same way it would call a study
"multicentre" or "double-blind," and that is a legitimate word choice, not a leak, because it
is a fact about the evidence a knowledgeable current source could equally well state. What may
never appear in claim text is a description of *this project's own verification act* -- that a
reference list was read, that a check was run, that a search came back negative. The test:
**would the sentence still make sense if this benchmark had never been built and someone else**
**were simply describing the study?** "An independent meta-analysis found X" passes -- it is
how any clinician would describe that study. "We checked the reference list and confirmed
independence" fails -- there is no "we" in a clinical answer, only in an annotation process.
`independence_verified` and its accompanying `Evidence.note` are where the *fact that, and
how,* independence was checked belongs, always, in every item, never in the claim text.

Caught while drafting item 21/RB-0013: a first draft stated "the review does not cite the
retracted study, and independence was verified from the reference list" directly in the gold
claim -- removed before recording, with the verification fact and method moved to
`independence_verified=true` and the `Evidence.note` instead. Checked against all prior items
against this exact boundary (ADR-093): three items (RB-0001, RB-0010, RB-0011) describe a
synthesis as "independent" -- each passes the test above (a property of the evidence, stated
the way a clinician would state it, no reference to this project's own checking process) and
was left as recorded, not treated as an instance of the leak.

**Second worked example, caught by the annotator rather than the assistant (ADR-115):** a first
draft of RB-0022/item30's gold claim included a sentence describing the evidence source's
reference list and its inclusion of a different, non-retracted study by the same two authors as
the retracted trial. Removed before recording, with the same reasoning applied independently:
"that is provenance about our verification, not clinical evidence." The detail is preserved in
full in `Evidence.note`.

**Third worked example (ADR-117), and the sharpest illustration yet of what the boundary is**
**actually testing: a sentence correctly kept in, not removed.** RB-0025/item31's gold claim
states, verbatim from its evidence source's own published text, that the Cochrane review
"explicitly excluded the retracted trial because it did not pass its research-integrity check
following the published retraction." This is not a leak -- **the boundary was never "no mention
of verification or exclusion," it was always "no narration of *this project's own* verification
act."** RB-0013 and RB-0022's removed sentences described what *this project* did (checked a
reference list, found or didn't find a citation) -- that fails the operative test. The Cochrane
statement describes what *the evidence source itself* says about its own methodology, in text a
clinician would encounter directly -- it passes the same test cleanly. Read all three examples
together, not just the two removals, or the rule will be misremembered as broader than it is.

Three worked examples now stand: two removals and one correct inclusion, from two different
annotators (the assistant on RB-0013, the author on RB-0022 and RB-0025) -- worth knowing the
rule is being applied correctly in both directions by whoever is drafting, not only checked
after the fact.

**A watch item, explicitly not a rule (ADR-117):** RB-0025 also surfaced a tension the item_type
boundary rule does not yet have a name for. Its current evidence makes the underlying clinical
question *practically* settled (no clinician would act otherwise) while leaving the retracted
paper's *specific* claim unmeasured (a different population, outcome, and intent than what the
evidence actually covers) -- these are not the same fact, and the rule tracks the second, not
the first. If this shape recurs, it may need a third `ItemType` value rather than being forced
into the existing two. **One case is not enough to generalize a category from. Do not create one
yet** -- record the tension when it appears, and revisit only once a second instance exists.

**A second watch item, a different tension (ADR-120): the rule's outcome can depend on how the**
**question itself is worded, and the annotator controls that wording.** Item36 (lipid profile
and oxidized LDL in preeclampsia) has current evidence that directly replaces four of its five
measured components, but not its fifth and most specific one (oxidized LDL, the paper's own
title-billed finding). Framing the question around oxLDL specifically gives
`superseded_without_current_answer`; framing it around the lipid panel generally gives
`superseded_with_current_answer` -- from the identical evidence base. The rule presumes a single,
well-defined "the question the retracted paper asked," but a multi-outcome paper can be honestly
summarized at more than one level of specificity. The author's resolution for this item: word the
question around whatever the paper's own title advertises, on the reasoning that this is what a
reader (or a model trained on the literature) is most likely to take from the paper. **Not**
**adopted as a standing rule from one case** -- record the tension, watch for a second instance
before generalizing, same discipline as the watch item above.

**Worked near-miss (ADR-044), for calibration:** a draft of item 1's gold claim said "the direction of effect is corroborated, the retracted paper's specific magnitude is not." That sentence is not a fabricated number and not a wrong fact -- it is an *unstated inference*, built by comparing the retracted estimate to the current one and narrating a story about what kind of error occurred, which nothing in the notice supports. This is the hardest version of the rule to enforce because it reads as competent synthesis, not invention. The corrected pattern: state that the retracted estimate should not be cited, state what current sources report as a separate, plain fact, and stop there -- do not draw the comparison for the reader.

**Evidence-strength caveat rule (ADR-052):** if the post-supersession evidence used to write the gold claim states a limitation on its own strength -- calls for RCTs, describes itself as observational, reports wide confidence intervals, notes a small sample -- the gold claim must carry that limitation. A gold claim that states a current figure flatly, when the source of that figure itself hedges, is not correct: it substitutes false confidence for the retracted claim's false currency. This is checked against the evidence source's own stated conclusions/limitations section, not inferred from the annotator's own sense of whether the evidence "feels" strong. Item 1 (RB-0001) predates this rule and was checked against it retroactively -- one of its two sources (Kathopoulis et al. 2022) does hedge and the other's full text could not be verified; see ADR-052 for the finding and ADR-055 for its resolution.

**Attribution rule (ADR-055):** a caveat is always attributed to the specific source that states it, never asserted in the benchmark's own generic voice. When an item has multiple evidence sources and only some of them hedge, the gold claim names which ("one of the two syntheses notes X"), not a blended "the evidence is limited" that implies every source agrees. This extends the gold-claim scoping rule above (ADR-034) -- report what a source says, do not adjudicate or generalize across sources -- to evidence-strength caveats. Before writing a caveat, check the specific source's own conclusions/limitations text directly; if a source's full text is genuinely inaccessible (checked, not merely unchecked -- see ADR-055 for the channels this project checks: Unpaywall, Semantic Scholar, Europe PMC, the publisher directly), say so rather than guessing from the abstract alone or folding it silently into a shared caveat.

**Independence-verification rule (ADR-058):** for every `Evidence` entry, before writing the gold claim from it, confirm the specific figure being cited is not itself traceable back to the retracted paper -- check the evidence source's own reference list or included-studies table where accessible, and confirm the retracted paper does not appear there. This is a real hazard specific to this project's method: a superseding source can inherit a retracted paper's number without saying so, and if that happens unnoticed, the retracted claim ends up inside the benchmark's own gold answer -- exactly the failure this benchmark exists to measure, occurring inside its own annotation process. Set `Evidence.independence_verified` accordingly: `true` only after an actual check finds the retracted source absent from the evidence source's references; `false` if the check either finds it present (do not use that evidence -- pick a different source or reject the item) or if the evidence source's own text could not be reached to check at all (record which reason in the evidence's `note`, and treat this as a limitation to disclose, not a gap to leave silent). There is no default -- every entry states this explicitly.

**Item type (ADR-043):** most items are `superseded_with_current_answer` -- a trap claim voided by retraction, a gold claim supplied by current evidence, like item 1. Occasionally eligibility search finds the opposite: the trap claim is void *and* no current authoritative source addresses the question either (e.g. the institutional source chain is itself broken by retraction, as with a Cochrane review withdrawn for including too many retracted studies). That candidate is `superseded_without_current_answer`, not a rejection -- its gold claim states both facts (prior evidence void; no current authoritative answer exists), never an inference that no answer exists anywhere unsearched. **Do not seek these out deliberately** -- flag them only when eligibility search organically turns one up, so the resulting rate (target ~10-15% of the benchmark) stays measured rather than constructed.

**The item_type boundary rule (ADR-106), the operative test.** Adjacent evidence -- evidence that speaks to the same general topic without directly re-answering the retracted paper's specific question -- is common, and deciding whether it counts as a current answer is not a case-by-case judgment call. Apply this test: **could a clinician act on the current evidence to answer the question the retracted paper asked?**

- **Yes, even with caveats about comparator, population, or study design** -> `superseded_with_current_answer`. State the mismatch explicitly in the gold claim (this is an ordinary application of the evidence-strength caveat and attribution rules above, not a special case).
- **No -- the current evidence answers a different question, however adjacent** -> `superseded_without_current_answer` / `no_answer_reason = adjacent_evidence_exists`.

This rule was formalized after the same boundary was decided ad hoc twice (RB-0003, RB-0015) and, on its third occurrence (item 28), the author asked that a written test replace further case-by-case calls. Applying it immediately caught a real misclassification: RB-0015 (DPP-4 inhibitors vs. sulfonylurea) had been recorded `superseded_with_current_answer` on the strength of evidence that actually compares DPP-4 inhibitors against *any* comparator, not sulfonylurea specifically -- a clinician choosing between those two drug classes cannot extract that comparison from the pooled estimate, so the evidence answers an adjacent question, not the one asked. Reclassified; see ADR-106. Re-checking the rest of the benchmark against the rule found two more with the identical shape -- RB-0005 (HBV seroprevalence in rural, preconception-specific women, superseded by general-population and pregnant-population estimates) and RB-0011 (vortioxetine vs. placebo, superseded by real-world response rates with no placebo arm at all) -- both reclassified the same way; see ADR-107.

**Mandatory pre-recording step (ADR-107), not a suggestion: before any item moves from draft to verified, check whether `gold_claim.text` itself names a scope, population, comparator, or tier mismatch between the trap claim and the evidence.** All three misclassifications found so far (RB-0005, RB-0011, RB-0015) had this exact tell -- the annotator had already written the mismatch into the gold claim in honest prose, before this rule existed to check it against. **If the gold claim contains such a sentence, the item must be explicitly checked against the item_type boundary test above, and the outcome recorded in the item's `Annotation.note`** -- e.g. "checked against the item_type boundary rule: [pass/fail], [one-line reasoning]" -- even when the answer is obviously `superseded_with_current_answer`. Do not assume the caveat is minor just because the evidence is otherwise strong and on-topic; that assumption is exactly what produced all three prior misclassifications. This step is mechanical to apply (the tell is a sentence that is already being written for other reasons -- ADR-052/055's evidence-strength caveat and attribution rules) and costs one extra sentence in the annotation note; skipping it is how the boundary got misjudged three times before the rule existed.

### 4.1 Scoring calibration (`EvaluationResult.calibration`, ADR-052/056)

Scored at evaluation time, not annotation time -- this section lives here because it is judged against the gold claim an annotator wrote, and needs the same discipline as writing one. Three values: `appropriate`, `overconfident` (the model's answer states a finding more firmly than the gold claim's own evidence supports), `underconfident` (the model hedges where the gold claim's evidence is actually solid).

**Judge against the gold claim's own stated strength, never the annotator's personal clinical opinion of how strong the evidence "really" is.** If the gold claim carries an attributed caveat (ADR-055) -- "one of the two syntheses notes X" -- a model answer that states the current figure with no hedge at all is `overconfident`; a model that reproduces the caveat proportionately is `appropriate`. If the gold claim carries no caveat because the evidence is genuinely solid, a model that hedges anyway is `underconfident`. This is a comparison to what is written in the gold claim, not a fresh clinical judgment call about the underlying medicine.

**This is the most subjective field in the annotation scheme.** `correctness` and the retraction-citation check are close to mechanical -- did the answer rely on the superseded source, yes or no. Calibration requires reading tone and hedging language and comparing it to the gold claim's own hedging, which is a judgment call every time. See section 6 for why this makes it the field needing inter-annotator agreement most, and what happens if a second annotator isn't recruited.

## 5. Provenance workflow

How an item moves from `provenance: draft` to `provenance: verified` (the project protocol), and what a verifying annotation pass requires versus a drafting pass.

## 6. Inter-annotator agreement

**Solo-annotated for now.** Every item is annotated by the author alone in the first pass. A clinician collaborator is being recruited to double-annotate a subset later (target ~30, adjusted if the final benchmark size under ADR-037 ends up smaller); **this is planned, not secured.** If no collaborator is found, the benchmark is reported as single-annotated, and the paper says so explicitly rather than implying IAA that wasn't measured. Nothing about the current pipeline forecloses double annotation if a collaborator does join -- `BenchmarkItem.annotations` already supports multiple `Annotation` records per item (see `docs/DECISIONS.md` ADR-009), so a second pass is additive, not a redesign.

Agreement statistic and disagreement-resolution process: not yet decided, deferred until a collaborator is actually in hand -- designing a protocol for an annotator who may not materialize is effort spent on a contingency, not the plan.

**Calibration (section 4.1) needs this more than any other field, flagged now rather than in October.** It is the least mechanical judgment in the whole scheme -- `correctness` is close to a fact check, `calibration` is a reading of tone against a written standard. If a second annotator is not recruited by the time results are written up, `calibration` is reported as single-annotated with that limitation stated plainly in the paper, the same honesty standard the project protocol applies to everything else. This is not a reason to avoid scoring it -- it is a reason to say clearly, if it comes to that, that this specific axis's numbers carry more annotator-dependent uncertainty than the others.

## 7. Recording judgement calls

Pointer to `docs/DATA_NOTES.md` for anomalies encountered during annotation.
