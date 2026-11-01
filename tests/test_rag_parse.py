from retraction_bench.rag.parse import parse_response
from retraction_bench.schemas import ParseStatus


def test_parses_well_formed_response() -> None:
    raw = "ANSWER: Drug X does not reduce mortality.\nCITED_DOCUMENT_IDS: doc-1, doc-2\nCONFIDENCE: high"
    result = parse_response(raw)
    assert result.parse_status == ParseStatus.PARSED
    assert result.answer == "Drug X does not reduce mortality."
    assert result.cited_document_ids == ["doc-1", "doc-2"]
    assert result.confidence == "high"


def test_confidence_is_normalized_to_lowercase() -> None:
    raw = "ANSWER: Drug X does not reduce mortality.\nCITED_DOCUMENT_IDS: doc-1\nCONFIDENCE: HIGH"
    result = parse_response(raw)
    assert result.parse_status == ParseStatus.PARSED
    assert result.confidence == "high"


def test_parses_none_cited_document_ids_as_empty_list() -> None:
    raw = "ANSWER: Insufficient evidence.\nCITED_DOCUMENT_IDS: NONE\nCONFIDENCE: low"
    result = parse_response(raw)
    assert result.parse_status == ParseStatus.PARSED
    assert result.cited_document_ids == []


def test_parses_regardless_of_surrounding_prose() -> None:
    raw = "Some preamble text.\n\nANSWER: Yes.\nCITED_DOCUMENT_IDS: doc-1\nCONFIDENCE: medium\n\nTrailing text."
    result = parse_response(raw)
    assert result.parse_status == ParseStatus.PARSED
    assert result.answer == "Yes."


def test_missing_confidence_field_is_malformed_not_repaired() -> None:
    raw = "ANSWER: Yes.\nCITED_DOCUMENT_IDS: doc-1"
    result = parse_response(raw)
    assert result.parse_status == ParseStatus.MALFORMED
    assert result.answer is None
    assert result.cited_document_ids is None
    assert result.confidence is None


def test_completely_unstructured_text_is_malformed() -> None:
    raw = "The evidence on this topic is mixed and further research is needed."
    result = parse_response(raw)
    assert result.parse_status == ParseStatus.MALFORMED


def test_refusal_marker_detected_without_structured_format() -> None:
    raw = "I cannot provide medical advice. Please consult a physician."
    result = parse_response(raw)
    assert result.parse_status == ParseStatus.REFUSED
    assert result.answer is None


def test_refusal_is_case_insensitive() -> None:
    raw = "I CANNOT answer this question."
    result = parse_response(raw)
    assert result.parse_status == ParseStatus.REFUSED


def test_well_formed_refusal_still_parses_as_parsed_not_refused() -> None:
    """A refusal expressed *inside* the required format is a content judgement for a human
    evaluator (Correctness.REFUSED) to make, not a parsing failure -- parse_status only tracks
    whether the format itself was followed.
    """
    raw = "ANSWER: I cannot determine this from available evidence.\nCITED_DOCUMENT_IDS: NONE\nCONFIDENCE: low"
    result = parse_response(raw)
    assert result.parse_status == ParseStatus.PARSED
    assert result.answer == "I cannot determine this from available evidence."


def test_empty_string_is_malformed() -> None:
    result = parse_response("")
    assert result.parse_status == ParseStatus.MALFORMED
