"""Turn scores into a top-N portfolio and measure it after costs."""

import numpy as np
import pandas as pd

from .config import COST_PER_SIDE, EXIT_RANK, HORIZON, TOP_N

PERIODS_PER_YEAR = 252 / HORIZON


def top_n_weights(scores: pd.Series, n: int = TOP_N) -> pd.DataFrame:
    """Equal weight in the n highest scores on each date; rows are dates, columns symbols."""
    rank = scores.groupby(level="date").rank(ascending=False, method="first")
    picked = (rank <= n).astype(float)
    weights = picked / picked.groupby(level="date").transform("sum")
    return weights.unstack("symbol").fillna(0.0)


def buffered_weights(scores: pd.Series, n: int = TOP_N, exit_rank: int = EXIT_RANK) -> pd.DataFrame:
    """Like top_n_weights, but a held stock stays until its rank falls below `exit_rank`.

    Cuts trading: a stock that slips from 18th to 25th is not sold and rebought.
    """
    rows, held = {}, []
    for day, s in scores.dropna().groupby(level="date"):
        rank = s.droplevel("date").rank(ascending=False, method="first").sort_values()
        held = [x for x in held if rank.get(x, exit_rank + 1) <= exit_rank][:n]
        held += [x for x in rank.index if x not in held][: n - len(held)]
        rows[day] = pd.Series(1 / len(held), index=held)
    return pd.DataFrame(rows).T.rename_axis(index="date", columns="symbol").sort_index(axis=1).fillna(0.0)


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


def bucket_returns(scores: pd.Series, fwd: pd.Series, buckets: int = 5) -> pd.Series:
    """Average yearly return before costs of each score bucket; bucket 1 holds the lowest scores."""
    both = pd.concat({"score": scores, "fwd": fwd}, axis=1).dropna()
    rank = both.groupby(level="date")["score"].rank(pct=True, method="first")
    bucket = np.ceil(rank * buckets).astype(int).rename("bucket")
    per_day = both["fwd"].groupby([both.index.get_level_values("date"), bucket]).mean()
    return per_day.groupby(level="bucket").mean() * PERIODS_PER_YEAR
