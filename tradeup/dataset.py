"""One row per (rebalance date, stock): features known at that day's close, and the return that follows."""

import pandas as pd

from .config import GRAPH_K, GRAPH_WINDOW, HORIZON
from .features import price_features, sector_relative
from .graph import neighbours, peer_mean, residual_returns
from .prices import INDEX, wide

PRICE = ["ret_5", "ret_21", "ret_63", "ret_126", "mom_12_1", "vol_21", "vol_63",
         "volume_ratio", "dist_high", "dist_low", "liquidity",
         "ret_5_sec", "ret_21_sec", "ret_63_sec"]
PEER = ["peer_ret_5", "peer_ret_21", "gap_ret_5", "gap_ret_21"]


def forward_return(open_: pd.DataFrame, horizon: int = HORIZON) -> pd.DataFrame:
    """Buy at the next day's open, sell at the open `horizon` days after that."""
    return open_.shift(-(horizon + 1)) / open_.shift(-1) - 1


def build(prices: pd.DataFrame, sectors: pd.Series) -> tuple[pd.DataFrame, pd.Series]:
    """Returns (rows indexed by date and symbol, index forward return per date)."""
    stocks = prices[prices["symbol"] != INDEX]
    close, high, low, volume, open_ = (wide(stocks, f) for f in ("close", "high", "low", "volume", "open"))
    index_open = wide(prices[prices["symbol"] == INDEX], "open").reindex(close.index).ffill()

    feats = price_features(close, high, low, volume)
    for n in (5, 21, 63):
        feats[f"ret_{n}_sec"] = sector_relative(feats[f"ret_{n}"], sectors)
    resid = residual_returns(close.pct_change(fill_method=None), sectors)
    fwd = forward_return(open_)

    rows = []
    for i in range(252, len(close), HORIZON):
        day = close.index[i]
        row = pd.DataFrame({k: v.iloc[i] for k, v in feats.items()})
        adj = neighbours(resid.iloc[i - GRAPH_WINDOW + 1 : i + 1], GRAPH_K)
        for n in (5, 21):
            row[f"peer_ret_{n}"] = peer_mean(adj, row[f"ret_{n}"])
            row[f"gap_ret_{n}"] = row[f"ret_{n}"] - row[f"peer_ret_{n}"]
        row["fwd"] = fwd.iloc[i]
        row = row[row["ret_63"].notna()]
        rows.append(pd.concat({day: row}, names=["date", "symbol"]))
    data = pd.concat(rows)

    # Rank within each day: the model compares stocks with each other, not days with each other.
    by_day = data.groupby(level="date")
    data[PRICE + PEER] = by_day[PRICE + PEER].rank(pct=True)
    data["target"] = by_day["fwd"].rank(pct=True)
    return data, forward_return(index_open)[INDEX].reindex(data.index.unique("date"))
