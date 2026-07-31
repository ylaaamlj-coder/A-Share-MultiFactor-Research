# A-Share Multi-Factor Quantitative Research Framework

基于 Python 与 JQData 数据接口搭建的 A 股基本面多因子量化研究框架。

本项目完成从数据获取、因子构建、有效性检验、组合构建、策略回测、交易成本模拟到基准比较的完整量化研究流程。

项目研究对象为沪深300成分股，利用基本面因子构建多因子选股策略，并通过历史数据验证策略表现。


## 1. Project Overview

在量化投资研究中，基本面因子是常见的选股方法之一。

本项目基于沪深300股票池，选取估值、盈利能力和成长性指标构建多因子模型，主要研究：

- 不同基本面因子的预测能力
- 因子组合收益表现
- 策略风险收益特征
- 换手率及交易成本影响
- 相对于沪深300指数的超额收益能力


## 2. Research Pipeline


JQData Market Data
        |
        v
Data Cleaning
        |
        v
Factor Construction
        |
        v
IC Analysis
        |
        v
Single Factor Portfolio Test
        |
        v
Multi-Factor Portfolio
        |
        v
Backtest
        |
        v
Transaction Cost Simulation
        |
        v
Benchmark Comparison
        |
        v
Visualization


## 3. Data Description


| Item | Description |
|---|---|
| Data Source | JQData |
| Stock Pool | CSI 300 Constituents |
| Frequency | Monthly Rebalance |
| Period | 2025-05-30 ~ 2026-04-29 |
| Stocks | 300 CSI300 stocks |
| Records | 3600 stock-month observations |


## 4. Factor Model


The model uses three fundamental factors:


| Factor | Description |
|---|---|
| PE Ratio | Valuation factor |
| ROE | Profitability factor |
| Revenue Growth | Growth factor |


Factor score:

Composite Score =
PE Score +
ROE Score +
Revenue Growth Score


Portfolio construction:

- Rank stocks by composite score
- Select high-score stocks
- Build equal-weight portfolio
- Monthly rebalance


## 5. Factor Analysis


### IC Analysis

Information Coefficient(IC) is used to evaluate factor predictive ability.


Analysis includes:

- IC Mean
- IC Stability
- Factor Direction


### Portfolio Group Test

Stocks are divided into five groups according to factor scores.


Low Score

↓

High Score


The return difference is used to evaluate factor effectiveness.



## 6. Backtest Results


### Portfolio Performance


| Metric | Result |
|---|---:|
| Backtest Period | 11 Months |
| Annual Return | 45.74% |
| Annual Volatility | 18.77% |
| Sharpe Ratio | 2.12 |
| Maximum Drawdown | -5.89% |



### After Transaction Cost


Transaction cost assumption:

Cost = 0.1% × Monthly Turnover


| Metric | Result |
|---|---:|
| Cumulative Return | 40.91% |
| Annual Return | 45.38% |
| Sharpe Ratio | 2.11 |
| Maximum Drawdown | -5.89% |
| Average Monthly Turnover | 21.52% |


The strategy performance remains stable after transaction cost simulation.


## 7. Benchmark Comparison


Benchmark:

CSI 300 Index
000300.XSHG


Benchmark data process:

- Download CSI300 daily close price from JQData
- Match monthly rebalance dates
- Calculate benchmark return
- Compare strategy performance


## 8. Visualization


### Cumulative Return Curve


![Cumulative Return](outputs/charts/cumulative_return.png)



### Drawdown Analysis


![Drawdown](outputs/charts/drawdown.png)



### IC Analysis


![IC Analysis](outputs/charts/ic_analysis.png)



### Group Return Test


![Group Return](outputs/charts/group_return.png)



## 9. Project Structure


A-Share-MultiFactor-Research
├── main.py
├── run_all.py
├── data_fetch.py
├── data_cleaner.py
├── factor_process.py
├── ic_analysis.py
├── backtest_group.py
├── multifactor.py
├── backtest_portfolio.py
├── turnover_calculator.py
├── benchmark.py
├── benchmark_analysis.py
├── visualization.py
├── requirements.txt
└── README.md


## 10. Environment


Python 3.10+


Install dependencies:


pip install -r requirements.txt


Configure JQData:


Create `.env` file:


JQDATA_USERNAME=your_username
JQDATA_PASSWORD=your_password


## 11. Run


Execute:


python run_all.py


The framework will automatically complete:

- Data acquisition
- Data cleaning
- Factor processing
- Backtest
- Benchmark comparison
- Visualization


## 12. Technology Stack


| Category | Tools |
|---|---|
| Language | Python |
| Data Processing | Pandas, NumPy |
| Data Source | JQData |
| Backtesting | Custom Python Framework |
| Visualization | Matplotlib |


## 13. Limitations


The current research period is relatively short.

The backtest results are mainly used to verify the research framework and modeling process, rather than represent long-term investment performance.


## Author


Ma Yanlong

International Economics and Trade

Python Quantitative Research / Data Analysis
