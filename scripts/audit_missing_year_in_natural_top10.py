"""Descriptive-only audit: does the recency reranker's "missing year sorts last" rule
systematically disadvantage supersession notices within the EXISTING, unmodified natural
top-10 retrieval pool? No reranker is invoked here, no outcome comparison is made -- this
reads only the baseline FAISS ranking (unchanged, `corpus/embed_index.search`) and the real
`pub_year_lookup.jsonl` built earlier this round. Written to make the audit reproducible, not
a frozen pipeline component.

Run with: `uv run python scripts/audit_missing_year_in_natural_top10.py` (repo root).
"""

from pathlib import Path

from retraction_bench.corpus.embed_index import load_index, search
from retraction_bench.corpus.pub_year_backfill import load_lookup
from retraction_bench.curate.benchmark_io import load_items, load_sources
from retraction_bench.rag.collect import RETRIEVAL_POOL_K, notice_eligible_item_ids

ROOT = Path(__file__).resolve().parent.parent
INDEX_DIR = ROOT / "data/interim/corpus/index"
PUB_YEAR_LOOKUP_PATH = ROOT / "data/interim/corpus/pub_year_lookup.jsonl"


def _default_embed_fn():
    from sentence_transformers import SentenceTransformer

    model = SentenceTransformer("BAAI/bge-large-en-v1.5")

    def embed(texts: list[str]):
        return model.encode(texts, batch_size=64, normalize_embeddings=True)

    return embed


def main() -> None:
    items = load_items()
    sources = {s.source_registry_id: s for s in load_sources()}
    index, manifest = load_index(INDEX_DIR)
    pub_year_lookup = load_lookup(PUB_YEAR_LOOKUP_PATH)
    eligible_ids = notice_eligible_item_ids(items, sources)
    embed_fn = _default_embed_fn()

    total_with_year = 0
    total_missing_year = 0
    per_item_rows = []

    for item in items:
        query_vector = embed_fn([item.question])
        hits = search(index, manifest, query_vector, k=RETRIEVAL_POOL_K)
        n_with_year = sum(1 for h in hits if pub_year_lookup.get(h["pmid"]) is not None)
        n_missing_year = len(hits) - n_with_year
        total_with_year += n_with_year
        total_missing_year += n_missing_year

        notice_in_pool = None
        notice_rank = None
        notice_missing_year = None
        if item.item_id in eligible_ids:
            notice_pmid = f"{item.supporting_sources[0]}-notice"
            pmids_in_order = [h["pmid"] for h in hits]
            notice_in_pool = notice_pmid in pmids_in_order
            notice_rank = pmids_in_order.index(notice_pmid) + 1 if notice_in_pool else None
            notice_missing_year = pub_year_lookup.get(notice_pmid) is None

        per_item_rows.append(
            {
                "item_id": item.item_id,
                "n_pool": len(hits),
                "n_with_year": n_with_year,
                "n_missing_year": n_missing_year,
                "notice_eligible": item.item_id in eligible_ids,
                "notice_in_natural_top10": notice_in_pool,
                "notice_natural_rank": notice_rank,
                "notice_missing_year": notice_missing_year,
            }
        )

    print(f"Items scanned: {len(items)}, pool size per item: {RETRIEVAL_POOL_K}")
    print(f"Total candidate-slots with year: {total_with_year}")
    print(f"Total candidate-slots missing year: {total_missing_year}")
    print()
    print("Per-item breakdown:")
    print(f"{'item_id':10} {'n_with_yr':10} {'n_missing':10} {'eligible':9} {'notice_in_top10':16} {'notice_rank':12} {'notice_missing_yr':18}")
    for r in per_item_rows:
        print(
            f"{r['item_id']:10} {r['n_with_year']:10} {r['n_missing_year']:10} "
            f"{str(r['notice_eligible']):9} {str(r['notice_in_natural_top10']):16} "
            f"{str(r['notice_natural_rank']):12} {str(r['notice_missing_year']):18}"
        )

    eligible_rows = [r for r in per_item_rows if r["notice_eligible"]]
    n_in_pool = sum(1 for r in eligible_rows if r["notice_in_natural_top10"])
    n_missing_among_in_pool = sum(1 for r in eligible_rows if r["notice_in_natural_top10"] and r["notice_missing_year"])
    print()
    print(f"Notice-eligible items: {len(eligible_rows)}")
    print(f"  Notice present in natural top-10: {n_in_pool}/{len(eligible_rows)}")
    print(f"  Of those, notice has missing year: {n_missing_among_in_pool}/{n_in_pool}")


if __name__ == "__main__":
    main()
