# Phase 1 item 3: item-level M1 (retrieval_with_notice) x M3 (post_notice, acknowledges) join

Prereg: `prereg/phase1_item3_m1_m3_item_join.md`.

Total joinable (item, model) cells (both M1 and hand-labeled M3 available): 48.

| Model | n items | phi | 95% CI | 2x2 breakdown (cites_trap x acknowledges) |
|---|---|---|---|---|
| llama3.1:8b-instruct-q4_K_M | 22 | -0.263 | [-0.471,-0.134] | TT=11 TF=9 FT=2 FF=0 |
| openai/gpt-oss-120b | 2 **(n<5, descriptive only, not tested)** | undefined (no variance) | n/a | TT=0 TF=0 FT=2 FF=0 |
| qwen2.5:7b-instruct-q4_K_M | 24 | 0.258 | [-0.146,0.639] | TT=9 TF=6 FT=3 FF=6 |

**Interpretation (prespecified rule applied, with the actual numbers, not the generic rule text):**

- **llama3.1:8b (n=22): phi=-0.263, 95% CI [-0.471, -0.134] -- excludes zero.** But this
  significant-looking negative association is driven almost entirely by a thin margin: only 2 of
  22 items have `cites_trap=False` at all (the FT/FF column), and both of those 2 happen to be
  `acknowledges=True`. A CI built on a 2-vs-20 split in one margin should not be read as a robust
  finding; it is reported exactly, not suppressed, but flagged as fragile.
- **qwen2.5:7b (n=24): phi=+0.258, 95% CI [-0.146, 0.639] -- includes zero.** Opposite sign from
  llama, not significant.
- **gpt-oss-120b (n=2):** untestable.

**Net conclusion: the three models do not show a consistent item-level association between
citing the trap under retrieval and later acknowledging it under confrontation** -- one
significant-but-fragile negative, one non-significant positive, one untestable. This does **not**
provide clean, consistent item-level support for the Discussion's current inference that the
citation/acknowledgment gap is "not a comprehension failure." That inference currently rests on
the *aggregate* contrast between sections 4.2 and 4.4 alone and should be **reworded to say so
explicitly** -- e.g. "this pattern is consistent with an evidence-integration bottleneck at the
aggregate level; an item-level join (Supplement, n=22-24 per model) does not show a consistent
association across models and should not be read as confirming a comprehension-failure account
either" -- rather than implying item-level support that this re-analysis does not find.
