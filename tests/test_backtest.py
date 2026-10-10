import pandas as pd
import pytest

from tradeup.backtest import (
    PERIODS_PER_YEAR,
    bucket_returns,
    buffered_weights,
    net_returns,
    rank_ic,
    stats,
    top_n_weights,
    turnover,
)


def scores_frame():
    dates = pd.to_datetime(["2021-01-01", "2021-01-08"])
    symbols = list("ABCDE")
    idx = pd.MultiIndex.from_product([dates, symbols], names=["date", "symbol"])
    return pd.Series([5, 4, 3, 2, 1, 1, 2, 3, 4, 5], index=idx)


def weights_frame():
    idx = pd.to_datetime(["2021-01-01", "2021-01-08", "2021-01-15"])
    return pd.DataFrame(
        {"A": [0.5, 0.5, 0.5], "B": [0.5, 0.5, 0.5]}, index=idx
    )


def test_top_n_picks_highest_and_sums_to_one():
    w = top_n_weights(scores_frame(), n=2)
    assert bool(((w.sum(axis=1) - 1).abs() < 1e-12).all())
    assert bool(((w > 0).sum(axis=1) == 2).all())
    day1 = pd.Timestamp("2021-01-01")
    day2 = pd.Timestamp("2021-01-08")
    assert w.loc[day1, "A"] == 0.5 and w.loc[day1, "B"] == 0.5
    assert w.loc[day1, "C"] == 0 and w.loc[day1, "E"] == 0
    assert w.loc[day2, "D"] == 0.5 and w.loc[day2, "E"] == 0.5
    assert w.loc[day2, "A"] == 0 and w.loc[day2, "B"] == 0


def test_net_returns_zero_cost_is_mean_forward():
    w = weights_frame()
    fwd = pd.DataFrame(
        {"A": [0.02, 0.04, -0.01], "B": [0.06, 0.00, 0.03]}, index=w.index
    )
    got = net_returns(w, fwd, cost=0.0)
    pd.testing.assert_series_equal(got, fwd.mean(axis=1), check_names=False)


def test_net_returns_first_period_charged_then_free():
    w = weights_frame()
    fwd = pd.DataFrame(0.01, index=w.index, columns=w.columns)
    cost = 0.01
    got = net_returns(w, fwd, cost=cost)
    assert got.iloc[0] == pytest.approx(0.01 - cost * 1.0)
    pd.testing.assert_series_equal(
        got.iloc[1:], pd.Series(0.01, index=w.index[1:]), check_names=False
    )


def test_turnover_constant_zero_full_replace_one():
    idx = pd.to_datetime(["2021-01-01", "2021-01-08", "2021-01-15"])
    const = pd.DataFrame(
        {"A": [1.0, 1.0, 1.0], "B": [0.0, 0.0, 0.0]}, index=idx
    )
    assert turnover(const) == 0.0
    flip = pd.DataFrame(
        {"A": [1.0, 0.0, 1.0], "B": [0.0, 1.0, 0.0]}, index=idx
    )
    assert turnover(flip) == pytest.approx(1.0)


def test_stats_constant_positive_return():
    out = stats(pd.Series([0.01] * 10))
    assert out["max_drawdown"] == 0.0
    assert out["cagr"] == pytest.approx(1.01**PERIODS_PER_YEAR - 1)


def test_stats_known_drop_drawdown():
    out = stats(pd.Series([0.0, 0.0, -0.5, 0.0, 0.0]))
    assert out["max_drawdown"] == pytest.approx(-0.5)


def test_rank_ic_perfect_and_reversed():
    dates = pd.to_datetime(["2021-01-01", "2021-01-08"])
    symbols = list("ABCD")
    idx = pd.MultiIndex.from_product([dates, symbols], names=["date", "symbol"])
    scores = pd.Series([1.0, 2.0, 3.0, 4.0] * 2, index=idx)
    same = pd.Series([10.0, 20.0, 30.0, 40.0] * 2, index=idx)
    rev = pd.Series([40.0, 30.0, 20.0, 10.0] * 2, index=idx)
    assert bool(((rank_ic(scores, same) - 1.0).abs() < 1e-12).all())
    assert bool(((rank_ic(scores, rev) + 1.0).abs() < 1e-12).all())


def buffered_scores():
    dates = pd.to_datetime(["2021-01-01", "2021-01-08", "2021-01-15"])
    symbols = list("ABCDE")
    idx = pd.MultiIndex.from_product([dates, symbols], names=["date", "symbol"])
    # Day 1: A B top; day 2: C D top with A slipping to 3rd, B to 4th;
    # day 3 repeats day 2 so holdings settle.
    vals = [5, 4, 3, 2, 1, 3, 2, 5, 4, 1, 3, 2, 5, 4, 1]
    return pd.Series(vals, index=idx)


def test_buffered_first_date_top_n_and_rows_sum():
    w = buffered_weights(buffered_scores(), n=2, exit_rank=3)
    day1 = pd.Timestamp("2021-01-01")
    assert w.loc[day1, "A"] == 0.5 and w.loc[day1, "B"] == 0.5
    assert bool(((w.sum(axis=1) - 1).abs() < 1e-12).all())
    assert bool(((w > 0).sum(axis=1) == 2).all())


def test_buffered_keeps_within_buffer_sells_below():
    w = buffered_weights(buffered_scores(), n=2, exit_rank=3)
    day2 = pd.Timestamp("2021-01-08")
    assert w.loc[day2, "A"] == 0.5  # rank 3: between n+1 and exit_rank, kept
    assert w.loc[day2, "B"] == 0  # rank 4: below exit_rank, sold
    assert w.loc[day2, "C"] == 0.5  # best not held replaces B


def test_buffered_drops_missing_score():
    dates = pd.to_datetime(["2021-01-01", "2021-01-08"])
    symbols = list("ABC")
    idx = pd.MultiIndex.from_product([dates, symbols], names=["date", "symbol"])
    scores = pd.Series([3.0, 2.0, 1.0, float("nan"), 3.0, 2.0], index=idx)
    w = buffered_weights(scores, n=2, exit_rank=3)
    day2 = pd.Timestamp("2021-01-08")
    assert w.loc[day2, "A"] == 0
    assert bool(((w.loc[day2] > 0).sum() == 2))


def test_buffered_matches_top_n_when_exit_equals_n():
    w = buffered_weights(buffered_scores(), n=2, exit_rank=2)
    t = top_n_weights(buffered_scores(), n=2)
    pd.testing.assert_frame_equal(
        w.reindex(columns=t.columns, fill_value=0.0), t, check_dtype=False
    )


def test_bucket_returns_rise_with_score_and_index():
    dates = pd.to_datetime(["2021-01-01", "2021-01-08", "2021-01-15"])
    symbols = [f"S{i}" for i in range(10)]
    idx = pd.MultiIndex.from_product([dates, symbols], names=["date", "symbol"])
    scores = pd.Series([float(i) for _ in dates for i in range(10)], index=idx)
    fwd = pd.Series([float(i) * 0.01 for _ in dates for i in range(10)], index=idx)
    got = bucket_returns(scores, fwd, buckets=5)
    assert list(got.index) == [1, 2, 3, 4, 5]
    assert bool((got.diff().dropna() > 0).all())
