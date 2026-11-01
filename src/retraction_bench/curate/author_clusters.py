"""Author-cluster detection and cap enforcement (ANNOTATION.md section 3.1.2, ADR-031).

A large share of any retracted-literature pool traces back to a small number
of repeat authors -- some well-documented serial fabricators (Boldt, Fujii),
some just prolific groups hit by a shared retraction event. Either way,
including many items tied to one author is a sampling-independence problem:
the benchmark risks measuring whether a model recognises a specific author
or scandal rather than whether it tracks evidence currency generally. This
module finds those clusters in a candidate pool and enforces a cap during
final item selection.
"""

from collections import defaultdict

import pandas as pd

DEFAULT_CAP = 2


def parse_authors(author_field: str) -> list[str]:
    """Retraction Watch's Author column is semicolon-separated full names."""
    return [name.strip() for name in author_field.split(";") if name.strip()]


def author_record_map(candidates: pd.DataFrame) -> dict[str, set[str]]:
    """Individual author name -> set of distinct record_ids they appear on, across the pool."""
    index: dict[str, set[str]] = defaultdict(set)
    for _, row in candidates.iterrows():
        for name in parse_authors(row["author"]):
            index[name].add(row["record_id"])
    return dict(index)


def clusters(candidates: pd.DataFrame, min_size: int = 3) -> dict[str, set[str]]:
    """Author names appearing on at least `min_size` distinct candidate records."""
    index = author_record_map(candidates)
    return {name: records for name, records in index.items() if len(records) >= min_size}


def authors_over_cap(
    candidate_record_id: str,
    candidate_authors: list[str],
    selected_record_ids: set[str],
    author_index: dict[str, set[str]],
    cap: int = DEFAULT_CAP,
) -> list[str]:
    """Which of this candidate's authors would exceed `cap` if it were added to the selection.

    Empty list means the candidate is safe to add with respect to the author cap.
    """
    over = []
    for name in candidate_authors:
        already_selected = author_index.get(name, set()) & selected_record_ids
        if len(already_selected) >= cap:
            over.append(name)
    return over
