# A-Share Multi-Factor Quantitative Research Framework

基于 **JQData 数据接口** 的 A 股基本面多因子量化研究框架。

本项目实现了一套完整的量化研究流程：

**数据获取 → 数据清洗 → 因子构建 → IC分析 → 单因子测试 → 多因子组合构建 → 回测分析 → 交易成本模拟 → 沪深300基准比较 → 可视化展示**

项目以沪深300成分股作为研究股票池，基于企业基本面因子构建多因子选股模型，研究不同因子的预测能力以及组合收益表现。


---

# 项目背景

基本面因子选股是量化投资研究中的经典方法。

本项目希望通过历史数据研究：

- 基本面因子是否具有选股能力；
- 多因子组合是否能够获得超额收益；
- 换手率和交易成本对策略表现的影响；
- 策略相对于市场基准的表现。


---

# Research Pipeline

JQData数据获取
    ↓
原始数据检查
    ↓
数据清洗
    ↓
因子构建
    ↓
IC分析
    ↓
单因子五分组回测
    ↓
多因子组合构建
    ↓
组合回测
    ↓
交易成本模拟
    ↓
沪深300基准比较
    ↓
结果可视化


---

# 数据说明

## 数据来源

| 项目 | 内容 |
|----|----|
| 数据接口 | JQData |
| 股票池 | 沪深300成分股 |
| 调仓频率 | 月度调仓 |
| 数据周期 | 2025-05-30 至 2026-04-29 |
| 调仓节点 | 12个月 |
| 股票数量 | 300只 |
| 数据规模 | 约3600条股票-日期记录 |


---

# Factor Design

本项目选择三个基本面因子：

| 因子 | 类型 | 含义 |
|-|-|-|
| PE Ratio | Value | 估值因子 |
| ROE | Quality | 盈利能力因子 |
| Revenue Growth | Growth | 成长因子 |


综合因子评分：

Composite Score =
PE Score
+
ROE Score
+
Revenue Growth Score


根据综合评分：

1. 股票排序；
2. 选择高评分股票；
3. 构建等权组合；
4. 月度调仓。


---

# 数据处理

## 数据清洗流程

包括：

- 缺失值检查；
- 异常值检测；
- PE异常值过滤；
- 去极值处理；
- 标准化处理。


异常值检测：

1% - 99% 分位数


---

# 因子有效性分析


## IC Analysis

使用 Information Coefficient(IC) 衡量因子预测未来收益能力。


分析内容：

- IC均值；
- IC稳定性；
- 因子方向有效性。


## 五分组测试


按照因子评分排序：

Group 1  Low Factor Score
    ↓
Group 5  High Factor Score


比较不同因子水平股票组合未来收益差异。


---

# Multi-Factor Portfolio


组合构建方式：

- 多因子综合评分；
- 股票排序；
- 高评分股票入选；
- 等权配置；
- 月度调仓。


回测指标：

- 累计收益；
- 年化收益；
- 年化波动率；
- Sharpe Ratio；
- 最大回撤；
- 换手率。


---

# Backtest Results


## 未加入交易成本


| 指标 | 结果 |
|-|-|
| 回测周期 | 11个月 |
| 年化收益 | 45.74% |
| 年化波动率 | 18.77% |
| Sharpe Ratio | 2.12 |
| 最大回撤 | -5.89% |


---

## 加入交易成本


交易成本：

成本 = 0.1% × 月度换手率


结果：

| 指标 | 结果 |
|-|-|
| 累计收益 | 40.91% |
| 年化收益 | 45.38% |
| 年化波动率 | 18.76% |
| Sharpe Ratio | 2.11 |
| 最大回撤 | -5.89% |
| 平均月换手率 | 21.52% |


加入交易成本后策略表现变化较小。


> 注：
>
> 当前研究周期较短，结果主要用于验证量化研究流程和模型框架，不代表长期收益能力。


---

# Benchmark Comparison


市场基准：

沪深300指数
000300.XSHG


基准处理流程：

1. JQData获取指数日线数据；
2. 匹配策略调仓日期；
3. 转换为月度收益；
4. 与策略收益比较。


---

# Visualization


## Cumulative Return

![Cumulative Return](outputs/charts/cumulative_return.png)


## Drawdown

![Drawdown](outputs/charts/drawdown.png)


## IC Analysis

![IC Analysis](outputs/charts/ic_analysis.png)


## Group Return

![Group Return](outputs/charts/group_return.png)



---

# Project Structure


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


---

# Environment


Python:

Python 3.10+


Install:

```bash
pip install -r requirements.txt
JQData配置：
创建：
.env
填写：
JQDATA_USERNAME=your_username

JQDATA_PASSWORD=your_password
Run
运行完整流程：
python run_all.py
生成：
data/

├── raw/

└── processed/


outputs/

├── charts/

└── results/
Technology Stack
Language
Python
Data Processing
Pandas
NumPy
Data Source
JQData
Quant Research
Factor Research
IC Analysis
Portfolio Backtesting
Visualization
Matplotlib
Summary
通过本项目完成了一套完整的A股量化研究框架：
搭建JQData数据获取流程；
完成股票数据清洗；
构建基本面多因子模型；
实现IC分析和分组测试；
完成组合回测；
加入交易成本模拟；
完成沪深300基准比较；
输出完整研究报告。
同时认识到：
由于样本周期限制，目前结果主要用于研究方法验证和流程展示，后续仍需要更长周期、更丰富因子以及更严格样本外测试。
Author
马彦龙
International Economics and Trade
Python Quantitative Research / Data Analysis
