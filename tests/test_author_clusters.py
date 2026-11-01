"""Tests for author-cluster detection and cap enforcement (ADR-031)."""

import pandas as pd

from retraction_bench.curate.author_clusters import (
    author_record_map,
    authors_over_cap,
    clusters,
    parse_authors,
)


def test_parse_authors_splits_and_strips() -> None:
    assert parse_authors("Yoshitaka Fujii;Hiroyoshi Tanaka; Mutsuko Ito ") == [
        "Yoshitaka Fujii",
        "Hiroyoshi Tanaka",
        "Mutsuko Ito",
    ]


def test_parse_authors_handles_single_author() -> None:
    assert parse_authors("Solo Author") == ["Solo Author"]


def _candidates() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "record_id": ["1", "2", "3", "4"],
            "author": [
                "A Fabricator;Co Author One",
                "A Fabricator;Co Author Two",
                "A Fabricator;Co Author Three",
                "Unrelated Person",
            ],
        }
    )


def test_author_record_map_counts_distinct_records_per_author() -> None:
    index = author_record_map(_candidates())
    assert index["A Fabricator"] == {"1", "2", "3"}
    assert index["Co Author One"] == {"1"}
    assert index["Unrelated Person"] == {"4"}


def test_clusters_finds_authors_at_or_above_min_size() -> None:
    found = clusters(_candidates(), min_size=3)
    assert set(found.keys()) == {"A Fabricator"}
    assert found["A Fabricator"] == {"1", "2", "3"}


def test_clusters_excludes_authors_below_min_size() -> None:
    found = clusters(_candidates(), min_size=2)
    assert "Unrelated Person" not in found


def test_authors_over_cap_flags_author_at_cap() -> None:
    index = author_record_map(_candidates())
    over = authors_over_cap(
        candidate_record_id="3",
        candidate_authors=["A Fabricator", "Co Author Three"],
        selected_record_ids={"1", "2"},
        author_index=index,
        cap=2,
    )
    assert over == ["A Fabricator"]


def test_authors_over_cap_empty_when_under_cap() -> None:
    index = author_record_map(_candidates())
    over = authors_over_cap(
        candidate_record_id="4",
        candidate_authors=["Unrelated Person"],
        selected_record_ids={"1", "2"},
        author_index=index,
        cap=2,
    )
    assert over == []
