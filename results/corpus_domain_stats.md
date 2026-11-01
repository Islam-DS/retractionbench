# Corpus domain composition (Phase 0 audit)

Computed directly from `data/interim/corpus/assembled_corpus.jsonl` (325,167 rows) and the raw
per-domain pre-dedup fetch files. No live API call.

## Final, deduplicated corpus (325,167 documents)

| Domain | Total documents | % of corpus | Background-only | % of background pool |
|---|---|---|---|---|
| Rehabilitation/Therapy | 258,020 | 79.35% | 258,017 | 79.37% |
| Pharmacology | 55,086 | 16.94% | 55,047 | 16.93% |
| Obstetrics/Gynecology | 12,061 | 3.71% | 12,022 | 3.70% |
| **Total** | 325,167 | 100% | 325,086 | 100% |

**Rehabilitation/Therapy accounts for 79.37% of the 325,086-document background pool** -- nearly
4 in 5 background documents, despite this domain retaining only one benchmark item (RB-0009) after
being retired from active annotation (main text §3.3).

Final-corpus domain-size ratios: Rehab:Pharmacology = 4.7x; Rehab:ObGyn = 21.5x.

## Raw, pre-deduplication per-domain fetch (before `corpus/assemble.py`'s global dedup)

| Domain | Raw row count (`raw_*.jsonl`) |
|---|---|
| Rehabilitation/Therapy | 330,753 |
| Pharmacology | 57,678 |
| Obstetrics/Gynecology | 12,107 |

Raw Rehab:ObGyn ratio = 330,753 / 12,107 = **27.32x** -- this is the figure the main text's §3.11
"~27-fold" claim refers to (confirmed by direct computation, not assumed). It is a *raw fetch*
ratio, not the final deduplicated-corpus ratio above; the two differ because assembly-time
deduplication removes a disproportionate share of Rehabilitation rows (duplicate-heavy per
`corpus/mesh_fetch.py`'s own resumability-bug history, ADR-133).
