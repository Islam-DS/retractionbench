"""Seed aggregation (the project protocol: every experiment runs under >=3 seeds and reports
variance -- this is the module that enforces "reports variance," not just runs the seeds).
"""

from dataclasses import dataclass

import numpy as np

MIN_SEEDS = 3


@dataclass
class SeedAggregateResult:
    mean: float
    std: float  # population-style ddof=0; the seeds run are the whole population of runs we have
    n_seeds: int
    values_by_seed: dict[int, float]
    below_min_seeds: bool  # True if n_seeds < MIN_SEEDS -- flagged, never silently accepted


def aggregate_across_seeds(values_by_seed: dict[int, float]) -> SeedAggregateResult:
    """Aggregate one metric's per-seed values into a mean and an explicit variance report.

    Does not raise on fewer than MIN_SEEDS -- a dry run (the project protocol's pipeline stage 4) legitimately
    runs a single seed, and this function is reused there. `below_min_seeds` is the signal callers
    (eval/stratify.py, and any figure/table generator) must check before treating a result as a
    headline number: the project protocol's >=3-seed requirement is enforced by the caller refusing to report
    a below-threshold result as final, not by this function refusing to compute one.
    """
    if not values_by_seed:
        raise ValueError("aggregate_across_seeds requires at least one seed's value")

    values = np.array(list(values_by_seed.values()), dtype=float)
    return SeedAggregateResult(
        mean=float(np.mean(values)),
        std=float(np.std(values, ddof=0)),
        n_seeds=len(values_by_seed),
        values_by_seed=dict(values_by_seed),
        below_min_seeds=len(values_by_seed) < MIN_SEEDS,
    )
