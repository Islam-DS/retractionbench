"""Regression test: append_entry must actually match and replace the Phase 0 placeholder.

An earlier version used "--" in the placeholder constant while the real
docs/DATA_NOTES.md uses an em dash, so the replacement silently never
matched and the placeholder lingered forever.
"""

from pathlib import Path

from retraction_bench.ingest.data_notes import _PLACEHOLDER, append_entry


def test_append_entry_replaces_placeholder(tmp_path: Path) -> None:
    notes_path = tmp_path / "DATA_NOTES.md"
    notes_path.write_text(f"# Data Notes\n\n## Entries\n\n{_PLACEHOLDER}\n", encoding="utf-8")

    append_entry(notes_path, "Some finding", ["first line", "second line"])

    text = notes_path.read_text(encoding="utf-8")
    assert _PLACEHOLDER not in text
    assert "Some finding" in text
    assert "- first line" in text
    assert "- second line" in text


def test_append_entry_appends_without_placeholder(tmp_path: Path) -> None:
    notes_path = tmp_path / "DATA_NOTES.md"
    notes_path.write_text("# Data Notes\n\n## Entries\n\n### existing entry\n\n- old line\n", encoding="utf-8")

    append_entry(notes_path, "New finding", ["new line"])

    text = notes_path.read_text(encoding="utf-8")
    assert "existing entry" in text
    assert "old line" in text
    assert "New finding" in text
    assert "new line" in text


def test_append_entry_is_idempotent_for_identical_same_day_entry(tmp_path: Path) -> None:
    notes_path = tmp_path / "DATA_NOTES.md"
    notes_path.write_text("# Data Notes\n\n## Entries\n", encoding="utf-8")

    append_entry(notes_path, "Repeated finding", ["count: 5"])
    append_entry(notes_path, "Repeated finding", ["count: 5"])

    text = notes_path.read_text(encoding="utf-8")
    assert text.count("Repeated finding") == 1


def test_append_entry_still_appends_when_content_actually_changed(tmp_path: Path) -> None:
    notes_path = tmp_path / "DATA_NOTES.md"
    notes_path.write_text("# Data Notes\n\n## Entries\n", encoding="utf-8")

    append_entry(notes_path, "Repeated finding", ["count: 5"])
    append_entry(notes_path, "Repeated finding", ["count: 6"])

    text = notes_path.read_text(encoding="utf-8")
    assert text.count("Repeated finding") == 2
    assert "count: 5" in text
    assert "count: 6" in text
