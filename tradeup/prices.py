"""Daily prices from Yahoo Finance, adjusted for splits, bonuses and dividends."""

import pandas as pd
import yfinance as yf

from .config import DATA, START

INDEX = "NIFTY"
PATH = DATA / "prices.parquet"


def download(symbols: list[str], start: str = START) -> pd.DataFrame:
    tickers = {f"{s}.NS": s for s in symbols} | {"^NSEI": INDEX}
    raw = yf.download(list(tickers), start=start, auto_adjust=True, progress=False, threads=True)
    long = raw.stack(level=1, future_stack=True).rename_axis(["date", "symbol"]).reset_index()
    long.columns = [c.lower() for c in long.columns]
    long["symbol"] = long["symbol"].map(tickers)
    long = long.dropna(subset=["close"])[["date", "symbol", "open", "high", "low", "close", "volume"]]
    DATA.mkdir(exist_ok=True)
    long.to_parquet(PATH, index=False)
    return long


def load() -> pd.DataFrame:
    return pd.read_parquet(PATH)


def wide(prices: pd.DataFrame, field: str) -> pd.DataFrame:
    """One column per symbol, one row per trading day."""
    return prices.pivot(index="date", columns="symbol", values=field).sort_index()
