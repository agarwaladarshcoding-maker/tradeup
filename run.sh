#!/bin/sh
# Start one OpenAlgo copy:  ./run.sh angel   or   ./run.sh zerodha
# angel   -> http://127.0.0.1:5001  (live prices, charts, paper trading)
# zerodha -> http://127.0.0.1:5002  (real orders)
case "$1" in
  angel|zerodha) cd "$(dirname "$0")/openalgo-$1" && exec uv run app.py ;;
  *) echo "usage: ./run.sh angel|zerodha" >&2; exit 1 ;;
esac
