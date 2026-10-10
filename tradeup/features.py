"""Price and volume features. Every value on day t uses data up to day t only."""

import numpy as np
import pandas as pd


def price_features(
    close: pd.DataFrame, high: pd.DataFrame, low: pd.DataFrame, volume: pd.DataFrame
) -> dict[str, pd.DataFrame]:
    daily = close.pct_change(fill_method=None)
    f = {f"ret_{n}": close / close.shift(n) - 1 for n in (5, 21, 63, 126)}
    f["mom_12_1"] = close.shift(21) / close.shift(252) - 1  # skips the latest month
    f["vol_21"] = daily.rolling(21).std()
    f["vol_63"] = daily.rolling(63).std()
    f["volume_ratio"] = volume.rolling(5).mean() / volume.rolling(63).mean()
    f["dist_high"] = close / high.rolling(252).max() - 1
    f["dist_low"] = close / low.rolling(252).min() - 1
    traded = (close * volume).rolling(21).mean()
    f["liquidity"] = np.log(traded.where(traded > 0))
    return {k: v.replace([np.inf, -np.inf], np.nan) for k, v in f.items()}


def group_mean(frame: pd.DataFrame, groups: pd.Series) -> pd.DataFrame:
    """Each cell replaced by the same-day mean of its column's group."""
    return frame.T.groupby(groups.reindex(frame.columns)).transform("mean").T


def sector_relative(frame: pd.DataFrame, sectors: pd.Series) -> pd.DataFrame:
    return frame - group_mean(frame, sectors)
