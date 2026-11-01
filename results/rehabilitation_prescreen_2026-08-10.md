# Rehabilitation/Therapy pre-screen, 2026-08-10

Prompted by the author having lost time on three earlier candidates that turned out
unusable only after opening the file. Requested: pre-screen Rehabilitation-only candidates
harder than usual before handing any over -- confirm the abstract still exists, confirm the
retraction notice is reachable, confirm the eligibility source is actually readable rather
than paywalled -- and report what fraction survive.

## Pool

89 candidate rows are tagged Rehabilitation/Therapy in the raw candidate CSV (unique within
that domain slice -- a record can only appear once per domain tag, per ADR-066). Excluding
the 4 record_ids already used or rejected under this domain (5684→item3, 5685→item6/
rejected, 6414→item7, plus any already used under a cross-listed domain), **73 Rehabilitation
candidates remain eligible.** Drawn via the balanced work queue restricted to this domain
only (author-cluster caps still applied).

**A domain-purity caveat worth stating up front, separate from the three technical checks
requested:** PubMed's "Rehabilitation" MeSH heading is administratively broad (already noted
in ADR-025), and this pool reflects that -- candidates drawn include cancer immunotherapy
xenograft studies, dental bone-graft rabbit models, thyroid cancer genetics, and hepatitis B
antiviral cohort studies, alongside genuinely rehab/physical-therapy-flavored topics (balance
assessment, spinal fusion, neuromodulation). A candidate can pass all three technical checks
below and still not be substantively "about" rehabilitation in the way a reader would expect
from the domain label. Not screened out on this basis (the author's three criteria were
technical, not topical), but flagged, since it bears on whether a Rehabilitation item's
retrieval behavior will actually reflect that domain's corpus, or largely reflect whatever
adjacent domain the paper's real subject matter belongs to.

## Method: three checks, applied in cheapest-first order

1. **Abstract exists and is intact** -- fetched each candidate's own PubMed record, applied
   the same validated classifier from `results/abstract_overwrite_measurement.md`
   (`original_retained` vs `replaced_by_retraction_text` vs `no_abstract`). Cheap, batchable.
2. **Retraction notice reachable** -- confirmed the notice PMID exists and resolves via
   PubMed EFetch. A small number of records have `retraction_pubmed_id = "0"` in Retraction
   Watch's own data (no notice PMID recorded at all) -- an immediate fail, distinct from a
   notice that exists but is bare/uninformative (which passes this check; informativeness is
   a separate, later judgment, `notice_specificity`).
3. **Eligibility source actually readable, not paywalled** -- for every candidate surviving
   1-2, ran a real search for current institutional evidence and attempted to read the best
   candidate source directly (not just a search-engine summary). The expensive step, done
   last, only on survivors of the cheap checks.

## Result: 30 candidates fully screened, 1 fully passed

| Stage | Pass | Drawn | Rate |
|---|---|---|---|
| 1. Abstract intact | 22 | 30 | 73% |
| 2. Notice reachable (of stage-1 passers) | 19 | 22 | 86% |
| 3. Eligibility source readable (of the 11 stage-2 passers actually checked) | 1 | 11 | 9% |

**Overall: 1 fully-passing candidate out of 30 drawn (≈3%), and out of the 19 that cleared
the first two (cheap) checks, only 11 were checked for eligibility within this pass's search
budget -- of those 11, 1 passed.** Not every stage-2 survivor was checked for eligibility
(9 remain unchecked); the ~9% eligibility-conditional pass rate among those checked is the
most defensible per-candidate estimate, and it is low enough that extrapolating it across
the full 73-candidate pool suggests perhaps 6-7 total candidates in the entire remaining
Rehabilitation pool would survive all three checks -- not confirmed, an extrapolation from a
15-candidate eligibility sample, stated as such.

**The eligibility-source check is the dominant filter, not the abstract or notice checks.**
Most Rehabilitation-tagged candidates that had an intact abstract and a reachable notice
still failed because no current, freely-readable institutional source could be found for
their specific claim within a reasonable per-candidate search budget (roughly comparable to
ANNOTATION.md section 3.2's existing 30-minute-per-candidate cap) -- either no systematic
review/guideline exists yet for that specific narrow question, or one exists but is
paywalled (Wiley, Taylor & Francis) with no open-access route found, or is nominally free
(NICE guidance) but blocked to direct fetching by anti-bot protections.

## The one full pass

**Record 20361** (Choi et al., "Risk of Hepatocellular Carcinoma in Patients Treated With
Entecavir vs Tenofovir for Chronic Hepatitis B," JAMA Oncology 2018, retracted-and-replaced
2019) -- full raw material prepared: `results/item17_raw_material.md`. Two structural
wrinkles disclosed there in full: (1) a PubMed-tag verification gap, handled per the project protocol
section 4's documented-discrepancy pathway, consistent with the ~8% gap rate already
measured pool-wide (ADR-028/030/066); (2) this is a "Retract and Replace" case with a
same-author corrected replacement paper, not a plain void retraction -- a shape this
benchmark hasn't had before and needs a deliberate annotator decision about which current
source the gold claim should rest on.

## Candidates checked and their failure point, for the record

| Record | Stage failed | Note |
|---|---|---|
| 8140 | Abstract (no_abstract) | |
| 8610 | Abstract (replaced) | Elsevier withdrawal boilerplate |
| 16669 | Notice (no notice PMID in RW data) | |
| 17937 | Eligibility | SNS/OAB systematic review paywalled (Taylor & Francis); NICE guidance blocked by anti-bot protection, not independently confirmed readable |
| 18004 | Abstract (replaced) | |
| 18060 | Eligibility | No systematic review/guideline found; only single-center retrospective studies |
| 18264 | Eligibility | No directly on-topic systematic review found (a veterinary-population review was the closest match, not a clean fit) |
| 18266 | Eligibility | No directly on-topic systematic review found |
| 18954 | Abstract (replaced) | |
| 20069 | Not checked (eligibility) | Also a likely structural mismatch: psychometric scale-validation study, not a treatment-efficacy claim |
| 20126 | Eligibility | No directly on-topic systematic review found |
| 20130 | Abstract (no_abstract) | |
| 20253 | Abstract (no_abstract) | |
| 20302 | Eligibility | On-topic 2023 review (Kishi et al.) found but paywalled, no OA route found |
| **20361** | **PASS** | **See above** |
| 20385 | Eligibility | No systematic review specifically on dexamethasone-and-fusion-outcomes found |
| 20570/20571 | Eligibility, also likely a scope problem | CD137/cetuximab paper is itself a **xenotransplant (mouse model) study**, not a clinical claim -- similar to item 13's rejection; would need rejecting on scope grounds even if a source existed |
| 20767 | Abstract (no_abstract) | |
| 20849 | Not checked (eligibility) | |
| 21065 | Eligibility, also a likely structural mismatch | On-topic systematic review found (balance measures after stroke) but for a different population (stroke vs. this paper's lower-limb amputation) than the retracted paper; also itself a reliability/psychometric study, not a treatment-efficacy claim |
| 21127 | Abstract (replaced) | |
| 21545 | Not checked (eligibility) | |
| 22856 | Eligibility | Related sildenafil/fetal-growth-restriction Cochrane review found but for a different indication (FGR, not oligohydramnios specifically); no clean match |
| 22892 | Eligibility | No systematic review specifically on CTLA-4 polymorphism and RAI efficacy found |
| 23160 | Notice (no notice PMID in RW data) | |
| 24292 | Notice (no notice PMID in RW data) | |
| 25058 | Not checked (eligibility) | |
| 26494 | Not checked (eligibility) | |
| 28623 | Not checked (eligibility) | Same record as item-14-adjacent TBCRC026 breast cancer trial, already seen cross-listed in ADR-066's duplicate investigation |

## What this means, stated plainly

**The survival rate is low, as the author anticipated it might be.** This is not simply
"Rehabilitation has a 27-fold larger corpus" (ADR-047's original concern) -- it may also be
harder to find genuinely current, openly-readable, on-topic institutional evidence for
Rehabilitation-tagged candidates specifically, at least in this sample. Two candidate
explanations, not distinguished by this pass as first written: (a) the domain-purity issue
above -- many "Rehabilitation" candidates are actually about oncology, hepatology, or
dentistry topics whose current literature lives in journals this search didn't happen to
find open-access versions of; (b) genuine physical-rehabilitation therapy questions (balance
assessment, neuromodulation, spinal procedures) may have thinner, more fragmented, or more
often paywalled current evidence than pharmacology or Ob/Gyn topics have had so far in this
project. **Addendum below disentangles these by hand-classifying all 30 screened
candidates.**

## Addendum, 2026-08-10: hand classification -- genuine rehabilitation vs. incidentally tagged

Requested to settle which of the two explanations above is doing the work. Method: every one
of the 30 screened candidates' title (and abstract where the title was ambiguous) read by
hand and placed in one of three categories, using the author's own definition --
physiotherapy, exercise, functional recovery -- as the test for "genuine": does the paper's
own core subject concern a rehabilitation-medicine intervention or outcome (physical/
occupational therapy, exercise-based intervention, assistive devices/prosthetics, motor or
functional recovery after injury or disease, physical modalities for pain, cardiopulmonary
or neurorehabilitation)? Classified **before** looking back at which candidates passed or
failed the technical checks, to avoid the classification being shaped by the answer it was
meant to explain.

**Result: 1 of 30 (3.3%) is genuinely about rehabilitation. 2 of 30 (6.7%) are borderline.
27 of 30 (90%) are incidentally tagged** -- their core subject is oncology, pharmacology,
dentistry/material science, obstetrics, endocrine surgery, or vascular intervention, with no
rehabilitation-medicine framing at all.

| Category | n | Records |
|---|---|---|
| Genuine | 1 | 21065 (test-retest reliability of dynamic balance measures in lower-limb amputees) |
| Borderline | 2 | 16669 (peripheral neuromodulation for sacroiliac joint pain -- a device/interventional-pain study, arguably within physiatry's scope but not physiotherapy or exercise); 24292 (neural therapy, a complementary-medicine injection technique, for post-surgical discomfort -- not physiotherapy or exercise either) |
| Incidental | 27 | Oncology (8140-adjacent shoulder surgery is orthopedic, not oncologic, but still not rehab; 20253, 20570, 20571, 20767, 21545, 22892, 25058, 28623 -- cancer biology/therapy); Pharmacology/cardiology (18004, 20126, 20302, 23160, 26494); Obstetrics/gynecology (21127, 22856); Dentistry/material science (18264, 18266); Hepatology (**20361, the one eligibility pass**); Endocrine surgery (20849); Hand surgery (20130); Vascular intervention (18060); Urology (17937); Regenerative medicine (8610); Nephrology psychometrics (20069); Spine surgery pharmacology (20385); Behavioral/endocrine (18954) |

**Eligibility rate split by category** (of candidates that reached the eligibility-check
stage -- most borderline/genuine candidates didn't, for reasons below):

| Category | Reached eligibility check | Passed |
|---|---|---|
| Genuine (n=1) | 1 | 0 |
| Borderline (n=2) | 0 -- both failed earlier, at the notice-reachability check (no notice PMID recorded at all) | -- |
| Incidental (n=27) | 10 | 1 (10%) |

**This does not cleanly confirm either hypothesis, and does not support extrapolating an
"eligibility rate for genuine rehabilitation research" at all -- there is only one genuine
data point.** That one candidate (21065) did reach the eligibility check and failed it (the
closest current source found was a systematic review of balance measures after *stroke*,
not lower-limb *amputation* -- a population mismatch -- and 21065 is itself a psychometric
reliability study rather than a treatment-efficacy trial, a structural mismatch independent
of the population one). That single failure is consistent with the author's second
hypothesis but proves nothing at n=1.

**What the classification does establish cleanly: the domain-tagging problem is real and
large, exactly the shape ADR-025 warned about, now measured rather than asserted.** 90% of
candidates drawn under the Rehabilitation/Therapy MeSH tag are not substantively about
rehabilitation. The overall ~9% eligibility-pass rate reported above is therefore mostly a
measurement of how well-served a grab-bag of oncology, pharmacology, and dentistry topics
(that happen to carry a Rehabilitation MeSH tag) are by current synthesis -- not a
measurement of how well-served *rehabilitation research specifically* is. Testing the
author's second hypothesis properly would need a sample with many more genuine-rehabilitation
candidates than this MeSH-tag-based draw produced -- which is itself informative: at this
draw rate (1 genuine in 30), reaching even 10 genuine candidates to test the hypothesis
properly would need drawing on the order of 300 candidates, well beyond the 73 currently
eligible in this domain's queue.
