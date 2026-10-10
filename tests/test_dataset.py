import numpy as np
import pandas as pd

from tradeup.dataset import FILING, FILING_PEER, PEER, PRICE, build, forward_return
from tradeup.prices import INDEX


def make_prices(seed=0, days=400, n_symbols=12):
    rng = np.random.default_rng(seed)
    dates = pd.bdate_range("2018-01-01", periods=days)
    symbols = [f"S{i:02d}" for i in range(n_symbols)]
    sectors = pd.Series({s: f"sec{i % 3}" for i, s in enumerate(symbols)})
    frames = []
    for s in symbols + [INDEX]:
        walk = 100 * np.exp(rng.normal(0, 0.01, days).cumsum())
        opens = walk * (1 + rng.normal(0, 0.001, days))
        frames.append(
            pd.DataFrame(
                {
                    "date": dates,
                    "symbol": s,
                    "open": opens,
                    "high": walk * 1.01,
                    "low": walk * 0.99,
                    "close": walk,
                    "volume": rng.integers(10_000, 100_000, days).astype(float),
                }
            )
        )
    return pd.concat(frames, ignore_index=True), sectors


def open_frame(seed=0, days=12):
    rng = np.random.default_rng(seed)
    idx = pd.bdate_range("2021-01-01", periods=days)
    return pd.DataFrame(
        rng.uniform(90, 110, (days, 2)), index=idx, columns=["A", "B"]
    )


def test_forward_return_formula():
    open_ = open_frame()
    h = 5
    got = forward_return(open_, horizon=h)
    t = 2
    expected = open_.iloc[t + 1 + h] / open_.iloc[t + 1] - 1
    pd.testing.assert_series_equal(got.iloc[t], expected, check_names=False)


def test_forward_return_trailing_rows_nan():
    open_ = open_frame()
    h = 5
    got = forward_return(open_, horizon=h)
    assert bool(got.iloc[-(h + 1) :].isna().all().all())
    assert bool(got.iloc[: -(h + 1)].notna().all().all())


def test_build_structure_columns_and_symbols():
    prices, sectors = make_prices()
    data, index_fwd = build(prices, sectors)
    assert list(data.index.names) == ["date", "symbol"]
    assert INDEX not in data.index.unique("symbol").tolist()
    for col in PRICE + PEER + ["fwd", "target"]:
        assert col in data.columns
    assert len(index_fwd) == len(data.index.unique("date"))


def test_build_feature_ranks_in_unit_interval():
    prices, sectors = make_prices()
    data, _ = build(prices, sectors)
    vals = data[PRICE + PEER].stack()
    assert len(vals) > 0
    assert bool(((vals > 0) & (vals <= 1)).all())


def test_build_dates_five_days_apart():
    prices, sectors = make_prices()
    data, _ = build(prices, sectors)
    dates = data.index.unique("date").sort_values()
    assert len(dates) > 2
    gaps = [
        np.busday_count(d1.date(), d2.date())
        for d1, d2 in zip(dates[:-1], dates[1:])
    ]
    assert all(g == 5 for g in gaps)


def test_build_no_look_ahead():
    prices, sectors = make_prices()
    data, _ = build(prices, sectors)
    d = data.index.unique("date").sort_values()[1]
    bumped = prices.copy()
    after = bumped["date"] > d
    for col in ("open", "high", "low", "close", "volume"):
        bumped.loc[after, col] *= 2.5
    data2, _ = build(bumped, sectors)
    pd.testing.assert_frame_equal(data.loc[d, PRICE + PEER], data2.loc[d, PRICE + PEER])


def make_filings(times, symbols=("S00", "S01")):
    return pd.DataFrame(
        {
            "symbol": [symbols[i % len(symbols)] for i in range(len(times))],
            "time": pd.to_datetime(times),
            "category": ["Updates"] * len(times),
            "text": ["receipt of order"] * len(times),
        }
    )


def test_build_without_filings_has_no_filing_columns():
    prices, sectors = make_prices()
    data, _ = build(prices, sectors, filings=None)
    assert not any(
        c.startswith("fil_") or c.startswith("peer_abnormal") or c.startswith("peer_tone")
        for c in data.columns
    )


def test_build_with_filings_has_filing_columns():
    prices, sectors = make_prices()
    filings = make_filings(["2018-06-01 10:00", "2018-07-02 10:00", "2018-08-01 10:00"])
    data, _ = build(prices, sectors, filings=filings)
    for col in FILING + FILING_PEER:
        assert col in data.columns


def test_build_filings_no_look_ahead():
    prices, sectors = make_prices()
    probe, _ = build(prices, sectors)
    d = probe.index.unique("date").sort_values()[1]
    stamp = lambda dt: (d + dt).strftime("%Y-%m-%d %H:%M")
    base = make_filings([stamp(pd.Timedelta(days=-7)), stamp(pd.Timedelta(days=-6))])
    data, _ = build(prices, sectors, filings=base)
    extra = pd.concat(
        [base, make_filings([stamp(pd.Timedelta(days=+7))])], ignore_index=True
    )
    data2, _ = build(prices, sectors, filings=extra)
    pd.testing.assert_frame_equal(data.loc[d, FILING], data2.loc[d, FILING])
