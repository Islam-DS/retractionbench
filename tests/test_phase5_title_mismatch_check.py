"""Unit tests for scripts/phase5_title_mismatch_check.py's title-normalization and similarity
functions, used to flag RW/PubMed PMID-title mismatches (author-requested validation, item 4,
2026-10-05 round) -- these caught the real, previously-undisclosed-at-this-granularity PMID
truncation case (RW record_id 250, "1834920") when run against the live data.
"""

import importlib.util
import sys
from pathlib import Path

_SPEC = importlib.util.spec_from_file_location(
    "phase5_title_mismatch_check",
    Path(__file__).resolve().parent.parent / "scripts" / "phase5_title_mismatch_check.py",
)
assert _SPEC is not None and _SPEC.loader is not None
_mod = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = _mod
_SPEC.loader.exec_module(_mod)
normalize_title = _mod.normalize_title
title_similarity = _mod.title_similarity


def test_normalize_strips_pub_version_suffix():
    assert normalize_title("Music for pain relief (Pub 2)") == normalize_title("Music for pain relief")


def test_normalize_strips_punctuation_and_case():
    assert normalize_title("Lidocaine-prilocaine cream!") == normalize_title("lidocaine prilocaine cream")


def test_identical_titles_score_1():
    assert title_similarity("Cello scrotum.", "Cello scrotum.") == 1.0


def test_unrelated_titles_score_low():
    sim = title_similarity(
        "A prospective randomized trial on the role of perioperative celecoxib administration "
        "for total knee arthroplasty: improving clinical outcomes",
        "Preprotein translocase of Escherichia coli: solubilization, purification, and "
        "reconstitution of the integral membrane subunits SecY/E.",
    )
    assert sim < 0.4


def test_empty_pubmed_title_scores_zero():
    assert title_similarity("Any real title", "") == 0.0


def test_pub_version_suffix_does_not_depress_similarity():
    sim = title_similarity("Topical negative pressure for treating chronic wounds",
                            "WITHDRAWN: Topical negative pressure for treating chronic wounds.")
    assert sim > 0.7
