# TradeUp — The Idea, Evaluated

Written 2026-10-04. Companion to [PLAN.md](PLAN.md), which covers the broker setup. This file covers what the system should decide and how to build it.

## 1. The idea in plain words

1. **Pick a universe.** A group of stocks in one market segment, deliberately mixed: some move together, some do not, and the strength of those links changes over time.
2. **Give every stock a set of signal modules** (6 to 10). Each one reads a different source and outputs numbers:
   - price and volume history (technical and statistical models),
   - news articles and exchange filings,
   - mathematical forecasts (volatility, trend, mean reversion and similar).
3. **Learn each stock's "driver profile".** Some stocks mostly follow technical patterns, some mostly follow sentiment. A model estimates this per stock.
4. **Connect the stocks in a graph.** Each stock is a node carrying its signals. Edges link related stocks. A graph neural network (GNN) lets each stock's forecast use what is happening to its neighbours.
5. **Output an allocation.** Given a sum of money, decide which stocks to hold and how much of each.

The core trading rule behind it:

- A stock is rising on sentiment, but its correlated peers show no such sentiment → the move is probably stock-specific noise or hype. **Give it less money.**
- A cluster of correlated stocks all show strong signals together → the move is probably real and sector-wide. **Give them more money.**

## 2. Verdict

| Question | Answer |
|---|---|
| Can it be built by one person? | Yes, in stages. Nothing here needs unusual infrastructure. |
| Is the core rule sound? | Yes. Peer confirmation is a real, documented effect, and it is the best part of the idea. |
| Will the full system make money? | Unproven. The honest prior is that most such systems do not beat a simple index fund after costs. |
| Is the GNN the important part? | No. It is the last 10 percent. Data quality and honest testing decide the outcome. |
| Biggest risk | A backtest that looks profitable because of leakage or over-tuning, followed by real losses. |

Recommendation: build it, but in the order in section 5, where each stage must beat the previous one before the next is started. The core rule can be tested without any GNN in a few weeks.

## 3. What is strong

- **Peer confirmation is real.** Research on linked firms shows that news about one firm reaches the prices of related firms with a delay. Starting points to read: Cohen and Frazzini, "Economic Links and Predictable Returns" (2008); Feng et al., "Temporal Relational Ranking for Stock Prediction" (2019), which is the closest published design to this one. (Cited from memory; check before relying on details.)
- **Ranking stocks against each other is the right framing.** Predicting whether one stock goes up is very hard. Predicting which stocks in a group will do better than the others is easier, and it is exactly what an allocation needs.
- **Mixing signal types helps.** Price signals and text signals fail at different times, so combining them is more stable than either alone.
- **The plumbing already exists.** The Angel One copy supplies prices and paper trading; the Zerodha copy places orders.

## 4. What is weak, and the fix for each

**4.1 Correlation is a poor way to build the graph.**
Correlation is calculated from the same prices the model already sees, so it adds little new information. It is also unstable, and in a market fall almost every stock becomes correlated with every other.
*Fix:* build the graph from four edge types, each stored as its own layer so the model can weight them differently:

| Edge type | Where it comes from | How often it changes |
|---|---|---|
| Same industry | NSE's industry classification, published with index constituent lists | Rarely |
| Same business group | A hand-made list (Tata, Adani, Bajaj and so on), about an hour of work | Rarely |
| Mentioned together | Count of news items naming both companies in the last 90 days | Weekly |
| Residual correlation | See below | Weekly |

Residual correlation is the corrected version of the original idea. First remove the part of each stock's return explained by the market and by its sector. Then correlate what is left over a rolling 60-day window, and keep only each stock's 5 to 10 strongest links. This shows which stocks move together for reasons beyond "the whole market went up", and because it is recalculated every week the graph changes as relationships change.

**4.2 One segment gives little diversification.**
Stocks inside one sector mostly move with the sector. A long-only portfolio inside one sector is mainly a bet on that sector.
*Fix:* use the Nifty 200 with sector labels instead of one segment. Stocks in the same sector form tight clusters, different sectors are loosely linked, and a few pairs (for example banks and the housing companies they lend to) link across sectors. That is the mixture of correlated and uncorrelated stocks the idea asks for. Cap the money in any one sector at about 25 percent.

**4.3 Telegram: dropped.**
Decided 2026-10-09. Indian tip channels are too often used for pump and dump schemes to be a usable signal.

**4.4 Sentiment history has to be rebuilt, not just downloaded.**
Price history for past years is easy to get. News history is the hard part: the backtest needs each item with the time it became public.
*Fix:* backfill from sources that keep archives, and run live collectors alongside.
- Exchange filings: NSE and BSE publish corporate announcements with timestamps going back years. Results, orders won, board decisions and rating changes are all here. This is the cleanest source.
- GDELT: a free database of world news since 2015 with article links, publication times and a tone score. Covers the main Indian English outlets.
- News site archives (Economic Times, Moneycontrol, Business Standard) for article text where needed.

Two traps when scoring old news with a language model. The model may already know what happened to the stock afterwards, which makes old sentiment scores look smarter than live ones would be. And archived articles are sometimes edited after publication. Both make the backtest too optimistic, so test the sentiment signal separately on news dated after the model's knowledge cutoff. (Availability of each source is from memory; check before building on it.)

**4.5 More years of data helps less than it seems.**
Five years of 200 stocks is about 250,000 daily rows, which sounds large. But on any one day the stocks move together, so they are not 200 separate examples. With weekly decisions, five years is about 260 truly separate periods. That is small, and each one is mostly noise. Five years also covers only one or two market moods; a model trained only in a rising market has never seen a falling one.
*Fix:* use as many years as the data allows (8 to 10 for prices). Start with simple models (ridge regression, gradient-boosted trees) and add the GNN only if it beats them on data it has never seen.

**4.6 Costs eat short-term edges.**
A delivery round trip in India costs roughly 0.2 to 0.3 percent in taxes and charges, before slippage, plus a fixed depository charge per stock sold. Short-term gains are taxed on top. (Check current figures on Zerodha's charges page.) A system that reshuffles the portfolio daily needs a large edge just to break even, and fixed per-stock charges hurt small accounts most.
*Fix:* hold for days to weeks, not intraday. Penalise turnover inside the allocation step. Include all costs in every backtest from day one.

**4.7 Long-only limits the rule.**
Shares cannot be shorted overnight in the cash market. "Lower bias" can only mean holding less or none.
*Fix:* accept long-only for version one. The output is weights from zero up to a cap, with cash allowed.

**4.8 Forecasting and allocating are two different problems.**
Asking one network to output money weights directly is hard to train and hard to debug. Brute force does not work either: even choosing 20 stocks out of 200 has more combinations than can ever be tried, before deciding how much to put in each.
*Fix:* two steps. The model outputs an expected-return score per stock. A standard algorithm, mean-variance optimisation, then finds the weights that give the most expected return for a chosen level of risk, subject to limits: a maximum per stock, a maximum per sector, and a penalty for trading too much. It solves in under a second with the `cvxpy` library. A simpler alternative worth testing against it is to buy the top 20 scores in equal amounts; this often does nearly as well.

**4.9 The "driver profile" does not need its own model.**
*Fix:* measure it directly. For each stock, check how much of its past return was explained by the technical signals and how much by the sentiment signals, and feed those two numbers in as node features.

## 5. How to build it

Each stage has a gate. If the gate fails, fix or stop; do not move on.

**Stage 0 — Data (2 to 3 weeks)**
- Daily prices for the universe, adjusted for splits and bonuses, pulled through the Angel One copy and stored locally (Parquet or DuckDB).
- Universe membership as it was on each past date, including stocks that were later removed. Using only today's members makes every backtest look better than reality.
- Collectors running continuously for exchange filings and news, each record stored with the time it became public.
- Backfill of past filings and news (section 4.4).
- *Gate:* prices match a second source on spot checks; collectors run a week without gaps.

**Stage 1 — Price-only baseline (2 weeks)**
- Features: returns over several windows, volatility, volume changes, distance from highs and lows, sector-relative versions of each.
- Model: gradient-boosted trees predicting next-week return rank.
- Testing: walk-forward (train on the past, test on the next period, roll forward), with a gap between train and test, and full costs.
- Compare against: Nifty index, equal-weight universe, plain momentum.
- *Gate:* out-of-sample rank correlation between score and later return is positive and stable across years (0.02 to 0.05 is a good result in this field), and the portfolio beats the comparisons after costs.

**Stage 2 — Sentiment and the core rule, no GNN (3 to 4 weeks)**
- Score each text item with a language model: which company, positive or negative, how important.
- Per stock per day: sentiment level, amount of news compared with normal, agreement between sources.
- **Peer features, built by hand:** the average sentiment and average return of each stock's neighbours, and the gap between a stock and its neighbours. This is the core rule written as a number. It is one layer of a GNN done manually.
- *Gate:* adding these features improves the Stage 1 results out of sample. If the hand-built peer features add nothing, a GNN will not either, and the idea needs rethinking before more is spent.

**Stage 3 — The GNN (4 to 6 weeks)**
- Per-stock sequence encoder (a small GRU or transformer over the last N days of features), then a graph attention layer over the multi-type edges, then a ranking loss.
- Tools: PyTorch Geometric. Microsoft's Qlib has working reference models of this kind.
- *Gate:* beats Stage 2 out of sample by a margin larger than the run-to-run variation from different random seeds.

**Stage 4 — Allocation (1 to 2 weeks)**
- Scores to weights by constrained optimisation: risk from a shrunk covariance estimate, caps per stock and per sector, turnover penalty, cash allowed.
- Hard limits outside the model: maximum loss per day, maximum position size, a switch that turns everything off.

**Stage 5 — Paper, then small real money (3 months or more)**
- Run daily in OpenAlgo Analyzer mode on the Angel One copy. Compare paper results with the backtest for the same dates; a large gap means the backtest is wrong.
- Then a small amount of real money through the Zerodha copy. The system proposes orders; the user places them (PLAN.md rule 1).

## 6. Rules for honest testing

1. No information from the future. Every feature uses only what was public before the decision time. News published after market close counts for the next day.
2. One final test period that is never looked at during development, used once.
3. Count every experiment. Trying 50 variants and reporting the best one is how false strategies are made.
4. Costs and slippage in every result, never added later.
5. A result that looks very good is a bug until proven otherwise.

## 7. Decisions still open

| Decision | Suggested default |
|---|---|
| Holding period | About one week, rebalanced weekly |
| Universe | Nifty 200, liquid names only |
| Long-only or with shorts | Long-only with cash |
| Capital for first live run | Small enough that losing all of it is acceptable |
| First text source | Exchange filings, then news |

This document is an engineering assessment, not investment advice. Real money goes in only after Stage 5 paper results hold up.
