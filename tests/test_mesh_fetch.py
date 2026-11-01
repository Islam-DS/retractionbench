"""Tests for MeSH-bounded, date-chunked PubMed corpus fetching. No live network calls."""

import json
from datetime import date
from pathlib import Path

import pytest

from retraction_bench.corpus.mesh_fetch import (
    DOMAIN_MESH_TERMS,
    _parse_efetch_xml,
    efetch_batch,
    esearch_count,
    esearch_with_history,
    fetch_domain_corpus,
    find_date_chunks,
)

SAMPLE_EFETCH_XML = """<?xml version="1.0"?>
<PubmedArticleSet>
  <PubmedArticle>
    <MedlineCitation>
      <PMID>12345</PMID>
      <Article>
        <ArticleTitle>A study of something.</ArticleTitle>
        <Abstract>
          <AbstractText Label="BACKGROUND">Background text.</AbstractText>
          <AbstractText Label="RESULTS">Results text.</AbstractText>
        </Abstract>
        <Journal>
          <Title>Journal of Examples</Title>
          <JournalIssue>
            <PubDate><Year>2019</Year></PubDate>
          </JournalIssue>
        </Journal>
      </Article>
    </MedlineCitation>
  </PubmedArticle>
  <PubmedArticle>
    <MedlineCitation>
      <PMID>67890</PMID>
      <Article>
        <ArticleTitle>Another study.</ArticleTitle>
        <Journal>
          <Title>Journal of More Examples</Title>
          <JournalIssue>
            <PubDate><Year>2021</Year></PubDate>
          </JournalIssue>
        </Journal>
      </Article>
    </MedlineCitation>
  </PubmedArticle>
</PubmedArticleSet>
"""


class _FakeResponse:
    def __init__(self, json_data: dict | None = None, text: str | None = None) -> None:
        self._json = json_data
        self.text = text or ""

    def raise_for_status(self) -> None:
        pass

    def json(self) -> dict:
        return self._json


class _FakeClient:
    """Routes by presence of `usehistory` (history search) vs its absence (count-only)
    vs a plain efetch URL, using a queue of pre-seeded responses per kind."""

    def __init__(self, count_responses=None, esearch_responses=None, efetch_responses=None) -> None:
        self._count_responses = list(count_responses or [])
        self._esearch_responses = list(esearch_responses or [])
        self._efetch_responses = list(efetch_responses or [])
        self.calls: list[dict] = []

    def get(self, url: str, params: dict, timeout: float | None = None) -> _FakeResponse:
        self.calls.append(params)
        if url.endswith("efetch.fcgi"):
            return self._efetch_responses.pop(0)
        if params.get("usehistory") == "y":
            return self._esearch_responses.pop(0)
        return self._count_responses.pop(0)

    def close(self) -> None:
        pass


@pytest.fixture(autouse=True)
def _ncbi_email(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("NCBI_EMAIL", "test@example.com")
    monkeypatch.delenv("NCBI_API_KEY", raising=False)


def test_domain_mesh_terms_cover_all_three_final_domains() -> None:
    assert set(DOMAIN_MESH_TERMS.keys()) == {
        "(HSC) Medicine - Pharmacology",
        "(HSC) Medicine - Obstetrics/Gynecology",
        "(HSC) Medicine - Rehabilitation/Therapy",
    }


def test_parse_efetch_xml_extracts_records() -> None:
    records = _parse_efetch_xml(SAMPLE_EFETCH_XML)
    assert len(records) == 2
    assert records[0].pmid == "12345"
    assert records[0].title == "A study of something."
    assert records[0].abstract == "Background text. Results text."
    assert records[0].journal == "Journal of Examples"
    assert records[0].pub_year == 2019


def test_parse_efetch_xml_handles_missing_abstract() -> None:
    records = _parse_efetch_xml(SAMPLE_EFETCH_XML)
    assert records[1].pmid == "67890"
    assert records[1].abstract == ""


def test_esearch_count_returns_count_without_history() -> None:
    client = _FakeClient(count_responses=[_FakeResponse({"esearchresult": {"count": "42"}})])
    assert esearch_count("some query", client=client) == 42
    assert "usehistory" not in client.calls[0]


def test_esearch_with_history_returns_webenv_query_key_count() -> None:
    client = _FakeClient(
        esearch_responses=[_FakeResponse({"esearchresult": {"webenv": "WEBENV1", "querykey": "1", "count": "42"}})]
    )
    webenv, query_key, count = esearch_with_history("some query", client=client)
    assert webenv == "WEBENV1"
    assert query_key == "1"
    assert count == 42


def test_efetch_batch_parses_response() -> None:
    client = _FakeClient(efetch_responses=[_FakeResponse(text=SAMPLE_EFETCH_XML)])
    records = efetch_batch("WEBENV1", "1", retstart=0, retmax=300, client=client)
    assert len(records) == 2
    assert client.calls[0]["retstart"] == "0"


def test_find_date_chunks_returns_single_chunk_when_under_cap() -> None:
    client = _FakeClient(count_responses=[_FakeResponse({"esearchresult": {"count": "500"}})])
    chunks = find_date_chunks("some mesh terms", client, date(2020, 1, 1), date(2020, 12, 31), max_count=9999)
    assert chunks == [(date(2020, 1, 1), date(2020, 12, 31), 500)]


def test_find_date_chunks_bisects_when_over_cap() -> None:
    # First call (full range) is over cap; both halves are under cap.
    client = _FakeClient(
        count_responses=[
            _FakeResponse({"esearchresult": {"count": "20000"}}),  # full range
            _FakeResponse({"esearchresult": {"count": "9000"}}),  # first half
            _FakeResponse({"esearchresult": {"count": "9500"}}),  # second half
        ]
    )
    chunks = find_date_chunks("some mesh terms", client, date(2020, 1, 1), date(2020, 12, 31), max_count=9999)
    assert len(chunks) == 2
    assert sum(c[2] for c in chunks) == 18500
    # chunks cover the full range with no gap
    assert chunks[0][0] == date(2020, 1, 1)
    assert chunks[1][1] == date(2020, 12, 31)
    assert chunks[0][1] < chunks[1][0]


def test_fetch_domain_corpus_writes_jsonl_and_tracks_progress(tmp_path: Path) -> None:
    output_path = tmp_path / "pharm.jsonl"
    client = _FakeClient(
        count_responses=[_FakeResponse({"esearchresult": {"count": "2"}})],
        esearch_responses=[_FakeResponse({"esearchresult": {"webenv": "WEBENV1", "querykey": "1", "count": "2"}})],
        efetch_responses=[_FakeResponse(text=SAMPLE_EFETCH_XML)],
    )
    fetched = fetch_domain_corpus("(HSC) Medicine - Pharmacology", output_path, client=client)
    assert fetched == 2
    lines = output_path.read_text(encoding="utf-8").strip().split("\n")
    assert len(lines) == 2
    row = json.loads(lines[0])
    assert row["pmid"] == "12345"
    assert row["domain"] == "(HSC) Medicine - Pharmacology"
    progress_path = output_path.with_suffix(".progress.json")
    assert progress_path.exists()
    assert len(json.loads(progress_path.read_text(encoding="utf-8"))) == 1


def test_fetch_domain_corpus_skips_chunks_already_marked_complete(tmp_path: Path) -> None:
    output_path = tmp_path / "pharm.jsonl"
    progress_path = output_path.with_suffix(".progress.json")
    # Pre-mark the only chunk's retstart as having reached its full count, so no
    # esearch/efetch calls should happen for it.
    client = _FakeClient(count_responses=[_FakeResponse({"esearchresult": {"count": "2"}})])
    from retraction_bench.corpus.mesh_fetch import DATE_END, DATE_START

    chunk_key = f"{DATE_START.isoformat()}:{DATE_END.isoformat()}"
    progress_path.write_text(json.dumps({chunk_key: 2}), encoding="utf-8")

    fetched = fetch_domain_corpus("(HSC) Medicine - Pharmacology", output_path, client=client)
    assert fetched == 0
    assert not output_path.exists() or output_path.read_text(encoding="utf-8") == ""


def test_fetch_domain_corpus_resumes_partial_chunk_without_reduplicating(tmp_path: Path) -> None:
    """ADR-133: a chunk interrupted after one batch must resume from that batch's retstart,
    not re-fetch the whole chunk from 0 and duplicate the already-written records.
    """
    output_path = tmp_path / "pharm.jsonl"
    progress_path = output_path.with_suffix(".progress.json")
    from retraction_bench.corpus.mesh_fetch import DATE_END, DATE_START

    chunk_key = f"{DATE_START.isoformat()}:{DATE_END.isoformat()}"
    # Simulate a prior interrupted run: one record already written, progress says retstart=1.
    output_path.write_text(json.dumps({"pmid": "99999", "domain": "(HSC) Medicine - Pharmacology"}) + "\n", encoding="utf-8")
    progress_path.write_text(json.dumps({chunk_key: 1}), encoding="utf-8")

    client = _FakeClient(
        count_responses=[_FakeResponse({"esearchresult": {"count": "2"}})],
        esearch_responses=[_FakeResponse({"esearchresult": {"webenv": "WEBENV1", "querykey": "1", "count": "2"}})],
        efetch_responses=[_FakeResponse(text=SAMPLE_EFETCH_XML)],
    )
    fetched = fetch_domain_corpus("(HSC) Medicine - Pharmacology", output_path, client=client, batch_size=300)
    lines = output_path.read_text(encoding="utf-8").strip().split("\n")
    pmids = [json.loads(line)["pmid"] for line in lines]
    # the pre-existing record is untouched, and the fetch resumed rather than restarting --
    # no second copy of it appears alongside the newly-fetched records
    assert pmids == ["99999", "12345", "67890"]
    assert fetched == 2
    # efetch was called with retstart=1 (the resume point), not 0 -- the actual bug fix
    assert client.calls[-1]["retstart"] == "1"
