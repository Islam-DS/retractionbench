import json
from pathlib import Path

import httpx
import pytest

from retraction_bench.corpus.pub_year_backfill import (
    BACKGROUND_SOURCE,
    FRESH_LOOKUP_SOURCE,
    UNRESOLVABLE_SOURCE,
    _parse_year,
    build_pub_year_lookup,
    fetch_pub_years_from_pubmed,
    load_lookup,
    write_lookup,
)


@pytest.fixture(autouse=True)
def _ncbi_email(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("NCBI_EMAIL", "test@example.com")
    monkeypatch.delenv("NCBI_API_KEY", raising=False)


def _mock_esummary_client(pmid_to_pubdate: dict[str, str]) -> httpx.Client:
    def handler(request: httpx.Request) -> httpx.Response:
        ids = request.url.params["id"].split(",")
        result = {"uids": ids}
        for pmid in ids:
            if pmid in pmid_to_pubdate:
                result[pmid] = {"pubdate": pmid_to_pubdate[pmid]}
            else:
                result[pmid] = {"error": "cannot get document summary"}
        return httpx.Response(200, json={"result": result})

    return httpx.Client(transport=httpx.MockTransport(handler))


# --- _parse_year: real, observed NCBI pubdate formats ---


@pytest.mark.parametrize(
    "pubdate,expected",
    [
        ("2017 Jun", 2017),
        ("2017", 2017),
        ("2017 Jun-Jul", 2017),
        ("2017 Jun 12", 2017),
        ("", None),
        ("no year here", None),
    ],
)
def test_parse_year(pubdate: str, expected: int | None) -> None:
    assert _parse_year(pubdate) == expected


# --- fetch_pub_years_from_pubmed ---


def test_fetch_pub_years_resolves_known_pmids_and_leaves_unknown_as_none() -> None:
    client = _mock_esummary_client({"111": "2019 Jan", "222": "2021"})
    result = fetch_pub_years_from_pubmed(["111", "222", "333"], client=client)
    assert result == {"111": 2019, "222": 2021, "333": None}


# --- build_pub_year_lookup: role-based branching, no gold-field use ---


def _write_corpus(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row) + "\n")


def test_background_rows_keep_existing_pub_year_unchanged_no_refetch(tmp_path: Path) -> None:
    corpus_path = tmp_path / "corpus.jsonl"
    _write_corpus(
        corpus_path,
        [{"pmid": "1", "corpus_role": "background", "pub_year": 2010, "domain": "d"}],
    )
    # A client that would error on ANY request -- proves background rows never trigger a fetch.
    client = httpx.Client(transport=httpx.MockTransport(lambda r: (_ for _ in ()).throw(AssertionError("should not be called"))))
    records = build_pub_year_lookup(corpus_path, client=client)
    assert records == [__import__("retraction_bench.corpus.pub_year_backfill", fromlist=["PubYearRecord"]).PubYearRecord(
        pmid="1", corpus_role="background", pub_year=2010, source=BACKGROUND_SOURCE
    )]


def test_benchmark_source_and_superseding_evidence_rows_resolved_fresh(tmp_path: Path) -> None:
    corpus_path = tmp_path / "corpus.jsonl"
    _write_corpus(
        corpus_path,
        [
            {"pmid": "100", "corpus_role": "benchmark_source", "domain": "d", "linked_source_registry_id": "rw-1"},
            {"pmid": "200", "corpus_role": "superseding_evidence", "domain": "d", "linked_source_registry_id": "10.1/x"},
        ],
    )
    client = _mock_esummary_client({"100": "2015 Mar", "200": "2022 Nov"})
    records = build_pub_year_lookup(corpus_path, client=client)
    by_pmid = {r.pmid: r for r in records}
    assert by_pmid["100"].pub_year == 2015
    assert by_pmid["100"].source == FRESH_LOOKUP_SOURCE
    assert by_pmid["200"].pub_year == 2022
    assert by_pmid["200"].source == FRESH_LOOKUP_SOURCE


def test_supersession_notice_rows_are_explicitly_unresolvable_never_guessed(tmp_path: Path) -> None:
    corpus_path = tmp_path / "corpus.jsonl"
    _write_corpus(
        corpus_path,
        [{"pmid": "rw-1-notice", "corpus_role": "supersession_notice", "domain": "d", "linked_source_registry_id": "rw-1"}],
    )
    client = httpx.Client(transport=httpx.MockTransport(lambda r: (_ for _ in ()).throw(AssertionError("should not be called"))))
    records = build_pub_year_lookup(corpus_path, client=client)
    assert records[0].pub_year is None
    assert records[0].source == UNRESOLVABLE_SOURCE
    assert "synthetic" in records[0].note


def test_unresolvable_real_pmid_is_none_not_guessed(tmp_path: Path) -> None:
    corpus_path = tmp_path / "corpus.jsonl"
    _write_corpus(corpus_path, [{"pmid": "999", "corpus_role": "benchmark_source", "domain": "d"}])
    client = _mock_esummary_client({})  # NCBI has nothing for this pmid
    records = build_pub_year_lookup(corpus_path, client=client)
    assert records[0].pub_year is None
    assert records[0].source == FRESH_LOOKUP_SOURCE
    assert "no parseable pubdate" in records[0].note


# --- write_lookup / load_lookup round-trip ---


def test_write_then_load_lookup_round_trips(tmp_path: Path) -> None:
    corpus_path = tmp_path / "corpus.jsonl"
    _write_corpus(
        corpus_path,
        [
            {"pmid": "1", "corpus_role": "background", "pub_year": 2010, "domain": "d"},
            {"pmid": "rw-1-notice", "corpus_role": "supersession_notice", "domain": "d"},
        ],
    )
    client = httpx.Client(transport=httpx.MockTransport(lambda r: (_ for _ in ()).throw(AssertionError("should not be called"))))
    records = build_pub_year_lookup(corpus_path, client=client)
    lookup_path = tmp_path / "lookup.jsonl"
    write_lookup(records, lookup_path)
    loaded = load_lookup(lookup_path)
    assert loaded == {"1": 2010, "rw-1-notice": None}
