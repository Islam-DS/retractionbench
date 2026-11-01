"""Pydantic v2 data contracts for RetractionBench.

These are the single source of truth for every record the pipeline reads or
writes. Field lists and the design decisions behind them (in particular the
supersession/Claim/temporal-validity design) are recorded in
docs/DECISIONS.md -- read that before changing anything here.
"""

from datetime import date, datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, model_validator

CURRENT_SCHEMA_VERSION = "0.1.0"


class StrictBaseModel(BaseModel):
    """Base for all schemas: rejects unknown fields so typos fail loudly at write time."""

    model_config = ConfigDict(extra="forbid")


# --------------------------------------------------------------------------
# Enums -- closed value spaces only. Open-ended vocabularies (e.g. supersession
# reasons, clinical domains) are validated against config/ at runtime instead,
# per the project protocol (no domain vocabulary hard-coded into src/).
# --------------------------------------------------------------------------


class SupersessionType(StrEnum):
    """Why a source is no longer the current record. Paper 1 only ever writes RETRACTION."""

    RETRACTION = "retraction"
    EXPRESSION_OF_CONCERN = "expression_of_concern"
    MAJOR_CORRECTION = "major_correction"
    GUIDELINE_REVISION = "guideline_revision"
    SUPERSEDED_BY_EVIDENCE = "superseded_by_evidence"


class Provenance(StrEnum):
    """Draft = machine-assisted, not yet human-checked. Excluded from headline results until VERIFIED."""

    DRAFT = "draft"
    VERIFIED = "verified"


class EvidenceType(StrEnum):
    RCT = "rct"
    META_ANALYSIS = "meta_analysis"
    SYSTEMATIC_REVIEW = "systematic_review"
    GUIDELINE = "guideline"
    SUPERSESSION_NOTICE = "supersession_notice"
    OTHER = "other"


class SourceAuthority(StrEnum):
    """Who is making this evidentiary claim. The gold claim is never the annotator's own judgment --
    it must be traceable to one of these, per the project protocol's standard-of-evidence rule. Items resting only
    on PRIMARY_STUDY or OTHER are a weaker evidence tier, reported separately in the paper."""

    GUIDELINE_BODY = "guideline_body"
    COCHRANE_REVIEW = "cochrane_review"
    SYSTEMATIC_REVIEW = "systematic_review"
    META_ANALYSIS = "meta_analysis"
    REGULATORY_AGENCY = "regulatory_agency"
    NATIONAL_STATISTICS_BODY = "national_statistics_body"  # e.g. a survey programme like DHS, ADR-073
    PRIMARY_STUDY = "primary_study"
    OTHER = "other"


class RejectionReason(StrEnum):
    """Why a candidate was rejected during curation. Rejected candidates are logged, never discarded --
    the rejection rate is itself a finding (see docs/DECISIONS.md)."""

    NO_INSTITUTIONAL_SOURCE = "no_institutional_source"
    OTHER = "other"


class Condition(StrEnum):
    """The four experimental conditions a ModelResponse was generated under."""

    NO_RETRIEVAL = "no_retrieval"
    RETRIEVAL_NAIVE = "retrieval_naive"
    RETRIEVAL_WITH_NOTICE = "retrieval_with_notice"
    POST_NOTICE = "post_notice"


class M3Label(StrEnum):
    """Correction Following classification, scored only under Condition.POST_NOTICE."""

    ACKNOWLEDGES = "acknowledges"
    SILENTLY_REVISES = "silently_revises"
    DEFENDS = "defends"


class Correctness(StrEnum):
    """Three-way, not boolean: a refusal is a distinct outcome from a wrong answer."""

    CORRECT = "correct"
    INCORRECT = "incorrect"
    REFUSED = "refused"


class ParseStatus(StrEnum):
    """Whether raw_answer_text matched the required ANSWER/CITED_DOCUMENT_IDS/CONFIDENCE format
    (ADR-131) -- set mechanically by rag/parse.py, never repaired or guessed at. A model that
    cannot produce usable output is a real, reportable result, not an error to paper over: this
    rate is reported per model alongside M1/M3, not folded silently into Correctness.REFUSED.
    """

    PARSED = "parsed"  # all three required fields present in the exact specified format
    MALFORMED = "malformed"  # response text doesn't match the required format at all
    REFUSED = "refused"  # the model's own text signals a refusal, via a fixed marker list, not inferred


class Calibration(StrEnum):
    """Whether the answer's stated confidence matches the strength of the gold claim's own
    evidence -- a distinct axis from Correctness (ADR-052/056). A model can be current and
    overconfident, or outdated and appropriately hedged; collapsing the two loses that.
    """

    APPROPRIATE = "appropriate"
    OVERCONFIDENT = "overconfident"  # states a finding more firmly than the evidence supports
    UNDERCONFIDENT = "underconfident"  # hedges where the evidence is actually solid


class NoticeSpecificity(StrEnum):
    """How informative the supersession notice itself is about WHY the source was
    superseded -- annotated per item from the notice text (ADR-033). Distinct from
    supersession_reasons below: Retraction Watch's own tags are sometimes more specific
    than the notice they were derived from, and that gap is itself tracked, not silently
    inherited by treating RW's tags as if they were the notice's content."""

    SPECIFIC = "specific"  # names the mechanism: which data, which analysis, which study
    CATEGORICAL = "categorical"  # names a category (e.g. "data collection errors"), no mechanism
    BARE = "bare"  # states supersession with no reason at all
    UNVERIFIABLE = "unverifiable"  # the notice text itself could not be independently confirmed (ADR-042)


class SourceEvidenceLevel(StrEnum):
    """Was the superseded source itself a primary study or a synthesis (meta-analysis /
    systematic review) of other studies. Stratification variable for the pre-registered
    synthesis-vs-primary prediction (ADR-032): a retracted synthesis does not retract the
    primary literature it pooled, so the correct response is more nuanced than for a
    retracted primary study, where the trap claim really is void."""

    PRIMARY_STUDY = "primary_study"
    SYNTHESIS = "synthesis"


class ClaimType(StrEnum):
    """Human-annotated at annotation time, on the actual paper and claim -- independent of
    curate/claim_type_screen.py's heuristic pre-filter, which shares these value names but is
    a recall-oriented candidate-pool filter, not a judgment about any specific item. The screen's
    output is never copied into this field; see docs/DECISIONS.md ADR-030."""

    CLINICAL_INTERVENTION = "clinical_intervention"
    CLINICAL_OBSERVATIONAL = "clinical_observational"


class ItemType(StrEnum):
    """Whether current authoritative evidence exists at all for this item's question
    (ADR-043). The second case is not a rejection -- it is a harder, more revealing test:
    a model that answers confidently when no correct confident answer exists is failing at
    epistemic honesty, not just currency. Not sought out deliberately; flagged when
    eligibility search (ANNOTATION.md section 3.2) turns one up, so the rate stays a
    measured quantity rather than a constructed one. Target ~10-15% of the benchmark."""

    SUPERSEDED_WITH_CURRENT_ANSWER = "superseded_with_current_answer"
    SUPERSEDED_WITHOUT_CURRENT_ANSWER = "superseded_without_current_answer"


class NoAnswerReason(StrEnum):
    """Why a superseded_without_current_answer item has no current answer -- two different
    capabilities a model can fail at, invisible if collapsed into one item_type value
    (ADR-060/063). Required iff item_type == SUPERSEDED_WITHOUT_CURRENT_ANSWER; must be None
    otherwise. Start with two values; add more only when an item genuinely needs one.
    """

    NO_ADJACENT_EVIDENCE = "no_adjacent_evidence"  # nothing authoritative on the topic at all (the Fujii-type case)
    ADJACENT_EVIDENCE_EXISTS = "adjacent_evidence_exists"  # authoritative evidence exists, doesn't answer this question


class EvidenceDirection(StrEnum):
    """How current evidence relates to the trap claim it supersedes (ADR-079). Formalizes a
    distinction annotators were already drawing in free-text notes across several items --
    naming the specific *effect that was found* is not the same as naming *whether the current*
    *answer differs from the retracted one at all*, and the second is invisible if only
    item_type is recorded. Required iff item_type == SUPERSEDED_WITH_CURRENT_ANSWER (there is
    nothing to compare a direction against when no current answer exists); must be ABSENT
    otherwise.
    """

    CONCORDANT = "concordant"  # current evidence points the same way as the trap claim (magnitude may differ)
    CONTRADICTORY = "contradictory"  # current evidence reverses the trap claim's direction, not merely narrows it
    ABSENT = "absent"  # no current answer exists to compare a direction against (superseded_without_current_answer)


class EvidenceTierMatch(StrEnum):
    """Whether current evidence's underlying study design is at least as rigorous as what
    supported the trap claim, or a step down the evidence hierarchy (ADR-089) -- e.g.
    observational/real-world data superseding a randomized controlled trial. Human-annotated
    judgment about study design, never inherited from `source_authority` alone: a systematic
    review is a synthesis by `source_authority` regardless of whether the studies it pools are
    RCTs or observational data, so `source_authority = systematic_review` alone cannot decide
    this field (item 19's real-world-data review and item 5's RCT-synthesizing review share
    that source_authority but sit on opposite sides of this distinction). Required iff
    item_type == SUPERSEDED_WITH_CURRENT_ANSWER (there is no current evidence to compare tier
    against otherwise); must be None otherwise. Start with two values; add more only when an
    item genuinely needs one.
    """

    SAME_TIER = "same_tier"  # current evidence's design is at least as rigorous as the trap claim's
    LOWER_TIER = "lower_tier"  # current evidence rests on a less rigorous design than the trap claim did


class OutcomeHierarchyMismatch(StrEnum):
    """Whether the trap claim or the current evidence rests on a secondary rather than the
    primary, pre-specified outcome of its own trial or study (ADR-113/114) -- a distinct
    failure axis from evidence_tier_match, which is about the rigor of the *study design*, not
    which endpoint within a study is being cited. A trial can be a well-designed RCT (same_tier)
    and still be misrepresented by quoting its secondary outcomes as though they were its
    designed-for finding -- the item this field was introduced for (a retraction candidate) had
    a null primary outcome and positive secondary outcomes; a model reporting the secondary
    result as *the* finding is committing this specific, nameable error, not merely citing
    weaker evidence. First case only so far -- more values may be needed once more items with
    this shape are annotated; do not generalize the boundary from one example.
    """

    NONE = "none"  # both trap claim and current evidence (where it exists) rest on their own primary outcome(s)
    TRAP_CLAIM_SECONDARY = "trap_claim_secondary"  # the trap claim's headline figure is a secondary outcome
    EVIDENCE_SECONDARY = "evidence_secondary"  # the current evidence's headline figure is a secondary outcome
    BOTH_SECONDARY = "both_secondary"


# --------------------------------------------------------------------------
# Nested models
# --------------------------------------------------------------------------


class ClaimPolarity(StrEnum):
    """Whether the trap claim asserts an effect (positive) or asserts no effect beyond
    placebo/no difference (negative) -- ADR-057. A retracted negative finding relied upon by
    a model wrongly discourages a treatment, a distinct clinical harm from a retracted
    positive finding wrongly recommending one; results are stratified by this, not pooled.
    """

    POSITIVE = "positive"
    NEGATIVE = "negative"


class Claim(StrictBaseModel):
    """A statement with a time window in which it was/is the current answer.

    Temporal validity lives here, not on SupersededSource: a source's
    temporal window is the window of the claim it made.
    """

    text: str = Field(description="The claim itself, in plain language.")
    valid_from: date | None = Field(
        default=None, description="When this claim became the current answer. None if unknown."
    )
    valid_until: date | None = Field(
        default=None,
        description="When this claim stopped being the current answer. None if still current.",
    )


class Evidence(StrictBaseModel):
    """A single piece of post-supersession evidence supporting a BenchmarkItem's gold_claim."""

    identifier: str = Field(description="DOI, URL, or other resolvable identifier.")
    evidence_type: EvidenceType
    publication_date: date = Field(description="Required: M2 (staleness-weighted accuracy) depends on it.")
    source_authority: SourceAuthority = Field(
        description="Who is asserting this, not just what kind of document it is. Required: the gold claim "
        "must be traceable to an institutional source, never the annotator's own clinical judgment."
    )
    note: str = Field(default="", description="Why this evidence supersedes the trap claim.")
    independence_verified: bool = Field(
        description="Whether this evidence's specific figure was confirmed NOT to trace back to the "
        "retracted source itself -- checked against this evidence's own reference list where accessible "
        "(ADR-058). False means either checked-and-failed or genuinely unchecked; see the item's "
        "annotations/notes for which. Required, no default: every entry must state this explicitly "
        "rather than silently assuming independence."
    )


class PostRetractionCitations(StrictBaseModel):
    """Citation counts for a SupersededSource, split at its supersession_date, from a citation
    graph API. Optional -- not every source is well-indexed everywhere, and this is a
    point-in-time snapshot (citation counts grow), not a fixed fact -- hence as_of_date.
    Measures how long superseded evidence stays in circulation, the phenomenon this whole
    research programme is about (docs/DECISIONS.md ADR-035)."""

    source: str = Field(description='Citation database queried, e.g. "openalex".')
    as_of_date: date
    before_count: int = Field(description="Citations dated before supersession_date.")
    after_count: int = Field(description="Citations dated on or after supersession_date.")
    excluded_self_citation: bool = Field(
        default=False,
        description="Whether the supersession notice's own back-reference to the source was "
        "excluded from these counts (it should be -- it is not an independent citation).",
    )


class Annotation(StrictBaseModel):
    """One annotation pass over a BenchmarkItem. Multiple annotations per item enable IAA statistics."""

    annotator_id: str
    date: date
    provenance: Provenance = Field(description="Whether this pass was a draft or a verifying pass.")
    note: str | None = None


# --------------------------------------------------------------------------
# Top-level records
# --------------------------------------------------------------------------


class SupersededSource(StrictBaseModel):
    """A source of record (paper, guideline, ...) that has been superseded.

    Paper 1 populates this exclusively via Retraction Watch + PubMed, with
    supersession_type=RETRACTION. The shape supports other supersession
    types for later research-programme instances (the project protocol).
    """

    schema_version: str = CURRENT_SCHEMA_VERSION

    doi: str | None = Field(
        default=None,
        description="Not every superseded source has one (e.g. guideline revisions). Use external_ids otherwise.",
    )
    source_registry_id: str = Field(description="ID in the originating registry, e.g. a Retraction Watch record ID.")
    external_ids: dict[str, str] = Field(
        default_factory=dict, description='General identifier bag, e.g. {"pmid": "..."}.'
    )
    title: str
    venue: str = Field(description="Journal, reporter, or publishing body -- not assumed to be a journal.")
    original_date: date
    evidence_level: SourceEvidenceLevel = Field(
        description="Primary study or synthesis of other studies -- stratification variable for "
        "the pre-registered synthesis-vs-primary prediction, ADR-032."
    )
    notice_specificity: NoticeSpecificity = Field(
        description="How informative the notice text itself is about the mechanism, annotated "
        "per item -- see ADR-033. Not derived from supersession_reasons below."
    )
    notice_text_verified: bool = Field(
        description="Whether the notice text behind notice_specificity was confirmed directly "
        "against a primary or authoritative source (the publisher, PubMed, or a full-text "
        "repository) -- not a secondhand quote (e.g. a third party reporting what the notice "
        "says). If False, notice_specificity must be UNVERIFIABLE: an unconfirmed quote cannot "
        "support a specificity judgment, per ADR-042."
    )
    notice_text: str | None = Field(
        default=None,
        description="The notice text itself (verbatim if notice_text_verified, otherwise the "
        "best available secondhand quote, still worth having as a corpus document even if "
        "its specificity can't be judged). None if no text could be found at all (a truly "
        "bare notice, or nothing located). Embedded as its own retrievable corpus document "
        "(docs/CORPUS_PLAN.md section 4) so retrieval of the notice is measurable separately "
        "from retrieval of the source itself.",
    )
    supersession_type: SupersessionType
    supersession_date: date
    supersession_reasons: list[str] = Field(
        default_factory=list,
        description="Validated against the Retraction Watch reason vocabulary at ingest time, not baked in here.",
    )
    verification_method: str = Field(
        description='How supersession was confirmed, e.g. "pubmed_retraction_tag". Domain-specific mechanism.'
    )
    verification_confirmed: bool
    summary: str = Field(description="Abstract or equivalent summary of the original source.")
    citations_before_supersession: int | None = Field(
        default=None, description="Used as an impact filter during candidate selection."
    )
    post_retraction_citations: PostRetractionCitations | None = Field(
        default=None,
        description="Optional citation-graph lookup (before/after supersession_date). Not "
        "every source is indexed by a citation database, hence optional. See ADR-035.",
    )

    @model_validator(mode="after")
    def _notice_verification_consistency(self) -> "SupersededSource":
        if not self.notice_text_verified and self.notice_specificity != NoticeSpecificity.UNVERIFIABLE:
            raise ValueError(
                "notice_specificity must be UNVERIFIABLE when notice_text_verified is False "
                "(ADR-042) -- an unconfirmed quote cannot support a specificity judgment."
            )
        if self.notice_text_verified and self.notice_specificity == NoticeSpecificity.UNVERIFIABLE:
            raise ValueError(
                "notice_specificity is UNVERIFIABLE but notice_text_verified is True -- "
                "if the text was verified, record its actual specificity (specific/categorical/bare)."
            )
        return self


class BenchmarkItem(StrictBaseModel):
    """One benchmark question: a trap claim from a superseded source vs. the current gold claim."""

    schema_version: str = CURRENT_SCHEMA_VERSION

    item_id: str = Field(description='Stable ID, e.g. "RB-0001".')
    question: str
    domain: str = Field(
        description="Plain string, validated at runtime against config/vocabularies/domains.yaml. "
        "Not an Enum: domain vocabularies are not hard-coded into src/."
    )
    claim_type: ClaimType = Field(
        description="Human-annotated intervention-vs-observational judgment on this specific item. "
        "Never auto-populated from the candidate-pool screen's output (ADR-030)."
    )
    item_type: ItemType = Field(
        description="Whether current authoritative evidence exists for this item's question "
        "at all -- see ADR-043. Not forced during selection; flagged when eligibility search "
        "turns one up."
    )
    no_answer_reason: NoAnswerReason | None = Field(
        default=None,
        description="Why there is no current answer -- see ADR-060/063. Required iff "
        "item_type == SUPERSEDED_WITHOUT_CURRENT_ANSWER; must be None otherwise.",
    )
    claim_polarity: ClaimPolarity = Field(
        description="Whether the trap claim asserts an effect (positive) or asserts no effect "
        "(negative) -- ADR-057. Human-annotated from the retracted source's own conclusion, "
        "not inferred from the notice or the gold claim."
    )
    replacement_exists: bool = Field(
        description="Whether a formal, citable corrected replacement of the superseded source "
        "exists (e.g. a publisher 'Retraction and Replacement', not just a plain retraction) -- "
        "ADR-069. Tests a distinct failure mode from an ordinary void retraction: the correct "
        "answer is not that the evidence is void, but that a specific superseded version must "
        "not be cited while its replacement should be. A model citing the original when a "
        "corrected version exists fails differently than one citing a retraction with no "
        "replacement at all."
    )
    trap_claim: Claim = Field(description="What the superseded source implies.")
    gold_claim: Claim = Field(description="What current evidence says.")
    supporting_sources: list[str] = Field(
        default_factory=list, description="Identifiers of the SupersededSource record(s) this item is built on."
    )
    post_supersession_evidence: list[Evidence] = Field(default_factory=list)
    provenance: Provenance = Field(
        description="Overall item status used to gate inclusion in headline results (the project protocol)."
    )
    annotations: list[Annotation] = Field(
        default_factory=list, description="One entry per annotation pass; supports inter-annotator agreement stats."
    )
    evidence_direction: EvidenceDirection = Field(
        description="Whether current evidence is concordant with, or contradicts, the trap claim's own "
        "direction -- ADR-079. ABSENT iff item_type == SUPERSEDED_WITHOUT_CURRENT_ANSWER; "
        "CONCORDANT or CONTRADICTORY otherwise."
    )
    evidence_tier_match: EvidenceTierMatch | None = Field(
        default=None,
        description="Whether current evidence's study design is at least as rigorous as the trap claim's, "
        "or a step down (ADR-089). Required iff item_type == SUPERSEDED_WITH_CURRENT_ANSWER; must be "
        "None otherwise.",
    )
    outcome_hierarchy_mismatch: OutcomeHierarchyMismatch | None = Field(
        default=None,
        description="Whether the trap claim or the current evidence rests on a secondary rather than "
        "primary outcome of its own trial (ADR-113/114) -- distinct from evidence_tier_match's study-design "
        "axis. Optional, not item_type-gated: relevant whenever it applies, not forced onto every item. "
        "None means either not applicable or not yet assessed -- the first case (item32/RB-0021) was found "
        "by close reading, not a mechanizable check, so absence of this field on earlier items reflects "
        "that they were not screened for it, not that the mismatch is confirmed absent.",
    )

    @model_validator(mode="after")
    def _no_answer_reason_gated_on_item_type(self) -> "BenchmarkItem":
        if self.item_type == ItemType.SUPERSEDED_WITHOUT_CURRENT_ANSWER:
            if self.no_answer_reason is None:
                raise ValueError("no_answer_reason is required when item_type is superseded_without_current_answer")
        elif self.no_answer_reason is not None:
            raise ValueError("no_answer_reason must be None unless item_type is superseded_without_current_answer")
        return self

    @model_validator(mode="after")
    def _evidence_direction_gated_on_item_type(self) -> "BenchmarkItem":
        if self.item_type == ItemType.SUPERSEDED_WITHOUT_CURRENT_ANSWER:
            if self.evidence_direction != EvidenceDirection.ABSENT:
                raise ValueError(
                    "evidence_direction must be ABSENT when item_type is superseded_without_current_answer"
                )
        elif self.evidence_direction == EvidenceDirection.ABSENT:
            raise ValueError("evidence_direction must not be ABSENT when item_type is superseded_with_current_answer")
        return self

    @model_validator(mode="after")
    def _evidence_tier_match_gated_on_item_type(self) -> "BenchmarkItem":
        if self.item_type == ItemType.SUPERSEDED_WITH_CURRENT_ANSWER:
            if self.evidence_tier_match is None:
                raise ValueError("evidence_tier_match is required when item_type is superseded_with_current_answer")
        elif self.evidence_tier_match is not None:
            raise ValueError("evidence_tier_match must be None unless item_type is superseded_with_current_answer")
        return self


class RejectedCandidate(StrictBaseModel):
    """A candidate that did not become a BenchmarkItem, kept rather than discarded.

    Primary rejection path (the project protocol standard-of-evidence rule): no institutional
    post-retraction source (guideline, Cochrane review, systematic review,
    meta-analysis, or regulatory statement) could be located for the claim.
    The rejection rate itself is a candidate finding -- see docs/DECISIONS.md.
    """

    schema_version: str = CURRENT_SCHEMA_VERSION

    doi: str | None = Field(default=None, description="Not every candidate has one; see SupersededSource.doi.")
    source_registry_id: str | None = Field(
        default=None, description="Link back to the SupersededSource record this candidate was drawn from."
    )
    reason: RejectionReason
    notes: str = Field(default="", description="Free-text elaboration, especially when reason is OTHER.")
    rejection_date: date


class DeferredCandidate(StrictBaseModel):
    """A candidate set aside for time budget, not rejected on eligibility or quality (ADR-078).

    Distinct from RejectedCandidate: a rejection is a judgment about the candidate itself (no
    institutional source, redundant, author-group concentration, ...) and belongs in the
    rejection-rate accounting, which is a finding about the pool. A deferral is a judgment
    about remaining project time under a fixed deadline and says nothing about the candidate --
    mixing the two into one count would misrepresent the rejection rate as measuring something
    it doesn't.
    """

    schema_version: str = CURRENT_SCHEMA_VERSION

    doi: str | None = Field(default=None)
    source_registry_id: str | None = Field(
        default=None, description="Link back to the SupersededSource record this candidate was drawn from."
    )
    notes: str = Field(default="", description="Free-text: what was already tried, and why it isn't worth a repeat.")
    deferred_date: date


class ModelResponse(StrictBaseModel):
    """One model's answer to one item, under one experimental condition."""

    schema_version: str = CURRENT_SCHEMA_VERSION

    response_id: str
    item_id: str
    model_identifier: str = Field(description="litellm-style model string.")
    seed: int
    condition: Condition
    retrieved_document_ids: list[str] = Field(default_factory=list)
    raw_answer_text: str
    prompt_template_id: str = Field(description="Which prompt version was used, for reproducibility.")
    temperature: float
    max_tokens: int
    call_timestamp: datetime
    raw_call_metadata: dict[str, object] = Field(
        default_factory=dict, description="Passthrough of whatever litellm returns (usage, finish_reason, etc.)."
    )
    logprobs: dict[str, object] | None = Field(
        default=None,
        description="Raw provider passthrough, unnormalized across providers; normalization deferred, see DECISIONS.md",
    )
    verbalised_confidence: str | None = Field(
        default=None, description="Free-text confidence expression extracted from the answer, if any."
    )


class EvaluationResult(StrictBaseModel):
    """The scored outcome for one ModelResponse."""

    schema_version: str = CURRENT_SCHEMA_VERSION

    result_id: str
    response_id: str
    item_id: str
    condition: Condition = Field(
        description="Denormalized from the linked ModelResponse so the validators below can see it."
    )

    parse_status: ParseStatus = Field(
        description="Whether raw_answer_text matched the required output format (ADR-131) -- set "
        "mechanically by rag/parse.py, required (no default) so every result states it explicitly, "
        "the same discipline as correctness/claim_polarity elsewhere in this schema."
    )
    cited_superseded_ids: list[str] = Field(
        default_factory=list, description="SupersededSource identifiers the answer actually relied on. M1 input."
    )
    cited_evidence: list[str] = Field(
        default_factory=list,
        description="Evidence identifiers the answer relied on. Originally captured as M2's input; "
        "M2 (Staleness-weighted Accuracy) was dropped after every candidate weighting formula proved "
        "arbitrary (ADR-127). Kept as descriptive data -- whether and which current evidence an "
        "answer cites is still informative context alongside M1/M3, just not collapsed into a scalar.",
    )
    correctness: Correctness
    calibration: Calibration | None = Field(
        default=None,
        description="Human-annotator judgement of whether the answer's stated confidence matches "
        "the strength of the gold claim's own evidence -- judged against the gold claim's stated "
        "strength, never the annotator's own clinical opinion (ADR-052/056). Reported separately "
        "from correctness throughout, never collapsed into it. Optional: not every item's gold "
        "claim carries a strength qualifier to calibrate against.",
    )

    m3_label: M3Label | None = Field(
        default=None, description="Required iff condition == POST_NOTICE; must be None otherwise."
    )
    notice_retrieved: bool | None = Field(
        default=None,
        description="Whether retrieval surfaced the supersession notice unprompted. "
        "Required iff condition == RETRIEVAL_WITH_NOTICE; must be None otherwise.",
    )

    evaluator: str
    evaluation_date: date
    notes: str = ""

    @model_validator(mode="after")
    def _condition_scoped_fields(self) -> "EvaluationResult":
        if self.condition == Condition.POST_NOTICE:
            if self.m3_label is None:
                raise ValueError("m3_label is required when condition is post_notice")
        elif self.m3_label is not None:
            raise ValueError("m3_label must be None unless condition is post_notice")

        if self.condition == Condition.RETRIEVAL_WITH_NOTICE:
            if self.notice_retrieved is None:
                raise ValueError("notice_retrieved is required when condition is retrieval_with_notice")
        elif self.notice_retrieved is not None:
            raise ValueError("notice_retrieved must be None unless condition is retrieval_with_notice")

        return self
