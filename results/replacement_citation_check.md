# Generation-side replacement-evidence citation check (exploratory, no new model calls)

Responses scored (retrieval_naive/retrieval_with_notice, parsed, items with resolved replacement evidence): 234
Responses where the replacement evidence was actually present in that response's own top-5 retrieved set: 126
Of those, responses where the model's answer cited the replacement evidence: 79

**Citation rate given retrieval: 0.627**

**Item-clustered 95% CI: [0.373, 0.857]** (n=126 responses clustered over only 7 items, not 126 independent draws -- retrieval is fixed per item, so responses sharing an item are correlated, not independent observations).

## Per-item breakdown

| Item | Total scored | Replacement retrieved (of total) | Replacement cited (of retrieved) |
|---|---|---|---|
| RB-0001 | 18 | 0 | 0 |
| RB-0002 | 18 | 18 | 18 |
| RB-0006 | 18 | 18 | 18 |
| RB-0008 | 18 | 18 | 14 |
| RB-0009 | 18 | 0 | 0 |
| RB-0010 | 18 | 0 | 0 |
| RB-0012 | 18 | 0 | 0 |
| RB-0013 | 18 | 0 | 0 |
| RB-0014 | 18 | 18 | 9 |
| RB-0017 | 18 | 18 | 11 |
| RB-0018 | 18 | 18 | 0 |
| RB-0021 | 18 | 18 | 9 |
| RB-0022 | 18 | 0 | 0 |
