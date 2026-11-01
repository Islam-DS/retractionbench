"""Proves the Pydantic contracts in schemas.py enforce what they claim.

Not a full test suite -- src/retraction_bench has no research logic yet.
This exists to prove correct data validates and malformed data is rejected.
"""

from datetime import date

import pytest
from pydantic import ValidationError

from retraction_bench.schemas import (
    BenchmarkItem,
    Calibration,
    Claim,
    ClaimPolarity,
    ClaimType,
    Condition,
    Correctness,
    DeferredCandidate,
    EvaluationResult,
    Evidence,
    EvidenceDirection,
    EvidenceTierMatch,
    EvidenceType,
    ItemType,
    NoAnswerReason,
    NoticeSpecificity,
    ParseStatus,
    PostRetractionCitations,
    Provenance,
    RejectedCandidate,
    RejectionReason,
    SourceAuthority,
    SourceEvidenceLevel,
    SupersededSource,
    SupersessionType,
)


def _valid_source() -> SupersededSource:
    return SupersededSource(
        doi=None,
        source_registry_id="rw-12345",
        external_ids={"pmid": "98765"},
        title="A trial that was later retracted",
        venue="Journal of Example Medicine",
        original_date=date(2010, 1, 1),
        evidence_level=SourceEvidenceLevel.PRIMARY_STUDY,
        notice_specificity=NoticeSpecificity.SPECIFIC,
        notice_text_verified=True,
        supersession_type=SupersessionType.RETRACTION,
        supersession_date=date(2015, 6, 1),
        supersession_reasons=["Data Fabrication"],
        verification_method="pubmed_retraction_tag",
        verification_confirmed=True,
        summary="Example abstract.",
        citations_before_supersession=42,
    )


def test_superseded_source_accepts_null_doi() -> None:
    # Not every superseded source has a DOI (e.g. guideline revisions);
    # external_ids is the general identifier mechanism instead.
    assert _valid_source().doi is None


def test_superseded_source_requires_evidence_level() -> None:
    with pytest.raises(ValidationError):
        SupersededSource(**{**_valid_source().model_dump(), "evidence_level": None})


def test_superseded_source_post_retraction_citations_defaults_to_none() -> None:
    assert _valid_source().post_retraction_citations is None


def test_superseded_source_accepts_post_retraction_citations() -> None:
    source = SupersededSource(
        **{
            **_valid_source().model_dump(),
            "post_retraction_citations": PostRetractionCitations(
                source="openalex",
                as_of_date=date(2026, 8, 6),
                before_count=3,
                after_count=19,
                excluded_self_citation=True,
            ),
        }
    )
    assert source.post_retraction_citations.after_count == 19


def test_superseded_source_rejects_unknown_field() -> None:
    with pytest.raises(ValidationError):
        SupersededSource(**{**_valid_source().model_dump(), "extra_field": "not allowed"})


def test_superseded_source_notice_text_defaults_to_none() -> None:
    assert _valid_source().notice_text is None


def test_superseded_source_accepts_notice_text() -> None:
    source = SupersededSource(**{**_valid_source().model_dump(), "notice_text": "The article is retracted."})
    assert source.notice_text == "The article is retracted."


def test_superseded_source_rejects_unverified_notice_with_a_specificity_value() -> None:
    # An unconfirmed quote cannot support a specificity judgment (ADR-042) -- if the text
    # wasn't verified, specificity must say so via UNVERIFIABLE, not silently claim a level.
    with pytest.raises(ValidationError):
        SupersededSource(**{**_valid_source().model_dump(), "notice_text_verified": False})


def test_superseded_source_rejects_verified_notice_marked_unverifiable() -> None:
    with pytest.raises(ValidationError):
        SupersededSource(
            **{
                **_valid_source().model_dump(),
                "notice_text_verified": True,
                "notice_specificity": NoticeSpecificity.UNVERIFIABLE,
            }
        )


def test_superseded_source_accepts_unverified_notice_marked_unverifiable() -> None:
    source = SupersededSource(
        **{
            **_valid_source().model_dump(),
            "notice_text_verified": False,
            "notice_specificity": NoticeSpecificity.UNVERIFIABLE,
        }
    )
    assert source.notice_specificity is NoticeSpecificity.UNVERIFIABLE


def test_benchmark_item_valid_round_trip() -> None:
    item = BenchmarkItem(
        item_id="RB-0001",
        question="Does drug X reduce mortality in condition Y?",
        domain="cardiology",
        claim_type=ClaimType.CLINICAL_INTERVENTION,
        item_type=ItemType.SUPERSEDED_WITH_CURRENT_ANSWER,
        claim_polarity=ClaimPolarity.POSITIVE,
        replacement_exists=False,
        evidence_direction=EvidenceDirection.CONTRADICTORY,
        evidence_tier_match=EvidenceTierMatch.SAME_TIER,
        trap_claim=Claim(text="Drug X reduces mortality.", valid_from=date(2010, 1, 1), valid_until=date(2015, 6, 1)),
        gold_claim=Claim(text="Drug X does not reduce mortality.", valid_from=date(2015, 6, 1), valid_until=None),
        supporting_sources=["rw-12345"],
        provenance=Provenance.DRAFT,
    )
    assert item.provenance is Provenance.DRAFT
    assert item.annotations == []
    assert item.claim_type is ClaimType.CLINICAL_INTERVENTION


def test_benchmark_item_requires_claim_polarity() -> None:
    with pytest.raises(ValidationError):
        BenchmarkItem(
            item_id="RB-0001",
            question="Does drug X reduce mortality in condition Y?",
            domain="cardiology",
            claim_type=ClaimType.CLINICAL_INTERVENTION,
            item_type=ItemType.SUPERSEDED_WITH_CURRENT_ANSWER,
            evidence_direction=EvidenceDirection.CONTRADICTORY,
            evidence_tier_match=EvidenceTierMatch.SAME_TIER,
            trap_claim=Claim(text="Drug X reduces mortality."),
            gold_claim=Claim(text="Drug X does not reduce mortality."),
            supporting_sources=["rw-12345"],
            provenance=Provenance.DRAFT,
            # claim_polarity omitted -- required.
        )


def test_benchmark_item_accepts_negative_claim_polarity() -> None:
    item = BenchmarkItem(
        item_id="RB-0002",
        question="Does treatment X relieve pain beyond placebo?",
        domain="rehabilitation",
        claim_type=ClaimType.CLINICAL_INTERVENTION,
        item_type=ItemType.SUPERSEDED_WITH_CURRENT_ANSWER,
        claim_polarity=ClaimPolarity.NEGATIVE,
        replacement_exists=False,
        evidence_direction=EvidenceDirection.CONTRADICTORY,
        evidence_tier_match=EvidenceTierMatch.SAME_TIER,
        trap_claim=Claim(text="Treatment X does not relieve pain beyond placebo."),
        gold_claim=Claim(text="Treatment X does relieve pain beyond placebo."),
        supporting_sources=["rw-1"],
        provenance=Provenance.DRAFT,
    )
    assert item.claim_polarity is ClaimPolarity.NEGATIVE


def test_benchmark_item_requires_no_answer_reason_under_without_current_answer() -> None:
    with pytest.raises(ValidationError):
        BenchmarkItem(
            item_id="RB-0005",
            question="Does treatment X relieve pain beyond placebo?",
            domain="rehabilitation",
            claim_type=ClaimType.CLINICAL_INTERVENTION,
            item_type=ItemType.SUPERSEDED_WITHOUT_CURRENT_ANSWER,
            claim_polarity=ClaimPolarity.POSITIVE,
            replacement_exists=False,
            evidence_direction=EvidenceDirection.ABSENT,
            trap_claim=Claim(text="Treatment X relieves pain."),
            gold_claim=Claim(text="No current authoritative source addresses this."),
            supporting_sources=["rw-1"],
            provenance=Provenance.DRAFT,
            # no_answer_reason omitted -- required.
        )


def test_benchmark_item_rejects_no_answer_reason_outside_without_current_answer() -> None:
    with pytest.raises(ValidationError):
        BenchmarkItem(
            item_id="RB-0006",
            question="Does treatment X relieve pain beyond placebo?",
            domain="rehabilitation",
            claim_type=ClaimType.CLINICAL_INTERVENTION,
            item_type=ItemType.SUPERSEDED_WITH_CURRENT_ANSWER,
            no_answer_reason=NoAnswerReason.NO_ADJACENT_EVIDENCE,
            claim_polarity=ClaimPolarity.POSITIVE,
            replacement_exists=False,
            evidence_direction=EvidenceDirection.CONCORDANT,
            evidence_tier_match=EvidenceTierMatch.SAME_TIER,
            trap_claim=Claim(text="Treatment X relieves pain."),
            gold_claim=Claim(text="Treatment X relieves pain, per current guidance."),
            supporting_sources=["rw-1"],
            provenance=Provenance.DRAFT,
        )


def test_benchmark_item_accepts_no_answer_reason_under_without_current_answer() -> None:
    item = BenchmarkItem(
        item_id="RB-0007",
        question="Does treatment X relieve pain beyond placebo?",
        domain="rehabilitation",
        claim_type=ClaimType.CLINICAL_INTERVENTION,
        item_type=ItemType.SUPERSEDED_WITHOUT_CURRENT_ANSWER,
        no_answer_reason=NoAnswerReason.ADJACENT_EVIDENCE_EXISTS,
        claim_polarity=ClaimPolarity.POSITIVE,
        replacement_exists=True,
        evidence_direction=EvidenceDirection.ABSENT,
        trap_claim=Claim(text="Treatment X relieves pain."),
        gold_claim=Claim(text="No current authoritative source addresses this specific question."),
        supporting_sources=["rw-1"],
        provenance=Provenance.DRAFT,
    )
    assert item.no_answer_reason is NoAnswerReason.ADJACENT_EVIDENCE_EXISTS


def test_benchmark_item_requires_evidence_direction() -> None:
    with pytest.raises(ValidationError):
        BenchmarkItem(
            item_id="RB-0007b",
            question="Does treatment X relieve pain beyond placebo?",
            domain="rehabilitation",
            claim_type=ClaimType.CLINICAL_INTERVENTION,
            item_type=ItemType.SUPERSEDED_WITH_CURRENT_ANSWER,
            claim_polarity=ClaimPolarity.POSITIVE,
            replacement_exists=False,
            evidence_tier_match=EvidenceTierMatch.SAME_TIER,
            trap_claim=Claim(text="Treatment X relieves pain."),
            gold_claim=Claim(text="Treatment X relieves pain, per current guidance."),
            supporting_sources=["rw-1"],
            provenance=Provenance.DRAFT,
            # evidence_direction omitted -- required.
        )


def test_benchmark_item_rejects_absent_evidence_direction_under_with_current_answer() -> None:
    with pytest.raises(ValidationError):
        BenchmarkItem(
            item_id="RB-0007c",
            question="Does treatment X relieve pain beyond placebo?",
            domain="rehabilitation",
            claim_type=ClaimType.CLINICAL_INTERVENTION,
            item_type=ItemType.SUPERSEDED_WITH_CURRENT_ANSWER,
            claim_polarity=ClaimPolarity.POSITIVE,
            replacement_exists=False,
            evidence_direction=EvidenceDirection.ABSENT,
            evidence_tier_match=EvidenceTierMatch.SAME_TIER,
            trap_claim=Claim(text="Treatment X relieves pain."),
            gold_claim=Claim(text="Treatment X relieves pain, per current guidance."),
            supporting_sources=["rw-1"],
            provenance=Provenance.DRAFT,
        )


def test_benchmark_item_rejects_non_absent_evidence_direction_under_without_current_answer() -> None:
    with pytest.raises(ValidationError):
        BenchmarkItem(
            item_id="RB-0007d",
            question="Does treatment X relieve pain beyond placebo?",
            domain="rehabilitation",
            claim_type=ClaimType.CLINICAL_INTERVENTION,
            item_type=ItemType.SUPERSEDED_WITHOUT_CURRENT_ANSWER,
            no_answer_reason=NoAnswerReason.NO_ADJACENT_EVIDENCE,
            claim_polarity=ClaimPolarity.POSITIVE,
            replacement_exists=False,
            evidence_direction=EvidenceDirection.CONCORDANT,
            trap_claim=Claim(text="Treatment X relieves pain."),
            gold_claim=Claim(text="No current authoritative source addresses this."),
            supporting_sources=["rw-1"],
            provenance=Provenance.DRAFT,
        )


def test_benchmark_item_requires_replacement_exists() -> None:
    with pytest.raises(ValidationError):
        BenchmarkItem(
            item_id="RB-0008",
            question="Does treatment X relieve pain beyond placebo?",
            domain="rehabilitation",
            claim_type=ClaimType.CLINICAL_INTERVENTION,
            item_type=ItemType.SUPERSEDED_WITH_CURRENT_ANSWER,
            claim_polarity=ClaimPolarity.POSITIVE,
            evidence_direction=EvidenceDirection.CONCORDANT,
            evidence_tier_match=EvidenceTierMatch.SAME_TIER,
            trap_claim=Claim(text="Treatment X relieves pain."),
            gold_claim=Claim(text="Treatment X relieves pain, per current guidance."),
            supporting_sources=["rw-1"],
            provenance=Provenance.DRAFT,
            # replacement_exists omitted -- required.
        )


def test_benchmark_item_requires_evidence_tier_match_under_with_current_answer() -> None:
    with pytest.raises(ValidationError):
        BenchmarkItem(
            item_id="RB-0008b",
            question="Does treatment X relieve pain beyond placebo?",
            domain="rehabilitation",
            claim_type=ClaimType.CLINICAL_INTERVENTION,
            item_type=ItemType.SUPERSEDED_WITH_CURRENT_ANSWER,
            claim_polarity=ClaimPolarity.POSITIVE,
            replacement_exists=False,
            evidence_direction=EvidenceDirection.CONCORDANT,
            trap_claim=Claim(text="Treatment X relieves pain."),
            gold_claim=Claim(text="Treatment X relieves pain, per current guidance."),
            supporting_sources=["rw-1"],
            provenance=Provenance.DRAFT,
            # evidence_tier_match omitted -- required.
        )


def test_benchmark_item_rejects_evidence_tier_match_under_without_current_answer() -> None:
    with pytest.raises(ValidationError):
        BenchmarkItem(
            item_id="RB-0008c",
            question="Does treatment X relieve pain beyond placebo?",
            domain="rehabilitation",
            claim_type=ClaimType.CLINICAL_INTERVENTION,
            item_type=ItemType.SUPERSEDED_WITHOUT_CURRENT_ANSWER,
            no_answer_reason=NoAnswerReason.NO_ADJACENT_EVIDENCE,
            claim_polarity=ClaimPolarity.POSITIVE,
            replacement_exists=False,
            evidence_direction=EvidenceDirection.ABSENT,
            evidence_tier_match=EvidenceTierMatch.SAME_TIER,
            trap_claim=Claim(text="Treatment X relieves pain."),
            gold_claim=Claim(text="No current authoritative source addresses this."),
            supporting_sources=["rw-1"],
            provenance=Provenance.DRAFT,
        )


def test_benchmark_item_accepts_lower_tier_evidence() -> None:
    item = BenchmarkItem(
        item_id="RB-0008d",
        question="Does treatment X relieve pain beyond placebo?",
        domain="rehabilitation",
        claim_type=ClaimType.CLINICAL_INTERVENTION,
        item_type=ItemType.SUPERSEDED_WITH_CURRENT_ANSWER,
        claim_polarity=ClaimPolarity.POSITIVE,
        replacement_exists=False,
        evidence_direction=EvidenceDirection.CONCORDANT,
        evidence_tier_match=EvidenceTierMatch.LOWER_TIER,
        trap_claim=Claim(text="Treatment X relieves pain, per a randomized controlled trial."),
        gold_claim=Claim(text="Treatment X relieves pain, per real-world observational data."),
        supporting_sources=["rw-1"],
        provenance=Provenance.DRAFT,
    )
    assert item.evidence_tier_match is EvidenceTierMatch.LOWER_TIER


def test_evidence_requires_independence_verified() -> None:
    with pytest.raises(ValidationError):
        Evidence(
            identifier="10.1234/example",
            evidence_type=EvidenceType.GUIDELINE,
            publication_date=date(2020, 1, 1),
            source_authority=SourceAuthority.GUIDELINE_BODY,
            # independence_verified omitted -- required.
        )


def test_benchmark_item_rejects_missing_required_fields() -> None:
    with pytest.raises(ValidationError):
        BenchmarkItem(item_id="RB-0002", question="Missing domain and claims.")


def test_evaluation_result_requires_m3_label_under_post_notice() -> None:
    with pytest.raises(ValidationError):
        EvaluationResult(
            result_id="er-1",
            response_id="resp-1",
            item_id="RB-0001",
            condition=Condition.POST_NOTICE,
            parse_status=ParseStatus.PARSED,
            correctness=Correctness.CORRECT,
            evaluator="human-1",
            evaluation_date=date(2026, 8, 4),
            # m3_label omitted -- required under post_notice.
        )


def test_evaluation_result_rejects_m3_label_outside_post_notice() -> None:
    with pytest.raises(ValidationError):
        EvaluationResult(
            result_id="er-2",
            response_id="resp-2",
            item_id="RB-0001",
            condition=Condition.NO_RETRIEVAL,
            parse_status=ParseStatus.PARSED,
            correctness=Correctness.REFUSED,
            m3_label="acknowledges",
            evaluator="human-1",
            evaluation_date=date(2026, 8, 4),
        )


def test_evaluation_result_valid_under_post_notice() -> None:
    result = EvaluationResult(
        result_id="er-3",
        response_id="resp-3",
        item_id="RB-0001",
        condition=Condition.POST_NOTICE,
        parse_status=ParseStatus.PARSED,
        correctness=Correctness.INCORRECT,
        m3_label="defends",
        evaluator="human-1",
        evaluation_date=date(2026, 8, 4),
    )
    assert result.m3_label.value == "defends"


def test_evaluation_result_rejects_notice_retrieved_outside_its_condition() -> None:
    with pytest.raises(ValidationError):
        EvaluationResult(
            result_id="er-4",
            response_id="resp-4",
            item_id="RB-0001",
            condition=Condition.NO_RETRIEVAL,
            parse_status=ParseStatus.PARSED,
            correctness=Correctness.CORRECT,
            notice_retrieved=True,
            evaluator="human-1",
            evaluation_date=date(2026, 8, 4),
        )


def test_evaluation_result_calibration_defaults_to_none() -> None:
    result = EvaluationResult(
        result_id="er-5",
        response_id="resp-5",
        item_id="RB-0001",
        condition=Condition.NO_RETRIEVAL,
        parse_status=ParseStatus.PARSED,
        correctness=Correctness.CORRECT,
        evaluator="human-1",
        evaluation_date=date(2026, 8, 9),
    )
    assert result.calibration is None


def test_evaluation_result_accepts_calibration() -> None:
    result = EvaluationResult(
        result_id="er-6",
        response_id="resp-6",
        item_id="RB-0002",
        condition=Condition.NO_RETRIEVAL,
        parse_status=ParseStatus.PARSED,
        correctness=Correctness.CORRECT,
        calibration=Calibration.OVERCONFIDENT,
        evaluator="human-1",
        evaluation_date=date(2026, 8, 9),
    )
    assert result.calibration == Calibration.OVERCONFIDENT


def test_evidence_requires_source_authority() -> None:
    # The gold claim must be traceable to an institutional source, never the
    # annotator's own judgment -- source_authority has no default for that reason.
    with pytest.raises(ValidationError):
        Evidence(
            identifier="10.1234/example",
            evidence_type=EvidenceType.GUIDELINE,
            publication_date=date(2020, 1, 1),
        )


def test_evidence_valid_with_source_authority() -> None:
    evidence = Evidence(
        identifier="10.1234/example",
        evidence_type=EvidenceType.GUIDELINE,
        publication_date=date(2020, 1, 1),
        source_authority=SourceAuthority.GUIDELINE_BODY,
        independence_verified=True,
    )
    assert evidence.source_authority is SourceAuthority.GUIDELINE_BODY


def test_rejected_candidate_valid_round_trip() -> None:
    rejected = RejectedCandidate(
        doi="10.1234/example",
        source_registry_id="rw-99999",
        reason=RejectionReason.NO_INSTITUTIONAL_SOURCE,
        notes="No guideline, Cochrane review, or meta-analysis found addressing this claim.",
        rejection_date=date(2026, 8, 5),
    )
    assert rejected.reason is RejectionReason.NO_INSTITUTIONAL_SOURCE


def test_rejected_candidate_rejects_missing_required_fields() -> None:
    with pytest.raises(ValidationError):
        RejectedCandidate(doi="10.1234/example")


def test_deferred_candidate_valid_round_trip() -> None:
    deferred = DeferredCandidate(
        doi="10.1234/example",
        source_registry_id="rw-5684",
        notes="Blocked on paywalled guideline text; not worth a third pass with seven weeks left.",
        deferred_date=date(2026, 8, 10),
    )
    assert deferred.source_registry_id == "rw-5684"


def test_deferred_candidate_rejects_missing_required_fields() -> None:
    with pytest.raises(ValidationError):
        DeferredCandidate(doi="10.1234/example")
