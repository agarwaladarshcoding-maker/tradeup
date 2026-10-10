"""Stock graph from residual correlation (IDEA.md section 4.1)."""

import numpy as np
import pandas as pd

from .features import group_mean


def residual_returns(returns: pd.DataFrame, sectors: pd.Series) -> pd.DataFrame:
    """Daily returns with the same-day sector average removed."""
    return returns - group_mean(returns, sectors)


def neighbours(window: pd.DataFrame, k: int, min_periods: int = 40) -> pd.DataFrame:
    """Row-normalised adjacency: each stock's k most positively correlated others."""
    corr = window.corr(min_periods=min_periods)
    corr = corr.mask(np.eye(len(corr), dtype=bool))
    keep = (corr.rank(axis=1, ascending=False) <= k) & (corr > 0)
    adj = keep.astype(float)
    return adj.div(adj.sum(axis=1).replace(0, np.nan), axis=0).fillna(0.0)


def peer_mean(adj: pd.DataFrame, values: pd.Series) -> pd.Series:
    """Average of each stock's neighbours' values, skipping missing ones."""
    v = values.reindex(adj.columns)
    total = adj.values @ v.fillna(0.0).values
    weight = adj.values @ v.notna().values.astype(float)
    return pd.Series(np.where(weight > 0, total / np.where(weight > 0, weight, 1), np.nan), index=adj.index)
