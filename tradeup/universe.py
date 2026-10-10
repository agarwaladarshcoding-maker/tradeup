"""Nifty 200 membership and industry labels, from NSE's published list."""

from datetime import date
from urllib.request import Request, urlopen

import pandas as pd

from .config import UNIVERSE_DIR

URL = "https://nsearchives.nseindia.com/content/indices/ind_nifty200list.csv"


def download() -> pd.DataFrame:
    # Each download is kept under its date, so membership history builds up
    # from today onwards. NSE does not publish past membership for free.
    raw = urlopen(Request(URL, headers={"User-Agent": "Mozilla/5.0"}), timeout=30).read()
    UNIVERSE_DIR.mkdir(exist_ok=True)
    path = UNIVERSE_DIR / f"nifty200_{date.today()}.csv"
    path.write_bytes(raw)
    return pd.read_csv(path)


def load() -> pd.DataFrame:
    """Latest saved membership: columns Company Name, Industry, Symbol, Series, ISIN Code."""
    files = sorted(UNIVERSE_DIR.glob("nifty200_*.csv"))
    return pd.read_csv(files[-1]) if files else download()


def sectors(universe: pd.DataFrame) -> pd.Series:
    return universe.set_index("Symbol")["Industry"]
