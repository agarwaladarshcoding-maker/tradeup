"""Candidate stocks and point-in-time membership.

Candidates are the Nifty Total Market list (about 750 stocks) with NSE's
industry labels. On each date the universe is the most heavily traded of
them over the months before, so a stock that was large in 2018 and has since
shrunk is still held in 2018. Delisted stocks are not in the list at all.
"""

from datetime import date
from urllib.request import Request, urlopen

import pandas as pd

from .config import LIQUIDITY_WINDOW, UNIVERSE_DIR, UNIVERSE_SIZE

URL = "https://nsearchives.nseindia.com/content/indices/ind_niftytotalmarket_list.csv"


def download() -> pd.DataFrame:
    # Each download is kept under its date, so membership history builds up
    # from today onwards. NSE does not publish past membership for free.
    raw = urlopen(Request(URL, headers={"User-Agent": "Mozilla/5.0"}), timeout=30).read()
    UNIVERSE_DIR.mkdir(exist_ok=True)
    path = UNIVERSE_DIR / f"totalmarket_{date.today()}.csv"
    path.write_bytes(raw)
    return pd.read_csv(path)


def load() -> pd.DataFrame:
    """Latest saved membership: columns Company Name, Industry, Symbol, Series, ISIN Code."""
    files = sorted(UNIVERSE_DIR.glob("totalmarket_*.csv"))
    return pd.read_csv(files[-1]) if files else download()


def sectors(universe: pd.DataFrame) -> pd.Series:
    return universe.set_index("Symbol")["Industry"]


def liquid_members(
    close: pd.DataFrame, volume: pd.DataFrame, size: int = UNIVERSE_SIZE, window: int = LIQUIDITY_WINDOW
) -> pd.DataFrame:
    """True where a stock is among the `size` most traded by value over the past `window` days."""
    traded = (close * volume).rolling(window, min_periods=window // 2).median()
    return traded.rank(axis=1, ascending=False) <= size
