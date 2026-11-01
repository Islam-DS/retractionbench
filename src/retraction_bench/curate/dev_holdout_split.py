"""Stratified dev/held-out split for hand-label validation sets.

Exists so that tuning a heuristic screen against hand labels doesn't
silently become tuning against the number reported as its performance.
Split once, tune only against dev, score once against held-out. See
docs/DECISIONS.md ADR-021 for why this was added.
"""

import pandas as pd

DEFAULT_SEED = 20260806
DEFAULT_DEV_FRACTION = 0.5


def stratified_dev_holdout_split(
    df: pd.DataFrame,
    label_col: str,
    seed: int = DEFAULT_SEED,
    dev_fraction: float = DEFAULT_DEV_FRACTION,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Split df into (dev, holdout), stratified by label_col, deterministic given seed.

    Each label group is split independently so both sets track the overall
    label distribution, then re-sorted back to original row order (not
    grouped by label) so neither set trivially reveals label via position.
    """
    dev_parts = []
    holdout_parts = []
    for _, group in df.groupby(label_col, sort=False):
        dev_group = group.sample(frac=dev_fraction, random_state=seed)
        holdout_group = group.drop(dev_group.index)
        dev_parts.append(dev_group)
        holdout_parts.append(holdout_group)

    dev = pd.concat(dev_parts).sort_index()
    holdout = pd.concat(holdout_parts).sort_index()
    return dev, holdout
