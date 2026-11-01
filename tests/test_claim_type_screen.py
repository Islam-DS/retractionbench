"""Tests for the claim-type screen's recall-oriented priority cascade (ADR-021 redesign).

Exclude only on confident preclinical signal or non-research ArticleType;
everything else -- including titles that match no keyword list at all --
passes through as a clinical candidate. That's the point: false negatives
are expensive, false positives are cheap (a human reviews every candidate).
"""

from pathlib import Path

from retraction_bench.curate.claim_type_screen import (
    DEFAULT_CLAIM_SCREEN_PATH,
    ClaimType,
    ClaimTypeScreenConfig,
    classify_claim_type,
    load_claim_type_screen,
)

FIXTURE_CONFIG = ClaimTypeScreenConfig(
    {
        "non_research_article_types": ["Letter", "Commentary/Editorial"],
        "preclinical_exclusion_terms": ["mouse model", "cell line", "nanoparticle", "canine"],
        "clinical_intervention_terms": ["randomized", "double-blind"],
        "clinical_observational_terms": ["cohort", "in patients with"],
    }
)


def test_non_research_article_type_forces_unclear_regardless_of_title() -> None:
    result = classify_claim_type("A randomized double-blind trial", ["Letter"], FIXTURE_CONFIG)
    assert result is ClaimType.UNCLEAR


def test_empty_title_is_unclear() -> None:
    assert classify_claim_type("", ["Research Article"], FIXTURE_CONFIG) is ClaimType.UNCLEAR


def test_preclinical_exclusion_wins_even_with_intervention_language() -> None:
    # "Efficacy of Drug X in a mouse model" is still animal research.
    result = classify_claim_type(
        "A randomized study of Drug X efficacy in a mouse model of disease", ["Research Article"], FIXTURE_CONFIG
    )
    assert result is ClaimType.PRECLINICAL


def test_clinical_intervention_term_matches() -> None:
    result = classify_claim_type(
        "A randomized double-blind trial of Drug X for hypertension", ["Research Article"], FIXTURE_CONFIG
    )
    assert result is ClaimType.CLINICAL_INTERVENTION


def test_clinical_observational_term_matches() -> None:
    result = classify_claim_type(
        "Risk factors in patients with hypertension: a cohort study", ["Research Article"], FIXTURE_CONFIG
    )
    assert result is ClaimType.CLINICAL_OBSERVATIONAL


def test_no_keyword_match_passes_through_as_clinical_observational() -> None:
    # The core recall-oriented behaviour change: a title matching nothing
    # used to default to `unclear` (old design); now it defaults to passing
    # through, since excluding it would be a silent, expensive false negative.
    result = classify_claim_type(
        "Carbetocin versus syntometrine for prevention of postpartum hemorrhage",
        ["Research Article"],
        FIXTURE_CONFIG,
    )
    assert result is ClaimType.CLINICAL_OBSERVATIONAL


def test_case_report_with_no_keyword_match_still_passes_through() -> None:
    result = classify_claim_type(
        "Hemolytic jaundice induced by pharmacological dose ascorbic acid: a case report",
        ["Case Report"],
        FIXTURE_CONFIG,
    )
    assert result is ClaimType.CLINICAL_OBSERVATIONAL


def test_biomaterials_term_excludes_as_preclinical() -> None:
    result = classify_claim_type(
        "Novel nanoparticle formulation for transdermal drug delivery", ["Research Article"], FIXTURE_CONFIG
    )
    assert result is ClaimType.PRECLINICAL


def test_non_rodent_animal_term_excludes_as_preclinical() -> None:
    result = classify_claim_type("A preliminary study on canine gastric motility", ["Research Article"], FIXTURE_CONFIG)
    assert result is ClaimType.PRECLINICAL


def test_real_claim_type_screen_yaml_loads() -> None:
    config = load_claim_type_screen()
    assert "cell line" in config.preclinical_exclusion_terms
    assert "nanoparticle" in config.preclinical_exclusion_terms
    assert "canine" in config.preclinical_exclusion_terms
    assert "randomized" in config.clinical_intervention_terms


def test_default_path_is_the_real_config_file() -> None:
    assert Path("config/vocabularies/claim_type_screen.yaml") == DEFAULT_CLAIM_SCREEN_PATH
