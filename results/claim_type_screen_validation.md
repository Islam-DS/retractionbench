# Claim-Type Screen Validation (ADR-021)

Recall-oriented pre-filter, not a classifier -- a human reads every candidate this screen passes through. The headline number is held-out recall on clinical_intervention + clinical_observational combined, below. The 4-class agreement/kappa figures further down describe the same run but are not the design target -- see ADR-021 for why.

## Headline: dev vs. held-out (stratified 50/50 split, seed=20260806)

### Held-out (headline) (n=50)

- **Recall on clinical (intervention + observational): 100.0%** [87.9%, 100.0%], TP=28, FN=0
- Precision: 84.8% [69.1%, 93.3%], FP=5, TN=17

### Dev (n=50)

- **Recall on clinical (intervention + observational): 100.0%** [88.3%, 100.0%], TP=29, FN=0
- Precision: 82.9% [67.3%, 91.9%], FP=6, TN=15

### All 100 (dev + held-out combined, for reference) (n=100)

- **Recall on clinical (intervention + observational): 100.0%** [93.7%, 100.0%], TP=57, FN=0
- Precision: 83.8% [73.3%, 90.7%], FP=11, TN=32


## 4-class agreement (descriptive, not the design target)

n=100. Overall agreement: **75/100 = 75.0%**, 95% Wilson CI [65.7%, 82.5%]. Cohen's kappa: **0.633**.

## Confusion matrix (rows = human, columns = screen, all 100)

| human \ screen | clinical_intervention | clinical_observational | preclinical | unclear |
| --- | --- | --- | --- | --- |
| clinical_intervention | 14 | 13 | 0 | 0 |
| clinical_observational | 0 | 30 | 0 | 0 |
| preclinical | 0 | 6 | 31 | 1 |
| unclear | 0 | 5 | 0 | 0 |

## Per-class precision / recall (4-way, all 100)

| class | precision | recall | support (human) | predicted (screen) |
| --- | --- | --- | --- | --- |
| clinical_intervention | 100.0% | 51.9% | 27 | 14 |
| clinical_observational | 55.6% | 100.0% | 30 | 54 |
| preclinical | 100.0% | 81.6% | 38 | 31 |
| unclear | 0.0% | 0.0% | 5 | 1 |

Restricting to rows where the screen output a non-`unclear` label: **75/99 = 75.8%** correct on the 4-way task (kept for continuity with the pre-redesign report; less relevant now that `unclear` is reserved for non-research ArticleType only, not a default).
