# v1 results

Test period 2019-01-02 to 2025-09-22, 333 rebalances every 5 trading days. Top 20 stocks, equal weight, 0.15% cost per side. Universe on each date: the 200 most traded of 755 candidates; 423 different stocks appear, 95,980 rows. Data from 2025-10-01 onwards is held back and was not used.

## Portfolios

|                                                     | cagr   | volatility   |   sharpe | max_drawdown   | turnover   |   excess_t |    ic |   ic_t |
|:----------------------------------------------------|:-------|:-------------|---------:|:---------------|:-----------|-----------:|------:|-------:|
| Momentum 12-1, top 20                               | 32.5%  | 28.9%        |    1.122 | -36.1%         | 13.7%      |      2.061 | 0.014 |  1.317 |
| Momentum 12-1, hold to rank 60                      | 30.0%  | 28.9%        |    1.054 | -37.6%         | 3.3%       |      1.728 | 0.014 |  1.317 |
| Model: price, top 20                                | 12.8%  | 20.5%        |    0.689 | -31.2%         | 69.3%      |     -2.063 | 0.035 |  5.121 |
| Model: price, hold to rank 60                       | 16.0%  | 20.3%        |    0.834 | -31.7%         | 37.9%      |     -1.183 | 0.035 |  5.121 |
| Model: price + price peers, top 20                  | 11.1%  | 21.1%        |    0.605 | -35.1%         | 70.7%      |     -2.463 | 0.035 |  5.302 |
| Model: price + price peers, hold to rank 60         | 17.4%  | 20.2%        |    0.894 | -29.9%         | 39.6%      |     -0.886 | 0.035 |  5.302 |
| Model: price + filings, top 20                      | 10.9%  | 21.1%        |    0.596 | -35.6%         | 75.7%      |     -2.474 | 0.034 |  5.049 |
| Model: price + filings, hold to rank 60             | 17.4%  | 20.2%        |    0.9   | -31.9%         | 42.2%      |     -0.89  | 0.034 |  5.049 |
| Model: price + filings + all peers, top 20          | 12.2%  | 21.5%        |    0.646 | -37.0%         | 76.0%      |     -2.103 | 0.035 |  5.416 |
| Model: price + filings + all peers, hold to rank 60 | 17.6%  | 21.4%        |    0.869 | -34.6%         | 43.7%      |     -0.761 | 0.035 |  5.416 |
| Equal weight, whole universe (no costs)             | 20.5%  | 22.4%        |    0.947 | -37.0%         |            |            |       |        |
| Nifty 50 index (no dividends, no costs)             | 13.3%  | 18.5%        |    0.771 | -34.6%         |            |            |       |        |

`excess_t` is the t-statistic of the return over the equal-weight line; above 2 is the usual bar. `ic` is the average rank correlation between score and the following return, `ic_t` its t-statistic.

## Yearly return by score bucket, before costs

Stocks sorted by score each week into five equal groups; 1 is the lowest scores, 5 the highest.

|                                    | 1     | 2     | 3     | 4     | 5     |
|:-----------------------------------|:------|:------|:------|:------|:------|
| Momentum 12-1                      | 18.0% | 17.4% | 19.4% | 22.6% | 28.7% |
| Model: price                       | 14.1% | 21.3% | 23.1% | 24.8% | 23.0% |
| Model: price + price peers         | 14.6% | 18.8% | 25.9% | 23.4% | 23.6% |
| Model: price + filings             | 14.7% | 23.1% | 22.9% | 19.8% | 25.6% |
| Model: price + filings + all peers | 14.2% | 20.7% | 24.3% | 20.5% | 26.5% |

## Rank IC by year

|   date |   Momentum 12-1 |   Model: price |   Model: price + price peers |   Model: price + filings |   Model: price + filings + all peers |
|-------:|----------------:|---------------:|-----------------------------:|-------------------------:|-------------------------------------:|
|   2019 |           0.059 |          0.054 |                        0.065 |                    0.043 |                                0.045 |
|   2020 |           0.002 |          0.029 |                        0.025 |                    0.029 |                                0.028 |
|   2021 |           0.016 |          0.026 |                        0.026 |                    0.028 |                                0.029 |
|   2022 |          -0.013 |          0.055 |                        0.053 |                    0.047 |                                0.047 |
|   2023 |           0.045 |          0.026 |                        0.026 |                    0.031 |                                0.036 |
|   2024 |           0.008 |          0.022 |                        0.017 |                    0.028 |                                0.03  |
|   2025 |          -0.029 |          0.032 |                        0.034 |                    0.031 |                                0.03  |
