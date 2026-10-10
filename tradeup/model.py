"""Walk-forward scoring: each year is predicted by a model trained only on earlier years."""

import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor

from .config import FIRST_TEST_YEAR

GAP = pd.Timedelta(days=21)  # longer than one label, so no training label reaches into the test year


def split(dates: pd.DatetimeIndex, year: int) -> tuple[pd.Series, pd.Series]:
    """Boolean masks (train, test) for one test year."""
    return dates < pd.Timestamp(year, 1, 1) - GAP, dates.year == year


def walk_forward(data: pd.DataFrame, features: list[str], first_year: int = FIRST_TEST_YEAR) -> pd.Series:
    data = data.dropna(subset=["target"])
    dates = data.index.get_level_values("date")
    scores = []
    for year in range(first_year, dates.year.max() + 1):
        train, test = split(dates, year)
        if not test.any():
            continue
        model = HistGradientBoostingRegressor(
            max_depth=3, learning_rate=0.05, max_iter=200, min_samples_leaf=100, random_state=0
        )
        model.fit(data.loc[train, features], data.loc[train, "target"])
        scores.append(pd.Series(model.predict(data.loc[test, features]), index=data.index[test]))
    return pd.concat(scores).rename("score")
