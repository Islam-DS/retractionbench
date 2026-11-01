"""Tests for the Phase 1 exploration report generator.

Uses the same small fixture as test_ingest_retraction_watch.py. No network,
no full database.
"""

from pathlib import Path

from retraction_bench.ingest.data_notes import _PLACEHOLDER
from retraction_bench.ingest.explore import append_data_quality_notes, build_report, load_enriched_frame
from retraction_bench.ingest.retraction_watch import load_raw_table

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "retraction_watch_sample.csv"


def _enriched_frame(tmp_path: Path):
    db_path = tmp_path / "test.duckdb"
    load_raw_table(FIXTURE_PATH, db_path=db_path)
    return load_enriched_frame(db_path)


def test_blank_rows_are_flagged_and_excluded_from_the_report(tmp_path: Path) -> None:
    df = _enriched_frame(tmp_path)
    assert int(df["is_blank_row"].sum()) == 1  # the fully-blank row appended to the fixture

    report = build_report(df)
    assert "1 completely blank rows" in report
    # 11 real rows, not 12 -- the blank row must not inflate the headline total.
    assert "Total raw records (all notice types): **11**" in report


def test_duplicate_record_id_excludes_blank_rows_correctly(tmp_path: Path) -> None:
    df = _enriched_frame(tmp_path)
    notes_path = tmp_path / "DATA_NOTES.md"
    notes_path.write_text(f"# Data Notes\n\n## Entries\n\n{_PLACEHOLDER}\n", encoding="utf-8")

    append_data_quality_notes(df, notes_path=notes_path)
    text = notes_path.read_text(encoding="utf-8")

    # Fixture has exactly one genuine duplicate (record_id 80004, x2) plus one
    # unrelated blank row. The blank row must not be counted as a "duplicate"
    # via pandas' NaN-matches-NaN semantics, and must not deflate nunique().
    assert "Duplicate Record IDs (among non-blank rows only): 2 rows across 1 distinct IDs" in text
    assert "Completely blank source rows" in text
    assert "1 records out of 12 total rows" in text


def test_malformed_and_negative_gap_records_are_findable_in_the_report(tmp_path: Path) -> None:
    df = _enriched_frame(tmp_path)
    report = build_report(df)

    # Record 80003 has an unparseable RetractionDate (13/45/2020) under Reinstatement.
    assert "| Reinstatement | 0 | 1 | 0 | 0 |" in report
    # Record 80002 has a negative gap (Correction retraction date predates the original paper).
    assert "| Correction | 0 | n/a | n/a | n/a | n/a | 1 |" in report
