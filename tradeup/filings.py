"""Company announcements from NSE, with the time each one became public.

    uv run python -m tradeup.filings          # download for every stock that was ever in the universe

One request returns a company's full history. Each company is saved to its
own file, so an interrupted run continues where it stopped.
"""

import json
import time
from http.cookiejar import CookieJar
from urllib.parse import quote
from urllib.request import HTTPCookieProcessor, Request, build_opener

import pandas as pd

from .config import DATA, START

DIR = DATA / "filings"
PAGE = "https://www.nseindia.com/companies-listing/corporate-filings-announcements"
API = "https://www.nseindia.com/api/corporate-announcements?index=equities&symbol={}&from_date={}&to_date={}"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36",
    "Accept": "application/json, text/html",
    "Accept-Language": "en-US,en",
    "Referer": PAGE,
}
CUTOFF = pd.Timedelta(hours=15)  # filings after 15:00 count for the next trading day

# Routine paperwork that says nothing about the business.
NOISE = ("share certificate", "trading window", "newspaper", "depositories and participants",
         "schedule of analyst", "investor meet", "analysts meet", "duplicate", "book closure",
         "record date", "postal ballot", "shareholders meeting", "change in registrar", "address")
POSITIVE = ("upgrade", "reaffirm", "award", "bagging", "receipt of order", "order win", "wins order",
            "secures", "secured order", "letter of intent", "letter of award", "approval received",
            "buyback", "buy-back", "bonus", "commissioning", "commissioned", "commenc", "expansion", "record high",
            "highest ever", "growth", "tie-up", "partnership", "launch")
NEGATIVE = ("downgrade", "default", "resign", "penalty", "fraud", "litigation", "show cause",
            "search and seizure", "insolven", "fire", "strike", "lockout", "closure", "suspension",
            "delay", "loss", "adverse", "demand notice", "pledge", "invocation", "recall")


def _opener():
    opener = build_opener(HTTPCookieProcessor(CookieJar()))
    opener.open(Request(PAGE, headers=HEADERS), timeout=30).read()  # sets the cookies the API needs
    return opener


def fetch(opener, symbol: str, start: str, end: str) -> pd.DataFrame:
    fmt = lambda d: pd.Timestamp(d).strftime("%d-%m-%Y")
    url = API.format(quote(symbol), fmt(start), fmt(end))
    rows = json.loads(opener.open(Request(url, headers=HEADERS), timeout=90).read())
    frame = pd.DataFrame(rows, columns=["symbol", "exchdisstime", "an_dt", "desc", "attchmntText"])
    # Before August 2020 the exchange's own time is "-"; the company's submission time stands in.
    parse = lambda col: pd.to_datetime(frame[col], format="%d-%b-%Y %H:%M:%S", errors="coerce")
    when = parse("exchdisstime").fillna(parse("an_dt"))
    out = pd.DataFrame({"symbol": symbol, "time": when, "category": frame["desc"], "text": frame["attchmntText"]})
    return out.dropna(subset=["time"]).sort_values("time").reset_index(drop=True)


def download(symbols: list[str], start: str = START, end: str | None = None, pause: float = 1.0) -> None:
    DIR.mkdir(parents=True, exist_ok=True)
    end = end or str(pd.Timestamp.today().date())
    opener, failed = _opener(), []
    for n, symbol in enumerate(s for s in symbols if not (DIR / f"{s}.parquet").exists()):
        for attempt in range(3):
            try:
                fetch(opener, symbol, start, end).to_parquet(DIR / f"{symbol}.parquet", index=False)
                break
            except Exception as error:  # blocked session or timeout: new cookies, then retry
                time.sleep(5 * (attempt + 1))
                try:
                    opener = _opener()
                except Exception:
                    pass
        else:
            failed.append(symbol)
            print("failed", symbol, repr(error)[:80], flush=True)
        if n % 25 == 0:
            print(n, symbol, flush=True)
        time.sleep(pause)
    print("done; failed:", failed, flush=True)


def load() -> pd.DataFrame:
    return pd.concat([pd.read_parquet(p) for p in sorted(DIR.glob("*.parquet"))], ignore_index=True)


def tone(filings: pd.DataFrame) -> pd.Series:
    """Crude word-list score per filing: +1, 0 or -1. A placeholder until a language model scores them."""
    text = (filings["category"].fillna("") + " " + filings["text"].fillna("")).str.lower()
    hits = lambda words: text.str.contains(r"\b(?:" + "|".join(words) + ")", regex=True)  # word starts, so "closure" skips "disclosure"
    return hits(POSITIVE).astype(int) - hits(NEGATIVE).astype(int)


def daily(filings: pd.DataFrame, days: pd.DatetimeIndex, symbols: pd.Index) -> dict[str, pd.DataFrame]:
    """Per trading day and stock: number of material filings, and their summed tone.

    A filing belongs to the first trading day whose 15:00 comes at or after it.
    """
    f = filings[filings["symbol"].isin(symbols)]
    f = f[~f["category"].fillna("").str.lower().str.contains("|".join(NOISE))]
    slot = days.searchsorted(f["time"] - CUTOFF, side="left")
    f = f.assign(tone=tone(f))[slot < len(days)].assign(date=days[slot[slot < len(days)]])
    grouped = f.groupby(["date", "symbol"])["tone"].agg(["size", "sum"])
    shape = lambda col: grouped[col].unstack("symbol").reindex(index=days, columns=symbols).fillna(0.0)
    return {"count": shape("size"), "tone": shape("sum")}


def filing_features(filings: pd.DataFrame, days: pd.DatetimeIndex, symbols: pd.Index) -> dict[str, pd.DataFrame]:
    d = daily(filings, days, symbols)
    count_5 = d["count"].rolling(5).sum()
    usual = d["count"].rolling(126, min_periods=60).mean() * 5
    f = {
        "fil_count_5": count_5,
        "fil_abnormal": count_5 - usual,
        "fil_tone_5": d["tone"].rolling(5).sum(),
        "fil_tone_21": d["tone"].rolling(21).sum(),
    }
    # No filings on record before a stock's first one: unknown, not zero.
    seen = d["count"].cumsum() > 0
    return {k: v.where(seen) for k, v in f.items()}


if __name__ == "__main__":
    from . import prices, universe

    px = prices.load()
    px = px[px["symbol"] != prices.INDEX]
    members = universe.liquid_members(prices.wide(px, "close"), prices.wide(px, "volume"))
    download(sorted(members.columns[members.any()]))
