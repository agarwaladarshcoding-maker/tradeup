"""Stage 0 and 1 end to end: data, features, walk-forward scores, backtest, report.

    uv run python -m tradeup.run            # reuse saved prices
    uv run python -m tradeup.run --refresh  # download prices again
"""

import sys

import numpy as np
import pandas as pd

from . import backtest, dataset, filings, model, prices, universe
from .config import COST_PER_SIDE, EXIT_RANK, HOLDOUT_START, HORIZON, REPORTS, TOP_N, UNIVERSE_SIZE


def evaluate(scores: pd.Series, data: pd.DataFrame, weigh) -> tuple[dict, pd.Series]:
    weights = weigh(scores)
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
    notes = filings.load() if filings.DIR.exists() else None
    data, index_fwd = dataset.build(px, universe.sectors(uni), notes)
    data = data.dropna(subset=["fwd"])

    P, G, F, FG = dataset.PRICE, dataset.PEER, dataset.FILING, dataset.FILING_PEER
    sets = {"Model: price": P, "Model: price + price peers": P + G}
    if notes is not None:
        sets |= {"Model: price + filings": P + F, "Model: price + filings + all peers": P + G + F + FG}
    scores = {name: model.walk_forward(data, cols) for name, cols in sets.items()}
    tested = next(iter(scores.values())).index
    scores = {"Momentum 12-1": data.loc[tested, "mom_12_1"]} | scores
    dates = tested.unique("date")

    table, ics = {}, {}
    for name, s in scores.items():
        table[f"{name}, top {TOP_N}"], ics[name] = evaluate(s, data, backtest.top_n_weights)
        table[f"{name}, hold to rank {EXIT_RANK}"], _ = evaluate(s, data, backtest.buffered_weights)
    table["Equal weight, whole universe (no costs)"] = backtest.stats(data["fwd"].unstack("symbol").loc[dates].mean(axis=1))
    table["Nifty 50 index (no dividends, no costs)"] = backtest.stats(index_fwd.loc[dates].dropna())

    summary = pd.DataFrame(table).T
    by_year = pd.DataFrame({k: v.groupby(v.index.year).mean() for k, v in ics.items()})
    buckets = pd.DataFrame({k: backtest.bucket_returns(s, data["fwd"]) for k, s in scores.items()}).T
    pct = ["cagr", "volatility", "max_drawdown", "turnover"]
    summary[pct] = summary[pct].map(lambda x: "" if pd.isna(x) else f"{x:.1%}")
    summary = summary.map(lambda x: "" if pd.isna(x) else f"{x:.3f}" if isinstance(x, float) else x)

    report = "\n\n".join([
        "# v1 results",
        f"Test period {dates[0].date()} to {dates[-1].date()}, {len(dates)} rebalances every {HORIZON} trading days. "
        f"Top {TOP_N} stocks, equal weight, {COST_PER_SIDE:.2%} cost per side. "
        f"Universe on each date: the {UNIVERSE_SIZE} most traded of {uni.shape[0]} candidates; "
        f"{data.index.unique('symbol').size} different stocks appear, {len(data):,} rows. "
        f"Data from {HOLDOUT_START} onwards is held back and was not used.",
        "## Portfolios", summary.to_markdown(),
        "`excess_t` is the t-statistic of the return over the equal-weight line; above 2 is the usual bar. "
        "`ic` is the average rank correlation between score and the following return, `ic_t` its t-statistic.",
        "## Yearly return by score bucket, before costs",
        "Stocks sorted by score each week into five equal groups; 1 is the lowest scores, 5 the highest.",
        buckets.map(lambda x: f"{x:.1%}").to_markdown(),
        "## Rank IC by year", by_year.round(3).to_markdown(),
    ])
    REPORTS.mkdir(exist_ok=True)
    (REPORTS / "v1_baseline.md").write_text(report + "\n")
    print(report)


if __name__ == "__main__":
    main("--refresh" in sys.argv)
