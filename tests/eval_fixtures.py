"""Shared minimal-valid-record builders for eval/stats tests. Not a test file itself (no
test_ prefix) -- imported by test_eval_stratify.py, test_eval_m1.py, test_eval_m3.py so each
doesn't reconstruct the same boilerplate BenchmarkItem/ModelResponse slightly differently.
"""

from datetime import date, datetime

from retraction_bench.schemas import (
    BenchmarkItem,
    Claim,
    ClaimPolarity,
    ClaimType,
    Condition,
    EvaluationResult,
    EvidenceDirection,
    EvidenceTierMatch,
    ItemType,
    ModelResponse,
    NoAnswerReason,
    Provenance,
)


def make_item(
    item_id: str,
    domain: str = "(HSC) Medicine - Pharmacology",
    item_type: ItemType = ItemType.SUPERSEDED_WITH_CURRENT_ANSWER,
    claim_polarity: ClaimPolarity = ClaimPolarity.POSITIVE,
) -> BenchmarkItem:
    if item_type == ItemType.SUPERSEDED_WITHOUT_CURRENT_ANSWER:
        return BenchmarkItem(
            item_id=item_id,
            question=f"Question for {item_id}?",
            domain=domain,
            claim_type=ClaimType.CLINICAL_INTERVENTION,
            item_type=item_type,
            no_answer_reason=NoAnswerReason.ADJACENT_EVIDENCE_EXISTS,
            claim_polarity=claim_polarity,
            replacement_exists=False,
            trap_claim=Claim(text="Trap claim text."),
            gold_claim=Claim(text="Gold claim text."),
            supporting_sources=["rw-1"],
            provenance=Provenance.VERIFIED,
            evidence_direction=EvidenceDirection.ABSENT,
        )
    return BenchmarkItem(
        item_id=item_id,
        question=f"Question for {item_id}?",
        domain=domain,
        claim_type=ClaimType.CLINICAL_INTERVENTION,
        item_type=item_type,
        claim_polarity=claim_polarity,
        replacement_exists=False,
        trap_claim=Claim(text="Trap claim text."),
        gold_claim=Claim(text="Gold claim text."),
        supporting_sources=["rw-1"],
        provenance=Provenance.VERIFIED,
        evidence_direction=EvidenceDirection.CONTRADICTORY,
        evidence_tier_match=EvidenceTierMatch.SAME_TIER,
    )


def make_response(
    response_id: str,
    item_id: str,
    model_identifier: str = "test-model",
    seed: int = 1,
    condition: Condition = Condition.NO_RETRIEVAL,
) -> ModelResponse:
    return ModelResponse(
        response_id=response_id,
        item_id=item_id,
        model_identifier=model_identifier,
        seed=seed,
        condition=condition,
        raw_answer_text="A model answer.",
        prompt_template_id="v1",
        temperature=0.0,
        max_tokens=512,
        call_timestamp=datetime(2026, 8, 20, 12, 0, 0),
    )


def make_result(
    result_id: str,
    response_id: str,
    item_id: str,
    condition: Condition = Condition.NO_RETRIEVAL,
    cited_superseded_ids: list[str] | None = None,
    m3_label: str | None = None,
    notice_retrieved: bool | None = None,
) -> EvaluationResult:
    from retraction_bench.schemas import Correctness, ParseStatus

    return EvaluationResult(
        result_id=result_id,
        response_id=response_id,
        item_id=item_id,
        condition=condition,
        parse_status=ParseStatus.PARSED,
        cited_superseded_ids=cited_superseded_ids or [],
        correctness=Correctness.CORRECT,
        m3_label=m3_label,
        notice_retrieved=notice_retrieved,
        evaluator="test-evaluator",
        evaluation_date=date(2026, 8, 20),
    )
