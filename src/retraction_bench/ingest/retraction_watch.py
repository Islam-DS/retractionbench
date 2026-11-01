"""Acquisition of the Retraction Watch database (Stage 1A).

Downloads the Crossref-hosted CSV release and loads it into DuckDB with its
raw shape fully preserved -- no coercion into SupersededSource, no dropped
columns, no silent type coercion. See docs/DECISIONS.md (ADR-015) for why
this access route was chosen over `git clone` or the Crossref REST API.
"""

from dataclasses import dataclass
from datetime import date
from pathlib import Path

import duckdb
import httpx

from retraction_bench.ingest.data_notes import append_entry

SOURCE_URL = "https://gitlab.com/crossref/retraction-watch-data/-/raw/main/retraction_watch.csv"
USER_AGENT = "retraction-bench-ingest/0.1 (academic research benchmark; non-commercial)"

RAW_DIR = Path("data/raw")
INTERIM_DIR = Path("data/interim")
DB_PATH = INTERIM_DIR / "retraction_watch.duckdb"
DATA_NOTES_PATH = Path("docs/DATA_NOTES.md")

RAW_TABLE_NAME = "raw_retraction_watch"

# The source header ends in a trailing comma (a quirk of the export, not of
# our fetch -- verified by inspecting the raw file directly), producing an
# unnamed 21st field. We name it explicitly rather than let a CSV reader
# guess, and keep it in the raw table so nothing is silently dropped.
RAW_COLUMNS = {
    "record_id": "VARCHAR",
    "title": "VARCHAR",
    "subject": "VARCHAR",
    "institution": "VARCHAR",
    "journal": "VARCHAR",
    "publisher": "VARCHAR",
    "country": "VARCHAR",
    "author": "VARCHAR",
    "urls": "VARCHAR",
    "article_type": "VARCHAR",
    "retraction_date": "VARCHAR",
    "retraction_doi": "VARCHAR",
    "retraction_pubmed_id": "VARCHAR",
    "original_paper_date": "VARCHAR",
    "original_paper_doi": "VARCHAR",
    "original_paper_pubmed_id": "VARCHAR",
    "retraction_nature": "VARCHAR",
    "reason": "VARCHAR",
    "paywalled": "VARCHAR",
    "notes": "VARCHAR",
    "trailing_unnamed": "VARCHAR",
}


@dataclass
class RawLoadReport:
    row_count: int
    trailing_column_nonempty_count: int


def cache_path_for(retrieval_date: date, raw_dir: Path = RAW_DIR) -> Path:
    return raw_dir / f"retraction_watch_{retrieval_date.isoformat()}.csv"


def download_csv(
    dest_dir: Path = RAW_DIR,
    force: bool = False,
    data_notes_path: Path = DATA_NOTES_PATH,
) -> Path:
    """Download the source CSV, caching by retrieval date. Never re-downloads same-day unless force=True."""
    dest_dir.mkdir(parents=True, exist_ok=True)
    today = date.today()
    dest = cache_path_for(today, dest_dir)

    if dest.exists() and not force:
        return dest

    tmp_dest = dest.with_suffix(dest.suffix + ".tmp")
    with (
        httpx.stream(
            "GET", SOURCE_URL, headers={"User-Agent": USER_AGENT}, follow_redirects=True, timeout=120.0
        ) as response,
        tmp_dest.open("wb") as f,
    ):
        response.raise_for_status()
        for chunk in response.iter_bytes():
            f.write(chunk)
    tmp_dest.replace(dest)

    append_entry(
        data_notes_path,
        "Retraction Watch source acquisition",
        [
            f"Source URL: {SOURCE_URL}",
            f"Access date: {today.isoformat()}",
            f"Cached to: {dest}",
            "Access method: anonymous HTTPS GET (see docs/DECISIONS.md ADR-015 for why, not `git clone`).",
        ],
    )
    return dest


def load_raw_table(csv_path: Path, db_path: Path = DB_PATH) -> RawLoadReport:
    """Load the CSV into DuckDB as-is: every column VARCHAR, no coercion, nothing dropped."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = duckdb.connect(str(db_path))
    try:
        conn.execute(
            f"""
            CREATE OR REPLACE TABLE {RAW_TABLE_NAME} AS
            SELECT * FROM read_csv(
                ?,
                columns = {RAW_COLUMNS!r},
                header = false,
                skip = 1,
                delim = ',',
                quote = '"',
                escape = '"'
            )
            """,
            [str(csv_path)],
        )
        row_count = conn.execute(f"SELECT count(*) FROM {RAW_TABLE_NAME}").fetchone()[0]
        trailing_nonempty = conn.execute(
            f"SELECT count(*) FROM {RAW_TABLE_NAME} WHERE trailing_unnamed IS NOT NULL AND trailing_unnamed != ''"
        ).fetchone()[0]
    finally:
        conn.close()
    return RawLoadReport(row_count=row_count, trailing_column_nonempty_count=trailing_nonempty)


def ingest(force: bool = False) -> RawLoadReport:
    """Full Stage 1A acquisition: download (if needed) + load into DuckDB."""
    csv_path = download_csv(force=force)
    return load_raw_table(csv_path)
