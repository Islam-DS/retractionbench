"""Unit tests for scripts/phase5_part_b_scaled_check.py's `_parse_pubmed`, specifically the
notice/original PMID mix-up check added per the author's explicit request (2026-10-05 round):
PubMed's `"Retraction of Publication"` pubtype applies to a retraction NOTICE's own PMID, while
`"Retracted Publication"` applies to the ORIGINAL article. If RW's `original_paper_pubmed_id`
actually points to a notice rather than the original, checking it for the first tag produces a
false gap. This was flagged as untested in the author's item-4 verification request; these tests
close that gap.
"""

import importlib.util
import sys
from pathlib import Path

_SPEC = importlib.util.spec_from_file_location(
    "phase5_part_b_scaled_check",
    Path(__file__).resolve().parent.parent / "scripts" / "phase5_part_b_scaled_check.py",
)
assert _SPEC is not None and _SPEC.loader is not None
_mod = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = _mod
_SPEC.loader.exec_module(_mod)
_parse_pubmed = _mod._parse_pubmed


def _esummary(pmid: str, title: str, pubtype: list[str]) -> dict:
    return {"result": {pmid: {"title": title, "pubtype": pubtype}}}


def test_original_article_tagged_retracted_publication_is_not_a_mixup():
    data = _esummary("123", "Some retracted paper.", ["Journal Article", "Retracted Publication"])
    r = _parse_pubmed(data, "123")
    assert r["tagged"] is True
    assert r["is_itself_a_retraction_notice"] is False


def test_notice_pmid_tagged_retraction_of_publication_is_flagged_as_mixup():
    data = _esummary("456", "Retraction: Some paper.", ["Published Erratum", "Retraction of Publication"])
    r = _parse_pubmed(data, "456")
    assert r["is_itself_a_retraction_notice"] is True
    # A notice's own PMID does not carry "Retracted Publication" -- these are distinct pubtypes,
    # not a substring of one another, and must not be conflated.
    assert r["tagged"] is False


def test_plain_untagged_article_is_neither():
    data = _esummary("789", "An ordinary paper.", ["Journal Article"])
    r = _parse_pubmed(data, "789")
    assert r["tagged"] is False
    assert r["is_itself_a_retraction_notice"] is False


def test_missing_record_returns_no_record_status():
    r = _parse_pubmed({"result": {}}, "999")
    assert r == {"status": "no_record"}


def test_record_with_error_key_returns_no_record_status():
    data = {"result": {"111": {"error": "cannot find uid"}}}
    r = _parse_pubmed(data, "111")
    assert r == {"status": "no_record"}
