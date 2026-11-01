"""Claim-type heuristic screen (Stage 1B).

Classifies a retracted paper's title + ArticleType into what kind of claim
it makes: clinical_intervention, clinical_observational, preclinical, or
unclear. Redesigned in ADR-021 as a recall-oriented pre-filter, not a
classifier: a human reads every candidate this screen passes through, so
false positives are cheap and false negatives are expensive. It excludes
ONLY on confident preclinical signal; everything else defaults to passing
through as a clinical candidate. See config/vocabularies/claim_type_screen.yaml's
header and docs/DECISIONS.md ADR-021 for why, and for the measured
recall/precision this screen actually achieves -- not assumed, measured.
"""

from enum import StrEnum
from pathlib import Path

import yaml

DEFAULT_CLAIM_SCREEN_PATH = Path("config/vocabularies/claim_type_screen.yaml")

CLINICAL_CLASSES = frozenset({"clinical_intervention", "clinical_observational"})


class ClaimType(StrEnum):
    CLINICAL_INTERVENTION = "clinical_intervention"
    CLINICAL_OBSERVATIONAL = "clinical_observational"
    PRECLINICAL = "preclinical"
    UNCLEAR = "unclear"


class ClaimTypeScreenConfig:
    def __init__(self, data: dict) -> None:
        self.non_research_article_types = set(data["non_research_article_types"])
        self.preclinical_exclusion_terms = [t.lower() for t in data["preclinical_exclusion_terms"]]
        self.clinical_intervention_terms = [t.lower() for t in data["clinical_intervention_terms"]]
        self.clinical_observational_terms = [t.lower() for t in data["clinical_observational_terms"]]


def load_claim_type_screen(path: Path = DEFAULT_CLAIM_SCREEN_PATH) -> ClaimTypeScreenConfig:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return ClaimTypeScreenConfig(data)


def _any_term_in(terms: list[str], title_lower: str) -> bool:
    return any(term in title_lower for term in terms)


def classify_claim_type(title: str, article_types: list[str], config: ClaimTypeScreenConfig) -> ClaimType:
    """Exclude on confident preclinical signal or non-research ArticleType; otherwise pass through.

    The pass-through default (clinical_observational when no keyword list
    fires at all) is deliberate: this screen's job is recall on "is this a
    clinical claim at all," not precise sub-classification. See the YAML
    header and ADR-021 for the recall-over-precision rationale.
    """
    if any(t in config.non_research_article_types for t in article_types):
        return ClaimType.UNCLEAR

    if not title:
        return ClaimType.UNCLEAR

    # Padded so " mice " style terms can match at title start/end without
    # requiring the caller to worry about boundary whitespace.
    title_lower = f" {title.lower()} "

    if _any_term_in(config.preclinical_exclusion_terms, title_lower):
        return ClaimType.PRECLINICAL
    if _any_term_in(config.clinical_intervention_terms, title_lower):
        return ClaimType.CLINICAL_INTERVENTION
    if _any_term_in(config.clinical_observational_terms, title_lower):
        return ClaimType.CLINICAL_OBSERVATIONAL
    return ClaimType.CLINICAL_OBSERVATIONAL
