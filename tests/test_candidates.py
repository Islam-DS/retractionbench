"""Tests for tier-1 candidate export, using a small purpose-built fixture.

Not the shared retraction_watch_sample.csv fixture -- several other tests
depend on its exact row count, and this needs rows engineered to hit every
filter dimension (tier, post-2015, PMID-resolvable, requested subject).
"""

from pathlib import Path

from retraction_bench.curate.candidates import export_tier1_candidates
from retraction_bench.ingest.retraction_watch import load_raw_table

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "retraction_watch_candidates_sample.csv"

SCREEN_YAML = """
schema_version: "0.1.0"
reasons:
  - reason: "Unreliable Results and/or Conclusions"
    screen_class: claim_invalidating
  - reason: "Concerns/Issues about Data"
    screen_class: claim_invalidating
  - reason: "Paper Mill"
    screen_class: process_only
"""


def _setup(tmp_path: Path) -> tuple[Path, Path]:
    db_path = tmp_path / "test.duckdb"
    load_raw_table(FIXTURE_PATH, db_path=db_path)
    screen_path = tmp_path / "reason_screen.yaml"
    screen_path.write_text(SCREEN_YAML, encoding="utf-8")
    return db_path, screen_path


def test_export_filters_to_tier1_post2015_pmid_and_requested_subjects(tmp_path: Path) -> None:
    db_path, screen_path = _setup(tmp_path)
    output_path = tmp_path / "candidates.csv"

    out = export_tier1_candidates(
        ["(HSC) Medicine - Oncology", "(HSC) Medicine - Pharmacology"],
        db_path=db_path,
        screen_path=screen_path,
        output_path=output_path,
    )

    # Only 90001 (clean oncology) and 90002 (clean pharmacology) should survive:
    # 90003 has a process_only reason too, 90004 predates 2016, 90005 has no
    # PMID, and 90006 (Cardiology) wasn't in the requested subject list.
    assert set(out["record_id"]) == {"90001", "90002"}
    assert output_path.exists()


def test_export_writes_expected_columns(tmp_path: Path) -> None:
    db_path, screen_path = _setup(tmp_path)
    output_path = tmp_path / "candidates.csv"

    out = export_tier1_candidates(
        ["(HSC) Medicine - Oncology"], db_path=db_path, screen_path=screen_path, output_path=output_path
    )

    assert list(out.columns) == [
        "domain",
        "record_id",
        "doi",
        "pmid",
        "title",
        "author",
        "journal",
        "original_date",
        "retraction_date",
        "reasons",
        "tier",
        "claim_type_screen_label",
    ]
    row = out.iloc[0]
    assert row["domain"] == "(HSC) Medicine - Oncology"
    assert row["doi"] == "10.1111/aaaa"
    assert row["tier"] == "tier_1_clean"
    assert row["claim_type_screen_label"] in {"clinical_intervention", "clinical_observational"}


def test_export_excludes_unrequested_subject(tmp_path: Path) -> None:
    db_path, screen_path = _setup(tmp_path)
    output_path = tmp_path / "candidates.csv"

    out = export_tier1_candidates(
        ["(HSC) Medicine - Oncology"], db_path=db_path, screen_path=screen_path, output_path=output_path
    )

    assert "(HSC) Medicine - Cardiology" not in set(out["domain"])


def test_export_excludes_preclinical_titles_even_with_clean_reason_tags(tmp_path: Path) -> None:
    # 90007 is tier_1_clean by reason tags alone, but its title is
    # unambiguously preclinical (cell line + mouse model) -- the claim-type
    # screen must exclude it even though the reason screen alone wouldn't.
    db_path, screen_path = _setup(tmp_path)
    output_path = tmp_path / "candidates.csv"

    out = export_tier1_candidates(
        ["(HSC) Medicine - Oncology"], db_path=db_path, screen_path=screen_path, output_path=output_path
    )

    assert "90007" not in set(out["record_id"])
