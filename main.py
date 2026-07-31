"""从 JQData 原始下载开始，一键运行 A 股基本面多因子研究流程。"""

# 导入 os，用于将工作目录固定为项目目录。
import os
# 导入 Path，定位 .env 和项目根目录。
from pathlib import Path
# 导入 sys，以便出现错误时向调用者返回失败状态。
import sys
# 导入 JQData 数据下载函数。
from data_fetch import DEFAULT_END_DATE, DEFAULT_START_DATE, fetch_monthly_dataset, login_jqdata, save_dataset
# 导入原始数据检查函数。
from data_check import build_report, load_data, save_report
# 导入数据清洗函数。
from data_cleaner import clean_data, save_clean_data
# 导入因子构建与处理函数。
from factor_process import process_factors, save_processed_factors
# 导入未来收益计算函数。
from return_calculator import calculate_future_returns, save_future_returns
# 导入 IC 分析函数。
from ic_analysis import run_ic_analysis, save_ic_results
# 导入五分组回测函数。
from backtest_group import run_group_backtest, save_group_results
# 导入多因子选股函数。
from multifactor import build_multifactor_score, save_multifactor_score
# 导入组合回测函数。
from backtest_portfolio import calculate_cost_metrics, calculate_metrics, run_cost_backtest, run_portfolio_backtest, save_cost_results, save_portfolio_results
# 导入换手率计算函数。
from turnover_calculator import calculate_turnover, save_turnover
# 导入绘图函数。
from visualization import create_all_charts
# 导入基准对比函数。
from benchmark_analysis import run_benchmark_analysis
# 导入沪深300基准数据下载函数。
from benchmark import fetch_hs300_monthly, save_hs300_monthly


# 获取 main.py 所在目录，作为整个项目的根目录。
PROJECT_DIR = Path(__file__).resolve().parent


def load_local_environment() -> None:
    """从项目根目录的 .env 加载 JQData 账号，支持直接运行 main.py。"""
    # 固定工作目录，确保各模块内的相对路径都指向本项目。
    os.chdir(PROJECT_DIR)
    # 定义本地账号文件路径。
    env_path = PROJECT_DIR / ".env"
    # .env 不存在时给出中文提示。
    if not env_path.exists():
        raise FileNotFoundError("未找到 .env 文件。请复制 .env.example 并重命名为 .env，再填写 JQData 账号。")
    # 尝试加载 python-dotenv，便于从 .env 读取账号。
    try:
        from dotenv import load_dotenv
    except ModuleNotFoundError as error:
        raise ModuleNotFoundError("缺少 python-dotenv。请执行：python -m pip install -r requirements.txt") from error
    # 加载 .env，保留系统中已有的环境变量。
    load_dotenv(env_path, override=False)


def fetch_raw_data() -> None:
    """登录 JQData 并下载当前配置日期范围内的原始研究数据。"""
    # 使用 .env 中的账号登录。
    login_jqdata()
    # 下载月末价格与基本面数据。
    raw_dataset = fetch_monthly_dataset(DEFAULT_START_DATE, DEFAULT_END_DATE)
    # 保存原始数据。
    saved_path = save_dataset(raw_dataset)
    # 输出下载结果。
    print(f"原始数据已保存至：{saved_path.resolve()}")


def check_raw_data() -> None:
    """生成原始数据质量检查报告。"""
    # 读取原始 CSV。
    raw_data = load_data()
    # 生成检查报告文本。
    report = build_report(raw_data)
    # 保存报告。
    save_report(report)
    # 打印报告，便于直接查看。
    print(report)


def run_research() -> None:
    """按完整顺序执行数据获取、因子检验、回测、基准分析和绘图。"""
    # 第零步：加载账号并固定项目工作目录。
    load_local_environment()
    # 第一步：从 JQData 下载原始数据。
    print("[1/12] 开始获取原始数据……")
    fetch_raw_data()
    # 第二步：检查原始数据质量。
    print("[2/12] 开始检查原始数据……")
    check_raw_data()
    # 第三步：清洗原始数据。
    print("[3/12] 开始清洗原始数据……")
    clean_data_frame = clean_data()
    save_clean_data(clean_data_frame)
    # 第四步：构造 EP、ROE 和营收增长率因子并做标准化。
    print("[4/12] 开始构造和处理因子……")
    processed_factor_data = process_factors()
    save_processed_factors(processed_factor_data)
    # 第五步：计算未来一个月收益率。
    print("[5/12] 开始计算未来收益率……")
    factor_return_data = calculate_future_returns()
    save_future_returns(factor_return_data)
    # 第六步：进行 Rank IC 分析。
    print("[6/12] 开始进行 IC 分析……")
    monthly_ic, ic_report = run_ic_analysis()
    save_ic_results(monthly_ic, ic_report)
    # 第七步：进行三个单因子的五分组回测。
    print("[7/12] 开始进行单因子五分组回测……")
    group_result = run_group_backtest()
    save_group_results(group_result)
    # 第八步：构建三个因子等权的综合得分。
    print("[8/12] 开始构建等权多因子组合……")
    multifactor_data = build_multifactor_score()
    save_multifactor_score(multifactor_data)
    # 第九步：计算原始与交易成本后的多因子组合绩效。
    print("[9/12] 开始进行多因子组合回测和交易成本模拟……")
    portfolio = run_portfolio_backtest()
    metrics = calculate_metrics(portfolio)
    save_portfolio_results(portfolio, metrics)
    turnover = calculate_turnover()
    save_turnover(turnover)
    cost_portfolio = run_cost_backtest(portfolio, turnover)
    cost_metrics = calculate_cost_metrics(cost_portfolio)
    save_cost_results(cost_portfolio, cost_metrics)
    # 第十步：生成 IC、分组和组合图表。
    print("[10/12] 开始生成基础研究图表……")
    create_all_charts()
    # 第十一步：通过 JQData 下载研究期内的沪深300月末收盘价。
    print("[11/12] 开始获取沪深300指数基准数据……")
    hs300_data = fetch_hs300_monthly()
    save_hs300_monthly(hs300_data)
    # 第十二步：计算策略相对沪深300的超额收益与信息比率。
    print("[12/12] 开始进行沪深300基准对比……")
    run_benchmark_analysis()
    # 打印原始与成本后的核心绩效，避免只展示未计成本的结果。
    print("\n研究流程已完成。原始组合核心指标：")
    print(metrics.round(4).to_string(index=False))
    print("\n扣除交易成本后的组合核心指标：")
    print(cost_metrics.round(4).to_string(index=False))


if __name__ == "__main__":
    # 直接运行该文件时执行完整研究流程，并提供中文错误提示。
    try:
        run_research()
    except (FileNotFoundError, ModuleNotFoundError, RuntimeError, ValueError) as error:
        print(f"\n运行终止：{error}")
        sys.exit(1)
