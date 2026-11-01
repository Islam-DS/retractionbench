"""Tests for Retraction Watch parsing and raw-loading logic.

Uses the small fixture at tests/fixtures/retraction_watch_sample.csv --
never the full database. No network access.
"""

from pathlib import Path

import duckdb
import pytest

from retraction_bench.ingest.parsing import (
    is_missing_value,
    is_resolvable_doi,
    parse_rw_date,
    split_multivalue,
)
from retraction_bench.ingest.retraction_watch import RAW_TABLE_NAME, load_raw_table

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "retraction_watch_sample.csv"


# --- parsing.py: pure function edge cases ---------------------------------


@pytest.mark.parametrize("raw", [None, "", "unavailable", "Unavailable", "UNAVAILABLE", "0", "  "])
def test_is_missing_value_recognizes_all_documented_sentinels(raw: str | None) -> None:
    assert is_missing_value(raw)


@pytest.mark.parametrize("raw", ["10.1007/s00500-023-08272-z", "10.5555/12345"])
def test_is_resolvable_doi_accepts_real_doi_syntax(raw: str) -> None:
    assert is_resolvable_doi(raw)


@pytest.mark.parametrize("raw", [None, "", "unavailable", "not-a-real-doi", "10.abc/xyz"])
def test_is_resolvable_doi_rejects_missing_and_malformed(raw: str | None) -> None:
    assert not is_resolvable_doi(raw)


def test_parse_rw_date_strict_success() -> None:
    assert parse_rw_date("11/3/2024 0:00").isoformat() == "2024-11-03"


@pytest.mark.parametrize("raw", [None, "", "13/45/2020 0:00", "2024-11-03", "not a date"])
def test_parse_rw_date_returns_none_rather_than_guessing(raw: str | None) -> None:
    # Strict per docs/DECISIONS.md: an ambiguous or malformed date must
    # never be silently coerced into a plausible-looking date.
    assert parse_rw_date(raw) is None


def test_split_multivalue_trims_and_drops_trailing_empty() -> None:
    assert split_multivalue("Fabrication/False Data;Concerns/Issues about Image;") == [
        "Fabrication/False Data",
        "Concerns/Issues about Image",
    ]


def test_split_multivalue_empty_input() -> None:
    assert split_multivalue("") == []
    assert split_multivalue(None) == []


# --- retraction_watch.py: raw DuckDB load against the fixture -------------


def test_load_raw_table_preserves_row_count_and_shape(tmp_path: Path) -> None:
    db_path = tmp_path / "test.duckdb"
    report = load_raw_table(FIXTURE_PATH, db_path=db_path)

    assert report.row_count == 12  # 11 real rows + 1 fully-blank artifact row
    assert report.trailing_column_nonempty_count == 0

    conn = duckdb.connect(str(db_path))
    try:
        columns = [row[0] for row in conn.execute(f"DESCRIBE {RAW_TABLE_NAME}").fetchall()]
        assert columns == [
            "record_id",
            "title",
            "subject",
            "institution",
            "journal",
            "publisher",
            "country",
            "author",
            "urls",
            "article_type",
            "retraction_date",
            "retraction_doi",
            "retraction_pubmed_id",
            "original_paper_date",
            "original_paper_doi",
            "original_paper_pubmed_id",
            "retraction_nature",
            "reason",
            "paywalled",
            "notes",
            "trailing_unnamed",
        ]

        # Raw shape: values are untouched strings, not coerced to other types.
        first_row = conn.execute(
            f"SELECT record_id, retraction_pubmed_id FROM {RAW_TABLE_NAME} ORDER BY record_id DESC LIMIT 1"
        ).fetchone()
        assert first_row == ("80007", "123456")

        # A malformed date stays exactly as the raw string -- parsing happens later, not here.
        malformed_date_row = conn.execute(
            f"SELECT retraction_date FROM {RAW_TABLE_NAME} WHERE record_id = '80003'"
        ).fetchone()
        assert malformed_date_row == ("13/45/2020 0:00",)

        # Duplicate Record IDs are preserved raw, not deduplicated at this stage.
        duplicate_count = conn.execute(f"SELECT count(*) FROM {RAW_TABLE_NAME} WHERE record_id = '80004'").fetchone()[0]
        assert duplicate_count == 2
    finally:
        conn.close()
