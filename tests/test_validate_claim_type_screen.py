"""Tests for the claim-type screen validation report, using a small synthetic hand-label fixture."""

from pathlib import Path

import pandas as pd
import pytest

from retraction_bench.curate.validate_claim_type_screen import run_validation

SCREEN_YAML = """
schema_version: "0.2.0"
non_research_article_types: ["Letter"]
preclinical_exclusion_terms: ["mouse model", "signaling pathway"]
clinical_intervention_terms: ["randomized"]
clinical_observational_terms: ["cohort"]
"""


def _fixture(tmp_path: Path, n_per_label: int = 3) -> tuple[Path, Path]:
    # Repeat each labeled example n_per_label times (distinct record_id/label_id)
    # so the stratified split has something real to split within each class.
    base = [
        ("A randomized trial of drug X", "Research Article;", "clinical_intervention"),
        ("A cohort study of disease Y", "Research Article;", "clinical_observational"),
        ("MiR pathway signaling pathway in a mouse model", "Research Article;", "preclinical"),
        ("Some unrelated title with no keyword match", "Research Article;", "clinical_observational"),
    ]
    rows = []
    label_id = 1
    for title, article_type, human_label in base:
        for i in range(n_per_label):
            rows.append((label_id, f"r{label_id}", f"{title} ({i})", article_type, human_label))
            label_id += 1
    hand_labels = pd.DataFrame(rows, columns=["label_id", "record_id", "title", "article_type", "human_label"])

    hand_labels_path = tmp_path / "hand_labels.csv"
    hand_labels.to_csv(hand_labels_path, index=False)

    screen_path = tmp_path / "claim_type_screen.yaml"
    screen_path.write_text(SCREEN_YAML, encoding="utf-8")
    return hand_labels_path, screen_path


def test_run_validation_writes_report_and_disagreements(tmp_path: Path) -> None:
    hand_labels_path, screen_path = _fixture(tmp_path, n_per_label=3)
    report_path = tmp_path / "report.md"
    disagreements_path = tmp_path / "disagreements.csv"

    df = run_validation(
        hand_labels_path=hand_labels_path,
        screen_path=screen_path,
        report_path=report_path,
        disagreements_path=disagreements_path,
        expected_n=12,
    )

    assert report_path.exists()
    assert disagreements_path.exists()
    assert "screen_label" in df.columns

    report_text = report_path.read_text(encoding="utf-8")
    assert "Held-out (headline)" in report_text
    assert "Dev (n=" in report_text
    assert "Recall on clinical" in report_text
    assert "Cohen's kappa" in report_text
    assert "Confusion matrix" in report_text

    # The "no keyword match" title is clinical_observational per the human but
    # the redesigned screen should now PASS it through (not exclude it) --
    # confirms the recall-oriented default is actually wired end to end.
    no_match_rows = df[df["title"].str.startswith("Some unrelated title")]
    assert (no_match_rows["screen_label"] == "clinical_observational").all()


def test_run_validation_rejects_incomplete_labels(tmp_path: Path) -> None:
    hand_labels_path, screen_path = _fixture(tmp_path, n_per_label=3)
    df = pd.read_csv(hand_labels_path)
    df.loc[0, "human_label"] = None
    df.to_csv(hand_labels_path, index=False)

    with pytest.raises(ValueError, match="human_label"):
        run_validation(
            hand_labels_path=hand_labels_path,
            screen_path=screen_path,
            report_path=tmp_path / "report.md",
            disagreements_path=tmp_path / "disagreements.csv",
            expected_n=12,
        )


def test_run_validation_rejects_wrong_row_count(tmp_path: Path) -> None:
    hand_labels_path, screen_path = _fixture(tmp_path, n_per_label=3)  # 12 rows, not 100

    with pytest.raises(ValueError, match="100"):
        run_validation(
            hand_labels_path=hand_labels_path,
            screen_path=screen_path,
            report_path=tmp_path / "report.md",
            disagreements_path=tmp_path / "disagreements.csv",
        )
