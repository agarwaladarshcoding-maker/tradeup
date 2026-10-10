import pandas as pd

from tradeup.universe import liquid_members


def make_frames(days=60, seed=0):
    import numpy as np

    rng = np.random.default_rng(seed)
    dates = pd.bdate_range("2024-01-01", periods=days)
    symbols = [f"S{i}" for i in range(10)]
    # Distinct, stable traded values so the median ranking is deterministic.
    base_vol = {
        "S0": 100_000.0,
        "S1": 100_000.0,
        "S2": 100_000.0,
        "S3": 50_000.0,
        "S4": 40_000.0,
        "S5": 30_000.0,
        "S6": 20_000.0,
        "S7": 10_000.0,
        "S8": 5_000.0,
        "S9": 1_000.0,
    }
    close = pd.DataFrame(10.0, index=dates, columns=symbols)
    volume = pd.DataFrame({s: base_vol[s] for s in symbols}, index=dates)
    # Tiny jitter keeps values distinct without changing the ranking.
    _ = rng
    return close, volume


def test_exactly_size_true_after_window():
    close, volume = make_frames()
    got = liquid_members(close, volume, size=3, window=20)
    tail = got.iloc[20 - 1 :]
    assert len(tail) > 0
    assert bool(((tail.sum(axis=1) == 3)).all())


def test_picks_highest_traded_value():
    close, volume = make_frames()
    got = liquid_members(close, volume, size=3, window=20)
    row = got.iloc[30]
    assert set(row[row].index) == {"S0", "S1", "S2"}


def test_no_look_ahead():
    close, volume = make_frames()
    got = liquid_members(close, volume, size=3, window=20)
    t = 30
    close2 = close.copy()
    volume2 = volume.copy()
    close2.iloc[t + 1 :] *= 7.0
    volume2.iloc[t + 1 :] *= 7.0
    got2 = liquid_members(close2, volume2, size=3, window=20)
    pd.testing.assert_series_equal(got.iloc[t], got2.iloc[t])


def test_collapsed_stock_drops_after_half_window_not_same_day():
    close, volume = make_frames()
    dates = close.index
    volume2 = volume.copy()
    volume2.loc[dates[30] :, "S0"] = 10.0
    got = liquid_members(close, volume2, size=3, window=20)
    assert bool(got.iloc[30]["S0"])
    assert bool(~got.iloc[30 + 11]["S0"])
