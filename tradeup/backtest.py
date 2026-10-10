"""Turn scores into a top-N portfolio and measure it after costs."""

import numpy as np
import pandas as pd

from .config import COST_PER_SIDE, HORIZON, TOP_N

PERIODS_PER_YEAR = 252 / HORIZON


def top_n_weights(scores: pd.Series, n: int = TOP_N) -> pd.DataFrame:
    """Equal weight in the n highest scores on each date; rows are dates, columns symbols."""
    rank = scores.groupby(level="date").rank(ascending=False, method="first")
    picked = (rank <= n).astype(float)
    weights = picked / picked.groupby(level="date").transform("sum")
    return weights.unstack("symbol").fillna(0.0)


def net_returns(weights: pd.DataFrame, fwd: pd.DataFrame, cost: float = COST_PER_SIDE) -> pd.Series:
    """Per-period portfolio return after charging `cost` on every rupee traded."""
    fwd = fwd.reindex(index=weights.index, columns=weights.columns).fillna(0.0)
    traded = weights.diff().abs().sum(axis=1)
    traded.iloc[0] = weights.iloc[0].abs().sum()
    return (weights * fwd).sum(axis=1) - cost * traded


def turnover(weights: pd.DataFrame) -> float:
    """Average share of the portfolio replaced per period."""
    return float(weights.diff().abs().sum(axis=1).iloc[1:].mean() / 2)


def stats(returns: pd.Series) -> dict[str, float]:
    growth = (1 + returns).cumprod()
    years = len(returns) / PERIODS_PER_YEAR
    return {
        "cagr": float(growth.iloc[-1] ** (1 / years) - 1),
        "volatility": float(returns.std() * np.sqrt(PERIODS_PER_YEAR)),
        "sharpe": float(returns.mean() / returns.std() * np.sqrt(PERIODS_PER_YEAR)),
        "max_drawdown": float((growth / growth.cummax() - 1).min()),
    }


def rank_ic(scores: pd.Series, fwd: pd.Series) -> pd.Series:
    """Per-date Spearman correlation between score and the return that followed."""
    both = pd.concat({"score": scores, "fwd": fwd}, axis=1).dropna()
    ranked = both.groupby(level="date").rank()
    return ranked.groupby(level="date").apply(lambda g: g["score"].corr(g["fwd"]))
