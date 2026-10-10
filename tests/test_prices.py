import pandas as pd

from tradeup.prices import wide


def long_frame(shuffled=False):
    df = pd.DataFrame(
        {
            "date": pd.to_datetime(
                ["2021-01-01", "2021-01-01", "2021-01-02", "2021-01-02"]
            ),
            "symbol": ["A", "B", "A", "B"],
            "close": [100.0, 200.0, 101.0, 202.0],
        }
    )
    if shuffled:
        df = df.iloc[[2, 0, 3, 1]].reset_index(drop=True)
    return df


def test_wide_pivots_values():
    got = wide(long_frame(), "close")
    assert got.loc[pd.Timestamp("2021-01-01"), "A"] == 100.0
    assert got.loc[pd.Timestamp("2021-01-01"), "B"] == 200.0
    assert got.loc[pd.Timestamp("2021-01-02"), "A"] == 101.0
    assert got.loc[pd.Timestamp("2021-01-02"), "B"] == 202.0


def test_wide_sorts_dates():
    got = wide(long_frame(shuffled=True), "close")
    assert got.index.is_monotonic_increasing
    assert got.index.tolist() == [
        pd.Timestamp("2021-01-01"),
        pd.Timestamp("2021-01-02"),
    ]


def test_wide_one_column_per_symbol():
    got = wide(long_frame(), "close")
    assert sorted(got.columns.tolist()) == ["A", "B"]
    assert len(got) == 2


def test_wide_missing_value_is_nan():
    df = pd.DataFrame(
        {
            "date": pd.to_datetime(["2021-01-01", "2021-01-02", "2021-01-02"]),
            "symbol": ["A", "A", "B"],
            "close": [100.0, 101.0, 202.0],
        }
    )
    got = wide(df, "close")
    assert pd.isna(got.loc[pd.Timestamp("2021-01-01"), "B"])
    assert got.loc[pd.Timestamp("2021-01-02"), "B"] == 202.0
