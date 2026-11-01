"""Replacement-evidence retrieval ceiling (ADR-163).

A ninth external review pointed out that M1 only measures whether a model stops citing the
retracted source, never whether it goes on to retrieve and cite the *correct current* evidence --
a gap this paper's own Limitations and Future Work sections already name explicitly. This script
answers the retrieval half of that gap directly, using data and infrastructure this project
already built: for every item with current authoritative evidence
(`item_type = superseded_with_current_answer`), what is the retrieval rank of its own
`post_supersession_evidence` document(s) in the live, frozen corpus, under the same paper-derived
query formulation and dense-embedding configuration `corpus/retrieval_ceiling.py` already uses for
trap-source and notice ranks?

This is a pure retrieval measurement -- no model generation, no new API call, no new annotation.
The superseding-evidence documents were already inserted into the corpus exactly once during
construction (`corpus/assemble.py`, `corpus_role = "superseding_evidence"`, linked by
`linked_source_registry_id = evidence.identifier`, i.e. the DOI/PMID recorded on the benchmark
item's own `post_supersession_evidence` entries) and the embedding model
(`BAAI/bge-large-en-v1.5`) is cached locally, so this reuses infrastructure rather than adding any.

Scope, stated up front: only items with `item_type = superseded_with_current_answer` have any
`post_supersession_evidence` to look for at all (15 of 28); a further subset may have failed
DOI-to-PMID resolution during corpus assembly (`AssemblyStats.superseding_evidence_unresolved`)
and are therefore not in the corpus to be found regardless of query quality -- those are reported
as a distinct, disclosed "not indexed" category, not folded into "not retrieved."

Run with: `uv run python scripts/replacement_retrieval_ceiling.py` (repo root). No live API call.
Writes `results/replacement_retrieval_ceiling.json` and `.md`.
"""

import json
from pathlib import Path

from retraction_bench.corpus.embed_index import load_index, search
from retraction_bench.curate.benchmark_io import load_items
from retraction_bench.schemas import ItemType

ROOT = Path(__file__).resolve().parent.parent
INDEX_DIR = ROOT / "data/interim/corpus/index"
K_VALUES = (1, 3, 5, 10, 20)


def _default_embed_fn():
    from sentence_transformers import SentenceTransformer

    model = SentenceTransformer("BAAI/bge-large-en-v1.5")

    def embed(texts: list[str]):
        return model.encode(texts, batch_size=64, normalize_embeddings=True)

    return embed


def _find_best_rank(results: list[dict], target_ids: set[str]) -> int | None:
    for i, r in enumerate(results, start=1):
        if r["corpus_role"] == "superseding_evidence" and r.get("linked_source_registry_id") in target_ids:
            return i
    return None


def main() -> None:
    items = [i for i in load_items() if i.item_type == ItemType.SUPERSEDED_WITH_CURRENT_ANSWER]
    index, manifest = load_index(INDEX_DIR)
    indexed_identifiers = {
        m["linked_source_registry_id"] for m in manifest if m["corpus_role"] == "superseding_evidence"
    }
    embed_fn = _default_embed_fn()

    per_item = []
    for item in items:
        target_ids = {ev.identifier for ev in item.post_supersession_evidence}
        indexed_targets = target_ids & indexed_identifiers
        if not target_ids:
            per_item.append({"item_id": item.item_id, "domain": item.domain, "status": "no_post_supersession_evidence_recorded"})
            continue
        if not indexed_targets:
            per_item.append(
                {
                    "item_id": item.item_id,
                    "domain": item.domain,
                    "status": "not_indexed",
                    "n_evidence_entries": len(target_ids),
                }
            )
            continue
        query_vector = embed_fn([item.question])
        results = search(index, manifest, query_vector, k=len(manifest))
        rank = _find_best_rank(results, indexed_targets)
        per_item.append(
            {
                "item_id": item.item_id,
                "domain": item.domain,
                "status": "indexed",
                "rank": rank,
                "n_evidence_entries": len(target_ids),
                "n_indexed_entries": len(indexed_targets),
            }
        )
        print(f"{item.item_id}: rank={rank}")

    indexed_results = [p for p in per_item if p["status"] == "indexed"]
    n_indexed = len(indexed_results)
    recall_at = {}
    for k in K_VALUES:
        recall_at[k] = (
            sum(1 for p in indexed_results if p["rank"] is not None and p["rank"] <= k) / n_indexed if n_indexed else None
        )

    report = {
        "n_items_with_current_answer": len(items),
        "n_no_evidence_recorded": sum(1 for p in per_item if p["status"] == "no_post_supersession_evidence_recorded"),
        "n_not_indexed": sum(1 for p in per_item if p["status"] == "not_indexed"),
        "n_indexed_and_measured": n_indexed,
        "recall_at": recall_at,
        "per_item": per_item,
    }
    out_json = ROOT / "results/replacement_retrieval_ceiling.json"
    out_json.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"wrote {out_json}")

    lines = [
        "# Replacement-evidence retrieval ceiling (exploratory, retrieval-only, no model generation)",
        "",
        f"Items with current authoritative evidence (`superseded_with_current_answer`): {len(items)}",
        f"- No `post_supersession_evidence` entries recorded: {report['n_no_evidence_recorded']}",
        f"- Recorded but not indexed (DOI/PMID resolution failed at corpus-build time): {report['n_not_indexed']}",
        f"- Indexed and measured: {n_indexed}",
        "",
        "## Recall@k (indexed items only, n={})".format(n_indexed),
        "",
        "| k | Recall@k |",
        "|---|---|",
    ]
    for k in K_VALUES:
        v = recall_at[k]
        lines.append(f"| {k} | {v:.3f} |" if v is not None else f"| {k} | -- |")
    lines.append("")
    lines.append("## Per-item ranks")
    lines.append("")
    lines.append("| Item | Domain | Status | Rank |")
    lines.append("|---|---|---|---|")
    for p in per_item:
        rank_str = str(p.get("rank", "--"))
        lines.append(f"| {p['item_id']} | {p['domain']} | {p['status']} | {rank_str} |")

    out_md = ROOT / "results/replacement_retrieval_ceiling.md"
    out_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {out_md}")


if __name__ == "__main__":
    main()
