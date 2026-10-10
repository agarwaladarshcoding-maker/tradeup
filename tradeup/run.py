"""Stage 0 and 1 end to end: data, features, walk-forward scores, backtest, report.

    uv run python -m tradeup.run            # reuse saved prices
    uv run python -m tradeup.run --refresh  # download prices again
"""

import sys

import numpy as np
import pandas as pd

from . import backtest, dataset, model, prices, universe
from .config import COST_PER_SIDE, HOLDOUT_START, HORIZON, REPORTS, TOP_N


def evaluate(scores: pd.Series, data: pd.DataFrame) -> tuple[dict, pd.Series]:
    weights = backtest.top_n_weights(scores)
    fwd = data["fwd"].unstack("symbol")
    returns = backtest.net_returns(weights, fwd)
    excess = returns - fwd.loc[returns.index].mean(axis=1)  # over holding every stock equally
    ic = backtest.rank_ic(scores, data["fwd"])
    row = backtest.stats(returns) | {
        "turnover": backtest.turnover(weights),
        "excess_t": excess.mean() / excess.std() * np.sqrt(len(excess)),
        "ic": ic.mean(),
        "ic_t": ic.mean() / ic.std() * np.sqrt(len(ic)),
    }
    return row, ic


def main(refresh: bool = False) -> None:
    uni = universe.load()
    px = prices.download(list(uni["Symbol"])) if refresh or not prices.PATH.exists() else prices.load()
    px = px[px["date"] < HOLDOUT_START]
    data, index_fwd = dataset.build(px, universe.sectors(uni))
    data = data.dropna(subset=["fwd"])

    scores = {
        "Model: price features": model.walk_forward(data, dataset.PRICE),
        "Model: price + peer features": model.walk_forward(data, dataset.PRICE + dataset.PEER),
    }
    tested = next(iter(scores.values())).index
    scores = {"Momentum 12-1": data.loc[tested, "mom_12_1"]} | scores
    dates = tested.unique("date")

    table, ics = {}, {}
    for name, s in scores.items():
        table[name], ics[name] = evaluate(s, data)
    table["Equal weight, all stocks (no costs)"] = backtest.stats(data["fwd"].unstack("symbol").loc[dates].mean(axis=1))
    table["Nifty 50 index (no dividends, no costs)"] = backtest.stats(index_fwd.loc[dates].dropna())

    summary = pd.DataFrame(table).T
    by_year = pd.DataFrame({k: v.groupby(v.index.year).mean() for k, v in ics.items()})
    pct = ["cagr", "volatility", "max_drawdown", "turnover"]
    summary[pct] = summary[pct].map(lambda x: "" if pd.isna(x) else f"{x:.1%}")
    summary = summary.map(lambda x: "" if pd.isna(x) else f"{x:.3f}" if isinstance(x, float) else x)

    report = "\n\n".join([
        "# v1 baseline results",
        f"Test period {dates[0].date()} to {dates[-1].date()}, {len(dates)} rebalances every {HORIZON} trading days. "
        f"Top {TOP_N} stocks, equal weight, {COST_PER_SIDE:.2%} cost per side. "
        f"{data.index.unique('symbol').size} stocks, {len(data):,} rows. "
        f"Data from {HOLDOUT_START} onwards is held back and was not used.",
        "## Portfolios", summary.to_markdown(),
        "`excess_t` is the t-statistic of the return over the equal-weight line; above 2 is the usual bar. "
        "`ic` is the average rank correlation between score and the following return, `ic_t` its t-statistic.",
        "## Rank IC by year", by_year.round(3).to_markdown(),
    ])
    REPORTS.mkdir(exist_ok=True)
    (REPORTS / "v1_baseline.md").write_text(report + "\n")
    print(report)


if __name__ == "__main__":
    main("--refresh" in sys.argv)
