# RetractionBench

Evaluating whether medical retrieval-augmented generation (RAG) systems handle retracted
evidence, and whether the retraction record they depend on is reliable.

RAG systems are usually evaluated on *groundedness*: does the answer match the retrieved
document? That check cannot tell whether the document has since been retracted. RetractionBench
measures this gap at five separate points: whether the retraction notice is retrieved, whether
current replacement evidence is retrieved, whether the retracted source is cited, whether the
replacement is cited, and whether the answer is substantively correct. It also audits the
retraction record itself: how often PubMed's machine-readable retraction tag is missing for
retractions listed by Retraction Watch.

**Contents of this repository:** the 28-item benchmark, the 900 cached model responses, the
author's blind hand labels, all analysis code, every results file the manuscript cites, the
prespecification documents, and the scripts that generate the manuscript's figures.

## Quick start

Requires [`uv`](https://docs.astral.sh/uv/) and Python 3.12+.

```bash
uv sync --group models      # install all dependencies (models group: FAISS, sentence-transformers)
uv run pytest               # run the test suite (one test skips without the raw RW database)
make reproduce              # regenerate every M1/M3/Correctness number from the cached responses
uv run python scripts/make_paper_figures.py   # regenerate every figure
```

`make reproduce` (equivalently `uv run retraction-bench evaluate`) recomputes the paper's model
results from `data/interim/eval/model_responses.jsonl` and the hand labels in `data/human/`,
with no API calls; `tests/test_reproduce_paper_numbers.py` checks the output against the
published numbers.

## Data

| Path | What it is |
|---|---|
| `data/benchmark/items.jsonl` | The 28 benchmark items: question, trap (retracted) claim, gold (current) claim, annotations |
| `data/benchmark/sources.jsonl` | The retracted source, notice, and current evidence record for each item |
| `data/benchmark/rejected_candidates.jsonl`, `deferred_candidates.jsonl` | Candidates evaluated but not included, with reasons |
| `data/human/` | The author's blind, randomized hand labels for M3 (150) and Correctness (100) |
| `data/interim/eval/model_responses.jsonl` | All 900 cached model responses (3 models x 4 conditions x 3 seeds) |
| `data/interim/eval/*_labeling_key.json` | Keys mapping blind labeling cards back to responses |
| `data/interim/eval/faithfulness_check_nli.json` | Per-response NLI scores for the groundedness check |
| `data/interim/phase5_*` | Record-level audit samples and raw API responses (PubMed, Crossref, OpenAlex) |
| `data/interim/corpus/CORPUS_FREEZE.json` | Manifest (record count, content hash) of the frozen retrieval corpus |
| `results/` | Every results file cited in the manuscript |
| `prereg/` | Prespecification documents, written before each analysis was run |

**Not included, and how to regenerate:**

- The Retraction Watch database is not redistributed. Download it from the Crossref-hosted
  mirror (`gitlab.com/crossref/retraction-watch-data`) and run
  `uv run retraction-bench ingest retraction-watch`.
- The retrieval corpus (~325,000 PubMed abstracts) and its FAISS index (~1.6 GB) are not
  included. They are rebuilt from PubMed with the modules in `src/retraction_bench/corpus/`
  (`mesh_fetch.py`, then `assemble.py`, then `embed_index.py`; requires `uv sync --group models`);
  `freeze.py` recomputes the manifest so you can check the rebuilt corpus matches
  `CORPUS_FREEZE.json`. None of this is needed to reproduce the reported results, which run from
  the cached responses.

## Which files back which result

| Result in the paper | Code | Output |
|---|---|---|
| Retraction record audit: missing PubMed tags, corroboration tiers, random sample | `scripts/phase5_*.py`, `src/retraction_bench/ingest/pubmed_rw_completeness.py` | `results/pubmed_rw_completeness_check.md`, `results/phase5_*` |
| Abstracts overwritten by retraction text | method documented in the results file | `results/abstract_overwrite_measurement.*` |
| Screening flow (71,540 records to 28 items) | `scripts/phase6_funnel_counts.py` | `results/phase6_funnel_counts.json` |
| Notice and trap-source ranks | `src/retraction_bench/corpus/retrieval_ceiling.py` | `results/retrieval_ceiling_report.json` |
| Replacement-evidence retrieval and citation | `scripts/replacement_retrieval_ceiling.py`, `scripts/replacement_citation_check.py` | `results/replacement_*` |
| Domain-scoped ranks | `scripts/phase1_domain_matched_ranks.py` | `results/phase1_domain_matched_ranks.*` |
| Recency reranker (PE1; needs the rebuilt corpus) | `scripts/run_pe1_and_report.py` | printed report |
| M1, M3, Correctness, paired tests | `make reproduce` (`src/retraction_bench/reproduce.py`) | `results/reproduced_paper_numbers.*` |
| Between-model contrasts | `scripts/phase1_item2_redo_paired_contrasts.py` | `results/phase1_item2_redo_paired_contrasts.*` |
| Citation vs. correctness (RQ3) | `scripts/correctness_citation_contingency.py` | `results/correctness_citation_contingency.*` |
| Secondary judge agreement (kappa) | `scripts/validate_llm_judge_agreement.py` | printed report |
| NLI groundedness check | `src/retraction_bench/eval/faithfulness_check.py`, `scripts/phase1_clustered_nli_ci.py` | `results/phase1_nli_clustered_cis.*` |
| Uncertainty keyword scan | `scripts/phase6_uncertainty_keyword_scan.py` | `results/phase6_uncertainty_keyword_scan.json` |
| Stratified and domain breakdowns | `scripts/phase6_recompute_unsaved_numbers.py` | `results/phase6_recomputed_numbers.*` |
| All figures | `scripts/make_paper_figures.py` | `paper/latex/figures/` |

## Repository layout

- `src/retraction_bench/`: ingestion, screening, corpus, retrieval, evaluation, and statistics code
- `scripts/`: one script per analysis reported in the manuscript
- `paper/latex/figures/`: the scripts that generate every manuscript figure, and the figures
- `docs/`: annotation protocol, rubrics, decision log (`DECISIONS.md`), analysis log, claims ledger
- `config/`: settings and controlled vocabularies (reason screen, claim-type screen, domains)
- `tests/`: test suite

## Citation

If you use RetractionBench, please cite it (see `CITATION.cff`):

> Islam, M. M. (2026). *RetractionBench: Evaluating Superseded-Evidence Handling in Medical
> Retrieval-Augmented Generation.* https://github.com/Islam-DS/retractionbench

## License

Code: [MIT](LICENSE). Benchmark data and hand labels (`data/benchmark/`, `data/human/`):
[CC-BY-4.0](DATA_LICENSE).

## Author

Md. Mahbubul Islam, AI & Robotics Laboratory, Department of AI & Big Data, al-Farabi Kazakh
National University. ORCID: [0009-0009-1910-1980](https://orcid.org/0009-0009-1910-1980)
