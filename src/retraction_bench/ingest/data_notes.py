"""Append-only writer for docs/DATA_NOTES.md.

Every exclusion rule, parse failure, or data-quality anomaly the ingest
pipeline finds gets recorded here with a count, per the project protocol's reviewer
scrutiny requirement -- never silently dropped.
"""

from datetime import date
from pathlib import Path

_PLACEHOLDER = "_(none yet — Phase 0, no data ingested)_"


def append_entry(notes_path: Path, heading: str, lines: list[str]) -> None:
    """Append a dated, headed entry to DATA_NOTES.md, replacing the Phase 0 placeholder on first use.

    Idempotent for same-day reruns: if the identical heading+body already
    appears under today's date, it is not appended again -- re-running
    `explore` or `ingest` shouldn't pile up duplicate notes when nothing
    about the underlying finding has changed.
    """
    text = notes_path.read_text(encoding="utf-8")
    if _PLACEHOLDER in text:
        text = text.replace(_PLACEHOLDER, "").rstrip() + "\n"

    body = "\n".join(f"- {line}" for line in lines)
    entry_header = f"### {date.today().isoformat()} -- {heading}"
    entry = f"\n{entry_header}\n\n{body}\n"
    if entry_header in text and body in text:
        notes_path.write_text(text, encoding="utf-8")
        return
    notes_path.write_text(text + entry, encoding="utf-8")
