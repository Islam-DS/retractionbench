"""Insufficient-data handling for thin strata.

This project's own annotation-phase power analysis (docs/DECISIONS.md ADR-099/101/102) already
established the operative rule by measurement, not by convention borrowed from elsewhere: below
~10 raw items in a stratum, a single item can swing a reported rate by more than 10 percentage
points, which is too unstable to present as a headline comparison. Below 5, individual items
should be named, not averaged into a rate at all. This module makes that rule executable instead
of a note repeated by hand at each checkpoint.
"""

from dataclasses import dataclass
from enum import StrEnum


class StratumReliability(StrEnum):
    RELIABLE = "reliable"  # n >= MIN_HEADLINE_N: safe to report as a headline rate/CI
    THIN = "thin"  # MIN_ITEMIZE_N <= n < MIN_HEADLINE_N: report, but flagged as exploratory
    TOO_THIN_TO_RATE = "too_thin_to_rate"  # n < MIN_ITEMIZE_N: report items individually, not a rate


MIN_HEADLINE_N = 10
MIN_ITEMIZE_N = 5


@dataclass
class StratumSizeCheck:
    n: int
    reliability: StratumReliability


def check_stratum_size(n: int) -> StratumSizeCheck:
    if n < 0:
        raise ValueError(f"stratum size cannot be negative, got {n}")
    if n >= MIN_HEADLINE_N:
        reliability = StratumReliability.RELIABLE
    elif n >= MIN_ITEMIZE_N:
        reliability = StratumReliability.THIN
    else:
        reliability = StratumReliability.TOO_THIN_TO_RATE
    return StratumSizeCheck(n=n, reliability=reliability)
