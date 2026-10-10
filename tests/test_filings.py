import pandas as pd

from tradeup.filings import daily, filing_features, tone


def test_tone_positive_negative_neutral():
    frame = pd.DataFrame(
        {
            "category": ["Updates", "Updates", "Updates"],
            "text": ["receipt of order for turbines", "resignation of director", "quarterly results presentation"],
        }
    )
    got = tone(frame)
    assert list(got) == [1, -1, 0]


def test_tone_disclosure_does_not_match_closure():
    frame = pd.DataFrame({"category": ["Disclosure under Regulation 30"], "text": ["x"]})
    assert list(tone(frame)) == [0]


def test_tone_handles_none():
    frame = pd.DataFrame({"category": [None, "Updates"], "text": ["resignation", None]})
    got = tone(frame)
    assert list(got) == [-1, 0]


def test_afternoon_filing_counts_next_day():
    days = pd.bdate_range("2024-01-01", periods=5)  # Mon..Fri
    symbols = pd.Index(["A", "B"])
    f = pd.DataFrame(
        {
            "symbol": ["A", "A"],
            "time": pd.to_datetime(["2024-01-02 14:00", "2024-01-02 16:00"]),
            "category": ["Updates", "Updates"],
            "text": ["x", "y"],
        }
    )
    count = daily(f, days, symbols)["count"]
    assert count.loc["2024-01-02", "A"] == 1
    assert count.loc["2024-01-03", "A"] == 1
    assert count["B"].sum() == 0


def test_saturday_filing_counts_monday():
    days = pd.bdate_range("2024-01-01", periods=10)
    symbols = pd.Index(["A"])
    f = pd.DataFrame(
        {
            "symbol": ["A"],
            "time": pd.to_datetime(["2024-01-06 10:00"]),
            "category": ["Updates"],
            "text": ["x"],
        }
    )
    count = daily(f, days, symbols)["count"]
    assert count.loc["2024-01-08", "A"] == 1
    assert count["A"].sum() == 1


def test_trading_window_filing_not_counted():
    days = pd.bdate_range("2024-01-01", periods=5)
    symbols = pd.Index(["A"])
    f = pd.DataFrame(
        {
            "symbol": ["A"],
            "time": pd.to_datetime(["2024-01-02 10:00"]),
            "category": ["Intimation of Trading Window Closure"],
            "text": ["x"],
        }
    )
    out = daily(f, days, symbols)
    assert out["count"]["A"].sum() == 0
    assert out["tone"]["A"].sum() == 0


def test_daily_drops_late_and_unknown_symbol_and_shape():
    days = pd.bdate_range("2024-01-01", periods=5)
    symbols = pd.Index(["A", "B"])
    f = pd.DataFrame(
        {
            "symbol": ["A", "ZZZ", "A"],
            "time": pd.to_datetime(["2024-01-02 10:00", "2024-01-02 10:00", "2024-02-01 10:00"]),
            "category": ["Updates", "Updates", "Updates"],
            "text": ["x", "y", "z"],
        }
    )
    out = daily(f, days, symbols)
    for key in ("count", "tone"):
        pd.testing.assert_index_equal(out[key].index, days)
        assert list(out[key].columns) == ["A", "B"]
    assert out["count"].loc["2024-01-02", "A"] == 1
    assert out["count"]["B"].sum() == 0
    assert out["count"].values.sum() == 1


def test_filing_features_count_5_rolling():
    days = pd.bdate_range("2024-01-01", periods=10)
    symbols = pd.Index(["A", "B"])
    times = [(d + pd.Timedelta(hours=10)).strftime("%Y-%m-%d %H:%M") for d in days[:5]]
    f = pd.DataFrame(
        {
            "symbol": ["A"] * 5,
            "time": pd.to_datetime(times),
            "category": ["Updates"] * 5,
            "text": ["x"] * 5,
        }
    )
    feats = filing_features(f, days, symbols)
    assert feats["fil_count_5"].loc[days[4], "A"] == 5
    assert feats["fil_count_5"].loc[days[5], "A"] == 4


def test_filing_features_nan_before_first_filing():
    days = pd.bdate_range("2024-01-01", periods=10)
    symbols = pd.Index(["A", "B"])
    f = pd.DataFrame(
        {
            "symbol": ["A"],
            "time": pd.to_datetime(["2024-01-04 10:00"]),
            "category": ["Updates"],
            "text": ["x"],
        }
    )
    feats = filing_features(f, days, symbols)
    for key, frame in feats.items():
        assert bool(frame.loc[days[:3], "A"].isna().all().all())
        assert bool(frame["B"].isna().all())


def test_filing_features_no_look_ahead():
    days = pd.bdate_range("2024-01-01", periods=10)
    symbols = pd.Index(["A"])
    base = pd.DataFrame(
        {
            "symbol": ["A", "A"],
            "time": pd.to_datetime(["2024-01-02 10:00", "2024-01-03 10:00"]),
            "category": ["Updates", "Updates"],
            "text": ["x", "y"],
        }
    )
    t = days[4]
    before = filing_features(base, days, symbols)
    extra = pd.concat(
        [
            base,
            pd.DataFrame(
                {
                    "symbol": ["A"],
                    "time": pd.to_datetime(["2024-01-09 10:00"]),
                    "category": ["Updates"],
                    "text": ["later"],
                }
            ),
        ],
        ignore_index=True,
    )
    after = filing_features(extra, days, symbols)
    for key in before:
        pd.testing.assert_series_equal(before[key].loc[t], after[key].loc[t], check_names=False)
