"""
Portfolio Backtesting Module

Features:
- Monthly portfolio return calculation
- Net value calculation
- Performance evaluation

Metrics:
- Annual Return
- Volatility
- Sharpe Ratio
- Maximum Drawdown

Supports:
- Transaction cost simulation

Author:
Ma Yanlong

回测多因子最高 20% 等权组合，并计算基础绩效指标。
"""

# 导入 Path 处理文件路径。
from pathlib import Path
# 导入 numpy 进行数值计算。
import numpy as np
# 导入 pandas 处理表格数据。
import pandas as pd
# 导入换手率计算函数。
from turnover_calculator import calculate_turnover, save_turnover


# 设置多因子选股结果路径。
INPUT_PATH = Path("data/processed/multifactor_score.csv")
# 设置组合月收益和净值路径。
RETURN_OUTPUT_PATH = Path("outputs/portfolio_return.csv")
# 设置组合绩效指标路径。
METRICS_OUTPUT_PATH = Path("outputs/portfolio_metrics.csv")
# 设置扣除交易成本后的月收益与净值路径。
COST_RETURN_OUTPUT_PATH = Path("outputs/tables/portfolio_return_cost.csv")
# 设置扣除交易成本后的绩效指标路径。
COST_METRICS_OUTPUT_PATH = Path("outputs/tables/portfolio_metrics_cost.csv")
# 设置单边佣金费率；例如 0.001 代表每 1 元换手成本为 0.1%。
COMMISSION_COST = 0.001


def run_portfolio_backtest(input_path=INPUT_PATH) -> pd.DataFrame:
    """计算每月持有最高 20% 股票的等权组合收益、净值和回撤。"""
    # 确认输入文件存在。
    if not Path(input_path).exists():
        raise FileNotFoundError(f"未找到多因子结果：{input_path}。请先运行 multifactor.py。")
    # 读取多因子得分数据。
    data = pd.read_csv(input_path, parse_dates=["trade_date"])
    # 只保留入选股票和已有未来收益的记录。
    selected_data = data.loc[data["selected"] & data["future_return"].notna()].copy()
    # 每月对入选股票未来收益取均值，代表等权持仓组合收益。
    portfolio = selected_data.groupby("trade_date", as_index=False)["future_return"].mean()
    # 改名为更清楚的组合月收益。
    portfolio = portfolio.rename(columns={"future_return": "monthly_return"})
    # 按时间排序。
    portfolio = portfolio.sort_values("trade_date").reset_index(drop=True)
    # 计算累计净值，初始净值为 1。
    portfolio["net_value"] = (1 + portfolio["monthly_return"]).cumprod()
    # 计算历史净值最高点。
    portfolio["running_max"] = portfolio["net_value"].cummax()
    # 计算回撤，负数表示从历史高点回落的幅度。
    portfolio["drawdown"] = portfolio["net_value"] / portfolio["running_max"] - 1
    # 返回组合回测时间序列。
    return portfolio


def calculate_metrics(portfolio: pd.DataFrame) -> pd.DataFrame:
    """计算年化收益、夏普比率和最大回撤。"""
    # 当没有有效回测月份时给出明确错误。
    if portfolio.empty:
        raise ValueError("没有可回测的组合收益，请检查 future_return 是否为空。")
    # 获取实际回测月数。
    months = len(portfolio)
    # 计算年化收益率；月频数据按 12 个月折算。
    annual_return = portfolio["net_value"].iloc[-1] ** (12 / months) - 1
    # 计算月收益标准差。
    monthly_volatility = portfolio["monthly_return"].std(ddof=1)
    # 假设无风险利率为零，计算年化夏普比率。
    sharpe_ratio = portfolio["monthly_return"].mean() / monthly_volatility * np.sqrt(12) if monthly_volatility else np.nan
    # 最大回撤为回撤序列的最小值。
    max_drawdown = portfolio["drawdown"].min()
    # 将核心指标整理成一行表。
    return pd.DataFrame([{
        "months": months,
        "annual_return": annual_return,
        "annualized_volatility": monthly_volatility * np.sqrt(12),
        "annualized_sharpe": sharpe_ratio,
        "max_drawdown": max_drawdown,
    }])


def run_cost_backtest(portfolio: pd.DataFrame, turnover_data: pd.DataFrame, commission_cost=COMMISSION_COST) -> pd.DataFrame:
    """将换手率和佣金费率计入原始组合收益，生成成本后净值。"""
    # 复制原始组合收益，确保不修改原始回测结果。
    cost_portfolio = portfolio.copy()
    # 将每期换手率按调仓日合并到组合收益上。
    cost_portfolio = cost_portfolio.merge(turnover_data[["trade_date", "turnover"]], on="trade_date", how="left")
    # 若个别日期没有换手率记录，则保守地将其设为零并提示数据问题。
    cost_portfolio["turnover"] = cost_portfolio["turnover"].fillna(0.0)
    # 根据“组合收益减去换手率乘佣金费率”计算净收益。
    cost_portfolio["net_return"] = cost_portfolio["monthly_return"] - cost_portfolio["turnover"] * commission_cost
    # 计算扣除交易成本后的累计净值。
    cost_portfolio["net_nav"] = (1 + cost_portfolio["net_return"]).cumprod()
    # 计算成本后净值的历史最高点。
    cost_portfolio["net_running_max"] = cost_portfolio["net_nav"].cummax()
    # 计算成本后回撤。
    cost_portfolio["net_drawdown"] = cost_portfolio["net_nav"] / cost_portfolio["net_running_max"] - 1
    # 返回成本后组合序列。
    return cost_portfolio


def calculate_cost_metrics(cost_portfolio: pd.DataFrame, commission_cost=COMMISSION_COST) -> pd.DataFrame:
    """计算扣除交易成本后的绩效和平均月换手率。"""
    # 没有有效收益时停止计算。
    if cost_portfolio.empty:
        raise ValueError("成本后组合为空，无法计算绩效指标。")
    # 获取可回测月数。
    months = len(cost_portfolio)
    # 计算成本后累计收益。
    cumulative_return = cost_portfolio["net_nav"].iloc[-1] - 1
    # 计算成本后年化收益。
    annual_return = cost_portfolio["net_nav"].iloc[-1] ** (12 / months) - 1
    # 计算成本后月度与年化波动率。
    monthly_volatility = cost_portfolio["net_return"].std(ddof=1)
    annualized_volatility = monthly_volatility * np.sqrt(12)
    # 假设无风险利率为零，计算成本后年化夏普比率。
    sharpe_ratio = cost_portfolio["net_return"].mean() / monthly_volatility * np.sqrt(12) if monthly_volatility else np.nan
    # 提取成本后最大回撤。
    max_drawdown = cost_portfolio["net_drawdown"].min()
    # 计算参与回测月份的平均换手率。
    average_turnover = cost_portfolio["turnover"].mean()
    # 汇总为一行指标表。
    return pd.DataFrame([{
        "months": months,
        "commission_cost": commission_cost,
        "cumulative_return": cumulative_return,
        "annual_return": annual_return,
        "annualized_volatility": annualized_volatility,
        "annualized_sharpe": sharpe_ratio,
        "max_drawdown": max_drawdown,
        "average_monthly_turnover": average_turnover,
    }])


def save_portfolio_results(portfolio: pd.DataFrame, metrics: pd.DataFrame) -> None:
    """保存组合净值序列和绩效指标。"""
    # 创建输出目录。
    RETURN_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    # 保存月收益、净值和回撤。
    portfolio.to_csv(RETURN_OUTPUT_PATH, index=False, encoding="utf-8-sig")
    # 保存汇总绩效指标。
    metrics.to_csv(METRICS_OUTPUT_PATH, index=False, encoding="utf-8-sig")


def save_cost_results(cost_portfolio: pd.DataFrame, cost_metrics: pd.DataFrame) -> None:
    """保存成本后组合净值序列和绩效指标。"""
    # 创建成本后结果目录。
    COST_RETURN_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    # 保存成本后每期收益、换手率、净值和回撤。
    cost_portfolio.to_csv(COST_RETURN_OUTPUT_PATH, index=False, encoding="utf-8-sig")
    # 保存成本后汇总指标。
    cost_metrics.to_csv(COST_METRICS_OUTPUT_PATH, index=False, encoding="utf-8-sig")


if __name__ == "__main__":
    # 运行组合回测。
    portfolio_result = run_portfolio_backtest()
    # 计算组合绩效。
    portfolio_metrics = calculate_metrics(portfolio_result)
    # 保存结果。
    save_portfolio_results(portfolio_result, portfolio_metrics)
    # 计算并保存月度换手率。
    turnover_result = calculate_turnover()
    save_turnover(turnover_result)
    # 基于换手率计算并保存交易成本后的回测结果。
    cost_portfolio_result = run_cost_backtest(portfolio_result, turnover_result)
    cost_metrics = calculate_cost_metrics(cost_portfolio_result)
    save_cost_results(cost_portfolio_result, cost_metrics)
    # 打印核心绩效。
    print(portfolio_metrics.round(4))
    print("扣除交易成本后的绩效：")
    print(cost_metrics.round(4))
    print(f"组合绩效已保存至：{METRICS_OUTPUT_PATH.resolve()}")
