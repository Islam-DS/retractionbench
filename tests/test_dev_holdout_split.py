"""Tests for the stratified dev/held-out split."""

import pandas as pd

from retraction_bench.curate.dev_holdout_split import stratified_dev_holdout_split


def _fixture() -> pd.DataFrame:
    labels = ["A"] * 20 + ["B"] * 10 + ["C"] * 3
    return pd.DataFrame({"id": range(len(labels)), "label": labels})


def test_split_is_disjoint_and_covers_all_rows() -> None:
    df = _fixture()
    dev, holdout = stratified_dev_holdout_split(df, "label", seed=1)

    assert set(dev["id"]) & set(holdout["id"]) == set()
    assert set(dev["id"]) | set(holdout["id"]) == set(df["id"])


def test_split_is_stratified_by_label() -> None:
    df = _fixture()
    dev, holdout = stratified_dev_holdout_split(df, "label", seed=1, dev_fraction=0.5)

    for label, count in [("A", 20), ("B", 10), ("C", 3)]:
        dev_count = (dev["label"] == label).sum()
        holdout_count = (holdout["label"] == label).sum()
        assert dev_count + holdout_count == count
        # Roughly half each way, allowing for odd-count rounding (e.g. C=3 -> 1/2 or 2/1).
        assert abs(dev_count - holdout_count) <= 1


def test_split_is_deterministic_given_same_seed() -> None:
    df = _fixture()
    dev1, _ = stratified_dev_holdout_split(df, "label", seed=42)
    dev2, _ = stratified_dev_holdout_split(df, "label", seed=42)
    assert list(dev1["id"]) == list(dev2["id"])


def test_different_seeds_give_different_splits() -> None:
    df = _fixture()
    dev1, _ = stratified_dev_holdout_split(df, "label", seed=1)
    dev2, _ = stratified_dev_holdout_split(df, "label", seed=2)
    assert list(dev1["id"]) != list(dev2["id"])
