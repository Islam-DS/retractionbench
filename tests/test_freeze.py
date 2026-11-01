"""Tests for corpus freeze-manifest hashing (ADR-054) and manifest rewriting (ADR-152)."""

import json

import pytest

from retraction_bench.corpus.freeze import content_sha256, write_manifest


def test_content_sha256_is_order_independent() -> None:
    rows_a = [{"pmid": "1", "abstract": "one"}, {"pmid": "2", "abstract": "two"}]
    rows_b = [{"pmid": "2", "abstract": "two"}, {"pmid": "1", "abstract": "one"}]
    assert content_sha256(rows_a) == content_sha256(rows_b)


def test_content_sha256_changes_when_a_document_is_added() -> None:
    before = [{"pmid": "1", "abstract": "one"}]
    after = [{"pmid": "1", "abstract": "one"}, {"pmid": "2", "abstract": "two"}]
    assert content_sha256(before) != content_sha256(after)


def test_content_sha256_changes_when_abstract_text_differs() -> None:
    rows_a = [{"pmid": "1", "abstract": "one"}]
    rows_b = [{"pmid": "1", "abstract": "one revised"}]
    assert content_sha256(rows_a) != content_sha256(rows_b)


def test_content_sha256_handles_missing_abstract() -> None:
    # Should not raise -- some rows (e.g. malformed upstream) may lack an abstract field.
    assert content_sha256([{"pmid": "1"}]) == content_sha256([{"pmid": "1", "abstract": ""}])


def _seed_manifest(path, record_count=1, content_sha256="old-hash"):
    path.write_text(
        json.dumps(
            {
                "freeze_date": "2026-08-09",
                "freeze_datetime_utc": "2026-08-09T01:59:00.915610Z",
                "record_count": record_count,
                "content_sha256": content_sha256,
                "update_history": [{"update_date": "2026-08-09", "reason": "original freeze"}],
            }
        ),
        encoding="utf-8",
    )


def test_write_manifest_raises_if_manifest_missing(tmp_path) -> None:
    rows = [{"pmid": "1", "abstract": "one", "domain": "Pharmacology", "corpus_role": "background", "pub_year": 2020}]
    with pytest.raises(FileNotFoundError):
        write_manifest(rows, tmp_path / "does_not_exist.json", reason="test")


def test_write_manifest_updates_record_count_and_hash(tmp_path) -> None:
    manifest_path = tmp_path / "CORPUS_FREEZE.json"
    _seed_manifest(manifest_path)
    rows = [
        {"pmid": "1", "abstract": "one", "domain": "Pharmacology", "corpus_role": "background", "pub_year": 2020},
        {"pmid": "2", "abstract": "two", "domain": "OB/GYN", "corpus_role": "background", "pub_year": 2021},
    ]
    result = write_manifest(rows, manifest_path, reason="test update")
    assert result["record_count"] == 2
    assert result["content_sha256"] == content_sha256(rows)
    on_disk = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert on_disk["record_count"] == 2


def test_write_manifest_preserves_and_appends_update_history(tmp_path) -> None:
    manifest_path = tmp_path / "CORPUS_FREEZE.json"
    _seed_manifest(manifest_path)
    rows = [{"pmid": "1", "abstract": "one", "domain": "Pharmacology", "corpus_role": "background", "pub_year": 2020}]
    result = write_manifest(rows, manifest_path, reason="test update")
    assert len(result["update_history"]) == 2
    assert result["update_history"][0]["reason"] == "original freeze"
    assert result["update_history"][1]["reason"] == "test update"
    assert result["update_history"][1]["previous_record_count"] == 1
    assert result["update_history"][1]["new_record_count"] == 1


def test_write_manifest_records_domain_and_role_counts(tmp_path) -> None:
    manifest_path = tmp_path / "CORPUS_FREEZE.json"
    _seed_manifest(manifest_path)
    rows = [
        {"pmid": "1", "abstract": "one", "domain": "Pharmacology", "corpus_role": "background", "pub_year": 2020},
        {"pmid": "2", "abstract": "two", "domain": "Pharmacology", "corpus_role": "background", "pub_year": 2020},
        {"pmid": "3", "abstract": "three", "domain": "OB/GYN", "corpus_role": "benchmark_source", "pub_year": 2021},
    ]
    result = write_manifest(rows, manifest_path, reason="test update")
    assert result["domain_counts"] == {"Pharmacology": 2, "OB/GYN": 1}
    assert result["corpus_role_counts"] == {"background": 2, "benchmark_source": 1}
    assert result["pub_year_min"] == 2020
    assert result["pub_year_max"] == 2021
