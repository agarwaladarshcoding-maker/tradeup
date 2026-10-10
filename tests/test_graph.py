import numpy as np
import pandas as pd

from tradeup.graph import neighbours, peer_mean, residual_returns


def returns_frame(seed=1, days=80, n=6):
    rng = np.random.default_rng(seed)
    idx = pd.bdate_range("2021-01-01", periods=days)
    cols = [f"S{i}" for i in range(n)]
    return pd.DataFrame(rng.normal(0, 0.01, (days, n)), index=idx, columns=cols)


def sectors_for(n=6):
    cols = [f"S{i}" for i in range(n)]
    return pd.Series({c: ("a" if i % 2 == 0 else "b") for i, c in enumerate(cols)})


def correlated_window(seed=7, days=100):
    rng = np.random.default_rng(seed)
    idx = pd.bdate_range("2021-01-01", periods=days)
    base = rng.normal(0, 0.01, days)
    return pd.DataFrame(
        {
            "A": base + rng.normal(0, 0.0005, days),
            "B": base + rng.normal(0, 0.0005, days),
            "C": -base + rng.normal(0, 0.0005, days),
            "D": rng.normal(0, 0.01, days),
            "E": rng.normal(0, 0.01, days),
        },
        index=idx,
    )


def test_residual_returns_sum_to_zero_within_sector():
    rets = returns_frame()
    sectors = sectors_for()
    resid = residual_returns(rets, sectors)
    for day in (resid.index[:5].tolist() + [resid.index[-1]]):
        for sec in sectors.unique():
            members = sectors[sectors == sec].index.tolist()
            assert abs(resid.loc[day, members].sum()) < 1e-12


def test_neighbours_row_sums_diagonal_and_degree():
    adj = neighbours(returns_frame(), k=2)
    assert bool((adj.to_numpy().diagonal() == 0).all())
    assert bool(((adj > 0).sum(axis=1) <= 2).all())
    sums = adj.sum(axis=1)
    assert bool((((sums - 1).abs() < 1e-12) | (sums == 0)).all())


def test_correlated_pair_are_neighbours():
    adj = neighbours(correlated_window(), k=2)
    assert adj.loc["A", "B"] > 0
    assert adj.loc["B", "A"] > 0


def test_negatively_correlated_pair_are_not_neighbours():
    adj = neighbours(correlated_window(), k=2)
    assert adj.loc["A", "C"] == 0
    assert adj.loc["C", "A"] == 0


def test_peer_mean_skips_nan_neighbours():
    adj = pd.DataFrame({"X": [0.0], "Y": [0.5], "Z": [0.5]}, index=["S"])
    values = pd.Series({"X": 99.0, "Y": 1.0, "Z": np.nan})
    assert peer_mean(adj, values).loc["S"] == 1.0


def test_peer_mean_nan_when_no_neighbours():
    adj = pd.DataFrame({"X": [0.0], "Y": [0.0]}, index=["S"])
    values = pd.Series({"X": 1.0, "Y": 2.0})
    assert np.isnan(peer_mean(adj, values).loc["S"])
