"""Strict parsing of raw model output against the required ANSWER/CITED_DOCUMENT_IDS/CONFIDENCE
format (ADR-131). No lenient repair, no fuzzy field extraction, no guessing at a missing
field's likely value -- a model that cannot produce the requested format is a real result
(ParseStatus.MALFORMED), reported per model alongside M1/M3, not quietly fixed up so every
response looks equally usable.
"""

import re
from dataclasses import dataclass

from retraction_bench.schemas import ParseStatus

_FIELD_PATTERN = re.compile(r"^(ANSWER|CITED_DOCUMENT_IDS|CONFIDENCE):\s*(.*)$", re.MULTILINE)

# Fixed, short list -- checked as a case-insensitive substring, not inferred loosely. Extend only
# when a real response is found that should have matched and didn't; do not broaden speculatively.
_REFUSAL_MARKERS = (
    "i cannot",
    "i can't",
    "i'm unable to",
    "i am unable to",
    "i won't",
    "i will not",
    "cannot provide",
    "unable to provide",
)


@dataclass
class ParsedResponse:
    parse_status: ParseStatus
    answer: str | None
    cited_document_ids: list[str] | None
    confidence: str | None


def _is_refusal(raw_text: str) -> bool:
    lowered = raw_text.lower()
    return any(marker in lowered for marker in _REFUSAL_MARKERS)


def parse_response(raw_text: str) -> ParsedResponse:
    fields: dict[str, str] = {}
    for match in _FIELD_PATTERN.finditer(raw_text):
        field_name, value = match.group(1), match.group(2).strip()
        fields[field_name] = value

    required = {"ANSWER", "CITED_DOCUMENT_IDS", "CONFIDENCE"}
    if required.issubset(fields.keys()):
        cited_raw = fields["CITED_DOCUMENT_IDS"]
        if cited_raw.strip().upper() == "NONE":
            cited_ids = []
        else:
            cited_ids = [s.strip() for s in cited_raw.split(",") if s.strip()]
        return ParsedResponse(
            parse_status=ParseStatus.PARSED,
            answer=fields["ANSWER"],
            cited_document_ids=cited_ids,
            confidence=fields["CONFIDENCE"].strip().lower(),
        )

    if _is_refusal(raw_text):
        return ParsedResponse(parse_status=ParseStatus.REFUSED, answer=None, cited_document_ids=None, confidence=None)

    return ParsedResponse(parse_status=ParseStatus.MALFORMED, answer=None, cited_document_ids=None, confidence=None)
