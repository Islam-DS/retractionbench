"""Tier-1 candidate export for hand review (Stage 1B).

Produces a plain, reviewable CSV -- not a BenchmarkItem, not yet annotated.
This is what the author hand-checks before committing to a candidate pool.
"""

from pathlib import Path

import pandas as pd

from retraction_bench.curate.claim_type_screen import DEFAULT_CLAIM_SCREEN_PATH
from retraction_bench.curate.reason_screen import DEFAULT_SCREEN_PATH, Tier
from retraction_bench.ingest.explore import load_enriched_frame
from retraction_bench.ingest.retraction_watch import DB_PATH

DEFAULT_OUTPUT_PATH = Path("data/interim/tier1_candidates.csv")


def export_tier1_candidates(
    subjects: list[str],
    db_path: Path = DB_PATH,
    screen_path: Path = DEFAULT_SCREEN_PATH,
    claim_screen_path: Path = DEFAULT_CLAIM_SCREEN_PATH,
    output_path: Path = DEFAULT_OUTPUT_PATH,
) -> pd.DataFrame:
    """Write one reviewable table of tier_1_clean, clinical-claim candidates across the given subjects.

    Scope matches the funnel used throughout domain selection (ADR-021):
    Retraction only, post-2015, PubMed-ID-resolvable, tier_1_clean, AND
    passed the claim-type screen as clinical_intervention or
    clinical_observational. Both screens are heuristic pre-filters, not
    ground truth -- see their respective ADRs.
    """
    df = load_enriched_frame(db_path, screen_path, claim_screen_path)
    df = df[~df["is_blank_row"]]
    retraction_df = df[df["retraction_nature"] == "Retraction"].copy()
    retraction_df = retraction_df[retraction_df["retraction_date_parsed"].dt.year >= 2016]
    retraction_df = retraction_df[retraction_df["original_paper_pubmed_id_resolvable"]]
    retraction_df = retraction_df[retraction_df["candidate_tier"] == Tier.TIER_1_CLEAN]
    retraction_df = retraction_df[retraction_df["is_clinical_claim"]]

    exploded = retraction_df.explode("subject_list")
    exploded = exploded[exploded["subject_list"].isin(subjects)]

    out = pd.DataFrame(
        {
            "domain": exploded["subject_list"],
            "record_id": exploded["record_id"],
            "doi": exploded["original_paper_doi"],
            "pmid": exploded["original_paper_pubmed_id"],
            "title": exploded["title"],
            "author": exploded["author"],
            "journal": exploded["journal"],
            "original_date": exploded["original_paper_date_parsed"].dt.date,
            "retraction_date": exploded["retraction_date_parsed"].dt.date,
            "reasons": exploded["reason_list"].apply(lambda rs: "; ".join(rs)),
            "tier": exploded["candidate_tier"].apply(str),
            # Screen output only -- a candidate-pool provenance label, never the annotated item's
            # claim_type (schemas.BenchmarkItem.claim_type is human-annotated separately; ADR-030).
            "claim_type_screen_label": exploded["claim_type"].apply(str),
        }
    )
    out = out.sort_values(["domain", "record_id"]).reset_index(drop=True)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(output_path, index=False)
    return out
