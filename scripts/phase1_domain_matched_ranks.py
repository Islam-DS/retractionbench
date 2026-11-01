"""Phase 1 item 7 (prereg/phase1_item7_domain_matched_ranks.md): domain-matched rank alongside
the already-published full-corpus rank, for trap/notice (24 items) and replacement evidence
(15 items). No new FAISS search beyond what the original measurements already required -- the
same full ranking is computed once per item and then filtered by domain, not re-queried.
"""

import json
from pathlib import Path

from retraction_bench.corpus.embed_index import load_index, search
from retraction_bench.curate.benchmark_io import load_items, load_sources
from retraction_bench.rag.collect import notice_eligible_item_ids
from retraction_bench.schemas import ItemType

ROOT = Path(__file__).resolve().parent.parent
INDEX_DIR = ROOT / "data/interim/corpus/index"
OUT_JSON = ROOT / "results/phase1_domain_matched_ranks.json"
OUT_MD = ROOT / "results/phase1_domain_matched_ranks.md"


def _default_embed_fn():
    from sentence_transformers import SentenceTransformer

    model = SentenceTransformer("BAAI/bge-large-en-v1.5")

    def embed(texts: list[str]):
        return model.encode(texts, batch_size=64, normalize_embeddings=True)

    return embed


def _find_rank(results: list[dict], role: str, target_ids: set[str]) -> int | None:
    for i, r in enumerate(results, start=1):
        if r["corpus_role"] == role and r.get("linked_source_registry_id") in target_ids:
            return i
    return None


def main() -> None:
    items = load_items()
    sources = {s.source_registry_id: s for s in load_sources()}
    eligible_ids = notice_eligible_item_ids(items, sources)
    current_answer_items = [i for i in items if i.item_type == ItemType.SUPERSEDED_WITH_CURRENT_ANSWER]

    index, manifest = load_index(INDEX_DIR)
    embed_fn = _default_embed_fn()

    rows = []
    for item in items:
        if item.item_id not in eligible_ids and item not in current_answer_items:
            continue
        query_vector = embed_fn([item.question])
        full_results = search(index, manifest, query_vector, k=len(manifest))
        domain_results = [r for r in full_results if r["domain"] == item.domain]

        row = {"item_id": item.item_id, "domain": item.domain}

        if item.item_id in eligible_ids:
            trap_source_ids = set(item.supporting_sources)
            row["trap_rank_full"] = _find_rank(full_results, "benchmark_source", trap_source_ids)
            row["trap_rank_domain"] = _find_rank(domain_results, "benchmark_source", trap_source_ids)
            row["notice_rank_full"] = _find_rank(full_results, "supersession_notice", trap_source_ids)
            row["notice_rank_domain"] = _find_rank(domain_results, "supersession_notice", trap_source_ids)

        if item in current_answer_items:
            target_ids = {ev.identifier for ev in item.post_supersession_evidence}
            row["replacement_rank_full"] = _find_rank(full_results, "superseding_evidence", target_ids)
            row["replacement_rank_domain"] = _find_rank(domain_results, "superseding_evidence", target_ids)

        row["domain_pool_size"] = len(domain_results)
        row["full_pool_size"] = len(full_results)
        rows.append(row)
        print(f"{item.item_id}: {row}")

    OUT_JSON.write_text(json.dumps(rows, indent=2), encoding="utf-8")
    print(f"\nwrote {OUT_JSON}")

    # Summary: how often domain-matched rank differs from full-corpus rank, and by how much.
    lines = [
        "# Phase 1 item 7: domain-matched vs. full-corpus retrieval ranks",
        "",
        "Prereg: `prereg/phase1_item7_domain_matched_ranks.md`. Same frozen corpus/index/embedding",
        "model as every other ranking measurement in this paper; domain-matched rank is the same",
        "full ranking filtered to same-domain candidates only, not a new or re-weighted search.",
        "",
        "| Item | Domain | Trap rank (full) | Trap rank (domain) | Notice rank (full) | Notice rank (domain) | Replacement rank (full) | Replacement rank (domain) | Domain pool size |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for r in rows:
        lines.append(
            f"| {r['item_id']} | {r['domain']} | {r.get('trap_rank_full','--')} | {r.get('trap_rank_domain','--')} | "
            f"{r.get('notice_rank_full','--')} | {r.get('notice_rank_domain','--')} | "
            f"{r.get('replacement_rank_full','--')} | {r.get('replacement_rank_domain','--')} | {r['domain_pool_size']} |"
        )
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {OUT_MD}")


if __name__ == "__main__":
    main()
