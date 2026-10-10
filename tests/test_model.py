import pandas as pd

from tradeup.model import GAP, split, walk_forward


def test_split_test_mask_is_exactly_that_year():
    dates = pd.DatetimeIndex(pd.date_range("2018-01-01", "2020-12-31", freq="D"))
    _, test = split(dates, 2020)
    assert bool((dates[test].year == 2020).all())
    assert int(test.sum()) == int((dates.year == 2020).sum())


def test_split_train_keeps_21_day_gap():
    dates = pd.DatetimeIndex(pd.date_range("2018-01-01", "2020-12-31", freq="D"))
    train, _ = split(dates, 2020)
    start = pd.Timestamp(2020, 1, 1)
    assert bool(((start - dates[train]) >= GAP).all())
    assert bool((dates[train] < start - GAP).all())


def make_frame(seed=0):
    import numpy as np

    rng = np.random.default_rng(seed)
    dates = pd.date_range("2019-01-02", "2021-12-29", freq="W-WED")
    symbols = [f"S{i:02d}" for i in range(30)]
    idx = pd.MultiIndex.from_product([dates, symbols], names=["date", "symbol"])
    return pd.DataFrame(
        {
            "f1": rng.normal(size=len(idx)),
            "f2": rng.normal(size=len(idx)),
            "target": rng.uniform(size=len(idx)),
        },
        index=idx,
    )


def test_walk_forward_only_test_years_and_aligned():
    data = make_frame()
    scores = walk_forward(data, ["f1", "f2"], first_year=2020)
    assert set(scores.index.get_level_values("date").year) <= {2020, 2021}
    assert bool(scores.index.isin(data.index).all())
    assert list(scores.index.names) == ["date", "symbol"]
    n_expected = int((data.index.get_level_values("date").year >= 2020).sum())
    assert len(scores) == n_expected


def test_walk_forward_deterministic():
    data = make_frame()
    first = walk_forward(data, ["f1", "f2"], first_year=2020)
    second = walk_forward(data, ["f1", "f2"], first_year=2020)
    pd.testing.assert_series_equal(first, second)
