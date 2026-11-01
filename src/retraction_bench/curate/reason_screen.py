"""Retraction Watch reason-tag screening (Stage 1B candidate selection).

Loads config/vocabularies/reason_screen.yaml and classifies a record's
reason tags into a candidate tier. THE SCREEN IS A HEURISTIC PRE-FILTER,
NOT GROUND TRUTH -- see the header of that YAML file and
docs/DECISIONS.md for why. The authoritative claim-invalidation judgment
is made by a human annotator reading the retraction notice.
"""

from enum import StrEnum
from pathlib import Path

import yaml

DEFAULT_SCREEN_PATH = Path("config/vocabularies/reason_screen.yaml")

# Tags in this set, and only this set, are allowed to be the *sole* ambiguous
# tag(s) on a record without dropping it out of tier_1_clean into tier_3.
# Image/data duplication is a deliberate research question (see ADR), not a
# default discard -- see docs/DECISIONS.md.
DUPLICATION_TAGS = frozenset(
    {
        "Duplication of/in Image",
        "Duplication of Data",
        "Euphemisms for Duplication",
    }
)


class ScreenClass(StrEnum):
    CLAIM_INVALIDATING = "claim_invalidating"
    PROCESS_ONLY = "process_only"
    PROCEDURAL_METADATA = "procedural_metadata"
    AMBIGUOUS = "ambiguous"


class Tier(StrEnum):
    TIER_1_CLEAN = "tier_1_clean"
    TIER_2_DUPLICATION = "tier_2_duplication"
    TIER_3_OTHER_AMBIGUOUS = "tier_3_other_ambiguous"


def load_reason_screen(path: Path = DEFAULT_SCREEN_PATH) -> dict[str, ScreenClass]:
    """Load the reason -> screen_class mapping. Raises if the file has an unknown screen_class value."""
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    mapping: dict[str, ScreenClass] = {}
    for entry in data["reasons"]:
        mapping[entry["reason"]] = ScreenClass(entry["screen_class"])
    return mapping


def classify_tier(reasons: list[str], screen: dict[str, ScreenClass]) -> Tier | None:
    """Classify a record's reason list into a candidate tier, or None if it's not a candidate at all.

    A reason absent from `screen` is treated as unclassified and, conservatively,
    as if it were ambiguous-but-not-a-duplication-tag -- it can knock a record
    out of tier_1/tier_2 into tier_3, but never manufactures a false tier_1.
    """
    classes = {r: screen.get(r) for r in reasons}

    if not any(c is ScreenClass.CLAIM_INVALIDATING for c in classes.values()):
        return None
    if any(c is ScreenClass.PROCESS_ONLY for c in classes.values()):
        return None

    non_duplication_ambiguous = any(
        (c is ScreenClass.AMBIGUOUS or c is None) and r not in DUPLICATION_TAGS for r, c in classes.items()
    )
    if non_duplication_ambiguous:
        return Tier.TIER_3_OTHER_AMBIGUOUS

    duplication_present = any(c is ScreenClass.AMBIGUOUS and r in DUPLICATION_TAGS for r, c in classes.items())
    if duplication_present:
        return Tier.TIER_2_DUPLICATION

    return Tier.TIER_1_CLEAN
