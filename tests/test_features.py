import numpy as np
import pandas as pd

from tradeup.features import price_features, sector_relative


def frames(seed=0, days=320, n=4):
    rng = np.random.default_rng(seed)
    idx = pd.bdate_range("2020-01-01", periods=days)
    cols = [f"S{i}" for i in range(n)]
    close = pd.DataFrame(
        100 * np.exp(rng.normal(0, 0.02, (days, n)).cumsum(axis=0)),
        index=idx,
        columns=cols,
    )
    volume = pd.DataFrame(
        rng.integers(1_000, 9_000, (days, n)).astype(float), index=idx, columns=cols
    )
    return close, close * 1.01, close * 0.99, volume


def test_ret_5_matches_handmade_series():
    idx = pd.bdate_range("2021-01-01", periods=10)
    close = pd.DataFrame({"A": np.arange(100.0, 110.0)}, index=idx)
    vol = pd.DataFrame({"A": np.full(10, 5000.0)}, index=idx)
    out = price_features(close, close * 1.01, close * 0.99, vol)
    expected = close["A"] / close["A"].shift(5) - 1
    pd.testing.assert_series_equal(out["ret_5"]["A"], expected, check_names=False)


def test_mom_12_1_ignores_latest_21_days():
    close, high, low, volume = frames()
    before = price_features(close, high, low, volume)["mom_12_1"]
    changed = close.copy()
    changed.iloc[-21:] *= 2.0
    after = price_features(changed, high, low, volume)["mom_12_1"]
    pd.testing.assert_frame_equal(before, after)


def test_no_look_ahead():
    close, high, low, volume = frames()
    t = 300
    before = price_features(close, high, low, volume)
    changed = [f.copy() for f in (close, high, low, volume)]
    for f in changed:
        f.iloc[t + 1 :] *= 3.0
    after = price_features(*changed)
    for name in before:
        pd.testing.assert_series_equal(before[name].iloc[t], after[name].iloc[t])


def test_zero_volume_gives_nan_liquidity():
    close, high, low, volume = frames(days=60, n=2)
    volume[:] = 0.0
    liq = price_features(close, high, low, volume)["liquidity"]
    assert liq.iloc[-1].isna().all()
    assert not bool(((liq == np.inf) | (liq == -np.inf)).sum().sum())


def test_sector_relative_zero_mean_within_sector():
    rng = np.random.default_rng(3)
    idx = pd.bdate_range("2021-01-01", periods=8)
    cols = list("ABCDEF")
    frame = pd.DataFrame(rng.normal(size=(8, 6)), index=idx, columns=cols)
    sectors = pd.Series({"A": "x", "B": "x", "C": "y", "D": "y", "E": "z", "F": "z"})
    out = sector_relative(frame, sectors)
    for sec in sectors.unique():
        members = sectors[sectors == sec].index.tolist()
        got = out[members].mean(axis=1)
        pd.testing.assert_series_equal(
            got, pd.Series(0.0, index=idx), check_names=False
        )


def test_dist_to_high_low_bounded():
    close, high, low, volume = frames()
    out = price_features(close, high, low, volume)
    assert bool((out["dist_high"].dropna() <= 0).all().all())
    assert bool((out["dist_low"].dropna() >= 0).all().all())
