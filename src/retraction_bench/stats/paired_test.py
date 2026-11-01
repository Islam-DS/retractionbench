"""Paired, item-level hypothesis testing and multiple-comparisons correction (ADR-153).

Added to close a real reproducibility gap: this project's central per-model comparison in the
paper (does a model's citation behavior actually change between `retrieval_naive` and
`retrieval_with_notice`) was, for the entire duration of this project, computed by an uncommitted
scratch script rather than any code in this repository -- the numbers were correct (independently
re-verified against this module before it replaced that script), but not reproducible by anyone
who only had this repository. This module, plus `eval/paired_m1.py`, is that fix.

Why a paired test at all, not CI overlap: two independent-sample CIs can overlap even when a
within-item paired comparison is highly significant (each item serves as its own control, which
removes the item-to-item variance that a between-condition CI comparison cannot). CI overlap is
therefore not a valid substitute for a real hypothesis test, and this project's own paper was
corrected on exactly this point during external review (ADR-151).
"""

from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np

DEFAULT_N_RESAMPLES = 10_000
DEFAULT_SEED = 42


@dataclass
class PairedTestResult:
    n_items: int
    mean_diff: float
    ci_low: float
    ci_high: float
    p_value: float
    n_resamples: int
    seed: int


def paired_bootstrap_permutation_test(
    diffs: Sequence[float],
    seed: int = DEFAULT_SEED,
    n_resamples: int = DEFAULT_N_RESAMPLES,
) -> PairedTestResult:
    """Given one paired difference per item (e.g. `notice_rate[item] - naive_rate[item]`), returns
    a percentile bootstrap CI on the mean difference and a two-sided sign-flip permutation p-value.

    The bootstrap CI resamples items with replacement (the item is the independent unit here, not
    the response -- each item already contributes exactly one paired difference, so this is a
    standard, not item-clustered-on-top-of-itself, bootstrap over those n_items differences). The
    permutation test independently randomizes the sign of each item's difference (the null
    hypothesis that condition assignment doesn't matter for that item, matching the standard
    paired sign-flip/Wilcoxon-style permutation test) and asks how often a random sign-flip
    produces a mean at least as extreme as the observed one.

    Both procedures use their own independent RNG stream (`seed` and `seed + 1`) so changing the
    bootstrap's resample count never perturbs the permutation p-value's random draws, or vice
    versa -- deterministic and independently reproducible given a fixed seed, matching this
    project's `stats/bootstrap.py` convention.
    """
    arr = np.asarray(diffs, dtype=float)
    n = len(arr)
    if n == 0:
        raise ValueError("paired_bootstrap_permutation_test requires at least one paired difference")
    mean_diff = float(arr.mean())

    if n == 1:
        # A single paired difference has no resampling variance and no permutation distribution
        # worth computing -- collapses to the point, matching stats/bootstrap.py's own single-
        # value convention, rather than fabricating a spread or a p-value from n=1.
        return PairedTestResult(
            n_items=1,
            mean_diff=mean_diff,
            ci_low=mean_diff,
            ci_high=mean_diff,
            p_value=1.0,
            n_resamples=n_resamples,
            seed=seed,
        )

    boot_rng = np.random.default_rng(seed)
    resample_means = np.empty(n_resamples)
    for i in range(n_resamples):
        idx = boot_rng.integers(0, n, size=n)
        resample_means[i] = arr[idx].mean()
    ci_low = float(np.percentile(resample_means, 2.5))
    ci_high = float(np.percentile(resample_means, 97.5))

    perm_rng = np.random.default_rng(seed + 1)
    signs = perm_rng.choice([-1.0, 1.0], size=(n_resamples, n))
    perm_means = (signs * arr).mean(axis=1)
    # +1/+1 (not +0/+0) in numerator/denominator: the observed assignment is itself one valid
    # permutation, so a p-value of exactly 0 is never reported even when no simulated permutation
    # is as extreme as the observed statistic -- the standard finite-permutation-test correction.
    p_value = float((np.sum(np.abs(perm_means) >= abs(mean_diff)) + 1) / (n_resamples + 1))

    return PairedTestResult(
        n_items=n,
        mean_diff=mean_diff,
        ci_low=ci_low,
        ci_high=ci_high,
        p_value=p_value,
        n_resamples=n_resamples,
        seed=seed,
    )


def holm_correction(pvalues: dict[str, float]) -> dict[str, float]:
    """Holm-Bonferroni step-down correction over a named family of p-values, tested as one family
    rather than each compared to alpha independently (this project's three prespecified
    model-specific M1 comparisons, per ADR-152). Returns adjusted p-values keyed the same way as
    the input; compare each to the same alpha (typically 0.05) you would have used uncorrected.

    Standard Holm procedure: sort ascending, multiply the i-th smallest (1-indexed) by
    (m - i + 1), then take the running maximum so adjusted p-values are monotonically
    non-decreasing in the sorted order (a later, larger p-value can never end up with a smaller
    adjusted value than an earlier, smaller one already assigned). Each adjusted value is capped
    at 1.0.
    """
    if not pvalues:
        raise ValueError("holm_correction requires at least one p-value")
    items = sorted(pvalues.items(), key=lambda kv: kv[1])
    m = len(items)
    adjusted: dict[str, float] = {}
    running_max = 0.0
    for i, (name, p) in enumerate(items, start=1):
        candidate = min(1.0, (m - i + 1) * p)
        running_max = max(running_max, candidate)
        adjusted[name] = running_max
    return adjusted
