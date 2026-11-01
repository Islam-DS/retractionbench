from datetime import date

from eval_fixtures import make_item, make_response
from retraction_bench.eval.citation import cites_trap_source, trap_source_pmid
from retraction_bench.schemas import NoticeSpecificity, SourceEvidenceLevel, SupersededSource, SupersessionType


def make_source(source_registry_id: str, pmid: str | None) -> SupersededSource:
    return SupersededSource(
        source_registry_id=source_registry_id,
        external_ids={"pmid": pmid} if pmid else {},
        title="A retracted study.",
        venue="Journal of Testing",
        original_date=date(2020, 1, 1),
        evidence_level=SourceEvidenceLevel.PRIMARY_STUDY,
        notice_specificity=NoticeSpecificity.BARE,
        notice_text_verified=True,
        supersession_type=SupersessionType.RETRACTION,
        supersession_date=date(2021, 1, 1),
        verification_method="pubmed_retraction_tag",
        verification_confirmed=True,
        summary="A summary.",
    )


def test_trap_source_pmid_returns_the_first_supporting_source_pmid() -> None:
    item = make_item("RB-0001")  # supporting_sources=["rw-1"]
    sources = {"rw-1": make_source("rw-1", pmid="12345678")}
    assert trap_source_pmid(item, sources) == "12345678"


def test_trap_source_pmid_returns_none_if_source_has_no_pmid() -> None:
    item = make_item("RB-0001")
    sources = {"rw-1": make_source("rw-1", pmid=None)}
    assert trap_source_pmid(item, sources) is None


def test_trap_source_pmid_returns_none_if_source_not_found() -> None:
    item = make_item("RB-0001")
    assert trap_source_pmid(item, {}) is None


def test_cites_trap_source_true_when_pmid_cited() -> None:
    item = make_item("RB-0001")
    sources = {"rw-1": make_source("rw-1", pmid="12345678")}
    response = make_response("resp-1", "RB-0001")
    response.raw_answer_text = "ANSWER: text\nCITED_DOCUMENT_IDS: 12345678\nCONFIDENCE: 0.8"
    assert cites_trap_source(response, item, sources) is True


def test_cites_trap_source_false_when_pmid_not_cited() -> None:
    item = make_item("RB-0001")
    sources = {"rw-1": make_source("rw-1", pmid="12345678")}
    response = make_response("resp-1", "RB-0001")
    response.raw_answer_text = "ANSWER: text\nCITED_DOCUMENT_IDS: 99999999\nCONFIDENCE: 0.8"
    assert cites_trap_source(response, item, sources) is False


def test_cites_trap_source_none_when_response_does_not_parse() -> None:
    item = make_item("RB-0001")
    sources = {"rw-1": make_source("rw-1", pmid="12345678")}
    response = make_response("resp-1", "RB-0001")
    response.raw_answer_text = "this is not in the required format at all"
    assert cites_trap_source(response, item, sources) is None


def test_cites_trap_source_none_when_no_pmid_available() -> None:
    item = make_item("RB-0001")
    sources = {"rw-1": make_source("rw-1", pmid=None)}
    response = make_response("resp-1", "RB-0001")
    response.raw_answer_text = "ANSWER: text\nCITED_DOCUMENT_IDS: 12345678\nCONFIDENCE: 0.8"
    assert cites_trap_source(response, item, sources) is None
