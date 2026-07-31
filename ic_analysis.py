"""使用 Rank IC 检验三个基本面因子与未来一个月收益的相关性。"""

# 导入 Path 处理文件路径。
from pathlib import Path
# 导入 pandas 处理表格数据和相关系数计算。
import pandas as pd


# 设置因子收益数据路径。
INPUT_PATH = Path("data/processed/factor_return.csv")
# 设置逐月 IC 结果路径。
MONTHLY_OUTPUT_PATH = Path("outputs/ic_monthly.csv")
# 设置 IC 汇总报告路径。
REPORT_OUTPUT_PATH = Path("outputs/ic_report.csv")
# 设置待检验的标准化因子列。
FACTOR_COLUMNS = ["ep_z", "roe_z", "revenue_growth_z"]


def calculate_rank_ic(data: pd.DataFrame) -> pd.DataFrame:
    """逐月计算因子排名和未来收益排名之间的 Spearman 相关系数。"""
    # 创建列表，用于保存每个月、每个因子的 IC。
    records = []
    # 逐个调仓日进行横截面检验。
    for trade_date, monthly_data in data.groupby("trade_date"):
        # 删除没有未来收益的末期样本。
        valid_data = monthly_data.dropna(subset=["future_return"])
        # 逐个因子计算 Rank IC。
        for factor in FACTOR_COLUMNS:
            # 同时删除因子和收益中可能存在的缺失值。
            sample = valid_data[[factor, "future_return"]].dropna()
            # 样本不足时无法得到有意义的横截面相关系数。
            if len(sample) >= 5:
                # 分别对因子和收益进行横截面排名。
                factor_rank = sample[factor].rank(method="average")
                return_rank = sample["future_return"].rank(method="average")
                # 排名后的 Pearson 相关系数就是 Spearman Rank IC，且不依赖 scipy。
                rank_ic = factor_rank.corr(return_rank)
            else:
                # 样本不足时保留为空值。
                rank_ic = float("nan")
            # 保存当期计算结果。
            records.append({"trade_date": trade_date, "factor": factor, "rank_ic": rank_ic, "sample_size": len(sample)})
    # 将记录整理为 DataFrame。
    return pd.DataFrame(records)


def summarize_ic(monthly_ic: pd.DataFrame) -> pd.DataFrame:
    """计算 IC 均值、标准差、ICIR 和正 IC 比例。"""
    # 按因子汇总统计指标。
    summary = monthly_ic.groupby("factor")["rank_ic"].agg(["mean", "std", "count"])
    # 将统计列改为更清楚的名称。
    summary = summary.rename(columns={"mean": "ic_mean", "std": "ic_std", "count": "valid_months"})
    # ICIR 定义为 IC 均值除以 IC 标准差。
    summary["icir"] = summary["ic_mean"] / summary["ic_std"]
    # 计算 IC 为正的月份比例。
    summary["positive_ic_ratio"] = monthly_ic.groupby("factor")["rank_ic"].apply(lambda values: (values.dropna() > 0).mean())
    # 将因子名从索引恢复为普通列。
    return summary.reset_index()


def run_ic_analysis(input_path=INPUT_PATH):
    """读取数据并返回逐月 IC 与汇总 IC 两张表。"""
    # 确认输入文件存在。
    if not Path(input_path).exists():
        raise FileNotFoundError(f"未找到因子收益数据：{input_path}。请先运行 return_calculator.py。")
    # 读取因子收益数据。
    data = pd.read_csv(input_path, parse_dates=["trade_date"])
    # 计算逐月 IC。
    monthly_ic = calculate_rank_ic(data)
    # 计算汇总指标。
    ic_report = summarize_ic(monthly_ic)
    # 返回两份结果。
    return monthly_ic, ic_report


def save_ic_results(monthly_ic: pd.DataFrame, ic_report: pd.DataFrame) -> None:
    """保存逐月 IC 和 IC 汇总报告。"""
    # 创建输出文件夹。
    MONTHLY_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    # 保存逐月 IC，供绘图使用。
    monthly_ic.to_csv(MONTHLY_OUTPUT_PATH, index=False, encoding="utf-8-sig")
    # 保存面试展示时更常用的汇总指标表。
    ic_report.to_csv(REPORT_OUTPUT_PATH, index=False, encoding="utf-8-sig")


if __name__ == "__main__":
    # 执行 IC 分析。
    monthly_ic_data, ic_summary = run_ic_analysis()
    # 保存分析结果。
    save_ic_results(monthly_ic_data, ic_summary)
    # 输出汇总结果。
    print(ic_summary.round(4))
    print(f"IC 报告已保存至：{REPORT_OUTPUT_PATH.resolve()}")
