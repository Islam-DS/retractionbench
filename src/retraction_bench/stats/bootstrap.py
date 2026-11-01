"""Bootstrap confidence intervals (the project protocol: every reported number carries one).

A percentile bootstrap, not a normal-approximation interval (Wilson, etc.) -- the project protocol's
evaluation-phase requirement is explicit and distinct from the Wilson-CI shortcuts used
throughout the annotation-phase power projections (docs/DECISIONS.md ADR-099/101/102), which
were exploratory sizing estimates, not the headline numbers this module produces. Deterministic
given a fixed seed: `make reproduce` must regenerate every number in the paper (the project protocol
section 5), so resampling here is seeded, never left to global numpy state.
"""

from collections.abc import Callable, Sequence
from dataclasses import dataclass

import numpy as np

DEFAULT_N_RESAMPLES = 10_000
DEFAULT_CONFIDENCE = 0.95
DEFAULT_SEED = 42


@dataclass
class BootstrapResult:
    point_estimate: float
    ci_low: float
    ci_high: float
    n: int  # size of the original sample the estimate was computed over
    n_resamples: int
    confidence: float
    seed: int


def bootstrap_ci(
    values: Sequence[float],
    statistic: Callable[[np.ndarray], float] = np.mean,
    n_resamples: int = DEFAULT_N_RESAMPLES,
    confidence: float = DEFAULT_CONFIDENCE,
    seed: int = DEFAULT_SEED,
) -> BootstrapResult:
    """Percentile bootstrap CI for `statistic` applied to `values`.

    Empty input is a caller error, not silently handled: an empty stratum has no point estimate
    to report, and returning a fabricated (nan, nan, nan) invites it to be printed as if it were
    a real result. Callers (eval/stratify.py) must check stratum size first and route empty or
    too-thin strata through the insufficient-data path (stats/strata.py) instead of calling this
    directly.
    """
    if len(values) == 0:
        raise ValueError("bootstrap_ci requires at least one value -- check stratum size before calling")

    arr = np.asarray(values, dtype=float)
    point_estimate = float(statistic(arr))

    if len(arr) == 1:
        # A single point has no resampling variance to estimate; the CI collapses to the point.
        return BootstrapResult(
            point_estimate=point_estimate,
            ci_low=point_estimate,
            ci_high=point_estimate,
            n=1,
            n_resamples=n_resamples,
            confidence=confidence,
            seed=seed,
        )

    rng = np.random.default_rng(seed)
    resample_stats = np.empty(n_resamples)
    for i in range(n_resamples):
        resample = rng.choice(arr, size=len(arr), replace=True)
        resample_stats[i] = statistic(resample)

    alpha = 1 - confidence
    ci_low = float(np.percentile(resample_stats, 100 * (alpha / 2)))
    ci_high = float(np.percentile(resample_stats, 100 * (1 - alpha / 2)))

    return BootstrapResult(
        point_estimate=point_estimate,
        ci_low=ci_low,
        ci_high=ci_high,
        n=len(arr),
        n_resamples=n_resamples,
        confidence=confidence,
        seed=seed,
    )


def bootstrap_proportion_ci(
    successes: Sequence[bool],
    n_resamples: int = DEFAULT_N_RESAMPLES,
    confidence: float = DEFAULT_CONFIDENCE,
    seed: int = DEFAULT_SEED,
) -> BootstrapResult:
    """Convenience wrapper for the common case: a bootstrap CI on a binary rate (M1's own shape,
    and each M3 category treated as its own indicator). Booleans are cast to 0.0/1.0 before
    calling bootstrap_ci, since np.mean over bools already works but resampling a bool array with
    np.random.Generator.choice needs a float dtype to be unambiguous across numpy versions.

    Treats every observation as an independent draw. This is the right model only when
    observations genuinely are independent draws -- it is the wrong model whenever several
    observations share a benchmark item (e.g. 3 seeds of the same item), since those responses
    are correlated with each other through whatever makes that item easy or hard. Use
    `bootstrap_proportion_ci_clustered` instead whenever the input has repeated-item structure;
    this function does not detect that structure itself and will silently understate uncertainty
    if used on clustered data (a real gap caught during external review, ADR pending).
    """
    return bootstrap_ci(
        [1.0 if s else 0.0 for s in successes],
        statistic=np.mean,
        n_resamples=n_resamples,
        confidence=confidence,
        seed=seed,
    )


def bootstrap_proportion_ci_clustered(
    successes: Sequence[bool],
    cluster_ids: Sequence[str],
    n_resamples: int = DEFAULT_N_RESAMPLES,
    confidence: float = DEFAULT_CONFIDENCE,
    seed: int = DEFAULT_SEED,
) -> BootstrapResult:
    """Cluster (block) bootstrap: resamples whole clusters (benchmark items) with replacement,
    keeping every observation within a resampled cluster together, rather than resampling
    individual observations independently. This is the statistically appropriate procedure when
    the data has repeated-measures structure -- e.g. 3 seeds x the same item -- since
    `bootstrap_proportion_ci`'s per-observation resampling treats those 3 correlated responses as
    3 independent draws and can understate the true sampling uncertainty as a result (the
    benchmark item, not the individual response, is the real independent experimental unit).

    `successes` and `cluster_ids` must be the same length and pair up positionally (successes[i]
    belongs to cluster_ids[i]). The point estimate is unchanged (still the raw pooled rate); only
    the CI's resampling unit changes.
    """
    if len(successes) != len(cluster_ids):
        raise ValueError("successes and cluster_ids must be the same length")
    if len(successes) == 0:
        raise ValueError("bootstrap_proportion_ci_clustered requires at least one value")

    by_cluster: dict[str, list[bool]] = {}
    for s, cid in zip(successes, cluster_ids):
        by_cluster.setdefault(cid, []).append(s)
    clusters = list(by_cluster.values())

    all_vals = np.asarray([1.0 if s else 0.0 for s in successes])
    point_estimate = float(all_vals.mean())

    if len(clusters) == 1:
        return BootstrapResult(
            point_estimate=point_estimate,
            ci_low=point_estimate,
            ci_high=point_estimate,
            n=len(successes),
            n_resamples=n_resamples,
            confidence=confidence,
            seed=seed,
        )

    rng = np.random.default_rng(seed)
    n_clusters = len(clusters)
    resample_stats = np.empty(n_resamples)
    for i in range(n_resamples):
        chosen = rng.integers(0, n_clusters, size=n_clusters)
        pooled: list[float] = []
        for idx in chosen:
            pooled.extend(1.0 if s else 0.0 for s in clusters[idx])
        resample_stats[i] = float(np.mean(pooled))

    alpha = 1 - confidence
    ci_low = float(np.percentile(resample_stats, 100 * (alpha / 2)))
    ci_high = float(np.percentile(resample_stats, 100 * (1 - alpha / 2)))

    return BootstrapResult(
        point_estimate=point_estimate,
        ci_low=ci_low,
        ci_high=ci_high,
        n=len(successes),
        n_resamples=n_resamples,
        confidence=confidence,
        seed=seed,
    )
