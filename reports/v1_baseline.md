# v1 baseline results

Test period 2019-01-02 to 2025-09-22, 333 rebalances every 5 trading days. Top 20 stocks, equal weight, 0.15% cost per side. 192 stocks, 82,550 rows. Data from 2025-10-01 onwards is held back and was not used.

## Portfolios

|                                         | cagr   | volatility   |   sharpe | max_drawdown   | turnover   |   excess_t |    ic |   ic_t |
|:----------------------------------------|:-------|:-------------|---------:|:---------------|:-----------|-----------:|------:|-------:|
| Momentum 12-1                           | 44.0%  | 27.1%        |    1.489 | -38.0%         | 12.3%      |      2.305 | 0.021 |  2.088 |
| Model: price features                   | 34.2%  | 22.1%        |    1.446 | -30.3%         | 61.9%      |      0.872 | 0.036 |  5.307 |
| Model: price + peer features            | 35.8%  | 21.7%        |    1.523 | -28.6%         | 64.1%      |      1.196 | 0.035 |  5.108 |
| Equal weight, all stocks (no costs)     | 30.6%  | 21.2%        |    1.367 | -33.6%         |            |            |       |        |
| Nifty 50 index (no dividends, no costs) | 13.3%  | 18.5%        |    0.771 | -34.6%         |            |            |       |        |

`excess_t` is the t-statistic of the return over the equal-weight line; above 2 is the usual bar. `ic` is the average rank correlation between score and the following return, `ic_t` its t-statistic.

## Rank IC by year

|   date |   Momentum 12-1 |   Model: price features |   Model: price + peer features |
|-------:|----------------:|------------------------:|-------------------------------:|
|   2019 |           0.05  |                   0.045 |                          0.043 |
|   2020 |           0.006 |                   0.032 |                          0.037 |
|   2021 |           0.017 |                   0.039 |                          0.037 |
|   2022 |           0.017 |                   0.049 |                          0.048 |
|   2023 |           0.045 |                   0.035 |                          0.033 |
|   2024 |           0.024 |                   0.03  |                          0.027 |
|   2025 |          -0.021 |                   0.018 |                          0.012 |
