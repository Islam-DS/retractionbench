"""PE1: retrieval-only test of the recency-only reranker against baseline dense retrieval.

Thin CLI wrapper -- the actual logic lives in `retraction_bench.rag.pe1_harness` (`run_pe1`),
which is what `tests/test_pe1_replacement_retrieval_rerank.py` unit-tests against a synthetic
fixture. Built and tested this round; **not executed against the real 15-item benchmark**, per
explicit instruction -- this file is the frozen harness. Exact command to run it later:
`uv run python scripts/pe1_replacement_retrieval_rerank.py` (repo root), after
`backfill_benchmark_pub_years.py` has been run at least once (already done this round; see
`reports/pub_year_backfill_integrity.md`).

No model generation, no new annotation -- reuses exactly the data `replacement_retrieval_ceiling.py`
(ADR-163) already established: the 15 `item_type=superseded_with_current_answer` items, their
`post_supersession_evidence` identifiers resolved to corpus PMIDs via the FAISS manifest's
`linked_source_registry_id`.

PRIMARY ENDPOINT (stated before any run): **hit@3** for the replacement document, baseline vs.
reranked, paired by item -- this metric's own existing headline cut-point
(`replacement_retrieval_ceiling.py`'s Recall@3 = 53.3% is already reported in the paper), and
the range where a pool-scoped reorder can actually move mass (unlike hit@10, which cannot
change at all under a pure reorder -- see `rag/recency_rerank.py`'s module docstring). hit@1
and hit@5 are SECONDARY. hit@10 is reported only as a structural-invariant sanity check, not an
endpoint. No correctness/citation outcome is computed here -- out of scope for PE1 (Phase 7).
"""

from pathlib import Path

from retraction_bench.corpus.embed_index import load_index
from retraction_bench.corpus.pub_year_backfill import load_lookup
from retraction_bench.curate.benchmark_io import load_items
from retraction_bench.rag.pe1_harness import HIT_K_VALUES, run_pe1
from retraction_bench.schemas import ItemType
from retraction_bench.stats.paired_test import paired_bootstrap_permutation_test

ROOT = Path(__file__).resolve().parent.parent
INDEX_DIR = ROOT / "data/interim/corpus/index"
PUB_YEAR_LOOKUP_PATH = ROOT / "data/interim/corpus/pub_year_lookup.jsonl"
POOL_K = 10  # == rag/collect.py's RETRIEVAL_POOL_K, frozen, not widened -- see recency_rerank.py
PRIMARY_K = 3


def _default_embed_fn():
    from sentence_transformers import SentenceTransformer

    model = SentenceTransformer("BAAI/bge-large-en-v1.5")

    def embed(texts: list[str]):
        return model.encode(texts, batch_size=64, normalize_embeddings=True)

    return embed


def main() -> None:
    items = [i for i in load_items() if i.item_type == ItemType.SUPERSEDED_WITH_CURRENT_ANSWER]
    index, manifest = load_index(INDEX_DIR)
    pub_year_lookup = load_lookup(PUB_YEAR_LOOKUP_PATH)
    embed_fn = _default_embed_fn()

    rows = run_pe1(items, index, manifest, pub_year_lookup, embed_fn, pool_k=POOL_K)

    print(f"{len(rows)} items with resolved replacement evidence scored")
    for k in HIT_K_VALUES:
        diffs = [float(r[f"reranked_hit@{k}"]) - float(r[f"baseline_hit@{k}"]) for r in rows]
        label = "PRIMARY" if k == PRIMARY_K else ("structural invariant, not an endpoint" if k == POOL_K else "secondary")
        test = paired_bootstrap_permutation_test(diffs)
        print(
            f"hit@{k} [{label}]: baseline={sum(r[f'baseline_hit@{k}'] for r in rows)}/{len(rows)}, "
            f"reranked={sum(r[f'reranked_hit@{k}'] for r in rows)}/{len(rows)}, "
            f"mean_diff={test.mean_diff:.4f}, CI=[{test.ci_low:.4f},{test.ci_high:.4f}], p={test.p_value:.4f}"
        )


if __name__ == "__main__":
    main()
