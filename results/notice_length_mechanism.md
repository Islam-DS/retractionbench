# What's actually being embedded: the notice-above-trap-source mechanism (ADR-090)

**Prompted by:** ADR-088's correlation holding at n=11 (r=0.75, down only slightly from n=8's
0.80). The author's instruction: correlation alone won't convince a reviewer -- show the actual
embedded documents for the three notice-above-trap-source cases and three contrasting
below-cases, so the mechanism (or its absence) is visible, not just implied by a coefficient.

**This is not a new statistical test.** It is a qualitative read of six documents already used
in the n=11 correlation (ADR-088), reported in full because the pattern is more legible in the
text itself than in any further summary statistic at this sample size.

## The three notice-above-trap-source cases (all `bare`)

| Item | Question | Embedded notice text (exactly what `corpus/embed_index.py` indexes) |
|---|---|---|
| RB-0007 | "How do post-neonatal mortality rates compare between rural and urban areas in Nigeria?" | `Notice: Rural-urban differentials in the rates and factors associated with post-neonatal mortality in Nigeria: Evidence from the 2013 national household survey` |
| RB-0008 | "How does electroconvulsive therapy alone compare with antipsychotic monotherapy for treating schizophrenia?" | `Notice: Electroconvulsive Therapy Alone for Schizophrenia: A Meta-analysis of Randomized, Single-blind, Controlled Trials` |
| RB-0011 | "How does vortioxetine compare with placebo in treating major depressive disorder?" | `Notice: Efficacy and safety of vortioxetine for the treatment of major depressive disorder: a randomised double-blind placebo-controlled study` |

**In all three, the embedded notice is the retracted paper's own title and nothing else** --
confirmed `notice_text=None` in each source record (ADR-071's "bare" category, ADR-042). Every
content word in the question (rural, urban, post-neonatal, mortality, Nigeria /
electroconvulsive, therapy, alone, schizophrenia / vortioxetine, placebo, major, depressive,
disorder) appears in the corresponding notice text, because the notice text *is* the source of
those words -- the question was written from the paper the title describes.

## Three contrasting cases where the notice ranks below (`unverifiable`, `categorical`, `specific`)

| Item | Question | Embedded notice text (truncated for this table; full text below) |
|---|---|---|
| RB-0004 | "How does ramosetron compare with granisetron for preventing vomiting after strabismus surgery in children?" | `Notice: Ramosetron compared with granisetron... Notice of formal retraction... Overwhelming evidence of fabrication, related to the fact that the distributions of many variables reported by Dr Fujii...` (747 chars) |
| RB-0006 | "What effect does vedolizumab have on biliary inflammation in patients with primary sclerosing cholangitis and inflammatory bowel disease?" | `Notice: Efficacy and Safety of Induction Dosing of Vedolizumab... This article has been retracted: please see Elsevier Policy on Article Withdrawal... PS124... presented at ILC 2016 have raised concerns that the source data in some cases are inconsistent...` (913 chars) |
| RB-0009 | "How does long-duration low-intensity ultrasound affect pain in patients with chronic upper trapezius trigger points?" | `Notice: Effects of Long Duration Low Intensity Ultrasound for Active Trapezius Trigger Points... withdrawn the following article... manufacturer of a device used in this study had contacted the author to disclose that the data reported... had possibly been affected by the failure of the device.` (814 chars) |

**Full text, RB-0004** (747 chars):
> Notice: Ramosetron compared with granisetron for the prevention of vomiting following
> strabismus surgery in children Notice of formal retraction of article by Dr Y. Fujii. This
> article is being retracted as a result of: (1) Overwhelming evidence of fabrication, related
> to the fact that the distributions of many variables reported by Dr Fujii in these studies
> could not have occurred by chance; and (2) The inability of Dr Fujii's institutions to attest
> to the integrity of the study and/or its data conducted under their auspices, as set out in
> the Joint Editors-in-Chief Request for Determination of April 9, 2012.

**Full text, RB-0006** (913 chars):
> Notice: Efficacy and Safety of Induction Dosing of Vedolizumab for Reducing Biliary
> Inflammation in Primary Sclerosing Cholangitis (PSC) in Individuals with Inflammatory Bowel
> Disease This article has been retracted: please see Elsevier Policy on Article Withdrawal...
> The abstract authors and presenters of PS124 -- EFFICACY AND SAFETY OF INDUCTION DOSING OF
> VEDOLIZUMAB FOR REDUCING BILIARY INFLAMMATION IN PRIMARY SCLEROSING CHOLANGITIS (PSC) IN
> INDIVIDUALS WITH INFLAMMATORY BOWEL DISEASE submitted and presented at ILC 2016 have raised
> concerns that the source data in some cases are inconsistent and requires further evaluation
> to determine the true magnitude of effect.

**Full text, RB-0009** (814 chars):
> Notice: Effects of Long Duration Low Intensity Ultrasound for Active Trapezius Trigger
> Points: A Randomized Clinical Trial We, the Authors, Editors and Publishers of Journal of
> Sport Rehabilitation, have withdrawn the following article in whole... The Editorial Office
> was contacted by the author with the request to withdraw this article, while informing the
> Editor-in-Chief that the manufacturer of a device used in this study had contacted the author
> to disclose that the data reported in the manuscript had possibly been affected by the
> failure of the device.

## What the contrast actually shows

Each of the three below-cases *also* begins with the paper's title (the same high-overlap text
the above-cases consist of entirely) -- but then adds 550-800 more characters of retraction-notice
boilerplate: editor names, publisher policy references, procedural dates, journal-internal
identifiers (PS124, ILC 2016), and explanatory prose about the retraction process itself. None
of that added text shares vocabulary with the clinical question, which was written about the
paper's subject matter, not about the mechanics of its retraction. Under cosine similarity
against a mean-pooled or otherwise aggregated embedding, that added text does not merely fail
to help -- it dilutes the vector's alignment with the question's high-overlap title terms,
pulling the whole document's embedding away from the question's embedding.

**This is a straightforward retrieval property, not evidence about supersession, and it should
be stated as such.** A bare notice ranks well because it is lexically almost identical to a
question written about the same paper -- the retraction adds no content to dilute that match.
An informative notice ranks worse not because retrieval somehow penalizes informativeness, but
because *any* additional text uncorrelated with the question's vocabulary will, all else equal,
reduce cosine similarity relative to a shorter, purely on-topic document. The mechanism is
generic to dense retrieval, not specific to correction records -- the same effect would appear
comparing a one-line document to a one-paragraph document on any topic, retraction or not.

**What stays a genuine, substantive finding, not explained away by this mechanism:** that
*informativeness and length are correlated in this pool* is itself real (ADR-084's pool-wide
measurement: most notices are short) and *practically consequential* -- if bare notices
systematically retrieve better than informative ones, a RAG system is systematically more
likely to surface the least explanatory version of a correction, regardless of why the
retrieval mechanism produces that outcome. The **mechanism** is boring (more text, less
lexical overlap); the **implication** (retrieval quietly favors the least informative
corrections) is not, and the paper should keep the two separate rather than let a mundane
mechanism undercut a real, reportable pattern.

## Status: still exploratory, still post-hoc

n=3 and n=3 is too small to generalize the specific mechanism claim beyond "consistent with,
not confirmed at scale." The correlation itself (ADR-088, n=11) is the same status: post-hoc,
not pre-registered, holding up under more data but not yet a finding. This document does not
upgrade either -- it explains *why* the correlation is plausible mechanistically, using visible
documents rather than only a coefficient, per the author's request.
