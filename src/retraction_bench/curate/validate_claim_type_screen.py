"""Validate the claim-type screen against the author's 100 hand labels (ADR-021).

Reads data/human/claim_type_hand_labels.csv (irreplaceable human input --
see the project protocol), splits it into a stratified dev/held-out pair,
and reports recall/precision on {clinical_intervention, clinical_observational}
combined -- the screen's actual job as a recall-oriented pre-filter, not
fine-grained 4-way agreement. Held-out is the headline number; dev exists
so that any future keyword-list tuning has somewhere to look that isn't
the number being reported.
"""

from pathlib import Path

import pandas as pd

from retraction_bench.curate.claim_type_screen import (
    CLINICAL_CLASSES,
    DEFAULT_CLAIM_SCREEN_PATH,
    classify_claim_type,
    load_claim_type_screen,
)
from retraction_bench.curate.dev_holdout_split import DEFAULT_SEED, stratified_dev_holdout_split
from retraction_bench.curate.scoring import binary_recall_precision, committed_accuracy, score
from retraction_bench.ingest.parsing import split_multivalue

DEFAULT_HAND_LABELS_PATH = Path("data/human/claim_type_hand_labels.csv")
DEFAULT_REPORT_PATH = Path("results/claim_type_screen_validation.md")
DEFAULT_DISAGREEMENTS_PATH = Path("results/claim_type_screen_disagreements.csv")

LABELS = ["clinical_intervention", "clinical_observational", "preclinical", "unclear"]
ABSTAIN_LABEL = "unclear"


def _markdown_table(headers: list[str], rows: list[list[object]]) -> str:
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(str(v) for v in row) + " |")
    return "\n".join(lines)


def _binary_section(title: str, y_true: list[str], y_pred: list[str]) -> str:
    m = binary_recall_precision(y_true, y_pred, positive_labels=set(CLINICAL_CLASSES))
    return (
        f"### {title} (n={len(y_true)})\n\n"
        f"- **Recall on clinical (intervention + observational): {m.recall * 100:.1f}%** "
        f"[{m.recall_ci[0] * 100:.1f}%, {m.recall_ci[1] * 100:.1f}%], TP={m.tp}, FN={m.fn}\n"
        f"- Precision: {m.precision * 100:.1f}% [{m.precision_ci[0] * 100:.1f}%, {m.precision_ci[1] * 100:.1f}%], "
        f"FP={m.fp}, TN={m.tn}\n"
    )


def run_validation(
    hand_labels_path: Path = DEFAULT_HAND_LABELS_PATH,
    screen_path: Path = DEFAULT_CLAIM_SCREEN_PATH,
    report_path: Path = DEFAULT_REPORT_PATH,
    disagreements_path: Path = DEFAULT_DISAGREEMENTS_PATH,
    expected_n: int = 100,
    split_seed: int = DEFAULT_SEED,
) -> pd.DataFrame:
    df = pd.read_csv(hand_labels_path)
    if len(df) != expected_n:
        raise ValueError(f"Expected {expected_n} hand-labeled rows, found {len(df)}")
    if df["human_label"].isna().any() or (df["human_label"] == "").any():
        raise ValueError("Not all rows have a human_label -- labeling isn't complete yet.")

    config = load_claim_type_screen()

    def predict(row: pd.Series) -> str:
        types = split_multivalue(row["article_type"])
        return classify_claim_type(row["title"], types, config).value

    df["screen_label"] = df.apply(predict, axis=1)

    dev, holdout = stratified_dev_holdout_split(df, "human_label", seed=split_seed)

    y_true_all, y_pred_all = df["human_label"].tolist(), df["screen_label"].tolist()
    result = score(y_true_all, y_pred_all, LABELS)
    committed_correct, committed_n = committed_accuracy(y_true_all, y_pred_all, ABSTAIN_LABEL)

    lo, hi = result.agreement_ci
    lines = [
        "# Claim-Type Screen Validation (ADR-021)\n",
        "Recall-oriented pre-filter, not a classifier -- a human reads every candidate this screen "
        "passes through. The headline number is held-out recall on clinical_intervention + "
        "clinical_observational combined, below. The 4-class agreement/kappa figures further down "
        "describe the same run but are not the design target -- see ADR-021 for why.\n",
        f"## Headline: dev vs. held-out (stratified 50/50 split, seed={split_seed})\n",
        _binary_section("Held-out (headline)", holdout["human_label"].tolist(), holdout["screen_label"].tolist()),
        _binary_section("Dev", dev["human_label"].tolist(), dev["screen_label"].tolist()),
        _binary_section("All 100 (dev + held-out combined, for reference)", y_true_all, y_pred_all),
        "\n## 4-class agreement (descriptive, not the design target)\n\n"
        f"n={result.n}. Overall agreement: **{result.agreement}/{result.n} = "
        f"{result.agreement_rate * 100:.1f}%**, 95% Wilson CI [{lo * 100:.1f}%, {hi * 100:.1f}%]. "
        f"Cohen's kappa: **{result.cohens_kappa:.3f}**.\n",
        "## Confusion matrix (rows = human, columns = screen, all 100)\n",
        _markdown_table(
            ["human \\ screen"] + LABELS,
            [[t] + [result.confusion[(t, p)] for p in LABELS] for t in LABELS],
        ),
        "\n## Per-class precision / recall (4-way, all 100)\n",
        _markdown_table(
            ["class", "precision", "recall", "support (human)", "predicted (screen)"],
            [
                [m.label, f"{m.precision * 100:.1f}%", f"{m.recall * 100:.1f}%", m.support, m.predicted_count]
                for m in result.per_class
            ],
        ),
        f"\nRestricting to rows where the screen output a non-`unclear` label: "
        f"**{committed_correct}/{committed_n} = {committed_correct / committed_n * 100:.1f}%** correct "
        "on the 4-way task (kept for continuity with the pre-redesign report; less relevant now that "
        "`unclear` is reserved for non-research ArticleType only, not a default).\n",
    ]
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines), encoding="utf-8")

    disagreements = df[df["human_label"] != df["screen_label"]][
        ["label_id", "record_id", "title", "human_label", "screen_label"]
    ]
    disagreements_path.parent.mkdir(parents=True, exist_ok=True)
    disagreements.to_csv(disagreements_path, index=False, encoding="utf-8")

    return df
