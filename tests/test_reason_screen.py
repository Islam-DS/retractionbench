"""Tests for the reason-screen loader and tier classifier."""

from pathlib import Path

from retraction_bench.curate.reason_screen import ScreenClass, Tier, classify_tier, load_reason_screen

FIXTURE_SCREEN = {
    "Unreliable Results and/or Conclusions": ScreenClass.CLAIM_INVALIDATING,
    "Paper Mill": ScreenClass.PROCESS_ONLY,
    "Investigation by Journal/Publisher": ScreenClass.PROCEDURAL_METADATA,
    "Duplication of/in Image": ScreenClass.AMBIGUOUS,
    "Duplication of Data": ScreenClass.AMBIGUOUS,
    "Objections by Author(s)": ScreenClass.AMBIGUOUS,
}


def test_load_reason_screen_from_yaml(tmp_path: Path) -> None:
    yaml_path = tmp_path / "reason_screen.yaml"
    yaml_path.write_text(
        """
schema_version: "0.1.0"
reasons:
  - reason: "Unreliable Results and/or Conclusions"
    screen_class: claim_invalidating
  - reason: "Paper Mill"
    screen_class: process_only
""",
        encoding="utf-8",
    )
    screen = load_reason_screen(yaml_path)
    assert screen["Unreliable Results and/or Conclusions"] is ScreenClass.CLAIM_INVALIDATING
    assert screen["Paper Mill"] is ScreenClass.PROCESS_ONLY


def test_no_claim_invalidating_reason_is_not_a_candidate() -> None:
    assert classify_tier([], FIXTURE_SCREEN) is None
    assert classify_tier(["Paper Mill"], FIXTURE_SCREEN) is None


def test_process_only_reason_disqualifies_regardless_of_claim_invalidating() -> None:
    assert classify_tier(["Unreliable Results and/or Conclusions", "Paper Mill"], FIXTURE_SCREEN) is None


def test_procedural_metadata_is_ignored_entirely() -> None:
    result = classify_tier(
        ["Unreliable Results and/or Conclusions", "Investigation by Journal/Publisher"], FIXTURE_SCREEN
    )
    assert result is Tier.TIER_1_CLEAN


def test_pure_claim_invalidating_is_tier_1() -> None:
    assert classify_tier(["Unreliable Results and/or Conclusions"], FIXTURE_SCREEN) is Tier.TIER_1_CLEAN


def test_duplication_only_ambiguous_is_tier_2() -> None:
    result = classify_tier(["Unreliable Results and/or Conclusions", "Duplication of/in Image"], FIXTURE_SCREEN)
    assert result is Tier.TIER_2_DUPLICATION


def test_multiple_duplication_tags_still_tier_2() -> None:
    result = classify_tier(
        ["Unreliable Results and/or Conclusions", "Duplication of/in Image", "Duplication of Data"],
        FIXTURE_SCREEN,
    )
    assert result is Tier.TIER_2_DUPLICATION


def test_non_duplication_ambiguous_is_tier_3() -> None:
    result = classify_tier(["Unreliable Results and/or Conclusions", "Objections by Author(s)"], FIXTURE_SCREEN)
    assert result is Tier.TIER_3_OTHER_AMBIGUOUS


def test_duplication_plus_other_ambiguous_is_tier_3_not_tier_2() -> None:
    result = classify_tier(
        ["Unreliable Results and/or Conclusions", "Duplication of/in Image", "Objections by Author(s)"],
        FIXTURE_SCREEN,
    )
    assert result is Tier.TIER_3_OTHER_AMBIGUOUS


def test_unmapped_reason_is_treated_conservatively_as_non_duplication_ambiguous() -> None:
    # A reason absent from the screen must never manufacture a false tier_1 --
    # it can only ever push a record toward tier_3, never clear it.
    reasons = ["Unreliable Results and/or Conclusions", "Some New Reason Not In The Vocabulary"]
    result = classify_tier(reasons, FIXTURE_SCREEN)
    assert result is Tier.TIER_3_OTHER_AMBIGUOUS


def test_real_reason_screen_yaml_loads_and_covers_documented_notice_types() -> None:
    screen = load_reason_screen()
    assert len(screen) == 112
    assert screen["Unreliable Results and/or Conclusions"] is ScreenClass.CLAIM_INVALIDATING
    assert screen["Paper Mill"] is ScreenClass.PROCESS_ONLY
    assert screen["Investigation by Journal/Publisher"] is ScreenClass.PROCEDURAL_METADATA
    assert screen["Duplication of/in Image"] is ScreenClass.AMBIGUOUS
