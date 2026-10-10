# TradeUp — Setup Plan

Two copies of [OpenAlgo](https://github.com/marketcalls/openalgo) run side by side on this Mac. One OpenAlgo copy can only connect to one broker, so each broker gets its own copy.

| | `openalgo-angel/` | `openalgo-zerodha/` |
|---|---|---|
| Broker | Angel One (SmartAPI) | Zerodha (Kite Connect, Personal plan) |
| Job | Live prices, charts, historical data, paper trading | Real buy and sell orders, positions, holdings |
| Dashboard | http://127.0.0.1:5001 | http://127.0.0.1:5002 |
| WebSocket | ws://127.0.0.1:8765 | ws://127.0.0.1:8766 |
| Internal bus (ZMQ) | 5555 | 5556 |
| Start | `./run.sh angel` | `./run.sh zerodha` |

Port 5000 is not used because macOS AirPlay Receiver occupies it.

Workflow: watch the market and paper-trade in the Angel One copy; when a trade is decided, place it in the Zerodha copy.

## Already done

- Both copies downloaded, each with its own `.env`, ports, cookie names, databases and Python environment.
- Both folders are git-ignored; their `.env` files hold secrets and must never be committed.

## What the user must do

1. **Angel One**
   - Have an Angel One account with TOTP enabled.
   - Create an app at https://smartapi.angelone.in and copy its API key.
   - Put the API key in `openalgo-angel/.env` as `BROKER_API_KEY`.
   - Daily login in the dashboard uses client code, PIN and the 6-digit TOTP.
2. **Zerodha**
   - Create a **Personal** app at https://developers.kite.trade.
   - Set its redirect URL to exactly `http://127.0.0.1:5002/zerodha/callback`.
   - Put the key and secret in `openalgo-zerodha/.env` as `BROKER_API_KEY` and `BROKER_API_SECRET`.
3. **Static IP** — required by SEBI for API orders. Find the current IP with `curl ifconfig.me`, register it in the Kite developer console, and register the same one with Angel One if SmartAPI asks for it. If the home IP changes, orders will be rejected until it is updated or a static IP is obtained.
4. **First run of each copy** — open the dashboard, create the local OpenAlgo admin user, log in to the broker, then generate an OpenAlgo API key (dashboard → API Key). Each copy has its own key.

## Next step (not built yet)

Small Python scripts in `scripts/` using the `openalgo` package:

- read live prices from the Angel One copy (port 5001);
- send orders to the Zerodha copy (port 5002);
- dry run by default, a `--live` flag and per-order size caps for real orders.

## Rules for any agent working here

1. Never place a live order; only the user does. Use Analyzer (sandbox) mode for all testing.
2. Never read, print or commit either `.env` file.
3. Do not change ports or cookie names in one copy without checking the other.
4. Upgrade a copy with `git pull` inside its folder, then compare `.sample.env` with `.env` for new settings.
