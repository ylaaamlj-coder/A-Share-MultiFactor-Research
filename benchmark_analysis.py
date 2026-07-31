"""比较多因子策略与真实沪深300月度基准，并输出超额收益分析。"""

# 在导入 pyplot 前设置无界面绘图模式。
import matplotlib
matplotlib.use("Agg")
# 导入绘图工具。
import matplotlib.pyplot as plt
# 导入 Path 处理项目相对路径。
from pathlib import Path
# 导入 numpy 计算年化指标。
import numpy as np
# 导入 pandas 读取和处理回测结果。
import pandas as pd


# 按用户要求优先读取复数形式的策略收益文件。
PRIMARY_STRATEGY_PATH = Path("outputs/portfolio_returns.csv")
# 兼容项目现有的单数形式文件，不修改任何既有回测模块。
FALLBACK_STRATEGY_PATH = Path("outputs/portfolio_return.csv")
# 设置沪深300月末收盘价路径。
BENCHMARK_PATH = Path("data/raw/hs300_monthly.csv")
# 设置对比明细表路径。
COMPARE_OUTPUT_PATH = Path("outputs/tables/benchmark_compare.csv")
# 设置文字报告路径。
REPORT_OUTPUT_PATH = Path("outputs/benchmark_report.txt")
# 设置策略与基准净值图路径。
NAV_CHART_PATH = Path("outputs/charts/strategy_vs_hs300.png")
# 设置累计超额收益图路径。
EXCESS_CHART_PATH = Path("outputs/charts/excess_return.png")


def _load_strategy_returns() -> pd.DataFrame:
    """读取现有策略月收益，优先使用 portfolio_returns.csv。"""
    # 根据文件是否存在确定实际策略文件。
    strategy_path = PRIMARY_STRATEGY_PATH if PRIMARY_STRATEGY_PATH.exists() else FALLBACK_STRATEGY_PATH
    # 两个文件都不存在时停止。
    if not strategy_path.exists():
        raise FileNotFoundError("未找到 outputs/portfolio_returns.csv 或 outputs/portfolio_return.csv。请先运行 backtest_portfolio.py。")
    # 读取策略结果。
    strategy = pd.read_csv(strategy_path, parse_dates=["trade_date"])
    # 检查现有回测结果所需字段。
    required_columns = {"trade_date", "monthly_return"}
    if not required_columns.issubset(strategy.columns):
        raise ValueError(f"策略收益文件缺少必要字段：{sorted(required_columns - set(strategy.columns))}")
    # 统一字段名称为 date 和 strategy_return。
    strategy = strategy[["trade_date", "monthly_return"]].rename(columns={"trade_date": "date", "monthly_return": "strategy_return"})
    # 返回按日期排序的策略月收益。
    return strategy.sort_values("date").reset_index(drop=True)


def _load_benchmark_returns() -> pd.DataFrame:
    """读取沪深300月末收盘价，并计算从当月到下月的基准收益。"""
    # 基准文件缺失时直接报错，不使用替代或伪造数据。
    if not BENCHMARK_PATH.exists():
        raise FileNotFoundError("未找到 data/raw/hs300_monthly.csv。请先运行 benchmark.py 获取真实沪深300基准数据。")
    # 读取指数月末收盘价。
    benchmark = pd.read_csv(BENCHMARK_PATH, parse_dates=["date"])
    # 检查指数文件必要字段。
    required_columns = {"date", "close"}
    if not required_columns.issubset(benchmark.columns):
        raise ValueError(f"沪深300基准文件缺少必要字段：{sorted(required_columns - set(benchmark.columns))}")
    # 按日期排序，避免 shift 方向错误。
    benchmark = benchmark[["date", "close"]].sort_values("date").drop_duplicates("date").reset_index(drop=True)
    # 计算从当前月末到下一月末的沪深300收益率。
    benchmark["benchmark_return"] = benchmark["close"].shift(-1) / benchmark["close"] - 1
    # 最后一个月没有下一期价格，删除该无效收益。
    return benchmark.dropna(subset=["benchmark_return"])[["date", "benchmark_return"]]


def build_comparison() -> pd.DataFrame:
    """对齐策略和基准收益，计算净值、超额收益与超额回撤。"""
    # 读取策略月收益。
    strategy = _load_strategy_returns()
    # 读取沪深300月收益。
    benchmark = _load_benchmark_returns()
    # 严格按调仓日内连接，缺少任一期基准时不继续计算。
    compare = strategy.merge(benchmark, on="date", how="left")
    # 找出缺失基准收益的日期。
    missing_dates = compare.loc[compare["benchmark_return"].isna(), "date"]
    if not missing_dates.empty:
        missing_text = "、".join(missing_dates.dt.strftime("%Y-%m-%d"))
        raise RuntimeError(f"沪深300基准收益缺少以下策略调仓日：{missing_text}。不使用不完整基准进行比较。")
    # 计算策略累计净值。
    compare["strategy_nav"] = (1 + compare["strategy_return"]).cumprod()
    # 计算沪深300累计净值。
    compare["benchmark_nav"] = (1 + compare["benchmark_return"]).cumprod()
    # 计算每月算术超额收益。
    compare["excess_return"] = compare["strategy_return"] - compare["benchmark_return"]
    # 计算相对净值，用于描述累计超额收益。
    compare["relative_nav"] = compare["strategy_nav"] / compare["benchmark_nav"]
    # 累计超额收益定义为策略净值相对基准净值的超额部分。
    compare["cumulative_excess_return"] = compare["relative_nav"] - 1
    # 计算超额净值从历史最高相对净值的回撤。
    compare["excess_drawdown"] = compare["relative_nav"] / compare["relative_nav"].cummax() - 1
    # 返回完整对比表。
    return compare


def _annual_return(nav: float, months: int) -> float:
    """根据累计净值和月数计算年化收益。"""
    # 月数为零时无法年化。
    if months == 0:
        return np.nan
    # 返回年化收益率。
    return nav ** (12 / months) - 1


def calculate_report_metrics(compare: pd.DataFrame) -> dict:
    """计算策略、基准和超额收益所需的核心指标。"""
    # 获取有效回测月份。
    months = len(compare)
    # 获取策略累计净值。
    strategy_nav = compare["strategy_nav"].iloc[-1]
    # 获取基准累计净值。
    benchmark_nav = compare["benchmark_nav"].iloc[-1]
    # 计算策略最大回撤。
    strategy_drawdown = compare["strategy_nav"] / compare["strategy_nav"].cummax() - 1
    # 计算策略年化波动率和夏普比率；无风险利率假设为零。
    strategy_monthly_volatility = compare["strategy_return"].std(ddof=1)
    strategy_sharpe = compare["strategy_return"].mean() / strategy_monthly_volatility * np.sqrt(12) if strategy_monthly_volatility else np.nan
    # 计算主动收益的年化信息比率。
    active_volatility = compare["excess_return"].std(ddof=1)
    information_ratio = compare["excess_return"].mean() / active_volatility * np.sqrt(12) if active_volatility else np.nan
    # 汇总并返回指标。
    return {
        "months": months,
        "strategy_cumulative_return": strategy_nav - 1,
        "strategy_annual_return": _annual_return(strategy_nav, months),
        "strategy_max_drawdown": strategy_drawdown.min(),
        "strategy_sharpe": strategy_sharpe,
        "benchmark_cumulative_return": benchmark_nav - 1,
        "benchmark_annual_return": _annual_return(benchmark_nav, months),
        "excess_cumulative_return": compare["cumulative_excess_return"].iloc[-1],
        "excess_annual_return": _annual_return(compare["relative_nav"].iloc[-1], months),
        "information_ratio": information_ratio,
        "excess_max_drawdown": compare["excess_drawdown"].min(),
    }


def save_report(metrics: dict) -> Path:
    """保存中文基准比较报告。"""
    # 创建输出目录。
    REPORT_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    # 组织报告文本。
    report = "\n".join([
        "沪深300基准比较报告",
        "=" * 32,
        f"有效回测月数：{metrics['months']}",
        "",
        "策略：",
        f"累计收益：{metrics['strategy_cumulative_return']:.2%}",
        f"年化收益：{metrics['strategy_annual_return']:.2%}",
        f"最大回撤：{metrics['strategy_max_drawdown']:.2%}",
        f"夏普比率：{metrics['strategy_sharpe']:.4f}",
        "",
        "沪深300基准：",
        f"累计收益：{metrics['benchmark_cumulative_return']:.2%}",
        f"年化收益：{metrics['benchmark_annual_return']:.2%}",
        "",
        "超额收益：",
        f"累计超额收益：{metrics['excess_cumulative_return']:.2%}",
        f"年化超额收益：{metrics['excess_annual_return']:.2%}",
        f"信息比率 IR：{metrics['information_ratio']:.4f}",
        f"超额最大回撤：{metrics['excess_max_drawdown']:.2%}",
    ])
    # 写入报告文件。
    REPORT_OUTPUT_PATH.write_text(report, encoding="utf-8")
    # 返回路径。
    return REPORT_OUTPUT_PATH


def plot_charts(compare: pd.DataFrame) -> tuple[Path, Path]:
    """绘制策略基准净值图与累计超额收益图。"""
    # 创建图表目录。
    NAV_CHART_PATH.parent.mkdir(parents=True, exist_ok=True)
    # 设置中文字体候选。
    plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "Arial Unicode MS"]
    plt.rcParams["axes.unicode_minus"] = False
    # 绘制策略和沪深300净值。
    nav_fig, nav_ax = plt.subplots(figsize=(10, 5))
    nav_ax.plot(compare["date"], compare["strategy_nav"], label="多因子策略", linewidth=2)
    nav_ax.plot(compare["date"], compare["benchmark_nav"], label="沪深300", linewidth=2)
    nav_ax.set(title="多因子策略与沪深300累计净值", xlabel="调仓日", ylabel="累计净值")
    nav_ax.legend()
    nav_fig.tight_layout()
    nav_fig.savefig(NAV_CHART_PATH, dpi=150)
    plt.close(nav_fig)
    # 绘制策略相对沪深300的累计超额收益。
    excess_fig, excess_ax = plt.subplots(figsize=(10, 5))
    excess_ax.plot(compare["date"], compare["cumulative_excess_return"], label="累计超额收益", color="tab:purple", linewidth=2)
    excess_ax.axhline(0, color="black", linewidth=0.8)
    excess_ax.set(title="多因子策略相对沪深300的累计超额收益", xlabel="调仓日", ylabel="累计超额收益")
    excess_ax.legend()
    excess_fig.tight_layout()
    excess_fig.savefig(EXCESS_CHART_PATH, dpi=150)
    plt.close(excess_fig)
    # 返回两个图表路径。
    return NAV_CHART_PATH, EXCESS_CHART_PATH


def run_benchmark_analysis() -> tuple[pd.DataFrame, dict]:
    """执行基准比较，保存对比表、文字报告和两张图表。"""
    # 构造策略与基准的月度比较表。
    compare = build_comparison()
    # 计算汇总指标。
    metrics = calculate_report_metrics(compare)
    # 创建对比表目录并保存明细。
    COMPARE_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    compare.to_csv(COMPARE_OUTPUT_PATH, index=False, encoding="utf-8-sig")
    # 保存文字报告和图表。
    save_report(metrics)
    plot_charts(compare)
    # 返回结果供 main.py 调用。
    return compare, metrics


if __name__ == "__main__":
    # 单独运行时完成基准比较。
    comparison, report_metrics = run_benchmark_analysis()
    # 输出主要文件位置。
    print(f"基准比较报告已保存至：{REPORT_OUTPUT_PATH.resolve()}")
    print(f"策略与基准净值图已保存至：{NAV_CHART_PATH.resolve()}")
    print(f"累计超额收益图已保存至：{EXCESS_CHART_PATH.resolve()}")
