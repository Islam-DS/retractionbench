# M2 Human Verification Packet

One record per surviving control candidate. Every field is drawn directly from `data/interim/m2_control_candidates.csv` and the real PubMed search/metadata results this session, cross-checked against `data/interim/corpus/CORPUS_FREEZE.json` (freeze date 2026-08-09) and `scripts/check_control_leakage.py`. **RECOMMENDED DECISION is a machine-generated suggestion only, computed from the checks actually run -- it is not a verification and does not replace the human sign-off this packet exists to collect.**

Candidates in this packet: 25 (across 22 treated items). 6 treated items (RB-0008, RB-0013, RB-0015, RB-0020, RB-0024, RB-0027) have no surviving candidate and are not included here -- see `reports/m2_candidate_matching_report.md` for why.

---

## CC-012 -- for RB-0001

1. **Treated item ID:** RB-0001
2. **Control candidate ID:** CC-012 (rank 1)
3. **Candidate title:** Tegoprazan in Gastroesophageal Reflux Disease and Related Acid-Mediated Conditions: A Systematic Review and Meta-Analysis.
4. **Authors:** Bandyopadhyay S, Goenka M, Routh D, et al.
5. **PMID:** 42006860
6. **DOI:** 10.1002/jgh3.70406
7. **Primary source URL:** https://pubmed.ncbi.nlm.nih.gov/42006860/
8. **Publisher URL:** https://doi.org/10.1002/jgh3.70406
9. **Publication date:** 2026-04-17 (JGH Open)
10. **Why it matches the treated item:** Domain and claim_type match exactly (hard constraints). Intervention/topic: tegoprazan vs PPI (GERD acid suppression). Claim shape: 18-study systematic review, single drug class vs standard comparator. Soft-preference notes: polarity: match; intervention_class/claim_shape: logged, not scored
11. **Evidence supporting non-superseded status:** NEEDS_HUMAN_VERIFICATION (automated check: PubMed article_types field contains no Retracted Publication / Expression of Concern / Corrected and Republished Article tag as of this search)
12. **PubMed status evidence:** `article_types` = Journal Article; Review; no Retracted Publication / Expression of Concern / Corrected and Republished Article tag present as of the search date this session.
13. **Publisher status evidence:** NOT YET CHECKED by this process -- publisher corrections/errata page must be checked directly by the human reviewer; this is exactly the gap `docs/ANNOTATION.md` section 3.2's standard exists to close.
14. **Correction / expression-of-concern check:** NEEDS_HUMAN_VERIFICATION / NEEDS_HUMAN_VERIFICATION -- automated PubMed-tag check only, not a publisher-level confirmation.
15. **Temporal eligibility:** PASS (corpus freeze date 2026-08-09; publication date 2026-04-17).
16. **Leakage result:** 0 findings (checked against all 89 treated-item source/evidence identifiers, scripts/check_control_leakage.py).
17. **Exact question the human must answer:** Verify that PMID 42006860 (DOI 10.1002/jgh3.70406) has no retraction, expression of concern, or major correction affecting the cited claim, checked (a) as of the corpus freeze date 2026-08-09 and (b) as of today. Confirm the claim itself has not been superseded under this project's own supersession_type taxonomy (retraction / expression_of_concern / major_correction / guideline_revision / evidence_superseded). 
18. **Recommended decision (machine-generated only -- NOT a verification):** APPROVE (preliminary) -- All automated checks available ran clean: hard constraints match, temporal check passes, no leakage, no proximity/evidence-shape flag raised during sourcing.

**Checklist (human completes):**

- [ ] Human clinical evidence -- PASS -- confirmed human clinical/biomedical study (species checked during sourcing).
- [ ] Same hard domain -- PASS -- (HSC) Medicine - Pharmacology matches by construction.
- [ ] Same claim type -- PASS -- clinical_intervention matches by construction.
- [ ] Same question form -- PASS -- question_form=quantitative.
- [ ] Non-superseded -- AUTOMATED CHECK ONLY -- PubMed article_types carries no Retracted/EoC/Corrected tag; NOT sufficient alone, human must check publisher corrections page + Retraction Watch directly.
- [ ] Temporally eligible -- PASS.
- [ ] Independent of treated claim -- No proximity concern flagged during sourcing.
- [ ] No leakage -- PASS -- 0 findings against 89 treated-item identifiers.
- [ ] Acceptable evidence tier -- systematic_review_meta_analysis.

---

## CC-017 -- for RB-0002

1. **Treated item ID:** RB-0002
2. **Control candidate ID:** CC-017 (rank 1)
3. **Candidate title:** Strategies to reduce and maintain low perinatal mortality in resource-poor settings - Findings from a four-decade observational study of birth records from a large public maternity hospital in Papua New Guinea.
4. **Authors:** Mola GDL, Unger HW.
5. **PMID:** 30209806
6. **DOI:** 10.1111/ajo.12876
7. **Primary source URL:** https://pubmed.ncbi.nlm.nih.gov/30209806/
8. **Publisher URL:** https://doi.org/10.1111/ajo.12876
9. **Publication date:** 2018-09-13 (Australian & New Zealand Journal of Obstetrics & Gynaecology)
10. **Why it matches the treated item:** Domain and claim_type match exactly (hard constraints). Intervention/topic: N/A (observational: birth mode and perinatal mortality trends). Claim shape: 39-year single-hospital observational cohort, 365,056 births. Soft-preference notes: polarity: match; intervention_class/claim_shape: logged, not scored
11. **Evidence supporting non-superseded status:** NEEDS_HUMAN_VERIFICATION (automated check: PubMed article_types field contains no Retracted Publication / Expression of Concern / Corrected and Republished Article tag as of this search)
12. **PubMed status evidence:** `article_types` = Journal Article; Observational Study; no Retracted Publication / Expression of Concern / Corrected and Republished Article tag present as of the search date this session.
13. **Publisher status evidence:** NOT YET CHECKED by this process -- publisher corrections/errata page must be checked directly by the human reviewer; this is exactly the gap `docs/ANNOTATION.md` section 3.2's standard exists to close.
14. **Correction / expression-of-concern check:** NEEDS_HUMAN_VERIFICATION / NEEDS_HUMAN_VERIFICATION -- automated PubMed-tag check only, not a publisher-level confirmation.
15. **Temporal eligibility:** PASS (corpus freeze date 2026-08-09; publication date 2018-09-13).
16. **Leakage result:** 0 findings (checked against all 89 treated-item source/evidence identifiers, scripts/check_control_leakage.py).
17. **Exact question the human must answer:** Verify that PMID 30209806 (DOI 10.1111/ajo.12876) has no retraction, expression of concern, or major correction affecting the cited claim, checked (a) as of the corpus freeze date 2026-08-09 and (b) as of today. Confirm the claim itself has not been superseded under this project's own supersession_type taxonomy (retraction / expression_of_concern / major_correction / guideline_revision / evidence_superseded). 
18. **Recommended decision (machine-generated only -- NOT a verification):** APPROVE (preliminary) -- All automated checks available ran clean: hard constraints match, temporal check passes, no leakage, no proximity/evidence-shape flag raised during sourcing.

**Checklist (human completes):**

- [ ] Human clinical evidence -- PASS -- confirmed human clinical/biomedical study (species checked during sourcing).
- [ ] Same hard domain -- PASS -- (HSC) Medicine - Obstetrics/Gynecology matches by construction.
- [ ] Same claim type -- PASS -- clinical_observational matches by construction.
- [ ] Same question form -- PASS -- question_form=quantitative.
- [ ] Non-superseded -- AUTOMATED CHECK ONLY -- PubMed article_types carries no Retracted/EoC/Corrected tag; NOT sufficient alone, human must check publisher corrections page + Retraction Watch directly.
- [ ] Temporally eligible -- PASS.
- [ ] Independent of treated claim -- No proximity concern flagged during sourcing.
- [ ] No leakage -- PASS -- 0 findings against 89 treated-item identifiers.
- [ ] Acceptable evidence tier -- large_observational_cohort.

---

## CC-030 -- for RB-0003

1. **Treated item ID:** RB-0003
2. **Control candidate ID:** CC-030 (rank 1)
3. **Candidate title:** Menopausal hormone therapy and incident benign paroxysmal positional vertigo in postmenopausal women: A prospective cohort study using UK Biobank data.
4. **Authors:** Li L, Chen J, Han X, et al.
5. **PMID:** 42526172
6. **DOI:** 10.1016/j.maturitas.2026.109076
7. **Primary source URL:** https://pubmed.ncbi.nlm.nih.gov/42526172/
8. **Publisher URL:** https://doi.org/10.1016/j.maturitas.2026.109076
9. **Publication date:** 2026-07-26 (Maturitas)
10. **Why it matches the treated item:** Domain and claim_type match exactly (hard constraints). Intervention/topic: N/A (observational: menopausal hormone therapy and BPPV incidence). Claim shape: prospective cohort, UK Biobank, n=157,245. Soft-preference notes: polarity: match; intervention_class/claim_shape: logged, not scored
11. **Evidence supporting non-superseded status:** NEEDS_HUMAN_VERIFICATION (automated check: PubMed article_types field contains no Retracted Publication / Expression of Concern / Corrected and Republished Article tag as of this search)
12. **PubMed status evidence:** `article_types` = Journal Article; no Retracted Publication / Expression of Concern / Corrected and Republished Article tag present as of the search date this session.
13. **Publisher status evidence:** NOT YET CHECKED by this process -- publisher corrections/errata page must be checked directly by the human reviewer; this is exactly the gap `docs/ANNOTATION.md` section 3.2's standard exists to close.
14. **Correction / expression-of-concern check:** NEEDS_HUMAN_VERIFICATION / NEEDS_HUMAN_VERIFICATION -- automated PubMed-tag check only, not a publisher-level confirmation.
15. **Temporal eligibility:** PASS (corpus freeze date 2026-08-09; publication date 2026-07-26).
16. **Leakage result:** 0 findings (checked against all 89 treated-item source/evidence identifiers, scripts/check_control_leakage.py).
17. **Exact question the human must answer:** Verify that PMID 42526172 (DOI 10.1016/j.maturitas.2026.109076) has no retraction, expression of concern, or major correction affecting the cited claim, checked (a) as of the corpus freeze date 2026-08-09 and (b) as of today. Confirm the claim itself has not been superseded under this project's own supersession_type taxonomy (retraction / expression_of_concern / major_correction / guideline_revision / evidence_superseded). 
18. **Recommended decision (machine-generated only -- NOT a verification):** APPROVE (preliminary) -- All automated checks available ran clean: hard constraints match, temporal check passes, no leakage, no proximity/evidence-shape flag raised during sourcing.

**Checklist (human completes):**

- [ ] Human clinical evidence -- PASS -- confirmed human clinical/biomedical study (species checked during sourcing).
- [ ] Same hard domain -- PASS -- (HSC) Medicine - Obstetrics/Gynecology matches by construction.
- [ ] Same claim type -- PASS -- clinical_observational matches by construction.
- [ ] Same question form -- PASS -- question_form=quantitative.
- [ ] Non-superseded -- AUTOMATED CHECK ONLY -- PubMed article_types carries no Retracted/EoC/Corrected tag; NOT sufficient alone, human must check publisher corrections page + Retraction Watch directly.
- [ ] Temporally eligible -- PASS.
- [ ] Independent of treated claim -- No proximity concern flagged during sourcing.
- [ ] No leakage -- PASS -- 0 findings against 89 treated-item identifiers.
- [ ] Acceptable evidence tier -- large_observational_cohort.

---

## CC-013 -- for RB-0004

1. **Treated item ID:** RB-0004
2. **Control candidate ID:** CC-013 (rank 1)
3. **Candidate title:** Tapinarof Versus Crisaborole for Pediatric Atopic Dermatitis: A Systematic Review and Meta-Analysis.
4. **Authors:** Alhusaini W, Alghamdi S, Almutairy W, et al.
5. **PMID:** 41912211
6. **DOI:** 10.5826/dpc.1601a6285
7. **Primary source URL:** https://pubmed.ncbi.nlm.nih.gov/41912211/
8. **Publisher URL:** https://doi.org/10.5826/dpc.1601a6285
9. **Publication date:** 2026-01-30 (Dermatology Practical & Conceptual)
10. **Why it matches the treated item:** Domain and claim_type match exactly (hard constraints). Intervention/topic: tapinarof vs crisaborole (pediatric atopic dermatitis). Claim shape: 24-study meta-analysis, head-to-head topical comparison. Soft-preference notes: polarity: match; intervention_class/claim_shape: logged, not scored
11. **Evidence supporting non-superseded status:** NEEDS_HUMAN_VERIFICATION (automated check: PubMed article_types field contains no Retracted Publication / Expression of Concern / Corrected and Republished Article tag as of this search)
12. **PubMed status evidence:** `article_types` = Journal Article; Review; no Retracted Publication / Expression of Concern / Corrected and Republished Article tag present as of the search date this session.
13. **Publisher status evidence:** NOT YET CHECKED by this process -- publisher corrections/errata page must be checked directly by the human reviewer; this is exactly the gap `docs/ANNOTATION.md` section 3.2's standard exists to close.
14. **Correction / expression-of-concern check:** NEEDS_HUMAN_VERIFICATION / NEEDS_HUMAN_VERIFICATION -- automated PubMed-tag check only, not a publisher-level confirmation.
15. **Temporal eligibility:** PASS (corpus freeze date 2026-08-09; publication date 2026-01-30).
16. **Leakage result:** 0 findings (checked against all 89 treated-item source/evidence identifiers, scripts/check_control_leakage.py).
17. **Exact question the human must answer:** Verify that PMID 41912211 (DOI 10.5826/dpc.1601a6285) has no retraction, expression of concern, or major correction affecting the cited claim, checked (a) as of the corpus freeze date 2026-08-09 and (b) as of today. Confirm the claim itself has not been superseded under this project's own supersession_type taxonomy (retraction / expression_of_concern / major_correction / guideline_revision / evidence_superseded). 
18. **Recommended decision (machine-generated only -- NOT a verification):** APPROVE (preliminary) -- All automated checks available ran clean: hard constraints match, temporal check passes, no leakage, no proximity/evidence-shape flag raised during sourcing.

**Checklist (human completes):**

- [ ] Human clinical evidence -- PASS -- confirmed human clinical/biomedical study (species checked during sourcing).
- [ ] Same hard domain -- PASS -- (HSC) Medicine - Pharmacology matches by construction.
- [ ] Same claim type -- PASS -- clinical_intervention matches by construction.
- [ ] Same question form -- PASS -- question_form=quantitative.
- [ ] Non-superseded -- AUTOMATED CHECK ONLY -- PubMed article_types carries no Retracted/EoC/Corrected tag; NOT sufficient alone, human must check publisher corrections page + Retraction Watch directly.
- [ ] Temporally eligible -- PASS.
- [ ] Independent of treated claim -- No proximity concern flagged during sourcing.
- [ ] No leakage -- PASS -- 0 findings against 89 treated-item identifiers.
- [ ] Acceptable evidence tier -- systematic_review_meta_analysis.

---

## CC-018 -- for RB-0005

1. **Treated item ID:** RB-0005
2. **Control candidate ID:** CC-018 (rank 1)
3. **Candidate title:** Global prevalences of erythropoiesis-associated micronutrient deficiencies (iron, folate, and vitamin B12) among pregnant women: a systematic review and meta-analysis.
4. **Authors:** Nguyen NTH, Chen YC, Nhu NT, et al.
5. **PMID:** 41414845
6. **DOI:** 10.1080/07853890.2025.2602960
7. **Primary source URL:** https://pubmed.ncbi.nlm.nih.gov/41414845/
8. **Publisher URL:** https://doi.org/10.1080/07853890.2025.2602960
9. **Publication date:** 2025-12-19 (Annals of Medicine)
10. **Why it matches the treated item:** Domain and claim_type match exactly (hard constraints). Intervention/topic: N/A (observational: micronutrient deficiency prevalence in pregnancy). Claim shape: 43-study systematic review, 28 countries, global prevalence estimate. Soft-preference notes: polarity: match; intervention_class/claim_shape: logged, not scored
11. **Evidence supporting non-superseded status:** NEEDS_HUMAN_VERIFICATION (automated check: PubMed article_types field contains no Retracted Publication / Expression of Concern / Corrected and Republished Article tag as of this search)
12. **PubMed status evidence:** `article_types` = Journal Article; Systematic Review; Meta-Analysis; no Retracted Publication / Expression of Concern / Corrected and Republished Article tag present as of the search date this session.
13. **Publisher status evidence:** NOT YET CHECKED by this process -- publisher corrections/errata page must be checked directly by the human reviewer; this is exactly the gap `docs/ANNOTATION.md` section 3.2's standard exists to close.
14. **Correction / expression-of-concern check:** NEEDS_HUMAN_VERIFICATION / NEEDS_HUMAN_VERIFICATION -- automated PubMed-tag check only, not a publisher-level confirmation.
15. **Temporal eligibility:** PASS (corpus freeze date 2026-08-09; publication date 2025-12-19).
16. **Leakage result:** 0 findings (checked against all 89 treated-item source/evidence identifiers, scripts/check_control_leakage.py).
17. **Exact question the human must answer:** Verify that PMID 41414845 (DOI 10.1080/07853890.2025.2602960) has no retraction, expression of concern, or major correction affecting the cited claim, checked (a) as of the corpus freeze date 2026-08-09 and (b) as of today. Confirm the claim itself has not been superseded under this project's own supersession_type taxonomy (retraction / expression_of_concern / major_correction / guideline_revision / evidence_superseded). 
18. **Recommended decision (machine-generated only -- NOT a verification):** APPROVE (preliminary) -- All automated checks available ran clean: hard constraints match, temporal check passes, no leakage, no proximity/evidence-shape flag raised during sourcing.

**Checklist (human completes):**

- [ ] Human clinical evidence -- PASS -- confirmed human clinical/biomedical study (species checked during sourcing).
- [ ] Same hard domain -- PASS -- (HSC) Medicine - Obstetrics/Gynecology matches by construction.
- [ ] Same claim type -- PASS -- clinical_observational matches by construction.
- [ ] Same question form -- PASS -- question_form=quantitative.
- [ ] Non-superseded -- AUTOMATED CHECK ONLY -- PubMed article_types carries no Retracted/EoC/Corrected tag; NOT sufficient alone, human must check publisher corrections page + Retraction Watch directly.
- [ ] Temporally eligible -- PASS.
- [ ] Independent of treated claim -- No proximity concern flagged during sourcing.
- [ ] No leakage -- PASS -- 0 findings against 89 treated-item identifiers.
- [ ] Acceptable evidence tier -- systematic_review_meta_analysis.

---

## CC-014 -- for RB-0006

1. **Treated item ID:** RB-0006
2. **Control candidate ID:** CC-014 (rank 1)
3. **Candidate title:** Beta-Lactam Plus Azithromycin or Doxycycline vs Fluoroquinolones in Adult Patients Hospitalized With Community-Acquired Pneumonia: A Systematic Review and Network Meta-analysis.
4. **Authors:** Farah MH, Abusalih M, Farah W, et al. (Mayo Clinic)
5. **PMID:** 42158387
6. **DOI:** 10.1093/ofid/ofag253
7. **Primary source URL:** https://pubmed.ncbi.nlm.nih.gov/42158387/
8. **Publisher URL:** https://doi.org/10.1093/ofid/ofag253
9. **Publication date:** 2026-05-01 (Open Forum Infectious Diseases)
10. **Why it matches the treated item:** Domain and claim_type match exactly (hard constraints). Intervention/topic: beta-lactam+azithromycin/doxycycline vs fluoroquinolone (CAP). Claim shape: 20-study network meta-analysis, GRADE-assessed. Soft-preference notes: polarity: match; intervention_class/claim_shape: logged, not scored
11. **Evidence supporting non-superseded status:** NEEDS_HUMAN_VERIFICATION (automated check: PubMed article_types field contains no Retracted Publication / Expression of Concern / Corrected and Republished Article tag as of this search)
12. **PubMed status evidence:** `article_types` = Journal Article; no Retracted Publication / Expression of Concern / Corrected and Republished Article tag present as of the search date this session.
13. **Publisher status evidence:** NOT YET CHECKED by this process -- publisher corrections/errata page must be checked directly by the human reviewer; this is exactly the gap `docs/ANNOTATION.md` section 3.2's standard exists to close.
14. **Correction / expression-of-concern check:** NEEDS_HUMAN_VERIFICATION / NEEDS_HUMAN_VERIFICATION -- automated PubMed-tag check only, not a publisher-level confirmation.
15. **Temporal eligibility:** PASS (corpus freeze date 2026-08-09; publication date 2026-05-01).
16. **Leakage result:** 0 findings (checked against all 89 treated-item source/evidence identifiers, scripts/check_control_leakage.py).
17. **Exact question the human must answer:** Verify that PMID 42158387 (DOI 10.1093/ofid/ofag253) has no retraction, expression of concern, or major correction affecting the cited claim, checked (a) as of the corpus freeze date 2026-08-09 and (b) as of today. Confirm the claim itself has not been superseded under this project's own supersession_type taxonomy (retraction / expression_of_concern / major_correction / guideline_revision / evidence_superseded). Additionally: MILD PROXIMITY: both this candidate and RB-0006 (vedolizumab/biliary inflammation) are antimicrobial/immunomodulatory pharmacology, but entirely different condition and drug class -- low concern.
18. **Recommended decision (machine-generated only -- NOT a verification):** UNCERTAIN -- A specific proximity/evidence-shape concern was flagged during sourcing (see note below) -- needs a human judgment call, not a clean pass.

**Checklist (human completes):**

- [ ] Human clinical evidence -- PASS -- confirmed human clinical/biomedical study (species checked during sourcing).
- [ ] Same hard domain -- PASS -- (HSC) Medicine - Pharmacology matches by construction.
- [ ] Same claim type -- PASS -- clinical_intervention matches by construction.
- [ ] Same question form -- PASS -- question_form=quantitative.
- [ ] Non-superseded -- AUTOMATED CHECK ONLY -- PubMed article_types carries no Retracted/EoC/Corrected tag; NOT sufficient alone, human must check publisher corrections page + Retraction Watch directly.
- [ ] Temporally eligible -- PASS.
- [ ] Independent of treated claim -- CHECK NOTE BELOW
- [ ] No leakage -- PASS -- 0 findings against 89 treated-item identifiers.
- [ ] Acceptable evidence tier -- systematic_review_meta_analysis.

---

## CC-007 -- for RB-0007

1. **Treated item ID:** RB-0007
2. **Control candidate ID:** CC-007 (rank 1)
3. **Candidate title:** Breastfeeding initiation and continuation among women on medicines: a systematic review and meta-analysis.
4. **Authors:** Nakijoba R, Musaazi J, Kyohaire I, et al.
5. **PMID:** 42031488
6. **DOI:** 10.1136/bmjopen-2025-107274
7. **Primary source URL:** https://pubmed.ncbi.nlm.nih.gov/42031488/
8. **Publisher URL:** https://doi.org/10.1136/bmjopen-2025-107274
9. **Publication date:** 2026-04-24 (BMJ Open)
10. **Why it matches the treated item:** Domain and claim_type match exactly (hard constraints). Intervention/topic: N/A (observational: breastfeeding prevalence by medication exposure). Claim shape: prevalence meta-analysis, GRADE-assessed, meta-regression. Soft-preference notes: polarity: match; intervention_class/claim_shape: logged, not scored
11. **Evidence supporting non-superseded status:** NEEDS_HUMAN_VERIFICATION (automated check: PubMed article_types field contains no Retracted Publication / Expression of Concern / Corrected and Republished Article tag as of this search)
12. **PubMed status evidence:** `article_types` = Journal Article; Systematic Review; Meta-Analysis; no Retracted Publication / Expression of Concern / Corrected and Republished Article tag present as of the search date this session.
13. **Publisher status evidence:** NOT YET CHECKED by this process -- publisher corrections/errata page must be checked directly by the human reviewer; this is exactly the gap `docs/ANNOTATION.md` section 3.2's standard exists to close.
14. **Correction / expression-of-concern check:** NEEDS_HUMAN_VERIFICATION / NEEDS_HUMAN_VERIFICATION -- automated PubMed-tag check only, not a publisher-level confirmation.
15. **Temporal eligibility:** PASS (corpus freeze date 2026-08-09; publication date 2026-04-24).
16. **Leakage result:** 0 findings (checked against all 89 treated-item source/evidence identifiers, scripts/check_control_leakage.py).
17. **Exact question the human must answer:** Verify that PMID 42031488 (DOI 10.1136/bmjopen-2025-107274) has no retraction, expression of concern, or major correction affecting the cited claim, checked (a) as of the corpus freeze date 2026-08-09 and (b) as of today. Confirm the claim itself has not been superseded under this project's own supersession_type taxonomy (retraction / expression_of_concern / major_correction / guideline_revision / evidence_superseded). 
18. **Recommended decision (machine-generated only -- NOT a verification):** APPROVE (preliminary) -- All automated checks available ran clean: hard constraints match, temporal check passes, no leakage, no proximity/evidence-shape flag raised during sourcing.

**Checklist (human completes):**

- [ ] Human clinical evidence -- PASS -- confirmed human clinical/biomedical study (species checked during sourcing).
- [ ] Same hard domain -- PASS -- (HSC) Medicine - Obstetrics/Gynecology matches by construction.
- [ ] Same claim type -- PASS -- clinical_observational matches by construction.
- [ ] Same question form -- PASS -- question_form=quantitative.
- [ ] Non-superseded -- AUTOMATED CHECK ONLY -- PubMed article_types carries no Retracted/EoC/Corrected tag; NOT sufficient alone, human must check publisher corrections page + Retraction Watch directly.
- [ ] Temporally eligible -- PASS.
- [ ] Independent of treated claim -- No proximity concern flagged during sourcing.
- [ ] No leakage -- PASS -- 0 findings against 89 treated-item identifiers.
- [ ] Acceptable evidence tier -- systematic_review_meta_analysis.

---

## CC-008 -- for RB-0009

1. **Treated item ID:** RB-0009
2. **Control candidate ID:** CC-008 (rank 1)
3. **Candidate title:** Effect of extracorporeal shockwave therapy for rotator cuff tendinopathy: a systematic review and meta-analysis.
4. **Authors:** Xue X, Song Q, Yang X, et al.
5. **PMID:** 38704572
6. **DOI:** 10.1186/s12891-024-07445-7
7. **Primary source URL:** https://pubmed.ncbi.nlm.nih.gov/38704572/
8. **Publisher URL:** https://doi.org/10.1186/s12891-024-07445-7
9. **Publication date:** 2024-05-04 (BMC Musculoskeletal Disorders)
10. **Why it matches the treated item:** Domain and claim_type match exactly (hard constraints). Intervention/topic: extracorporeal shockwave therapy (musculoskeletal pain/function). Claim shape: 16-RCT meta-analysis, single modality vs sham/other. Soft-preference notes: polarity: match; intervention_class/claim_shape: logged, not scored
11. **Evidence supporting non-superseded status:** NEEDS_HUMAN_VERIFICATION (automated check: PubMed article_types field contains no Retracted Publication / Expression of Concern / Corrected and Republished Article tag as of this search)
12. **PubMed status evidence:** `article_types` = Journal Article; Systematic Review; Meta-Analysis; no Retracted Publication / Expression of Concern / Corrected and Republished Article tag present as of the search date this session.
13. **Publisher status evidence:** NOT YET CHECKED by this process -- publisher corrections/errata page must be checked directly by the human reviewer; this is exactly the gap `docs/ANNOTATION.md` section 3.2's standard exists to close.
14. **Correction / expression-of-concern check:** NEEDS_HUMAN_VERIFICATION / NEEDS_HUMAN_VERIFICATION -- automated PubMed-tag check only, not a publisher-level confirmation.
15. **Temporal eligibility:** PASS (corpus freeze date 2026-08-09; publication date 2024-05-04).
16. **Leakage result:** 0 findings (checked against all 89 treated-item source/evidence identifiers, scripts/check_control_leakage.py).
17. **Exact question the human must answer:** Verify that PMID 38704572 (DOI 10.1186/s12891-024-07445-7) has no retraction, expression of concern, or major correction affecting the cited claim, checked (a) as of the corpus freeze date 2026-08-09 and (b) as of today. Confirm the claim itself has not been superseded under this project's own supersession_type taxonomy (retraction / expression_of_concern / major_correction / guideline_revision / evidence_superseded). Additionally: TOPICAL PROXIMITY FLAG: RB-0009 is also a physical/energy-based modality (low-intensity ultrasound) for chronic musculoskeletal pain. Different modality (shockwave vs ultrasound) and different specific condition (rotator cuff tendinopathy vs RB-0009's own chronic upper-limb pain population) -- not the same trial or claim -- but same broad rehab-modality subfield. Only Rehab-domain candidate found (1-item domain, per docs/M2_CONTROL_PROTOCOL.md section 7 risk #3); human reviewer judgment required on whether this is close enough to be informative or too close to be a clean independent control.
18. **Recommended decision (machine-generated only -- NOT a verification):** UNCERTAIN -- A specific proximity/evidence-shape concern was flagged during sourcing (see note below) -- needs a human judgment call, not a clean pass.

**Checklist (human completes):**

- [ ] Human clinical evidence -- PASS -- confirmed human clinical/biomedical study (species checked during sourcing).
- [ ] Same hard domain -- PASS -- (HSC) Medicine - Rehabilitation/Therapy matches by construction.
- [ ] Same claim type -- PASS -- clinical_intervention matches by construction.
- [ ] Same question form -- PASS -- question_form=quantitative.
- [ ] Non-superseded -- AUTOMATED CHECK ONLY -- PubMed article_types carries no Retracted/EoC/Corrected tag; NOT sufficient alone, human must check publisher corrections page + Retraction Watch directly.
- [ ] Temporally eligible -- PASS.
- [ ] Independent of treated claim -- CHECK NOTE BELOW
- [ ] No leakage -- PASS -- 0 findings against 89 treated-item identifiers.
- [ ] Acceptable evidence tier -- systematic_review_meta_analysis.

---

## CC-031 -- for RB-0010

1. **Treated item ID:** RB-0010
2. **Control candidate ID:** CC-031 (rank 1)
3. **Candidate title:** Impact of OMEGA-3 fatty acid in patients undergoing hemodialysis: a systematic review and meta-analysis.
4. **Authors:** Ahmed Jilani HB, Baig BM, Rasool A, et al.
5. **PMID:** 42321661
6. **DOI:** 10.1186/s12882-026-05140-4
7. **Primary source URL:** https://pubmed.ncbi.nlm.nih.gov/42321661/
8. **Publisher URL:** https://doi.org/10.1186/s12882-026-05140-4
9. **Publication date:** 2026-06-19 (BMC Nephrology)
10. **Why it matches the treated item:** Domain and claim_type match exactly (hard constraints). Intervention/topic: omega-3 PUFA supplementation (hemodialysis, cardiovascular outcomes). Claim shape: systematic review, RCTs pooled, single intervention vs placebo. Soft-preference notes: polarity: match; intervention_class/claim_shape: logged, not scored
11. **Evidence supporting non-superseded status:** NEEDS_HUMAN_VERIFICATION (automated check: PubMed article_types field contains no Retracted Publication / Expression of Concern / Corrected and Republished Article tag as of this search)
12. **PubMed status evidence:** `article_types` = Systematic Review; Journal Article; Meta-Analysis; no Retracted Publication / Expression of Concern / Corrected and Republished Article tag present as of the search date this session.
13. **Publisher status evidence:** NOT YET CHECKED by this process -- publisher corrections/errata page must be checked directly by the human reviewer; this is exactly the gap `docs/ANNOTATION.md` section 3.2's standard exists to close.
14. **Correction / expression-of-concern check:** NEEDS_HUMAN_VERIFICATION / NEEDS_HUMAN_VERIFICATION -- automated PubMed-tag check only, not a publisher-level confirmation.
15. **Temporal eligibility:** PASS (corpus freeze date 2026-08-09; publication date 2026-06-19).
16. **Leakage result:** 0 findings (checked against all 89 treated-item source/evidence identifiers, scripts/check_control_leakage.py).
17. **Exact question the human must answer:** Verify that PMID 42321661 (DOI 10.1186/s12882-026-05140-4) has no retraction, expression of concern, or major correction affecting the cited claim, checked (a) as of the corpus freeze date 2026-08-09 and (b) as of today. Confirm the claim itself has not been superseded under this project's own supersession_type taxonomy (retraction / expression_of_concern / major_correction / guideline_revision / evidence_superseded). 
18. **Recommended decision (machine-generated only -- NOT a verification):** APPROVE (preliminary) -- All automated checks available ran clean: hard constraints match, temporal check passes, no leakage, no proximity/evidence-shape flag raised during sourcing.

**Checklist (human completes):**

- [ ] Human clinical evidence -- PASS -- confirmed human clinical/biomedical study (species checked during sourcing).
- [ ] Same hard domain -- PASS -- (HSC) Medicine - Pharmacology matches by construction.
- [ ] Same claim type -- PASS -- clinical_intervention matches by construction.
- [ ] Same question form -- PASS -- question_form=quantitative.
- [ ] Non-superseded -- AUTOMATED CHECK ONLY -- PubMed article_types carries no Retracted/EoC/Corrected tag; NOT sufficient alone, human must check publisher corrections page + Retraction Watch directly.
- [ ] Temporally eligible -- PASS.
- [ ] Independent of treated claim -- No proximity concern flagged during sourcing.
- [ ] No leakage -- PASS -- 0 findings against 89 treated-item identifiers.
- [ ] Acceptable evidence tier -- systematic_review_meta_analysis.

---

## CC-032 -- for RB-0010

1. **Treated item ID:** RB-0010
2. **Control candidate ID:** CC-032 (rank 2)
3. **Candidate title:** Meta Analysis of DHA and EPA Supplementation on Cardiovascular Outcomes and Atrial Fibrillation Risk.
4. **Authors:** Shayan SK, Abbood RS, Al-Taie SF, et al.
5. **PMID:** 42144851
6. **DOI:** 10.1002/prp2.70265
7. **Primary source URL:** https://pubmed.ncbi.nlm.nih.gov/42144851/
8. **Publisher URL:** https://doi.org/10.1002/prp2.70265
9. **Publication date:** 2026-06 (Pharmacology Research & Perspectives)
10. **Why it matches the treated item:** Domain and claim_type match exactly (hard constraints). Intervention/topic: EPA+DHA supplementation (secondary CVD prevention, atrial fibrillation). Claim shape: 25-RCT meta-analysis, PROSPERO-registered. Soft-preference notes: polarity: match; intervention_class/claim_shape: logged, not scored
11. **Evidence supporting non-superseded status:** NEEDS_HUMAN_VERIFICATION (automated check: PubMed article_types field contains no Retracted Publication / Expression of Concern / Corrected and Republished Article tag as of this search)
12. **PubMed status evidence:** `article_types` = Journal Article; Meta-Analysis; Review; no Retracted Publication / Expression of Concern / Corrected and Republished Article tag present as of the search date this session.
13. **Publisher status evidence:** NOT YET CHECKED by this process -- publisher corrections/errata page must be checked directly by the human reviewer; this is exactly the gap `docs/ANNOTATION.md` section 3.2's standard exists to close.
14. **Correction / expression-of-concern check:** NEEDS_HUMAN_VERIFICATION / NEEDS_HUMAN_VERIFICATION -- automated PubMed-tag check only, not a publisher-level confirmation.
15. **Temporal eligibility:** PASS (corpus freeze date 2026-08-09; publication date 2026-06).
16. **Leakage result:** 0 findings (checked against all 89 treated-item source/evidence identifiers, scripts/check_control_leakage.py).
17. **Exact question the human must answer:** Verify that PMID 42144851 (DOI 10.1002/prp2.70265) has no retraction, expression of concern, or major correction affecting the cited claim, checked (a) as of the corpus freeze date 2026-08-09 and (b) as of today. Confirm the claim itself has not been superseded under this project's own supersession_type taxonomy (retraction / expression_of_concern / major_correction / guideline_revision / evidence_superseded). Additionally: Backup candidate (rank 2) for RB-0010, same intervention class as CC-031 (omega-3), different population/outcome. Frozen matching rule does not clearly separate these two -- left for human reviewer to pick, per docs/M2_CONTROL_PROTOCOL.md section 2.6.
18. **Recommended decision (machine-generated only -- NOT a verification):** UNCERTAIN -- A specific proximity/evidence-shape concern was flagged during sourcing (see note below) -- needs a human judgment call, not a clean pass.

**Checklist (human completes):**

- [ ] Human clinical evidence -- PASS -- confirmed human clinical/biomedical study (species checked during sourcing).
- [ ] Same hard domain -- PASS -- (HSC) Medicine - Pharmacology matches by construction.
- [ ] Same claim type -- PASS -- clinical_intervention matches by construction.
- [ ] Same question form -- PASS -- question_form=quantitative.
- [ ] Non-superseded -- AUTOMATED CHECK ONLY -- PubMed article_types carries no Retracted/EoC/Corrected tag; NOT sufficient alone, human must check publisher corrections page + Retraction Watch directly.
- [ ] Temporally eligible -- PASS.
- [ ] Independent of treated claim -- CHECK NOTE BELOW
- [ ] No leakage -- PASS -- 0 findings against 89 treated-item identifiers.
- [ ] Acceptable evidence tier -- systematic_review_meta_analysis.

---

## CC-015 -- for RB-0011

1. **Treated item ID:** RB-0011
2. **Control candidate ID:** CC-015 (rank 1)
3. **Candidate title:** Pharmacological treatments for generalised anxiety disorder: a systematic review and network meta-analysis.
4. **Authors:** Slee A, Nazareth I, Bondaronek P, Liu Y, Cheng Z, Freemantle N.
5. **PMID:** 30712879
6. **DOI:** 10.1016/S0140-6736(18)31793-8
7. **Primary source URL:** https://pubmed.ncbi.nlm.nih.gov/30712879/
8. **Publisher URL:** https://doi.org/10.1016/S0140-6736(18)31793-8
9. **Publication date:** 2019-01-31 (The Lancet)
10. **Why it matches the treated item:** Domain and claim_type match exactly (hard constraints). Intervention/topic: antidepressant/anxiolytic class comparison (generalized anxiety disorder). Claim shape: 89-trial network meta-analysis, Lancet, PROSPERO-registered. Soft-preference notes: polarity: match; intervention_class/claim_shape: logged, not scored
11. **Evidence supporting non-superseded status:** NEEDS_HUMAN_VERIFICATION (automated check: PubMed article_types field contains no Retracted Publication / Expression of Concern / Corrected and Republished Article tag as of this search)
12. **PubMed status evidence:** `article_types` = Journal Article; Systematic Review; Network Meta-Analysis; no Retracted Publication / Expression of Concern / Corrected and Republished Article tag present as of the search date this session.
13. **Publisher status evidence:** NOT YET CHECKED by this process -- publisher corrections/errata page must be checked directly by the human reviewer; this is exactly the gap `docs/ANNOTATION.md` section 3.2's standard exists to close.
14. **Correction / expression-of-concern check:** NEEDS_HUMAN_VERIFICATION / NEEDS_HUMAN_VERIFICATION -- automated PubMed-tag check only, not a publisher-level confirmation.
15. **Temporal eligibility:** PASS (corpus freeze date 2026-08-09; publication date 2019-01-31).
16. **Leakage result:** 0 findings (checked against all 89 treated-item source/evidence identifiers, scripts/check_control_leakage.py).
17. **Exact question the human must answer:** Verify that PMID 30712879 (DOI 10.1016/S0140-6736(18)31793-8) has no retraction, expression of concern, or major correction affecting the cited claim, checked (a) as of the corpus freeze date 2026-08-09 and (b) as of today. Confirm the claim itself has not been superseded under this project's own supersession_type taxonomy (retraction / expression_of_concern / major_correction / guideline_revision / evidence_superseded). Additionally: TOPICAL PROXIMITY FLAG: RB-0011 (vortioxetine vs placebo, major depressive disorder) and this candidate (GAD pharmacotherapy) are both psychiatric pharmacotherapy reviews. Different specific disorder (GAD vs MDD) and this review evaluates a drug class, not vortioxetine specifically -- not a disguised replacement, but human reviewer should judge whether same-broad-field proximity is acceptable.
18. **Recommended decision (machine-generated only -- NOT a verification):** UNCERTAIN -- A specific proximity/evidence-shape concern was flagged during sourcing (see note below) -- needs a human judgment call, not a clean pass.

**Checklist (human completes):**

- [ ] Human clinical evidence -- PASS -- confirmed human clinical/biomedical study (species checked during sourcing).
- [ ] Same hard domain -- PASS -- (HSC) Medicine - Pharmacology matches by construction.
- [ ] Same claim type -- PASS -- clinical_intervention matches by construction.
- [ ] Same question form -- PASS -- question_form=quantitative.
- [ ] Non-superseded -- AUTOMATED CHECK ONLY -- PubMed article_types carries no Retracted/EoC/Corrected tag; NOT sufficient alone, human must check publisher corrections page + Retraction Watch directly.
- [ ] Temporally eligible -- PASS.
- [ ] Independent of treated claim -- CHECK NOTE BELOW
- [ ] No leakage -- PASS -- 0 findings against 89 treated-item identifiers.
- [ ] Acceptable evidence tier -- systematic_review_meta_analysis.

---

## CC-019 -- for RB-0012

1. **Treated item ID:** RB-0012
2. **Control candidate ID:** CC-019 (rank 1)
3. **Candidate title:** Long-Term Prospective Cohort Study of Cervical Cancer Screening Using Triage of Women Who Are Human Papillomavirus-Positive With Dual Stain and Human Papillomavirus Genotyping.
4. **Authors:** Wentzensen N, Egemen D, Clarke MA, et al. (NCI / Kaiser Permanente Northern California)
5. **PMID:** 41701950
6. **DOI:** 10.1200/JCO-25-00689
7. **Primary source URL:** https://pubmed.ncbi.nlm.nih.gov/41701950/
8. **Publisher URL:** https://doi.org/10.1200/JCO-25-00689
9. **Publication date:** 2026-02-17 (Journal of Clinical Oncology)
10. **Why it matches the treated item:** Domain and claim_type match exactly (hard constraints). Intervention/topic: N/A (observational: HPV triage strategy performance). Claim shape: prospective cohort, n=9,645, 5-year modeled risk. Soft-preference notes: polarity: match; intervention_class/claim_shape: logged, not scored
11. **Evidence supporting non-superseded status:** NEEDS_HUMAN_VERIFICATION (automated check: PubMed article_types field contains no Retracted Publication / Expression of Concern / Corrected and Republished Article tag as of this search)
12. **PubMed status evidence:** `article_types` = Journal Article; Observational Study; no Retracted Publication / Expression of Concern / Corrected and Republished Article tag present as of the search date this session.
13. **Publisher status evidence:** NOT YET CHECKED by this process -- publisher corrections/errata page must be checked directly by the human reviewer; this is exactly the gap `docs/ANNOTATION.md` section 3.2's standard exists to close.
14. **Correction / expression-of-concern check:** NEEDS_HUMAN_VERIFICATION / NEEDS_HUMAN_VERIFICATION -- automated PubMed-tag check only, not a publisher-level confirmation.
15. **Temporal eligibility:** PASS (corpus freeze date 2026-08-09; publication date 2026-02-17).
16. **Leakage result:** 0 findings (checked against all 89 treated-item source/evidence identifiers, scripts/check_control_leakage.py).
17. **Exact question the human must answer:** Verify that PMID 41701950 (DOI 10.1200/JCO-25-00689) has no retraction, expression of concern, or major correction affecting the cited claim, checked (a) as of the corpus freeze date 2026-08-09 and (b) as of today. Confirm the claim itself has not been superseded under this project's own supersession_type taxonomy (retraction / expression_of_concern / major_correction / guideline_revision / evidence_superseded). 
18. **Recommended decision (machine-generated only -- NOT a verification):** APPROVE (preliminary) -- All automated checks available ran clean: hard constraints match, temporal check passes, no leakage, no proximity/evidence-shape flag raised during sourcing.

**Checklist (human completes):**

- [ ] Human clinical evidence -- PASS -- confirmed human clinical/biomedical study (species checked during sourcing).
- [ ] Same hard domain -- PASS -- (HSC) Medicine - Obstetrics/Gynecology matches by construction.
- [ ] Same claim type -- PASS -- clinical_observational matches by construction.
- [ ] Same question form -- PASS -- question_form=quantitative.
- [ ] Non-superseded -- AUTOMATED CHECK ONLY -- PubMed article_types carries no Retracted/EoC/Corrected tag; NOT sufficient alone, human must check publisher corrections page + Retraction Watch directly.
- [ ] Temporally eligible -- PASS.
- [ ] Independent of treated claim -- No proximity concern flagged during sourcing.
- [ ] No leakage -- PASS -- 0 findings against 89 treated-item identifiers.
- [ ] Acceptable evidence tier -- large_observational_cohort.

---

## CC-003 -- for RB-0014

1. **Treated item ID:** RB-0014
2. **Control candidate ID:** CC-003 (rank 1)
3. **Candidate title:** Alternative magnesium sulphate regimens for women with pre-eclampsia and eclampsia.
4. **Authors:** Diaz V, Long Q, Oladapo OT (Cochrane)
5. **PMID:** 37815037
6. **DOI:** 10.1002/14651858.CD007388.pub3
7. **Primary source URL:** https://pubmed.ncbi.nlm.nih.gov/37815037/
8. **Publisher URL:** https://doi.org/10.1002/14651858.CD007388.pub3
9. **Publication date:** 2023-10-10 (Cochrane Database of Systematic Reviews)
10. **Why it matches the treated item:** Domain and claim_type match exactly (hard constraints). Intervention/topic: magnesium sulphate regimen comparison (eclampsia/pre-eclampsia). Claim shape: Cochrane systematic review, multiple regimen comparisons, GRADE-assessed. Soft-preference notes: polarity: match; intervention_class/claim_shape: logged, not scored
11. **Evidence supporting non-superseded status:** NEEDS_HUMAN_VERIFICATION (automated check: PubMed article_types field contains no Retracted Publication / Expression of Concern / Corrected and Republished Article tag as of this search)
12. **PubMed status evidence:** `article_types` = Systematic Review; Journal Article; no Retracted Publication / Expression of Concern / Corrected and Republished Article tag present as of the search date this session.
13. **Publisher status evidence:** NOT YET CHECKED by this process -- publisher corrections/errata page must be checked directly by the human reviewer; this is exactly the gap `docs/ANNOTATION.md` section 3.2's standard exists to close.
14. **Correction / expression-of-concern check:** NEEDS_HUMAN_VERIFICATION / NEEDS_HUMAN_VERIFICATION -- automated PubMed-tag check only, not a publisher-level confirmation.
15. **Temporal eligibility:** PASS (corpus freeze date 2026-08-09; publication date 2023-10-10).
16. **Leakage result:** 0 findings (checked against all 89 treated-item source/evidence identifiers, scripts/check_control_leakage.py).
17. **Exact question the human must answer:** Verify that PMID 37815037 (DOI 10.1002/14651858.CD007388.pub3) has no retraction, expression of concern, or major correction affecting the cited claim, checked (a) as of the corpus freeze date 2026-08-09 and (b) as of today. Confirm the claim itself has not been superseded under this project's own supersession_type taxonomy (retraction / expression_of_concern / major_correction / guideline_revision / evidence_superseded). 
18. **Recommended decision (machine-generated only -- NOT a verification):** APPROVE (preliminary) -- All automated checks available ran clean: hard constraints match, temporal check passes, no leakage, no proximity/evidence-shape flag raised during sourcing.

**Checklist (human completes):**

- [ ] Human clinical evidence -- PASS -- confirmed human clinical/biomedical study (species checked during sourcing).
- [ ] Same hard domain -- PASS -- (HSC) Medicine - Obstetrics/Gynecology matches by construction.
- [ ] Same claim type -- PASS -- clinical_intervention matches by construction.
- [ ] Same question form -- PASS -- question_form=quantitative.
- [ ] Non-superseded -- AUTOMATED CHECK ONLY -- PubMed article_types carries no Retracted/EoC/Corrected tag; NOT sufficient alone, human must check publisher corrections page + Retraction Watch directly.
- [ ] Temporally eligible -- PASS.
- [ ] Independent of treated claim -- No proximity concern flagged during sourcing.
- [ ] No leakage -- PASS -- 0 findings against 89 treated-item identifiers.
- [ ] Acceptable evidence tier -- cochrane_review.

---

## CC-033 -- for RB-0016

1. **Treated item ID:** RB-0016
2. **Control candidate ID:** CC-033 (rank 1)
3. **Candidate title:** Comparing Umbilical Cord Management Strategies in Nonvigorous Newborns: A Systematic Review and Network Meta-analysis.
4. **Authors:** Aldemerdash MA, Abdellatif M, Refaey D, et al.
5. **PMID:** 40315887
6. **DOI:** 10.1055/a-2598-7291
7. **Primary source URL:** https://pubmed.ncbi.nlm.nih.gov/40315887/
8. **Publisher URL:** https://doi.org/10.1055/a-2598-7291
9. **Publication date:** 2025-05-02 (American Journal of Perinatology)
10. **Why it matches the treated item:** Domain and claim_type match exactly (hard constraints). Intervention/topic: umbilical cord management strategy (nonvigorous newborns). Claim shape: 10-study network meta-analysis, n=2541 newborns. Soft-preference notes: polarity: match; intervention_class/claim_shape: logged, not scored
11. **Evidence supporting non-superseded status:** NEEDS_HUMAN_VERIFICATION (automated check: PubMed article_types field contains no Retracted Publication / Expression of Concern / Corrected and Republished Article tag as of this search)
12. **PubMed status evidence:** `article_types` = Journal Article; Systematic Review; Comparative Study; Network Meta-Analysis; no Retracted Publication / Expression of Concern / Corrected and Republished Article tag present as of the search date this session.
13. **Publisher status evidence:** NOT YET CHECKED by this process -- publisher corrections/errata page must be checked directly by the human reviewer; this is exactly the gap `docs/ANNOTATION.md` section 3.2's standard exists to close.
14. **Correction / expression-of-concern check:** NEEDS_HUMAN_VERIFICATION / NEEDS_HUMAN_VERIFICATION -- automated PubMed-tag check only, not a publisher-level confirmation.
15. **Temporal eligibility:** PASS (corpus freeze date 2026-08-09; publication date 2025-05-02).
16. **Leakage result:** 0 findings (checked against all 89 treated-item source/evidence identifiers, scripts/check_control_leakage.py).
17. **Exact question the human must answer:** Verify that PMID 40315887 (DOI 10.1055/a-2598-7291) has no retraction, expression of concern, or major correction affecting the cited claim, checked (a) as of the corpus freeze date 2026-08-09 and (b) as of today. Confirm the claim itself has not been superseded under this project's own supersession_type taxonomy (retraction / expression_of_concern / major_correction / guideline_revision / evidence_superseded). 
18. **Recommended decision (machine-generated only -- NOT a verification):** APPROVE (preliminary) -- All automated checks available ran clean: hard constraints match, temporal check passes, no leakage, no proximity/evidence-shape flag raised during sourcing.

**Checklist (human completes):**

- [ ] Human clinical evidence -- PASS -- confirmed human clinical/biomedical study (species checked during sourcing).
- [ ] Same hard domain -- PASS -- (HSC) Medicine - Obstetrics/Gynecology matches by construction.
- [ ] Same claim type -- PASS -- clinical_intervention matches by construction.
- [ ] Same question form -- PASS -- question_form=quantitative.
- [ ] Non-superseded -- AUTOMATED CHECK ONLY -- PubMed article_types carries no Retracted/EoC/Corrected tag; NOT sufficient alone, human must check publisher corrections page + Retraction Watch directly.
- [ ] Temporally eligible -- PASS.
- [ ] Independent of treated claim -- No proximity concern flagged during sourcing.
- [ ] No leakage -- PASS -- 0 findings against 89 treated-item identifiers.
- [ ] Acceptable evidence tier -- systematic_review_meta_analysis.

---

## CC-034 -- for RB-0016

1. **Treated item ID:** RB-0016
2. **Control candidate ID:** CC-034 (rank 2)
3. **Candidate title:** The effect of delayed cord clamping on early cardiac and cerebral hemodynamics, mortality, and severe intraventricular hemorrhage in preterm infants < 32 weeks: a systematic review and meta-analysis of clinical trials.
4. **Authors:** Aljohani E, Goyal M.
5. **PMID:** 40009183
6. **DOI:** 10.1007/s00431-025-06026-7
7. **Primary source URL:** https://pubmed.ncbi.nlm.nih.gov/40009183/
8. **Publisher URL:** https://doi.org/10.1007/s00431-025-06026-7
9. **Publication date:** 2025-02-26 (European Journal of Pediatrics)
10. **Why it matches the treated item:** Domain and claim_type match exactly (hard constraints). Intervention/topic: delayed cord clamping vs immediate clamping/milking (preterm <32wk). Claim shape: 15-study meta-analysis, n=2967. Soft-preference notes: polarity: match; intervention_class/claim_shape: logged, not scored
11. **Evidence supporting non-superseded status:** NEEDS_HUMAN_VERIFICATION (automated check: PubMed article_types field contains no Retracted Publication / Expression of Concern / Corrected and Republished Article tag as of this search)
12. **PubMed status evidence:** `article_types` = Journal Article; Systematic Review; Meta-Analysis; no Retracted Publication / Expression of Concern / Corrected and Republished Article tag present as of the search date this session.
13. **Publisher status evidence:** NOT YET CHECKED by this process -- publisher corrections/errata page must be checked directly by the human reviewer; this is exactly the gap `docs/ANNOTATION.md` section 3.2's standard exists to close.
14. **Correction / expression-of-concern check:** NEEDS_HUMAN_VERIFICATION / NEEDS_HUMAN_VERIFICATION -- automated PubMed-tag check only, not a publisher-level confirmation.
15. **Temporal eligibility:** PASS (corpus freeze date 2026-08-09; publication date 2025-02-26).
16. **Leakage result:** 0 findings (checked against all 89 treated-item source/evidence identifiers, scripts/check_control_leakage.py).
17. **Exact question the human must answer:** Verify that PMID 40009183 (DOI 10.1007/s00431-025-06026-7) has no retraction, expression of concern, or major correction affecting the cited claim, checked (a) as of the corpus freeze date 2026-08-09 and (b) as of today. Confirm the claim itself has not been superseded under this project's own supersession_type taxonomy (retraction / expression_of_concern / major_correction / guideline_revision / evidence_superseded). Additionally: Backup candidate (rank 2) for RB-0016, same intervention family (cord clamping/management) as CC-033, narrower population. Left for human reviewer to pick.
18. **Recommended decision (machine-generated only -- NOT a verification):** UNCERTAIN -- A specific proximity/evidence-shape concern was flagged during sourcing (see note below) -- needs a human judgment call, not a clean pass.

**Checklist (human completes):**

- [ ] Human clinical evidence -- PASS -- confirmed human clinical/biomedical study (species checked during sourcing).
- [ ] Same hard domain -- PASS -- (HSC) Medicine - Obstetrics/Gynecology matches by construction.
- [ ] Same claim type -- PASS -- clinical_intervention matches by construction.
- [ ] Same question form -- PASS -- question_form=quantitative.
- [ ] Non-superseded -- AUTOMATED CHECK ONLY -- PubMed article_types carries no Retracted/EoC/Corrected tag; NOT sufficient alone, human must check publisher corrections page + Retraction Watch directly.
- [ ] Temporally eligible -- PASS.
- [ ] Independent of treated claim -- CHECK NOTE BELOW
- [ ] No leakage -- PASS -- 0 findings against 89 treated-item identifiers.
- [ ] Acceptable evidence tier -- systematic_review_meta_analysis.

---

## CC-004 -- for RB-0017

1. **Treated item ID:** RB-0017
2. **Control candidate ID:** CC-004 (rank 1)
3. **Candidate title:** Postoperative oral cephalexin and metronidazole effectiveness in preventing complications in obese pregnant women undergoing cesarean delivery: A systematic review and meta-analysis.
4. **Authors:** Oliveira JA, Lemos MJ, Dias YJM, et al.
5. **PMID:** 41785716
6. **DOI:** 10.1016/j.ejogrb.2026.115039
7. **Primary source URL:** https://pubmed.ncbi.nlm.nih.gov/41785716/
8. **Publisher URL:** https://doi.org/10.1016/j.ejogrb.2026.115039
9. **Publication date:** 2026-03-01 (European Journal of Obstetrics, Gynecology, and Reproductive Biology)
10. **Why it matches the treated item:** Domain and claim_type match exactly (hard constraints). Intervention/topic: postoperative oral antibiotics (cesarean SSI prevention). Claim shape: 3-RCT meta-analysis, single intervention vs standard prophylaxis. Soft-preference notes: polarity: match; intervention_class/claim_shape: logged, not scored
11. **Evidence supporting non-superseded status:** NEEDS_HUMAN_VERIFICATION (automated check: PubMed article_types field contains no Retracted Publication / Expression of Concern / Corrected and Republished Article tag as of this search)
12. **PubMed status evidence:** `article_types` = Journal Article; Systematic Review; Meta-Analysis; no Retracted Publication / Expression of Concern / Corrected and Republished Article tag present as of the search date this session.
13. **Publisher status evidence:** NOT YET CHECKED by this process -- publisher corrections/errata page must be checked directly by the human reviewer; this is exactly the gap `docs/ANNOTATION.md` section 3.2's standard exists to close.
14. **Correction / expression-of-concern check:** NEEDS_HUMAN_VERIFICATION / NEEDS_HUMAN_VERIFICATION -- automated PubMed-tag check only, not a publisher-level confirmation.
15. **Temporal eligibility:** PASS (corpus freeze date 2026-08-09; publication date 2026-03-01).
16. **Leakage result:** 0 findings (checked against all 89 treated-item source/evidence identifiers, scripts/check_control_leakage.py).
17. **Exact question the human must answer:** Verify that PMID 41785716 (DOI 10.1016/j.ejogrb.2026.115039) has no retraction, expression of concern, or major correction affecting the cited claim, checked (a) as of the corpus freeze date 2026-08-09 and (b) as of today. Confirm the claim itself has not been superseded under this project's own supersession_type taxonomy (retraction / expression_of_concern / major_correction / guideline_revision / evidence_superseded). 
18. **Recommended decision (machine-generated only -- NOT a verification):** APPROVE (preliminary) -- All automated checks available ran clean: hard constraints match, temporal check passes, no leakage, no proximity/evidence-shape flag raised during sourcing.

**Checklist (human completes):**

- [ ] Human clinical evidence -- PASS -- confirmed human clinical/biomedical study (species checked during sourcing).
- [ ] Same hard domain -- PASS -- (HSC) Medicine - Obstetrics/Gynecology matches by construction.
- [ ] Same claim type -- PASS -- clinical_intervention matches by construction.
- [ ] Same question form -- PASS -- question_form=quantitative.
- [ ] Non-superseded -- AUTOMATED CHECK ONLY -- PubMed article_types carries no Retracted/EoC/Corrected tag; NOT sufficient alone, human must check publisher corrections page + Retraction Watch directly.
- [ ] Temporally eligible -- PASS.
- [ ] Independent of treated claim -- No proximity concern flagged during sourcing.
- [ ] No leakage -- PASS -- 0 findings against 89 treated-item identifiers.
- [ ] Acceptable evidence tier -- systematic_review_meta_analysis.

---

## CC-005 -- for RB-0018

1. **Treated item ID:** RB-0018
2. **Control candidate ID:** CC-005 (rank 1)
3. **Candidate title:** Can universal cervical length screening with vaginal progesterone for a short cervix reduce preterm birth? A systematic review and meta-analyses.
4. **Authors:** Zethelius M, Bergman L, Ekelund AC, et al.
5. **PMID:** 42161360
6. **DOI:** 10.1111/aogs.70253
7. **Primary source URL:** https://pubmed.ncbi.nlm.nih.gov/42161360/
8. **Publisher URL:** https://doi.org/10.1111/aogs.70253
9. **Publication date:** 2026-05-20 (Acta Obstetricia et Gynecologica Scandinavica)
10. **Why it matches the treated item:** Domain and claim_type match exactly (hard constraints). Intervention/topic: cervical length screening + vaginal progesterone (preterm birth prevention). Claim shape: systematic review, RCT + cohort evidence, GRADE-assessed, PROSPERO-registered. Soft-preference notes: polarity: match; intervention_class/claim_shape: logged, not scored
11. **Evidence supporting non-superseded status:** NEEDS_HUMAN_VERIFICATION (automated check: PubMed article_types field contains no Retracted Publication / Expression of Concern / Corrected and Republished Article tag as of this search)
12. **PubMed status evidence:** `article_types` = Journal Article; Systematic Review; Meta-Analysis; no Retracted Publication / Expression of Concern / Corrected and Republished Article tag present as of the search date this session.
13. **Publisher status evidence:** NOT YET CHECKED by this process -- publisher corrections/errata page must be checked directly by the human reviewer; this is exactly the gap `docs/ANNOTATION.md` section 3.2's standard exists to close.
14. **Correction / expression-of-concern check:** NEEDS_HUMAN_VERIFICATION / NEEDS_HUMAN_VERIFICATION -- automated PubMed-tag check only, not a publisher-level confirmation.
15. **Temporal eligibility:** PASS (corpus freeze date 2026-08-09; publication date 2026-05-20).
16. **Leakage result:** 0 findings (checked against all 89 treated-item source/evidence identifiers, scripts/check_control_leakage.py).
17. **Exact question the human must answer:** Verify that PMID 42161360 (DOI 10.1111/aogs.70253) has no retraction, expression of concern, or major correction affecting the cited claim, checked (a) as of the corpus freeze date 2026-08-09 and (b) as of today. Confirm the claim itself has not been superseded under this project's own supersession_type taxonomy (retraction / expression_of_concern / major_correction / guideline_revision / evidence_superseded). 
18. **Recommended decision (machine-generated only -- NOT a verification):** APPROVE (preliminary) -- All automated checks available ran clean: hard constraints match, temporal check passes, no leakage, no proximity/evidence-shape flag raised during sourcing.

**Checklist (human completes):**

- [ ] Human clinical evidence -- PASS -- confirmed human clinical/biomedical study (species checked during sourcing).
- [ ] Same hard domain -- PASS -- (HSC) Medicine - Obstetrics/Gynecology matches by construction.
- [ ] Same claim type -- PASS -- clinical_intervention matches by construction.
- [ ] Same question form -- PASS -- question_form=quantitative.
- [ ] Non-superseded -- AUTOMATED CHECK ONLY -- PubMed article_types carries no Retracted/EoC/Corrected tag; NOT sufficient alone, human must check publisher corrections page + Retraction Watch directly.
- [ ] Temporally eligible -- PASS.
- [ ] Independent of treated claim -- No proximity concern flagged during sourcing.
- [ ] No leakage -- PASS -- 0 findings against 89 treated-item identifiers.
- [ ] Acceptable evidence tier -- systematic_review_meta_analysis.

---

## CC-001 -- for RB-0019

1. **Treated item ID:** RB-0019
2. **Control candidate ID:** CC-001 (rank 1)
3. **Candidate title:** Does gabapentin add value to multimodal analgesia in thoracic surgery? A procedure-specific meta-analysis.
4. **Authors:** Lemos Gonzalez G, Felippe VA, Wegner BFM, et al.
5. **PMID:** 42371403
6. **DOI:** 10.1080/17581869.2026.2694372
7. **Primary source URL:** https://pubmed.ncbi.nlm.nih.gov/42371403/
8. **Publisher URL:** https://doi.org/10.1080/17581869.2026.2694372
9. **Publication date:** 2026-06-29 (Pain Management)
10. **Why it matches the treated item:** Domain and claim_type match exactly (hard constraints). Intervention/topic: gabapentin (perioperative analgesic adjunct). Claim shape: two-arm RCT meta-analysis, single intervention vs placebo. Soft-preference notes: polarity: match; intervention_class/claim_shape: logged, not scored
11. **Evidence supporting non-superseded status:** NEEDS_HUMAN_VERIFICATION (automated check: PubMed article_types field contains no Retracted Publication / Expression of Concern / Corrected and Republished Article tag as of this search)
12. **PubMed status evidence:** `article_types` = Journal Article; Review; no Retracted Publication / Expression of Concern / Corrected and Republished Article tag present as of the search date this session.
13. **Publisher status evidence:** NOT YET CHECKED by this process -- publisher corrections/errata page must be checked directly by the human reviewer; this is exactly the gap `docs/ANNOTATION.md` section 3.2's standard exists to close.
14. **Correction / expression-of-concern check:** NEEDS_HUMAN_VERIFICATION / NEEDS_HUMAN_VERIFICATION -- automated PubMed-tag check only, not a publisher-level confirmation.
15. **Temporal eligibility:** PASS (corpus freeze date 2026-08-09; publication date 2026-06-29).
16. **Leakage result:** 0 findings (checked against all 89 treated-item source/evidence identifiers, scripts/check_control_leakage.py).
17. **Exact question the human must answer:** Verify that PMID 42371403 (DOI 10.1080/17581869.2026.2694372) has no retraction, expression of concern, or major correction affecting the cited claim, checked (a) as of the corpus freeze date 2026-08-09 and (b) as of today. Confirm the claim itself has not been superseded under this project's own supersession_type taxonomy (retraction / expression_of_concern / major_correction / guideline_revision / evidence_superseded). 
18. **Recommended decision (machine-generated only -- NOT a verification):** APPROVE (preliminary) -- All automated checks available ran clean: hard constraints match, temporal check passes, no leakage, no proximity/evidence-shape flag raised during sourcing.

**Checklist (human completes):**

- [ ] Human clinical evidence -- PASS -- confirmed human clinical/biomedical study (species checked during sourcing).
- [ ] Same hard domain -- PASS -- (HSC) Medicine - Pharmacology matches by construction.
- [ ] Same claim type -- PASS -- clinical_intervention matches by construction.
- [ ] Same question form -- PASS -- question_form=quantitative.
- [ ] Non-superseded -- AUTOMATED CHECK ONLY -- PubMed article_types carries no Retracted/EoC/Corrected tag; NOT sufficient alone, human must check publisher corrections page + Retraction Watch directly.
- [ ] Temporally eligible -- PASS.
- [ ] Independent of treated claim -- No proximity concern flagged during sourcing.
- [ ] No leakage -- PASS -- 0 findings against 89 treated-item identifiers.
- [ ] Acceptable evidence tier -- systematic_review_meta_analysis.

---

## CC-006 -- for RB-0021

1. **Treated item ID:** RB-0021
2. **Control candidate ID:** CC-006 (rank 1)
3. **Candidate title:** Efficacy of sequential letrozole and gonadotropin therapy for ovulation induction in women with polycystic ovary syndrome: a systematic review and meta-analysis.
4. **Authors:** Sajjad W, Saddique MN, Shahid F, et al.
5. **PMID:** 41496930
6. **DOI:** 10.1097/MS9.0000000000004506
7. **Primary source URL:** https://pubmed.ncbi.nlm.nih.gov/41496930/
8. **Publisher URL:** https://doi.org/10.1097/MS9.0000000000004506
9. **Publication date:** 2025-12-04 (Annals of Medicine and Surgery)
10. **Why it matches the treated item:** Domain and claim_type match exactly (hard constraints). Intervention/topic: letrozole + gonadotropin (ovulation induction, PCOS). Claim shape: 8-RCT meta-analysis, single combination regimen vs alternatives. Soft-preference notes: polarity: match; intervention_class/claim_shape: logged, not scored
11. **Evidence supporting non-superseded status:** NEEDS_HUMAN_VERIFICATION (automated check: PubMed article_types field contains no Retracted Publication / Expression of Concern / Corrected and Republished Article tag as of this search)
12. **PubMed status evidence:** `article_types` = Journal Article; no Retracted Publication / Expression of Concern / Corrected and Republished Article tag present as of the search date this session.
13. **Publisher status evidence:** NOT YET CHECKED by this process -- publisher corrections/errata page must be checked directly by the human reviewer; this is exactly the gap `docs/ANNOTATION.md` section 3.2's standard exists to close.
14. **Correction / expression-of-concern check:** NEEDS_HUMAN_VERIFICATION / NEEDS_HUMAN_VERIFICATION -- automated PubMed-tag check only, not a publisher-level confirmation.
15. **Temporal eligibility:** PASS (corpus freeze date 2026-08-09; publication date 2025-12-04).
16. **Leakage result:** 0 findings (checked against all 89 treated-item source/evidence identifiers, scripts/check_control_leakage.py).
17. **Exact question the human must answer:** Verify that PMID 41496930 (DOI 10.1097/MS9.0000000000004506) has no retraction, expression of concern, or major correction affecting the cited claim, checked (a) as of the corpus freeze date 2026-08-09 and (b) as of today. Confirm the claim itself has not been superseded under this project's own supersession_type taxonomy (retraction / expression_of_concern / major_correction / guideline_revision / evidence_superseded). Additionally: TOPICAL PROXIMITY FLAG: both this candidate and RB-0021 concern ART/fertility interventions (different specific interventions -- embryo transfer timing vs. ovulation induction -- but same fertility-treatment subfield). Not a disguised replacement (different trial, different specific claim), but closer than ideal on intervention_class; human reviewer should confirm this is an acceptable match, not simply accept it.
18. **Recommended decision (machine-generated only -- NOT a verification):** UNCERTAIN -- A specific proximity/evidence-shape concern was flagged during sourcing (see note below) -- needs a human judgment call, not a clean pass.

**Checklist (human completes):**

- [ ] Human clinical evidence -- PASS -- confirmed human clinical/biomedical study (species checked during sourcing).
- [ ] Same hard domain -- PASS -- (HSC) Medicine - Obstetrics/Gynecology matches by construction.
- [ ] Same claim type -- PASS -- clinical_intervention matches by construction.
- [ ] Same question form -- PASS -- question_form=quantitative.
- [ ] Non-superseded -- AUTOMATED CHECK ONLY -- PubMed article_types carries no Retracted/EoC/Corrected tag; NOT sufficient alone, human must check publisher corrections page + Retraction Watch directly.
- [ ] Temporally eligible -- PASS.
- [ ] Independent of treated claim -- CHECK NOTE BELOW
- [ ] No leakage -- PASS -- 0 findings against 89 treated-item identifiers.
- [ ] Acceptable evidence tier -- systematic_review_meta_analysis.

---

## CC-020 -- for RB-0022

1. **Treated item ID:** RB-0022
2. **Control candidate ID:** CC-020 (rank 1)
3. **Candidate title:** Misoprostol combined with cervical single or double balloon catheters versus misoprostol alone for labor induction of singleton pregnancies: a meta-analysis of randomized trials.
4. **Authors:** Ornat L, Alonso-Ventura V, Bueno-Notivol J, Chedraui P, Perez-Lopez FR.
5. **PMID:** 30741051
6. **DOI:** 10.1080/14767058.2019.1574741
7. **Primary source URL:** https://pubmed.ncbi.nlm.nih.gov/30741051/
8. **Publisher URL:** https://doi.org/10.1080/14767058.2019.1574741
9. **Publication date:** 2019-02-10 (Journal of Maternal-Fetal & Neonatal Medicine)
10. **Why it matches the treated item:** Domain and claim_type match exactly (hard constraints). Intervention/topic: misoprostol + balloon catheter vs misoprostol alone (labor induction). Claim shape: 15-RCT meta-analysis. Soft-preference notes: polarity: match; intervention_class/claim_shape: logged, not scored
11. **Evidence supporting non-superseded status:** NEEDS_HUMAN_VERIFICATION (automated check: PubMed article_types field contains no Retracted Publication / Expression of Concern / Corrected and Republished Article tag as of this search)
12. **PubMed status evidence:** `article_types` = Journal Article; Meta-Analysis; Systematic Review; no Retracted Publication / Expression of Concern / Corrected and Republished Article tag present as of the search date this session.
13. **Publisher status evidence:** NOT YET CHECKED by this process -- publisher corrections/errata page must be checked directly by the human reviewer; this is exactly the gap `docs/ANNOTATION.md` section 3.2's standard exists to close.
14. **Correction / expression-of-concern check:** NEEDS_HUMAN_VERIFICATION / NEEDS_HUMAN_VERIFICATION -- automated PubMed-tag check only, not a publisher-level confirmation.
15. **Temporal eligibility:** PASS (corpus freeze date 2026-08-09; publication date 2019-02-10).
16. **Leakage result:** 0 findings (checked against all 89 treated-item source/evidence identifiers, scripts/check_control_leakage.py).
17. **Exact question the human must answer:** Verify that PMID 30741051 (DOI 10.1080/14767058.2019.1574741) has no retraction, expression of concern, or major correction affecting the cited claim, checked (a) as of the corpus freeze date 2026-08-09 and (b) as of today. Confirm the claim itself has not been superseded under this project's own supersession_type taxonomy (retraction / expression_of_concern / major_correction / guideline_revision / evidence_superseded). Additionally: TOPICAL PROXIMITY FLAG: uses misoprostol, the same drug as RB-0016's own trap claim (repeat misoprostol vs expectant management for miscarriage) -- assigned to RB-0022 (exercise/male infertility) instead specifically to avoid that overlap, since RB-0022 has no drug/topic relation to misoprostol at all. Flagged for the record regardless.
18. **Recommended decision (machine-generated only -- NOT a verification):** UNCERTAIN -- A specific proximity/evidence-shape concern was flagged during sourcing (see note below) -- needs a human judgment call, not a clean pass.

**Checklist (human completes):**

- [ ] Human clinical evidence -- PASS -- confirmed human clinical/biomedical study (species checked during sourcing).
- [ ] Same hard domain -- PASS -- (HSC) Medicine - Obstetrics/Gynecology matches by construction.
- [ ] Same claim type -- PASS -- clinical_intervention matches by construction.
- [ ] Same question form -- PASS -- question_form=quantitative.
- [ ] Non-superseded -- AUTOMATED CHECK ONLY -- PubMed article_types carries no Retracted/EoC/Corrected tag; NOT sufficient alone, human must check publisher corrections page + Retraction Watch directly.
- [ ] Temporally eligible -- PASS.
- [ ] Independent of treated claim -- CHECK NOTE BELOW
- [ ] No leakage -- PASS -- 0 findings against 89 treated-item identifiers.
- [ ] Acceptable evidence tier -- systematic_review_meta_analysis.

---

## CC-002 -- for RB-0023

1. **Treated item ID:** RB-0023
2. **Control candidate ID:** CC-002 (rank 1)
3. **Candidate title:** Optimizing diabetes care in pregnancy: A systematic review of glycemic targets, treatment initiation, and glucose-lowering pharmacological management for T1DM, T2DM, and GDM.
4. **Authors:** Villanueva G, Cogo E, Buckley B, et al. (Cochrane Response)
5. **PMID:** 42597015
6. **DOI:** 10.1002/pmf2.70224
7. **Primary source URL:** https://pubmed.ncbi.nlm.nih.gov/42597015/
8. **Publisher URL:** https://doi.org/10.1002/pmf2.70224
9. **Publication date:** 2026-03-06 (Pregnancy (Hoboken, N.J.))
10. **Why it matches the treated item:** Domain and claim_type match exactly (hard constraints). Intervention/topic: metformin/insulin/glibenclamide (glycemic management in pregnancy). Claim shape: multi-arm systematic review, Cochrane-standard methods, WHO-outcome-aligned. Soft-preference notes: polarity: match; intervention_class/claim_shape: logged, not scored
11. **Evidence supporting non-superseded status:** NEEDS_HUMAN_VERIFICATION (automated check: PubMed article_types field contains no Retracted Publication / Expression of Concern / Corrected and Republished Article tag as of this search)
12. **PubMed status evidence:** `article_types` = Journal Article; Review; no Retracted Publication / Expression of Concern / Corrected and Republished Article tag present as of the search date this session.
13. **Publisher status evidence:** NOT YET CHECKED by this process -- publisher corrections/errata page must be checked directly by the human reviewer; this is exactly the gap `docs/ANNOTATION.md` section 3.2's standard exists to close.
14. **Correction / expression-of-concern check:** NEEDS_HUMAN_VERIFICATION / NEEDS_HUMAN_VERIFICATION -- automated PubMed-tag check only, not a publisher-level confirmation.
15. **Temporal eligibility:** PASS (corpus freeze date 2026-08-09; publication date 2026-03-06).
16. **Leakage result:** 0 findings (checked against all 89 treated-item source/evidence identifiers, scripts/check_control_leakage.py).
17. **Exact question the human must answer:** Verify that PMID 42597015 (DOI 10.1002/pmf2.70224) has no retraction, expression of concern, or major correction affecting the cited claim, checked (a) as of the corpus freeze date 2026-08-09 and (b) as of today. Confirm the claim itself has not been superseded under this project's own supersession_type taxonomy (retraction / expression_of_concern / major_correction / guideline_revision / evidence_superseded). 
18. **Recommended decision (machine-generated only -- NOT a verification):** APPROVE (preliminary) -- All automated checks available ran clean: hard constraints match, temporal check passes, no leakage, no proximity/evidence-shape flag raised during sourcing.

**Checklist (human completes):**

- [ ] Human clinical evidence -- PASS -- confirmed human clinical/biomedical study (species checked during sourcing).
- [ ] Same hard domain -- PASS -- (HSC) Medicine - Pharmacology matches by construction.
- [ ] Same claim type -- PASS -- clinical_intervention matches by construction.
- [ ] Same question form -- PASS -- question_form=quantitative.
- [ ] Non-superseded -- AUTOMATED CHECK ONLY -- PubMed article_types carries no Retracted/EoC/Corrected tag; NOT sufficient alone, human must check publisher corrections page + Retraction Watch directly.
- [ ] Temporally eligible -- PASS.
- [ ] Independent of treated claim -- No proximity concern flagged during sourcing.
- [ ] No leakage -- PASS -- 0 findings against 89 treated-item identifiers.
- [ ] Acceptable evidence tier -- systematic_review_meta_analysis_cochrane_methods.

---

## CC-035 -- for RB-0025

1. **Treated item ID:** RB-0025
2. **Control candidate ID:** CC-035 (rank 1)
3. **Candidate title:** Probiotics are effective at preventing Clostridium difficile-associated diarrhea: a systematic review and meta-analysis.
4. **Authors:** Lau CS, Chamberlain RS.
5. **PMID:** 26955289
6. **DOI:** 10.2147/IJGM.S98280
7. **Primary source URL:** https://pubmed.ncbi.nlm.nih.gov/26955289/
8. **Publisher URL:** https://doi.org/10.2147/IJGM.S98280
9. **Publication date:** 2016-02-22 (International Journal of General Medicine)
10. **Why it matches the treated item:** Domain and claim_type match exactly (hard constraints). Intervention/topic: probiotic supplementation (antibiotic-associated / C. difficile diarrhea prevention). Claim shape: 26-RCT meta-analysis, n=7957. Soft-preference notes: polarity: match; intervention_class/claim_shape: logged, not scored
11. **Evidence supporting non-superseded status:** NEEDS_HUMAN_VERIFICATION (automated check: PubMed article_types field contains no Retracted Publication / Expression of Concern / Corrected and Republished Article tag as of this search)
12. **PubMed status evidence:** `article_types` = Journal Article; no Retracted Publication / Expression of Concern / Corrected and Republished Article tag present as of the search date this session.
13. **Publisher status evidence:** NOT YET CHECKED by this process -- publisher corrections/errata page must be checked directly by the human reviewer; this is exactly the gap `docs/ANNOTATION.md` section 3.2's standard exists to close.
14. **Correction / expression-of-concern check:** NEEDS_HUMAN_VERIFICATION / NEEDS_HUMAN_VERIFICATION -- automated PubMed-tag check only, not a publisher-level confirmation.
15. **Temporal eligibility:** PASS (corpus freeze date 2026-08-09; publication date 2016-02-22).
16. **Leakage result:** 0 findings (checked against all 89 treated-item source/evidence identifiers, scripts/check_control_leakage.py).
17. **Exact question the human must answer:** Verify that PMID 26955289 (DOI 10.2147/IJGM.S98280) has no retraction, expression of concern, or major correction affecting the cited claim, checked (a) as of the corpus freeze date 2026-08-09 and (b) as of today. Confirm the claim itself has not been superseded under this project's own supersession_type taxonomy (retraction / expression_of_concern / major_correction / guideline_revision / evidence_superseded). 
18. **Recommended decision (machine-generated only -- NOT a verification):** APPROVE (preliminary) -- All automated checks available ran clean: hard constraints match, temporal check passes, no leakage, no proximity/evidence-shape flag raised during sourcing.

**Checklist (human completes):**

- [ ] Human clinical evidence -- PASS -- confirmed human clinical/biomedical study (species checked during sourcing).
- [ ] Same hard domain -- PASS -- (HSC) Medicine - Pharmacology matches by construction.
- [ ] Same claim type -- PASS -- clinical_intervention matches by construction.
- [ ] Same question form -- PASS -- question_form=quantitative.
- [ ] Non-superseded -- AUTOMATED CHECK ONLY -- PubMed article_types carries no Retracted/EoC/Corrected tag; NOT sufficient alone, human must check publisher corrections page + Retraction Watch directly.
- [ ] Temporally eligible -- PASS.
- [ ] Independent of treated claim -- No proximity concern flagged during sourcing.
- [ ] No leakage -- PASS -- 0 findings against 89 treated-item identifiers.
- [ ] Acceptable evidence tier -- systematic_review_meta_analysis.

---

## CC-036 -- for RB-0025

1. **Treated item ID:** RB-0025
2. **Control candidate ID:** CC-036 (rank 2)
3. **Candidate title:** A Systematic Review, Meta-Analysis, and Meta-Regression Evaluating the Efficacy and Mechanisms of Action of Probiotics and Synbiotics in the Prevention of Surgical Site Infections and Surgery-Related Complications.
4. **Authors:** Skonieczna-Zydecka K, Kaczmarczyk M, Loniewski I, et al.
5. **PMID:** 30558358
6. **DOI:** 10.3390/jcm7120556
7. **Primary source URL:** https://pubmed.ncbi.nlm.nih.gov/30558358/
8. **Publisher URL:** https://doi.org/10.3390/jcm7120556
9. **Publication date:** 2018-12-16 (Journal of Clinical Medicine)
10. **Why it matches the treated item:** Domain and claim_type match exactly (hard constraints). Intervention/topic: probiotics/synbiotics (surgical site infection prevention). Claim shape: 35-trial meta-analysis + meta-regression, n=3028. Soft-preference notes: polarity: match; intervention_class/claim_shape: logged, not scored
11. **Evidence supporting non-superseded status:** NEEDS_HUMAN_VERIFICATION (automated check: PubMed article_types field contains no Retracted Publication / Expression of Concern / Corrected and Republished Article tag as of this search)
12. **PubMed status evidence:** `article_types` = Journal Article; no Retracted Publication / Expression of Concern / Corrected and Republished Article tag present as of the search date this session.
13. **Publisher status evidence:** NOT YET CHECKED by this process -- publisher corrections/errata page must be checked directly by the human reviewer; this is exactly the gap `docs/ANNOTATION.md` section 3.2's standard exists to close.
14. **Correction / expression-of-concern check:** NEEDS_HUMAN_VERIFICATION / NEEDS_HUMAN_VERIFICATION -- automated PubMed-tag check only, not a publisher-level confirmation.
15. **Temporal eligibility:** PASS (corpus freeze date 2026-08-09; publication date 2018-12-16).
16. **Leakage result:** 0 findings (checked against all 89 treated-item source/evidence identifiers, scripts/check_control_leakage.py).
17. **Exact question the human must answer:** Verify that PMID 30558358 (DOI 10.3390/jcm7120556) has no retraction, expression of concern, or major correction affecting the cited claim, checked (a) as of the corpus freeze date 2026-08-09 and (b) as of today. Confirm the claim itself has not been superseded under this project's own supersession_type taxonomy (retraction / expression_of_concern / major_correction / guideline_revision / evidence_superseded). Additionally: Backup candidate (rank 2) for RB-0025, same intervention class (probiotics) as CC-035, different indication (SSI vs C. diff diarrhea). Left for human reviewer to pick.
18. **Recommended decision (machine-generated only -- NOT a verification):** UNCERTAIN -- A specific proximity/evidence-shape concern was flagged during sourcing (see note below) -- needs a human judgment call, not a clean pass.

**Checklist (human completes):**

- [ ] Human clinical evidence -- PASS -- confirmed human clinical/biomedical study (species checked during sourcing).
- [ ] Same hard domain -- PASS -- (HSC) Medicine - Pharmacology matches by construction.
- [ ] Same claim type -- PASS -- clinical_intervention matches by construction.
- [ ] Same question form -- PASS -- question_form=quantitative.
- [ ] Non-superseded -- AUTOMATED CHECK ONLY -- PubMed article_types carries no Retracted/EoC/Corrected tag; NOT sufficient alone, human must check publisher corrections page + Retraction Watch directly.
- [ ] Temporally eligible -- PASS.
- [ ] Independent of treated claim -- CHECK NOTE BELOW
- [ ] No leakage -- PASS -- 0 findings against 89 treated-item identifiers.
- [ ] Acceptable evidence tier -- systematic_review_meta_analysis.

---

## CC-016 -- for RB-0026

1. **Treated item ID:** RB-0026
2. **Control candidate ID:** CC-016 (rank 1)
3. **Candidate title:** Cure Rates of Control Interventions in Randomized Trials of Onychomycosis Treatments.
4. **Authors:** Gupta AK, Venkataraman M, Quinlan EM, Bamimore MA.
5. **PMID:** 34121113
6. **DOI:** 10.7547/20-226
7. **Primary source URL:** https://pubmed.ncbi.nlm.nih.gov/34121113/
8. **Publisher URL:** https://doi.org/10.7547/20-226
9. **Publication date:** 2022 (Journal of the American Podiatric Medical Association)
10. **Why it matches the treated item:** Domain and claim_type match exactly (hard constraints). Intervention/topic: placebo/vehicle control-arm cure rates (onychomycosis). Claim shape: 19-trial meta-analysis of CONTROL-arm effect sizes, not an active-drug efficacy claim. Soft-preference notes: polarity: match; intervention_class/claim_shape: logged, not scored
11. **Evidence supporting non-superseded status:** NEEDS_HUMAN_VERIFICATION (automated check: PubMed article_types field contains no Retracted Publication / Expression of Concern / Corrected and Republished Article tag as of this search)
12. **PubMed status evidence:** `article_types` = Journal Article; Meta-Analysis; Systematic Review; no Retracted Publication / Expression of Concern / Corrected and Republished Article tag present as of the search date this session.
13. **Publisher status evidence:** NOT YET CHECKED by this process -- publisher corrections/errata page must be checked directly by the human reviewer; this is exactly the gap `docs/ANNOTATION.md` section 3.2's standard exists to close.
14. **Correction / expression-of-concern check:** NEEDS_HUMAN_VERIFICATION / NEEDS_HUMAN_VERIFICATION -- automated PubMed-tag check only, not a publisher-level confirmation.
15. **Temporal eligibility:** PASS (corpus freeze date 2026-08-09; publication date 2022).
16. **Leakage result:** 0 findings (checked against all 89 treated-item source/evidence identifiers, scripts/check_control_leakage.py).
17. **Exact question the human must answer:** Verify that PMID 34121113 (DOI 10.7547/20-226) has no retraction, expression of concern, or major correction affecting the cited claim, checked (a) as of the corpus freeze date 2026-08-09 and (b) as of today. Confirm the claim itself has not been superseded under this project's own supersession_type taxonomy (retraction / expression_of_concern / major_correction / guideline_revision / evidence_superseded). Additionally: EVIDENCE-SHAPE FLAG: unlike other candidates, this meta-analysis characterizes placebo/vehicle cure rates rather than an active intervention's efficacy claim -- atypical fit for a 'current authoritative answer' in the same sense as RB-0026's own NSAID claim. Human reviewer should judge whether this evidence shape is acceptable or whether a direct active-drug meta-analysis should be sought instead.
18. **Recommended decision (machine-generated only -- NOT a verification):** UNCERTAIN -- A specific proximity/evidence-shape concern was flagged during sourcing (see note below) -- needs a human judgment call, not a clean pass.

**Checklist (human completes):**

- [ ] Human clinical evidence -- PASS -- confirmed human clinical/biomedical study (species checked during sourcing).
- [ ] Same hard domain -- PASS -- (HSC) Medicine - Pharmacology matches by construction.
- [ ] Same claim type -- PASS -- clinical_intervention matches by construction.
- [ ] Same question form -- PASS -- question_form=quantitative.
- [ ] Non-superseded -- AUTOMATED CHECK ONLY -- PubMed article_types carries no Retracted/EoC/Corrected tag; NOT sufficient alone, human must check publisher corrections page + Retraction Watch directly.
- [ ] Temporally eligible -- PASS.
- [ ] Independent of treated claim -- CHECK NOTE BELOW
- [ ] No leakage -- PASS -- 0 findings against 89 treated-item identifiers.
- [ ] Acceptable evidence tier -- systematic_review_meta_analysis.

---

## CC-021 -- for RB-0028

1. **Treated item ID:** RB-0028
2. **Control candidate ID:** CC-021 (rank 1)
3. **Candidate title:** Association between markers of female adiposity and live birth among patients undergoing fertility treatment or attempting unassisted conception.
4. **Authors:** Lee IT, Barnhart KT, Hwang WT, et al.
5. **PMID:** 40605077
6. **DOI:** 10.1093/humrep/deaf124
7. **Primary source URL:** https://pubmed.ncbi.nlm.nih.gov/40605077/
8. **Publisher URL:** https://doi.org/10.1093/humrep/deaf124
9. **Publication date:** 2025-09-01 (Human Reproduction)
10. **Why it matches the treated item:** Domain and claim_type match exactly (hard constraints). Intervention/topic: N/A (observational: adiposity biomarkers vs live birth). Claim shape: secondary analysis of RCT-recruited cohort (FAZST), n=2370 couples. Soft-preference notes: polarity: match; intervention_class/claim_shape: logged, not scored
11. **Evidence supporting non-superseded status:** NEEDS_HUMAN_VERIFICATION (automated check: PubMed article_types field contains no Retracted Publication / Expression of Concern / Corrected and Republished Article tag as of this search)
12. **PubMed status evidence:** `article_types` = Journal Article; Randomized Controlled Trial; Research Support, N.I.H., Intramural; no Retracted Publication / Expression of Concern / Corrected and Republished Article tag present as of the search date this session.
13. **Publisher status evidence:** NOT YET CHECKED by this process -- publisher corrections/errata page must be checked directly by the human reviewer; this is exactly the gap `docs/ANNOTATION.md` section 3.2's standard exists to close.
14. **Correction / expression-of-concern check:** NEEDS_HUMAN_VERIFICATION / NEEDS_HUMAN_VERIFICATION -- automated PubMed-tag check only, not a publisher-level confirmation.
15. **Temporal eligibility:** PASS (corpus freeze date 2026-08-09; publication date 2025-09-01).
16. **Leakage result:** 0 findings (checked against all 89 treated-item source/evidence identifiers, scripts/check_control_leakage.py).
17. **Exact question the human must answer:** Verify that PMID 40605077 (DOI 10.1093/humrep/deaf124) has no retraction, expression of concern, or major correction affecting the cited claim, checked (a) as of the corpus freeze date 2026-08-09 and (b) as of today. Confirm the claim itself has not been superseded under this project's own supersession_type taxonomy (retraction / expression_of_concern / major_correction / guideline_revision / evidence_superseded). Additionally: EVIDENCE-SHAPE NOTE: PubMed tags this 'Randomized Controlled Trial' because it draws on an RCT's cohort (FAZST), but the reported finding itself is an observational biomarker-outcome association, not a tested intervention effect -- matched here as clinical_observational on substance, not on the PubMed type tag. Human reviewer should confirm this framing is acceptable.
18. **Recommended decision (machine-generated only -- NOT a verification):** UNCERTAIN -- A specific proximity/evidence-shape concern was flagged during sourcing (see note below) -- needs a human judgment call, not a clean pass.

**Checklist (human completes):**

- [ ] Human clinical evidence -- PASS -- confirmed human clinical/biomedical study (species checked during sourcing).
- [ ] Same hard domain -- PASS -- (HSC) Medicine - Obstetrics/Gynecology matches by construction.
- [ ] Same claim type -- PASS -- clinical_observational matches by construction.
- [ ] Same question form -- PASS -- question_form=quantitative.
- [ ] Non-superseded -- AUTOMATED CHECK ONLY -- PubMed article_types carries no Retracted/EoC/Corrected tag; NOT sufficient alone, human must check publisher corrections page + Retraction Watch directly.
- [ ] Temporally eligible -- PASS.
- [ ] Independent of treated claim -- CHECK NOTE BELOW
- [ ] No leakage -- PASS -- 0 findings against 89 treated-item identifiers.
- [ ] Acceptable evidence tier -- large_observational_cohort.

---
