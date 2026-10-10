# TradeUp

Ranks Nifty 200 stocks each week using price signals and a graph of related
stocks, then holds the top 20. Research code; it places no orders.

- [IDEA.md](IDEA.md) — the idea, its weak points, and the staged build plan.
- [PLAN.md](PLAN.md) — the two OpenAlgo broker copies and the rules for working with them.
- [reports/v1_baseline.md](reports/v1_baseline.md) — latest backtest results.

## Run

    uv sync
    uv run python -m tradeup.run --refresh   # download prices, then backtest
    uv run python -m tradeup.run             # backtest on saved prices
    uv run pytest -q

## Layout

| File | Job |
|---|---|
| `tradeup/universe.py` | Nifty 200 members and industries from NSE; each download is saved under its date in `universe/` |
| `tradeup/prices.py` | Adjusted daily prices from Yahoo Finance into `data/prices.parquet` |
| `tradeup/features.py` | Price and volume features |
| `tradeup/graph.py` | Residual-correlation graph and neighbour averages |
| `tradeup/dataset.py` | One row per rebalance date and stock: features and the following return |
| `tradeup/model.py` | Walk-forward training and scoring |
| `tradeup/backtest.py` | Top-N portfolio, costs, statistics |
| `tradeup/run.py` | Runs all of the above and writes the report |

## Known limits of v1

- The universe is today's Nifty 200 applied to past years. Stocks that fell
  out of the index are missing, so absolute returns are too high. Comparisons
  between strategies on the same universe are less affected.
- Prices come from Yahoo Finance, not yet cross-checked against Angel One.
- No news or filings yet, so the graph uses price links only.
- Data from 2025-10-01 onwards is held back for one final test.
