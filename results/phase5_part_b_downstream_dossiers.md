# Phase 5 Part B v2: dossiers for the 12 `rw_derived_only` gap cases

Per author instruction (2026-10-05 round, item 2): re-check every case Part B v2 classified
`rw_derived_only` against PubMed's own text/structured fields, the notice, and the publisher
page, rather than accepting the automated OpenAlex/Crossref-only classification as final. This
produced real reclassifications, reported below with the revised independent lower bound.
Git hash at time of this check: `88309ed802fa074547589613f87f682c55f68c5c` (plus this session's
uncommitted edits).

**Headline result of this re-check: the automated Part B v2 result (17/299 = 5.69%) undercounted**
**independent corroboration and, separately, included one case that is not a real gap at all.**
Revised: **16/298 = 5.37%, Wilson 95% CI [3.33%, 8.54%]**, with an independently-corroborated
lower bound of **11/298 = 3.69%, Wilson 95% CI [2.07%, 6.49%]** -- more than double the
automated-classification lower bound of 1.67% (5/299), because PubMed's own bibliographic
cross-references (`CommentsCorrectionsList`: `Update in`/`Update of`/`Erratum in`) and, in one
case, the notice's own unstructured title text, not just the checked PMID's own `pubtype` field,
often confirm a withdrawal/retraction on a *different, chained* PMID than the one RW's
`original_paper_pubmed_id` points to.

## Method

For each of the 12 cases: (1) re-fetched PubMed's full EFetch XML record (not just the ESummary
used for the automated check) and inspected `CommentsCorrectionsList` for `UpdateIn`/`UpdateOf`/
`ErratumIn`/`RetractionIn` entries; (2) where such an entry existed, fetched the referenced PMID
and checked its own title and `pubtype`; (3) attempted to fetch the publisher's page directly via
its DOI; (4) cross-checked RW's own raw row (`reason`, `retraction_pubmed_id`, `retraction_doi`,
`urls`) for anything the automated check had not used.

## Case-by-case

| PMID | RW title | RW reason | Re-check finding | Revised classification |
|---|---|---|---|---|
| 4827125 | Cello scrotum | Falsification/Fabrication of Data | No `CommentsCorrectionsList` entry. Publisher page (bmj.com) returned HTTP 403, unfetchable. PMC page (PMC1610985) fetched successfully, shows no retraction banner. RW's own `retraction_pubmed_id` is `"0"` (no locatable notice). | **Unchanged: `rw_derived_only`.** (This is the well-known 1974 BMJ hoax letter, publicly confirmed as a hoax by its author in 2008-2009; RW's claim is almost certainly correct, but no independently-fetchable source confirms it here.) |
| **1834920** | A prospective randomized trial on...celecoxib...total knee arthroplasty (the Scott Reuben fraud case) | Criminal Proceedings; Ethical Violations; Falsification/Fabrication of Data | **RW's `original_paper_pubmed_id` (1834920) and `retraction_pubmed_id` (1929981) are both wrong -- truncated by one trailing digit.** Live PubMed search on the RW title string returns the real PMID **18349203** (Reuben SS et al., *Anesth Analg* 2008); its `pubtype` list already includes **`"Retracted Publication"`** -- PubMed correctly tags the real article. The real retraction notice (DOI `10.1213/01.ane.0000346785.39457.f4`, matching RW's `retraction_doi` field exactly) resolves to PMID **19299812**, not RW's `retraction_pubmed_id` 1929981 (also a truncated/dropped-digit value). PMID 1834920 itself is an unrelated 1991 *Methods in Cell Biology* paper on *E. coli* protein translocation -- not retracted, not by Reuben, not on this topic at all. | **Reclassified: not a gap case. Excluded from the denominator entirely** (same treatment as a notice/mix-up case) -- checking PubMed tag status on PMID 1834920 was never a valid test, since that is not the retracted article. The real article (18349203) is correctly tagged by PubMed, so this case, properly checked, is not evidence of *any* PubMed tagging failure. |
| **16625614** | Music for pain relief (Pub 2) | Notice - Limited or No Information; Removed | PubMed's own `CommentsCorrectionsList` on PMID 16625614 carries an `Update in` entry to PMID **24163271**. Fetched live, full notice text: title **"WITHDRAWN: Music for pain relief."** **Stated reason (the notice's own text, not RW's): purely administrative --** *"the PaPaS Review Group withdrew the 2011 protocol... as there were significant delays in preparing the full review, which did not meet the expectations of Cochrane and PaPaS editorial processes and timelines."* No data-integrity, fraud, or error language anywhere in the notice. | **Reclassified: `independent_evidence` (broad tier only -- see Independence, two ways, below).** PubMed's own title text on the chained successor record confirms a withdrawal occurred, independent of RW/OpenAlex/Crossref, but the notice's own stated reason is a timeline/process issue, not the kind of data-integrity event "retraction" usually implies -- disclosed verbatim, not smoothed over. |
| **10796371** | Lidocaine-prilocaine cream for analgesia during circumcision (Cochrane) | Removed | `CommentsCorrectionsList` `Update in` -> PMID **25840001**, title **"WITHDRAWN: Lidocaine-prilocaine cream for analgesia during circumcision in newborn boys."** **Stated reason (notice's own text): administrative consolidation --** *"The authors have requested this review to be withdrawn. The reason is the intervention...is covered in the Cochrane Review of 'Pain relief for neonatal circumcision'."* Again, no data-integrity language. | **Reclassified: `independent_evidence` (broad tier only).** Same caveat as above: confirms a withdrawal occurred; the stated reason is that the topic is now covered by a different review, not an error/integrity finding. |
| **11279736** | Topical negative pressure for treating chronic wounds (Cochrane) | Retract and Replace | `CommentsCorrectionsList` `Update in` -> PMID **26059170** (RW's own `retraction_pubmed_id`, not PubMed's immediate next-version PMID 18646080), title **"WITHDRAWN: Topical negative pressure for treating chronic wounds."** **Stated reason (notice's own text): administrative restructuring --** *"This review has been split into three reviews each addressing a single wound type... The original parent review...is being withdrawn."* No data-integrity language. | **Reclassified: `independent_evidence` (broad tier only).** Confirms a withdrawal occurred, consistent with RW's own "Retract and Replace" reason code (the split reviews are the replacements); the mechanism is editorial restructuring, not a correction of an error in the original. |
| **25069726** | Therapeutic touch for healing acute wounds (Pub 3) | Concerns/Issues about Data; Unreliable Data | `CommentsCorrectionsList` chain: `Update of` PMID 22696330 (pub2), `Update in` PMID 27140910 (pub4). RW's own `retraction_pubmed_id` points further down the chain to PMID **27581995** (pub6): title **"WITHDRAWN: Therapeutic touch for healing acute wounds,"** `pubtype` includes **`"Retracted Publication"`** itself. **Stated reason: not found.** PMID 27581995's own PubMed record carries no withdrawal-reason text anywhere (its "abstract" is just the original review's unchanged background/methods/results); a live fetch of the Cochrane Library page itself (`cochranelibrary.com`) returned HTTP 403, unfetchable. RW's own reason field (data concerns, unreliable data) is the only reason text available for this case, and it is not independently corroborated by any fetchable notice text. | **Reclassified: `independent_evidence` (broad tier only)** -- the strongest case structurally (PubMed's own structured `Retracted Publication` tag on the chained PMID, not just "WITHDRAWN:" title text), but the *reason* RW gives is still uncorroborated; also the coincidental PMID that overlaps Part A's curated pool (ANALYSIS_LOG 5.20). |
| 10905393 | Bilateral ovarian steroid cell tumor... | Informed/Patient Consent - None/Withdrawn | No `CommentsCorrectionsList` entry. Publisher page (degruyterbrill.com) returned HTTP 405 on direct fetch; redirect chain did not resolve to fetchable content. RW's `retraction_pubmed_id` is `"0"`. | **Unchanged: `rw_derived_only`.** |
| **29561487** | Anterior Maxillary Segmental Distraction Osteogenesis... | Concerns/Issues about Data and Results | No `CommentsCorrectionsList` entry on 29561487 itself, but RW's own `retraction_pubmed_id` (30439738) was followed up live: its PubMed title is **"Anterior Maxillary Segmental Distraction Osteogenesis...: Retraction."** **Stated reason: not found beyond the title itself** -- the notice record has no abstract text; its `pubtype` list, oddly, still only shows `["Journal Article"]`, not `"Retraction of Publication"` (a further, separate structured-tag gap on the notice's own record, not just the original's). Publisher page (journals.lww.com) returned HTTP 402 Payment Required. | **Reclassified: `independent_evidence` (both tiers -- see below)** -- this is the one upgrade that is *not* only a `CommentsCorrectionsList` hop: the title itself, on a PMID directly reachable from RW's own `retraction_pubmed_id`, states "Retraction" in PubMed's unstructured text, the same rule already used for the curated pool (S1.6.1) and the original Part B automated pass. |
| 10638886 | Abnormal Bone and Calcium Metabolism in Patients After Stroke | Cites Retracted Work; Misconduct - Official Investigation(s) | No `CommentsCorrectionsList` entry. This is one of the Yoshihiro Sato mass-retraction cases (RW's own notice-search URL points to `?s=yoshihiro+sato`); RW's `retraction_pubmed_id` is `"0"`. Publisher page (Elsevier, linkinghub redirect) did not resolve to fetchable content. | **Unchanged: `rw_derived_only`.** |
| **30383461** | Radicalisation and mental health | Duplication of Content through Error by Journal/Publisher | `CommentsCorrectionsList` `Erratum in` -> PMID **34057018**, title **"Notice of duplicate publication: Conference proceedings of the 4th Masterclass Psychiatry..."**, `pubtype` includes **`"Published Erratum"`** and **`"Retraction Notice"`** -- a third distinct PubMed pubtype value, alongside `"Retracted Publication"`/`"Retraction of Publication"`, not previously catalogued by this project. **Stated reason: the title itself is the reason** -- the same conference proceedings were published twice by journal/publisher error, matching RW's reason code exactly. No abstract text beyond the title. | **Reclassified: `independent_evidence` (broad tier only, via the `CommentsCorrectionsList` hop).** This is the one case in this batch where PubMed's own structured tag (`Retraction Notice`) and RW's stated reason agree precisely. |
| 11753710 | Limited Dosage for HES? | Concerns/Issues about Article; Date of Article and/or Notice Unknown | No `CommentsCorrectionsList` entry. One of the Joachim Boldt mass-retraction cases (RW's own notice-search URL: `?s=Joachim+Boldt`) -- RW itself could not locate a specific notice (`retraction_pubmed_id = "0"`, reason includes "Date ... Unknown"). Publisher page (thieme-connect.de) returned a bot-protection interstitial, unfetchable. | **Unchanged: `rw_derived_only`.** |

## Independence, two ways (author-requested distinction, 2026-10-05 second pass)

The six upgrades above all rest on one of two different kinds of signal, and the two should not
be collapsed into a single "independent" count without saying which kind is being used:

- **Strict tier**: independent evidence found on the *same* PMID RW's `original_paper_pubmed_id`
  points to -- PubMed's own title/abstract text on that exact record, or a Crossref
  `relation`/`update-to` entry with `source: "publisher"` on that exact record. This is the rule
  originally prespecified for Part A (S1.6.1) and used, unchanged, by the automated Part B v2
  pass. **5/298** (one of the original automated pass's 5 independent cases, the 29561487
  hop-free title-text case, applied to the corrected 298 denominator) -- unaffected by the
  `CommentsCorrectionsList`-chain rule below, since none of these require following a link away
  from the checked PMID. Wilson 95% CI [0.72%, 3.87%].
- **Broad tier**: strict, *plus* independent evidence found on a PMID one or more hops away via
  PubMed's own `CommentsCorrectionsList` (`Update in`/`Update of`/`Erratum in`) -- the rule this
  round's dossier re-check actually used for the other five upgrades (the four Cochrane
  `"WITHDRAWN:"` cases plus the duplicate-publication erratum case). **11/298**, Wilson 95% CI
  [2.07%, 6.49%] (as reported above).

**This `CommentsCorrectionsList`-chain rule is post hoc, not prespecified** -- it did not exist
in the original Part A/Part B classification rules (`prereg/phase5_record_level_audit.md`'s
2026-10-04 addendum) and was only introduced after seeing that five of the twelve
`rw_derived_only` cases happened to have exactly this kind of chained record. A fourth prereg
addendum (`prereg/phase5_record_level_audit.md`, 2026-10-05) now discloses this explicitly,
before it is used for anything further. Both tiers are reported in the paper, not just the
broader one, so a reader can judge for themselves how much of the revised lower bound rests on a
rule designed in response to this specific data.

**A separate, important caveat found while reading the notices (not a counting-rule issue):**
three of the four Cochrane `"WITHDRAWN:"` cases (16625614/24163271, 10796371/25840001,
11279736/26059170) state, in the notice's own text, a purely **administrative** reason for the
withdrawal -- timeline delays, consolidation into another review, or splitting into several more
specific reviews -- with no data-integrity, error, or misconduct language anywhere in the
notice. Only the fourth (25069726, chaining to 27581995) and the duplicate-publication erratum
case (30383461/34057018) have a stated or inferable reason consistent with RW's own
classification. The `CommentsCorrectionsList` hop reliably confirms *that a withdrawal event*
happened at Cochrane's own initiative -- it does not, by itself, confirm *why*, and in most of
these cases the "why" PubMed's own record discloses is not the kind of event "retraction" is
usually taken to mean. This is disclosed in the paper (section 3.8) rather than left implicit in
a classification label.

## Revised tallies

| | Automated (Part B v2, as run) | Revised, strict tier only | Revised, broad tier (this dossier re-check) |
|---|---|---|---|
| Resolved denominator | 299 | 298 | 298 (excludes PMID 1834920, a wrong-identifier RW row, not a real gap case) |
| Gap count | 17 | 16 | 16 |
| Gap rate | 5.69%, Wilson CI [3.58%, 8.92%] | 5.37%, Wilson CI [3.33%, 8.54%] | **5.37%, Wilson CI [3.33%, 8.54%]** (same gap rate -- only the independence tiering changes, not whether a case is a gap at all) |
| `independent_evidence` | 5 (29.4%) | **5 (31.25% of 16)** | **11 (68.75%)** |
| `rw_derived_only` | 12 (70.6%) | 11 (68.75% of 16) | **5 (31.25%)** |
| `rw_only_uncorroborated` | 0 (0.0%) | 0 (0.0%) | 0 (0.0%) |
| Independently-corroborated lower bound | 1.67% (5/299) | **1.68% (5/298), Wilson CI [0.72%, 3.87%]** | **3.69% (11/298), Wilson CI [2.07%, 6.49%]** |

All three columns are kept, per this project's standing discipline: the automated classification
is not deleted or silently replaced, and the dossier-level re-check is reported as an additional,
more labor-intensive pass that found real signal the cheaper, API-only classification missed
(and one case the API-only classification should never have counted in the first place). The
broad-tier lower bound (3.69%, 11/298) is closely comparable to, and nominally above, the curated
pool's own lower bound (3.4%, 10/296); the strict-tier lower bound (1.68%, 5/298) is comparable
to the automated pass's original 1.67% -- strengthening, not reversing, the "statistically
indistinguishable" headline finding either way, since the gap *rate* itself (the primary
endpoint) does not depend on which independence tier is used.

**Two newly-discovered traps, added to `docs/RW_PUBMED_METADATA_TRAPS.md`:** (1) Retraction
Watch's PMID fields can be flatly wrong -- not a placeholder, not a notice/original mix-up, but a
different real article entirely, apparently via digit truncation (confirmed for record_id 250:
both `original_paper_pubmed_id` and `retraction_pubmed_id` are missing their final digit relative
to the real PMIDs). (2) For Cochrane Database of Systematic Reviews entries specifically, the
PubMed-tagged "WITHDRAWN:"/`Retraction Notice` signal frequently lands on a *later* PMID in the
review's own pub-version chain (`pub2` -> `pub3` -> ... ) than the specific pub-version PMID RW's
`original_paper_pubmed_id` references -- checking only that exact PMID's own `pubtype` misses
independent corroboration that is one or two hops away in PubMed's own `CommentsCorrectionsList`.
**This information exists in PubMed's `CommentsCorrectionsList` field but not in its `pubtype`**
**tag** -- a distinct, separate machine-readability gap from the one section 3.8's headline
figure measures (`pubtype` vs. RW), stated explicitly in the paper rather than left implicit in
this results file alone.
