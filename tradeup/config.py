from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
UNIVERSE_DIR = ROOT / "universe"
REPORTS = ROOT / "reports"

START = "2015-01-01"
# Rule 2 in IDEA.md section 6: nothing on or after this date is evaluated
# during development. It is used once, at the end.
HOLDOUT_START = "2025-10-01"

UNIVERSE_SIZE = 200  # stocks in the universe on any date
LIQUIDITY_WINDOW = 126  # trading days of traded value used to pick them

HORIZON = 5  # trading days between rebalances
TOP_N = 20  # stocks held
EXIT_RANK = 60  # a held stock is sold only when its score rank falls below this
COST_PER_SIDE = 0.0015  # fraction of traded value: taxes, charges, slippage
FIRST_TEST_YEAR = 2019

GRAPH_WINDOW = 60  # trading days of residual returns per correlation
GRAPH_K = 8  # neighbours kept per stock
