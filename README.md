# A-Share Multi-Factor Quantitative Research Framework

A Python-based quantitative research framework for exploring fundamental factor investing strategies in the Chinese A-share market.

This project implements a complete quantitative research pipeline, including:

- Data acquisition
- Data quality inspection
- Data cleaning
- Factor construction
- Factor effectiveness evaluation
- Portfolio construction
- Backtesting
- Transaction cost simulation
- Benchmark comparison
- Performance visualization

The research universe is based on CSI 300 constituent stocks. The project aims to evaluate whether fundamental factors can provide effective stock selection signals and examine the performance of a multi-factor portfolio.

---

# 1. Research Background

Factor investing is one of the major quantitative investment approaches.

This project focuses on fundamental factors and investigates:

- Whether individual factors have predictive ability for future returns;
- Whether combining multiple factors improves portfolio performance;
- How transaction costs affect strategy returns;
- How the strategy performs compared with the CSI 300 Index.

The project is designed as a complete quantitative research workflow rather than a single backtesting script.

---

# 2. Research Workflow

JQData Market Data
        |
        ↓
Raw Data Collection
        |
        ↓
Data Quality Check
        |
        ↓
Data Cleaning
        |
        ↓
Factor Processing
        |
        ↓
IC Analysis
        |
        ↓
Single Factor Group Backtest
        |
        ↓
Multi-Factor Portfolio Construction
        |
        ↓
Portfolio Backtest
        |
        ↓
Transaction Cost Simulation
        |
        ↓
CSI 300 Benchmark Comparison
        |
        ↓
Visualization

---

# 3. Dataset

## Data Source

- Data provider: JQData
- Market: China A-share Market
- Stock Universe: CSI 300 Constituents
- Rebalancing Frequency: Monthly
- Research Period:

2025-05-30 to 2026-04-29

## Dataset Scale

- 12 monthly rebalance dates
- Around 300 stocks per period
- 3,600 stock-date observations

---

# 4. Factor Construction

The project uses three fundamental factors:

| Factor | Description |
|--------|-------------|
| PE Ratio | Valuation factor |
| ROE | Profitability factor |
| Revenue Growth | Growth factor |


The factors represent three common dimensions of fundamental investing:

- Valuation
- Quality
- Growth

---

# 5. Factor Processing

Before analysis, raw data goes through several preprocessing steps:

## Data Cleaning

Including:

- Missing value inspection
- Duplicate record checking
- Invalid value filtering
- Extreme value detection


## Outlier Treatment

Extreme values are identified using:

1% - 99% percentile method

After processing:

- Factors are cleaned;
- Extreme observations are controlled;
- Data is prepared for standardized scoring.

---

# 6. Factor Effectiveness Evaluation

## Information Coefficient (IC) Analysis

IC is used to evaluate the relationship between factor scores and future stock returns.

The analysis includes:

- Average IC
- IC stability
- Factor predictive direction


## Quintile Portfolio Analysis

Stocks are sorted according to factor scores and divided into five groups.

Example:

Low Factor Score
        |
        |
High Factor Score

The return difference between groups is analyzed to evaluate factor effectiveness.

---

# 7. Multi-Factor Portfolio Construction

A composite factor score is constructed:

Composite Score =
PE Score
+
ROE Score
+
Revenue Growth Score

Portfolio construction process:

1. Calculate standardized factor scores;
2. Rank stocks by composite score;
3. Select high-score stocks;
4. Construct an equally weighted portfolio;
5. Rebalance monthly.

---

# 8. Backtest Results

## Portfolio Performance Before Transaction Costs

| Metric | Result |
|---|---:|
| Backtest Period | 11 months |
| Annual Return | 45.74% |
| Annual Volatility | 18.77% |
| Sharpe Ratio | 2.12 |
| Maximum Drawdown | -5.89% |


## Portfolio Performance After Transaction Costs

Transaction cost assumption:

Cost = 0.1% × Monthly Turnover

Results:

| Metric | Result |
|---|---:|
| Cumulative Return | 40.91% |
| Annual Return | 45.38% |
| Annual Volatility | 18.76% |
| Sharpe Ratio | 2.11 |
| Maximum Drawdown | -5.89% |
| Average Monthly Turnover | 21.52% |


The strategy performance remains relatively stable after considering transaction costs.

---

# 9. Benchmark Comparison

The CSI 300 Index is used as the benchmark:

Index Code:
000300.XSHG

Benchmark processing:

- Download CSI 300 daily closing prices through JQData;
- Match portfolio rebalance dates;
- Generate monthly benchmark returns;
- Compare portfolio performance against market performance.

---

# 10. Visualization

The project generates several research charts:

## Cumulative Return Curve

outputs/charts/cumulative_return.png

Shows:

- Portfolio growth trend
- Benchmark comparison


## Drawdown Analysis

outputs/charts/drawdown.png

Shows:

- Maximum drawdown
- Risk characteristics


## IC Analysis

outputs/charts/ic_analysis.png

Shows:

- Factor predictive ability


## Group Return Analysis

outputs/charts/group_return.png

Shows:

- Return differences among factor groups

---

# 11. Project Structure

A-Share-MultiFactor-Research
│
├── main.py
├── run_all.py                 # Complete research pipeline
│
├── data_fetch.py              # JQData data acquisition
├── data_check.py              # Data quality inspection
├── data_cleaner.py            # Data cleaning
│
├── factor_process.py          # Factor construction and processing
├── ic_analysis.py             # IC evaluation
├── backtest_group.py          # Quintile portfolio backtest
│
├── multifactor.py             # Multi-factor model
├── backtest_portfolio.py      # Portfolio backtest
├── turnover_calculator.py     # Turnover calculation
│
├── benchmark.py               # CSI 300 benchmark data
├── benchmark_analysis.py      # Benchmark comparison
│
├── visualization.py           # Research visualization
│
├── requirements.txt
└── README.md

---

# 12. Environment Setup

## Requirements

Python:

Python 3.10+


Install dependencies:

```bash
pip install -r requirements.txt
JQData Configuration
Create:
.env
Add:
JQDATA_USERNAME=your_username

JQDATA_PASSWORD=your_password
13. Running the Project
Run the complete pipeline:
python run_all.py
After completion:
data/
├── raw/
└── processed/


outputs/
└── charts/
will be generated.
14. Technology Stack
Programming Language
Python
Data Processing
Pandas
NumPy
Data Source
JQData
Quantitative Research
Factor analysis
IC evaluation
Portfolio backtesting
Transaction cost simulation
Visualization
Matplotlib
15. Project Limitations
Although the framework completes the full quantitative research process, several limitations remain:
The current sample period is relatively short;
Backtest results are for research validation only;
Longer historical periods are required for robustness testing;
Additional factors and risk controls can be introduced in future improvements.
Author
Ma Yanlong
International Economics and Trade
Python Quantitative Research / Data Analysis
