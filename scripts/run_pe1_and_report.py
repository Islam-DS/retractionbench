"""Runs the frozen PE1 harness against the real benchmark and produces the full report:
item-level table, primary/secondary endpoint tests, structural ceiling, and sanity checks.

Calls `retraction_bench.rag.pe1_harness.run_pe1` and
`retraction_bench.stats.paired_test.paired_bootstrap_permutation_test` exactly as implemented
-- nothing in the reranker rule, candidate pool, PE1 target definition, baseline retrieval, or
statistical test is touched by this script. This file only computes diffs from `run_pe1`'s
already-complete output and prints/validates them.

Run with: `uv run python scripts/run_pe1_and_report.py` (repo root).
"""

import json
from pathlib import Path

from retraction_bench.corpus.embed_index import load_index
from retraction_bench.corpus.pub_year_backfill import load_lookup
from retraction_bench.curate.benchmark_io import load_items
from retraction_bench.rag.pe1_harness import run_pe1
from retraction_bench.schemas import ItemType
from retraction_bench.stats.paired_test import paired_bootstrap_permutation_test

ROOT = Path(__file__).resolve().parent.parent
INDEX_DIR = ROOT / "data/interim/corpus/index"
PUB_YEAR_LOOKUP_PATH = ROOT / "data/interim/corpus/pub_year_lookup.jsonl"
CEILING_PATH = ROOT / "results/replacement_retrieval_ceiling.json"
POOL_K = 10
PRIMARY_K = 3


def _default_embed_fn():
    from sentence_transformers import SentenceTransformer

    model = SentenceTransformer("BAAI/bge-large-en-v1.5")

    def embed(texts: list[str]):
        return model.encode(texts, batch_size=64, normalize_embeddings=True)

    return embed


def main() -> None:
    print("=== 1. EXECUTION CONFIRMATION ===")
    items = [i for i in load_items() if i.item_type == ItemType.SUPERSEDED_WITH_CURRENT_ANSWER]
    print(f"Loaded {len(items)} items with item_type=superseded_with_current_answer")
    index, manifest = load_index(INDEX_DIR)
    pub_year_lookup = load_lookup(PUB_YEAR_LOOKUP_PATH)
    embed_fn = _default_embed_fn()
    print(f"Index/manifest loaded ({len(manifest)} documents). pub_year_lookup loaded ({len(pub_year_lookup)} entries).")
    print(f"Frozen params: RETRIEVAL_POOL_K={POOL_K}, primary endpoint=hit@{PRIMARY_K}")

    rows_run1 = run_pe1(items, index, manifest, pub_year_lookup, embed_fn, pool_k=POOL_K)
    print(f"run_pe1 produced {len(rows_run1)} rows (items with resolved replacement evidence)")

    # --- 2. BASELINE REPLICATION CHECK against the already-published ceiling ---
    print("\n=== 2. BASELINE REPLICATION CHECK ===")
    ceiling = json.loads(CEILING_PATH.read_text(encoding="utf-8"))
    ceiling_rank_by_item = {p["item_id"]: p.get("rank") for p in ceiling["per_item"] if p["status"] == "indexed"}
    replication_ok = True
    for r in rows_run1:
        published_rank = ceiling_rank_by_item.get(r["item_id"])
        if published_rank is not None and published_rank <= POOL_K:
            ok = r["baseline_rank"] == published_rank
        else:
            ok = r["baseline_rank"] is None
        if not ok:
            replication_ok = False
        print(
            f"  {r['item_id']}: published_full_corpus_rank={published_rank}, "
            f"pe1_baseline_rank(pool={POOL_K})={r['baseline_rank']} -> {'OK' if ok else 'MISMATCH'}"
        )
    print(f"Baseline replication: {'PASS' if replication_ok else 'FAIL'}")
    if not replication_ok:
        print("STOPPING: baseline replication check failed -- diagnosing, not silently repairing.")
        return

    # --- sanity checks 2/3/5/6/7 ---
    print("\n=== 9. SANITY CHECKS ===")
    check_same_set = all(set(r["baseline_pmids"]) == set(r["reranked_pmids"]) for r in rows_run1)
    print(f"2. Reranked contains exactly the same documents as baseline, every item: {'PASS' if check_same_set else 'FAIL'}")

    check_no_outside_pool = all(
        r["reranked_rank"] is None or r["reranked_rank"] <= POOL_K for r in rows_run1
    ) and all((r["baseline_rank"] is not None) == (r["reranked_rank"] is not None) for r in rows_run1)
    print(f"3. No target outside baseline top-{POOL_K} becomes reachable: {'PASS' if check_no_outside_pool else 'FAIL'}")

    rows_run2 = run_pe1(items, index, manifest, pub_year_lookup, embed_fn, pool_k=POOL_K)
    check_deterministic = all(
        r1["reranked_pmids"] == r2["reranked_pmids"] for r1, r2 in zip(rows_run1, rows_run2, strict=True)
    )
    print(f"5. Reranker is deterministic (re-run matches exactly): {'PASS' if check_deterministic else 'FAIL'}")

    baseline_misses = [r for r in rows_run1 if r["baseline_rank"] is None]
    check_misses_stay_misses = all(r["reranked_rank"] is None for r in baseline_misses)
    print(
        f"6. The {len(baseline_misses)} baseline-miss items remain misses "
        f"(never present in the original top-{POOL_K}): {'PASS' if check_misses_stay_misses else 'FAIL'}"
    )

    check_hit10_identical = all(r[f"baseline_hit@{POOL_K}"] == r[f"reranked_hit@{POOL_K}"] for r in rows_run1)
    print(f"7. hit@{POOL_K} identical between baseline and reranked: {'PASS' if check_hit10_identical else 'FAIL'}")

    forbidden_fields = {"corpus_role", "linked_source_registry_id", "source_authority", "evidence_tier", "item_id"}
    from retraction_bench.rag.recency_rerank import CandidateDocument

    candidate_fields = set(CandidateDocument.__dataclass_fields__)
    check_no_forbidden = forbidden_fields.isdisjoint(candidate_fields)
    print(f"4. No forbidden metadata reaches the reranker (CandidateDocument fields={sorted(candidate_fields)}): "
          f"{'PASS' if check_no_forbidden else 'FAIL'}")

    all_sanity_pass = all(
        [check_same_set, check_no_outside_pool, check_deterministic, check_misses_stay_misses, check_hit10_identical, check_no_forbidden]
    )
    if not all_sanity_pass:
        print("\nSTOPPING: at least one sanity check failed -- diagnosing, not silently repairing or reporting a result.")
        return

    # --- 3. ITEM-LEVEL TABLE ---
    print("\n=== 3. ITEM-LEVEL RESULTS TABLE ===")
    header = (
        f"{'item_id':10} {'base_rank':9} {'rrk_rank':9} {'b_h1':5} {'r_h1':5} "
        f"{'b_h3':5} {'r_h3':5} {'b_h5':5} {'r_h5':5} {'in_top10':9}"
    )
    print(header)
    for r in rows_run1:
        in_top10 = r["baseline_rank"] is not None
        print(
            f"{r['item_id']:10} {str(r['baseline_rank']):9} {str(r['reranked_rank']):9} "
            f"{str(r['baseline_hit@1']):5} {str(r['reranked_hit@1']):5} "
            f"{str(r['baseline_hit@3']):5} {str(r['reranked_hit@3']):5} "
            f"{str(r['baseline_hit@5']):5} {str(r['reranked_hit@5']):5} "
            f"{str(in_top10):9}"
        )

    n_improved = sum(1 for r in rows_run1 if (r["reranked_rank"] or 999) < (r["baseline_rank"] or 999))
    n_worsened = sum(1 for r in rows_run1 if (r["reranked_rank"] or 999) > (r["baseline_rank"] or 999))
    n_unchanged = len(rows_run1) - n_improved - n_worsened
    n_entering_hit3 = sum(1 for r in rows_run1 if not r["baseline_hit@3"] and r["reranked_hit@3"])
    n_leaving_hit3 = sum(1 for r in rows_run1 if r["baseline_hit@3"] and not r["reranked_hit@3"])
    print(f"\nImproved (rank got better): {n_improved}")
    print(f"Worsened (rank got worse): {n_worsened}")
    print(f"Unchanged rank: {n_unchanged}")
    print(f"Newly entering hit@3: {n_entering_hit3}")
    print(f"Leaving hit@3: {n_leaving_hit3}")

    # --- 7. STRUCTURAL CEILING ---
    print("\n=== 7. STRUCTURAL CEILING ===")
    n_in_pool = sum(1 for r in rows_run1 if r["baseline_rank"] is not None)
    print(
        f"Baseline top-{POOL_K} contains the replacement document for {n_in_pool}/{len(rows_run1)} items "
        f"({100*n_in_pool/len(rows_run1):.1f}%) -- matches the previously published Recall@10 ceiling. "
        f"The remaining {len(rows_run1) - n_in_pool} items' replacement document is not in the pool at all; "
        "reordering cannot make them hits under this intervention, and a miss on those items is not evidence "
        "against recency ranking -- it never had access to the document."
    )

    # --- 4/5/6/8. PRIMARY + SECONDARY STATISTICAL TESTS ---
    print(f"\n=== 4. PRIMARY RESULT: hit@{PRIMARY_K} ===")
    baseline_hit3 = [float(r[f"baseline_hit@{PRIMARY_K}"]) for r in rows_run1]
    reranked_hit3 = [float(r[f"reranked_hit@{PRIMARY_K}"]) for r in rows_run1]
    diffs_hit3 = [r2 - b2 for b2, r2 in zip(baseline_hit3, reranked_hit3, strict=True)]
    n = len(rows_run1)
    test_hit3 = paired_bootstrap_permutation_test(diffs_hit3)
    print(f"baseline hit@{PRIMARY_K}: {sum(baseline_hit3):.0f}/{n} = {100*sum(baseline_hit3)/n:.1f}%")
    print(f"reranked hit@{PRIMARY_K}: {sum(reranked_hit3):.0f}/{n} = {100*sum(reranked_hit3)/n:.1f}%")
    print(f"paired difference: {100*test_hit3.mean_diff:.1f} percentage points")
    print(f"95% CI: [{100*test_hit3.ci_low:.1f}, {100*test_hit3.ci_high:.1f}] pp")
    print(f"paired permutation p-value: {test_hit3.p_value:.4f}")
    print(f"n_items: {test_hit3.n_items}")
    print("item-level differences (hit@3, reranked - baseline):")
    for r, d in zip(rows_run1, diffs_hit3, strict=True):
        print(f"  {r['item_id']}: {d:+.0f}")

    print("\n=== 5. SECONDARY RESULTS ===")
    for k in (1, 5):
        b = [float(r[f"baseline_hit@{k}"]) for r in rows_run1]
        rr = [float(r[f"reranked_hit@{k}"]) for r in rows_run1]
        d = [x - y for y, x in zip(b, rr, strict=True)]
        t = paired_bootstrap_permutation_test(d)
        print(
            f"hit@{k}: baseline={sum(b):.0f}/{n}, reranked={sum(rr):.0f}/{n}, "
            f"diff={100*t.mean_diff:.1f}pp, CI=[{100*t.ci_low:.1f},{100*t.ci_high:.1f}], p={t.p_value:.4f}"
        )
    rank_changes = [
        (r["baseline_rank"] - r["reranked_rank"]) for r in rows_run1 if r["baseline_rank"] is not None and r["reranked_rank"] is not None
    ]
    print(f"best-rank change (positive = improved), per in-pool item: {rank_changes}")

    print("\n=== 10. SCIENTIFIC INTERPRETATION ===")
    verdict = "excludes zero" if (test_hit3.ci_low > 0 or test_hit3.ci_high < 0) else "includes zero"
    print(
        f"The recency/metadata reranking changed replacement-evidence retrieval at the item level "
        f"(hit@{PRIMARY_K}: {100*sum(baseline_hit3)/n:.1f}% -> {100*sum(reranked_hit3)/n:.1f}%, "
        f"95% CI {verdict}). This is a retrieval-only result over {n_in_pool}/{n} items whose replacement "
        f"document was reachable in the baseline top-{POOL_K} at all; it does not speak to citation, "
        f"correctness, or notice retrieval, and is not evidence the intervention is 'supersession-aware' "
        f"or that it 'solves' the superseded-evidence problem."
    )

    print("\n=== 11. SHOULD DOWNSTREAM GENERATION PROCEED? ===")
    print(
        "Not decided by this script. This phase was retrieval-only per instruction; no placebo, "
        "control, generation, or correctness labeling was run."
    )


if __name__ == "__main__":
    main()
