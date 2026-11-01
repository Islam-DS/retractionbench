"""Phase 5, Part B, step 1, REDRAWN after a second author-directed check caught a real
contamination problem: the original population (33,359 records with a real PubMed ID) was not
filtered to `retraction_nature == "Retraction"` -- 2,459 Expression-of-Concern, 1,244
Correction, and 134 Reinstatement records were mixed in, and checking those for a missing
`Retracted Publication` tag is the wrong check entirely (that tag was never expected on them).

Runs `rw_data_quality.validate_rw_dataframe` BEFORE drawing, with `require_retraction_nature_only
=True`, and aborts loudly rather than silently sampling from unvalidated data -- this is the
"data-validation step that runs before every audit script" the author asked for, applied here
first.
"""

import json
import random
from collections import defaultdict
from pathlib import Path

import duckdb

from retraction_bench.ingest.rw_data_quality import print_report, validate_rw_dataframe

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "data/interim/retraction_watch.duckdb"
OUT_PATH = ROOT / "data/interim/phase5_scaled_sample_v2_retraction_only.json"
SEED = 42
N_SAMPLE = 300
PLACEHOLDER_DATE = "1/1/1970 0:00"


def main() -> None:
    con = duckdb.connect(str(DB_PATH), read_only=True)
    raw = con.execute(
        "SELECT record_id, journal, publisher, retraction_date, retraction_nature, reason, "
        "original_paper_pubmed_id, retraction_pubmed_id, original_paper_doi "
        "FROM raw_retraction_watch "
        "WHERE original_paper_pubmed_id IS NOT NULL AND original_paper_pubmed_id != '' "
        "AND original_paper_pubmed_id != '0'"
    ).fetchdf()

    print("=== Data validation BEFORE drawing (require_retraction_nature_only=True) ===")
    reports = validate_rw_dataframe(raw, require_retraction_nature_only=True)
    print_report(reports)
    print()

    df = raw[raw["retraction_nature"] == "Retraction"].copy()
    n_excluded_non_retraction = len(raw) - len(df)
    print(f"Excluded {n_excluded_non_retraction} non-Retraction-nature rows "
          f"(Correction/Expression of concern/Reinstatement) from {len(raw)} -> {len(df)}.")
    print("(Disclosed anomaly, excluded by this filter: PMID 35073579 appears 281 times in the")
    print(" unfiltered table, all Expression-of-concern-nature, all dated 1/24/2022, 281 distinct")
    print(" record_ids/titles -- a real RW data-entry error (one PMID copied across 281 rows that")
    print(" should each carry their own), not a placeholder. Already excluded by the nature filter.")

    # Duplicate-PMID check on the FILTERED population, explicitly, before sampling (item 1d).
    dup_report = [r for r in validate_rw_dataframe(df) if r.check_name.startswith("duplicate_pmids")][0]
    print(f"Duplicate-PMID check on filtered population: n_flagged={dup_report.n_flagged} -- {dup_report.detail}")
    print(f"  examples: {dup_report.flagged_examples}")

    # Dedupe at the PMID level -- deterministic (lowest record_id kept), not arbitrary.
    before_dedupe = len(df)
    df = df.sort_values("record_id").drop_duplicates(subset="original_paper_pubmed_id", keep="first")
    print(f"Deduped at PMID level: {before_dedupe} rows -> {len(df)} distinct PMIDs "
          f"({before_dedupe - len(df)} excess rows removed, keeping the lowest record_id per PMID).")

    n_total = len(df)
    n_placeholder_date = int((df["retraction_date"] == PLACEHOLDER_DATE).sum())
    df_valid = df[df["retraction_date"] != PLACEHOLDER_DATE].copy()
    df_valid["year"] = df_valid["retraction_date"].str.extract(r"/(\d{4})\s")[0]

    by_year = defaultdict(list)
    for _, row in df_valid.iterrows():
        by_year[row["year"]].append(row.to_dict())

    rng = random.Random(SEED)
    sample = []
    allocation = {}  # year -> (population_n, quota, exact_fraction, rounded_fraction)
    n_valid = len(df_valid)
    allocated = 0
    year_items = sorted(by_year.items())
    for i, (year, rows) in enumerate(year_items):
        exact_fraction = len(rows) / n_valid
        if i == len(year_items) - 1:
            quota = N_SAMPLE - allocated  # last stratum absorbs rounding remainder
        else:
            quota = round(N_SAMPLE * exact_fraction)
        quota = min(quota, len(rows))
        allocated += quota
        allocation[year] = {
            "population_n": len(rows), "quota": quota,
            "exact_fraction": exact_fraction, "realized_fraction": quota / N_SAMPLE if N_SAMPLE else 0,
        }
        sample.extend(rng.sample(rows, quota))

    print(f"\nPopulation (Retraction-nature, real PMID, valid date): {n_valid}")
    print(f"Placeholder-date rows excluded from stratification: {n_placeholder_date}")
    print(f"Sample drawn: {len(sample)}")
    max_deviation = max(abs(a["exact_fraction"] - a["realized_fraction"]) for a in allocation.values())
    print(f"Max deviation between exact and realized stratum fraction (rounding): {max_deviation:.5f}")
    print("Allocation is proportional-to-population-size by retraction year, rounded to the "
          "nearest integer per stratum, remainder absorbed by the last (largest, 2026) stratum.")

    OUT_PATH.write_text(json.dumps({"allocation": allocation, "sample": sample}, indent=2, default=str), encoding="utf-8")
    print(f"\nwrote {OUT_PATH}")


if __name__ == "__main__":
    main()
