# TradeUp

Ranks the 200 most traded NSE stocks each week using price signals and a graph of related
stocks, then holds the top 20. Research code; it places no orders.

- [IDEA.md](IDEA.md) — the idea, its weak points, and the staged build plan.
- [PLAN.md](PLAN.md) — the two OpenAlgo broker copies and the rules for working with them.
- [reports/v1_baseline.md](reports/v1_baseline.md) — latest backtest results.

## Run

    uv sync
    uv run python -m tradeup.run --refresh   # download prices, then backtest
    uv run python -m tradeup.filings         # download company announcements (about an hour, resumable)
    uv run python -m tradeup.run             # backtest on saved prices and filings
    uv run pytest -q

## Layout

| File | Job |
|---|---|
| `tradeup/universe.py` | About 750 candidate stocks with industries from NSE, and which 200 were most traded on each past date |
| `tradeup/prices.py` | Adjusted daily prices from Yahoo Finance into `data/prices.parquet` |
| `tradeup/features.py` | Price and volume features |
| `tradeup/filings.py` | NSE company announcements with publication times; count and tone features |
| `tradeup/graph.py` | Residual-correlation graph and neighbour averages |
| `tradeup/dataset.py` | One row per rebalance date and stock: features and the following return |
| `tradeup/model.py` | Walk-forward training and scoring |
| `tradeup/backtest.py` | Top-N portfolio, costs, statistics |
| `tradeup/run.py` | Runs all of the above and writes the report |

## Known limits of v1

- Candidates are stocks listed today. A stock that shrank is still included
  in the years it was large, but a stock that was delisted is missing
  entirely, so absolute returns are still somewhat too high.
- Prices come from Yahoo Finance, not yet cross-checked against Angel One.
- Filing tone is a word list, not a language model. Treat it as a placeholder.
- No general news yet, only exchange filings.
- Data from 2025-10-01 onwards is held back for one final test.
