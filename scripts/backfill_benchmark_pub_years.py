"""Phase 1 of the recency-reranker infrastructure repair.

Builds `data/interim/corpus/pub_year_lookup.jsonl` -- one real, independently-sourced
`pub_year` (or an explicitly documented `None`) per corpus document, covering all 325,167
rows. Background rows' existing `pub_year` is carried through unchanged; the 57
`benchmark_source`/`superseding_evidence` rows missing it are resolved fresh from NCBI
ESummary by their own real PMID; the 24 `supersession_notice` rows are recorded as
unresolvable (no real external identifier exists for them in the schema) rather than guessed.

Does not modify `assembled_corpus.jsonl`, `corpus_manifest.jsonl`, or any benchmark file --
this lookup is a new, separate, additive artifact. See
`src/retraction_bench/corpus/pub_year_backfill.py` for the full provenance discipline.

Run with: `uv run python scripts/backfill_benchmark_pub_years.py` (repo root). Makes live
NCBI ESummary calls for the 57 real benchmark-role PMIDs only (one or two batched requests).
"""

from pathlib import Path

from dotenv import load_dotenv

from retraction_bench.corpus.pub_year_backfill import build_pub_year_lookup, write_lookup

load_dotenv()

ROOT = Path(__file__).resolve().parent.parent
CORPUS_PATH = ROOT / "data/interim/corpus/assembled_corpus.jsonl"
OUTPUT_PATH = ROOT / "data/interim/corpus/pub_year_lookup.jsonl"


def main() -> None:
    records = build_pub_year_lookup(CORPUS_PATH)
    write_lookup(records, OUTPUT_PATH)

    by_role: dict[str, list] = {}
    for r in records:
        by_role.setdefault(r.corpus_role, []).append(r)

    print(f"wrote {OUTPUT_PATH} ({len(records)} records)")
    for role, recs in sorted(by_role.items()):
        n = len(recs)
        n_resolved = sum(1 for r in recs if r.pub_year is not None)
        print(f"  {role}: n={n}, pub_year resolved={n_resolved}, missing={n - n_resolved}")


if __name__ == "__main__":
    main()
