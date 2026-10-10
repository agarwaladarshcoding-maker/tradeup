"""One row per (rebalance date, stock): features known at that day's close, and the return that follows."""

import pandas as pd

from .config import GRAPH_K, GRAPH_WINDOW, HORIZON
from .features import price_features, sector_relative
from .filings import filing_features
from .graph import neighbours, peer_mean, residual_returns
from .prices import INDEX, wide
from .universe import liquid_members

PRICE = ["ret_5", "ret_21", "ret_63", "ret_126", "mom_12_1", "vol_21", "vol_63",
         "volume_ratio", "dist_high", "dist_low", "liquidity",
         "ret_5_sec", "ret_21_sec", "ret_63_sec"]
PEER = ["peer_ret_5", "peer_ret_21", "gap_ret_5", "gap_ret_21"]
FILING = ["fil_count_5", "fil_abnormal", "fil_tone_5", "fil_tone_21"]
FILING_PEER = [f"{kind}_{name}" for kind in ("peer", "gap") for name in ("abnormal", "tone_5", "tone_21")]


def forward_return(open_: pd.DataFrame, horizon: int = HORIZON) -> pd.DataFrame:
    """Buy at the next day's open, sell at the open `horizon` days after that."""
    return open_.shift(-(horizon + 1)) / open_.shift(-1) - 1


def build(
    prices: pd.DataFrame, sectors: pd.Series, filings: pd.DataFrame | None = None
) -> tuple[pd.DataFrame, pd.Series]:
    """Returns (rows indexed by date and symbol, index forward return per date).

    Each date holds only the stocks in the universe on that date; sector
    averages and graph neighbours are taken among those stocks.
    """
    stocks = prices[prices["symbol"] != INDEX]
    close, high, low, volume, open_ = (wide(stocks, f) for f in ("close", "high", "low", "volume", "open"))
    index_open = wide(prices[prices["symbol"] == INDEX], "open").reindex(close.index).ffill()

    feats = price_features(close, high, low, volume)
    events = filing_features(filings, close.index, close.columns) if filings is not None else {}
    returns = close.pct_change(fill_method=None)
    members = liquid_members(close, volume)
    fwd = forward_return(open_)

    rows = []
    for i in range(252, len(close), HORIZON):
        day = close.index[i]
        held = members.columns[members.iloc[i] & feats["ret_63"].iloc[i].notna()]
        row = pd.DataFrame({k: v.iloc[i][held] for k, v in (feats | events).items()})
        for n in (5, 21, 63):
            row[f"ret_{n}_sec"] = sector_relative(feats[f"ret_{n}"].iloc[[i]][held], sectors).iloc[0]
        window = returns.iloc[i - GRAPH_WINDOW + 1 : i + 1][held]
        adj = neighbours(residual_returns(window, sectors), GRAPH_K)
        for name in ["ret_5", "ret_21"] + [k for k in events if k != "fil_count_5"]:
            short = name.removeprefix("fil_")
            row[f"peer_{short}"] = peer_mean(adj, row[name])
            row[f"gap_{short}"] = row[name] - row[f"peer_{short}"]
        row["fwd"] = fwd.iloc[i][held]
        rows.append(pd.concat({day: row}, names=["date", "symbol"]))
    data = pd.concat(rows)

    # Rank within each day: the model compares stocks with each other, not days with each other.
    ranked = [c for c in data.columns if c != "fwd"]
    by_day = data.groupby(level="date")
    data[ranked] = by_day[ranked].rank(pct=True)
    data["target"] = by_day["fwd"].rank(pct=True)
    return data, forward_return(index_open)[INDEX].reindex(data.index.unique("date"))
