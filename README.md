# A-Share Multi-Factor Quantitative Research Framework

基于 JQData 数据接口的 A 股基本面多因子量化研究框架。

本项目完成了一套从**数据获取 → 数据清洗 → 因子构建 → 因子有效性检验 → 组合构建 → 回测分析 → 交易成本模拟 → 基准对比**的完整量化研究流程。

项目主要用于研究基本面因子在沪深300成分股中的选股效果，并验证多因子组合在样本期内的收益表现。

---

## 1. 项目背景

在 A 股市场中，基本面因子是量化选股的重要研究方向。

本项目选择沪深300成分股作为研究池，基于企业基本面指标构建多因子模型，通过历史数据回测分析：

- 不同因子的预测能力；
- 因子组合的收益表现；
- 策略换手情况；
- 交易成本影响；
- 相对于沪深300指数的表现。

---

# 2. 项目流程

整体研究流程如下：
JQData数据获取
        |
        ↓
原始数据检查
        |
        ↓
数据清洗
        |
        ↓
因子构建
        |
        ↓
IC分析
        |
        ↓
单因子五分组测试
        |
        ↓
多因子组合构建
        |
        ↓
组合回测
        |
        ↓
交易成本模拟
        |
        ↓
沪深300基准比较
        |
        ↓
结果可视化

---

# 3. 数据说明

## 数据来源

- 数据接口：JQData
- 股票池：沪深300成分股
- 调仓频率：月度调仓
- 数据周期：2025-05-30 至 2026-04-29

共：

- 12个调仓节点
- 300只沪深300股票
- 约3600条股票-日期记录


## 使用因子

项目采用基本面多因子模型：

| 因子 | 含义 |
|----|----|
| PE Ratio | 市盈率估值因子 |
| ROE | 盈利能力因子 |
| Revenue Growth | 营收增长因子 |


---

# 4. 因子处理方法

针对原始数据：

## 数据清洗

包括：

- 缺失值检查
- 异常值检测
- PE异常值过滤
- 去极值处理
- 标准化处理


异常值处理采用：

- 1% - 99% 分位数检测
- 后续因子标准化处理


---

# 5. 因子有效性分析

## IC分析

通过 Information Coefficient(IC) 衡量因子预测未来收益能力。

分析内容：

- IC均值
- IC稳定性
- 因子方向有效性


## 分组回测

采用五分组方法：
Low Factor Score
        |
        |
High Factor Score

观察不同因子水平股票组合未来收益差异。


---

# 6. 多因子组合构建

将多个基本面因子进行综合：Composite Score=PE Score+ROE Score+Revenue Growth Score

根据综合评分排序：

- 选择高评分股票；
- 构建等权组合；
- 月度调仓。


---

# 7. 回测结果

## 原始组合表现

| 指标 | 结果 |
|----|----|
| 回测周期 | 11个月 |
| 年化收益 | 45.74% |
| 年化波动率 | 18.77% |
| Sharpe | 2.12 |
| 最大回撤 | -5.89% |


## 加入交易成本后

交易成本假设：成本 = 0.1% × 月度换手率


结果：

| 指标 | 结果 |
|----|----|
| 累计收益 | 40.91% |
| 年化收益 | 45.38% |
| 年化波动率 | 18.76% |
| Sharpe | 2.11 |
| 最大回撤 | -5.89% |
| 平均月换手率 | 21.52% |


交易成本前后表现接近，说明策略收益并非完全依赖忽略交易成本。

---

# 8. 沪深300基准分析

项目通过 JQData 获取：000300.XSHG

作为市场基准。


基准数据处理：

- 获取指数日线收盘价；
- 匹配策略调仓日期；
- 生成月度收益序列；
- 对比策略收益。


---

# 9. 项目结果展示

## 策略累计收益曲线

将图片放置：outputs/charts/cumulative_return.png

展示：

![累计收益曲线](outputs/charts/cumulative_return.png)


---

## 回撤曲线

图片：outputs/charts/drawdown.png


![最大回撤](outputs/charts/drawdown.png)


---

## IC分析结果

图片：outputs/charts/ic_analysis.png


![IC分析](outputs/charts/ic_analysis.png)


---

## 分组收益结果

图片：outputs/charts/group_return.png


![分组收益](outputs/charts/group_return.png)


---

# 10. 项目结构
A-Share-MultiFactor-Research
│
├── main.py
│
├── run_all.py              # 一键运行流程
│
├── data_fetch.py           # JQData数据获取
│
├── data_cleaner.py         # 数据清洗
│
├── factor_process.py       # 因子处理
│
├── ic_analysis.py          # IC分析
│
├── backtest_group.py       # 分组回测
│
├── multifactor.py          # 多因子组合
│
├── backtest_portfolio.py   # 组合回测
│
├── turnover_calculator.py  # 换手率计算
│
├── benchmark.py            # 沪深300基准
│
├── visualization.py        # 可视化
│
├── requirements.txt
│
└── README.md

---

# 11. 环境配置

Python:
Python 3.10+

安装依赖：

```bash
pip install -r requirements.txt
配置 JQData：
创建：
.env
填写：
JQDATA_USERNAME=your_username

JQDATA_PASSWORD=your_password

12. 运行方式
一键运行：
python run_all.py
运行完成后生成：
data/
    raw/
    processed/


outputs/
    charts/
    results/

13. 技术栈
编程语言
Python
数据处理
Pandas
NumPy
数据接口
JQData
回测分析
自建月频回测框架
可视化
Matplotlib

14. 项目总结
通过该项目完成了一套完整的量化研究流程：
熟悉 JQData 数据接口使用；
掌握基本面因子构建方法；
完成 IC 分析和分组回测；
搭建多因子选股模型；
实现交易成本模拟；
完成基准收益比较和结果分析。
同时认识到：
当前研究样本周期较短，回测结果主要用于验证研究流程和模型框架，不代表长期真实收益能力。

Author
马彦龙
International Economics and Trade
Python Quantitative Research / Data Analysis
