"""Tests for PubMed ESummary verification. No live network calls -- a fake
client stands in, seeded with response shapes confirmed against the real
API (see pubmed.py's module docstring for how that was checked).
"""

from pathlib import Path

import pandas as pd
import pytest

from retraction_bench.ingest.pubmed import (
    BATCH_SIZE,
    PubMedVerification,
    load_cache,
    save_cache,
    verify_candidates_csv,
    verify_pmids,
    verify_pmids_cached,
)


class _FakeResponse:
    def __init__(self, json_data: dict) -> None:
        self._json = json_data

    def raise_for_status(self) -> None:
        pass

    def json(self) -> dict:
        return self._json


class _FakeClient:
    def __init__(self, response_for_batch) -> None:
        self._response_for_batch = response_for_batch  # callable(ids: list[str]) -> dict
        self.calls: list[dict] = []

    def get(self, url: str, params: dict) -> _FakeResponse:
        self.calls.append(params)
        ids = params["id"].split(",")
        return _FakeResponse(self._response_for_batch(ids))

    def close(self) -> None:
        pass


def _esummary_response(ids: list[str], retracted: set[str], errored: set[str]) -> dict:
    result = {"uids": ids}
    for pmid in ids:
        if pmid in errored:
            result[pmid] = {"uid": pmid, "error": "cannot get document summary"}
        elif pmid in retracted:
            result[pmid] = {"uid": pmid, "pubtype": ["Journal Article", "Retracted Publication"]}
        else:
            result[pmid] = {"uid": pmid, "pubtype": ["Journal Article"]}
    return {"header": {"type": "esummary", "version": "0.3"}, "result": result}


@pytest.fixture(autouse=True)
def _ncbi_email(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("NCBI_EMAIL", "test@example.com")
    monkeypatch.delenv("NCBI_API_KEY", raising=False)


def test_verify_pmids_detects_retracted_tag() -> None:
    client = _FakeClient(lambda ids: _esummary_response(ids, retracted={"25482610"}, errored=set()))
    results = verify_pmids(["25482610", "1"], client=client)

    assert results["25482610"].is_retracted_tagged is True
    assert results["25482610"].pubtypes == ["Journal Article", "Retracted Publication"]
    assert results["1"].is_retracted_tagged is False


def test_verify_pmids_handles_unresolvable_pmid_as_error_not_false() -> None:
    client = _FakeClient(lambda ids: _esummary_response(ids, retracted=set(), errored={"999999999999"}))
    results = verify_pmids(["999999999999"], client=client)

    result = results["999999999999"]
    assert result.pubtypes is None
    assert result.is_retracted_tagged is False
    assert result.error is not None


def test_verify_pmids_requires_ncbi_email(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("NCBI_EMAIL", raising=False)
    with pytest.raises(RuntimeError, match="NCBI_EMAIL"):
        verify_pmids(["1"], client=_FakeClient(lambda ids: _esummary_response(ids, set(), set())))


def test_verify_pmids_batches_large_requests() -> None:
    pmids = [str(i) for i in range(BATCH_SIZE + 10)]
    client = _FakeClient(lambda ids: _esummary_response(ids, retracted=set(), errored=set()))

    results = verify_pmids(pmids, client=client)

    assert len(results) == len(pmids)
    assert len(client.calls) == 2  # one full batch + one partial batch
    assert len(client.calls[0]["id"].split(",")) == BATCH_SIZE
    assert len(client.calls[1]["id"].split(",")) == 10


def test_cache_round_trip(tmp_path: Path) -> None:
    cache_path = tmp_path / "cache.csv"
    original = {
        "1": PubMedVerification(pmid="1", pubtypes=["Journal Article"], is_retracted_tagged=False),
        "2": PubMedVerification(
            pmid="2", pubtypes=["Journal Article", "Retracted Publication"], is_retracted_tagged=True
        ),
        "3": PubMedVerification(
            pmid="3", pubtypes=None, is_retracted_tagged=False, error="cannot get document summary"
        ),
    }
    save_cache(cache_path, original)
    reloaded = load_cache(cache_path)

    assert reloaded.keys() == original.keys()
    for pmid in original:
        assert reloaded[pmid] == original[pmid]


def test_verify_pmids_cached_skips_already_cached_pmids(tmp_path: Path) -> None:
    cache_path = tmp_path / "cache.csv"
    client = _FakeClient(lambda ids: _esummary_response(ids, retracted={"25482610"}, errored=set()))

    first = verify_pmids_cached(["25482610", "1"], cache_path=cache_path, client=client)
    assert len(client.calls) == 1
    assert first["25482610"].is_retracted_tagged is True

    # Second call for the same PMIDs plus one new one should only fetch the new one.
    second = verify_pmids_cached(["25482610", "1", "2"], cache_path=cache_path, client=client)
    assert len(client.calls) == 2  # one more call, for "2" only
    assert client.calls[1]["id"] == "2"
    assert second["25482610"].is_retracted_tagged is True


def test_verify_candidates_csv_adds_verification_columns(tmp_path: Path) -> None:
    candidates_path = tmp_path / "candidates.csv"
    pd.DataFrame({"record_id": ["r1", "r2"], "pmid": ["25482610", "999999999999"]}).to_csv(candidates_path, index=False)
    output_path = tmp_path / "verified.csv"
    cache_path = tmp_path / "cache.csv"
    client = _FakeClient(lambda ids: _esummary_response(ids, retracted={"25482610"}, errored={"999999999999"}))

    out = verify_candidates_csv(candidates_path, output_path=output_path, cache_path=cache_path, client=client)

    assert output_path.exists()
    row1 = out[out["record_id"] == "r1"].iloc[0]
    row2 = out[out["record_id"] == "r2"].iloc[0]
    assert row1["pubmed_retracted_tag_confirmed"] == True  # noqa: E712 -- explicit bool check on a real column
    assert row2["pubmed_retracted_tag_confirmed"] == False  # noqa: E712
    assert row2["pubmed_lookup_error"] != ""
