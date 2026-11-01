"""Phase 6: per-step counts for the candidate-screening flow diagram (Supplementary Figure s-funnel).

Applies `curate.candidates.export_tier1_candidates`'s filters one at a time, in its own order, and
records how many Retraction Watch records survive each step -- so the flow diagram shows a real
count at every stage instead of the earlier "n varies". The final step must reproduce the committed
candidate pool (`data/interim/tier1_candidates_final3.csv`: 364 rows, 296 distinct papers), which
is asserted. The annotation-stage counts are read from the benchmark's own records.

Output: results/phase6_funnel_counts.json
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

from retraction_bench.curate.claim_type_screen import DEFAULT_CLAIM_SCREEN_PATH
from retraction_bench.curate.reason_screen import DEFAULT_SCREEN_PATH, Tier
from retraction_bench.ingest.explore import load_enriched_frame
from retraction_bench.ingest.retraction_watch import DB_PATH

ROOT = Path(__file__).resolve().parent.parent
POOL = ROOT / "data/interim/tier1_candidates_final3.csv"
OUT = ROOT / "results/phase6_funnel_counts.json"
SUBJECTS = [
    "(HSC) Medicine - Pharmacology",
    "(HSC) Medicine - Obstetrics/Gynecology",
    "(HSC) Medicine - Rehabilitation/Therapy",
]


def _jsonl_count(path: Path) -> int:
    return sum(1 for line in path.read_text(encoding="utf-8").splitlines() if line.strip())


def main() -> None:
    df = load_enriched_frame(DB_PATH, DEFAULT_SCREEN_PATH, DEFAULT_CLAIM_SCREEN_PATH)
    steps = [("Retraction Watch rows at ingestion", len(df))]
    df = df[~df["is_blank_row"]]
    steps.append(("Non-blank records", len(df)))
    df = df[df["retraction_nature"] == "Retraction"]
    steps.append(("Retraction-nature records", len(df)))
    df = df[df["retraction_date_parsed"].dt.year >= 2016]
    steps.append(("Retracted 2016 or later", len(df)))
    df = df[df["original_paper_pubmed_id_resolvable"]]
    steps.append(("Original paper has a resolvable PubMed ID", len(df)))
    df = df[df["candidate_tier"] == Tier.TIER_1_CLEAN]
    steps.append(("Reason screen: tier_1_clean", len(df)))
    df = df[df["is_clinical_claim"]]
    steps.append(("Claim-type screen: clinical claim", len(df)))

    exploded = df.explode("subject_list")
    in_domains = exploded[exploded["subject_list"].isin(SUBJECTS)]
    rows_by_domain = in_domains["subject_list"].value_counts().to_dict()
    n_rows = len(in_domains)
    n_papers = in_domains["record_id"].nunique()

    with POOL.open(encoding="utf-8") as f:
        pool = list(csv.DictReader(f))
    assert n_rows == len(pool), (n_rows, len(pool))
    assert n_papers == len({r["record_id"] for r in pool}), (n_papers,)

    bench = ROOT / "data/benchmark"
    included = _jsonl_count(bench / "items.jsonl")
    rejected = _jsonl_count(bench / "rejected_candidates.jsonl")
    deferred = _jsonl_count(bench / "deferred_candidates.jsonl")

    result = {
        "screening_steps": [{"step": s, "n_records": n} for s, n in steps],
        "three_domain_pool": {"rows": n_rows, "distinct_papers": n_papers, "rows_by_domain": rows_by_domain},
        "annotation": {
            "candidates_evaluated": included + rejected + deferred,
            "included": included,
            "rejected": rejected,
            "deferred": deferred,
        },
    }
    OUT.write_text(json.dumps(result, indent=1), encoding="utf-8")
    print(json.dumps(result, indent=1))


if __name__ == "__main__":
    main()
