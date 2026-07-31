"""检查沪深300月频原始数据的完整性和异常情况。"""

# 导入 Path，用于处理输入和输出文件路径。
from pathlib import Path
# 导入 pandas，用于读取和统计 CSV 数据。
import pandas as pd


# 定义原始数据文件路径。
INPUT_PATH = Path("data/raw/csi300_monthly_raw.csv")
# 定义检查报告的输出路径。
REPORT_PATH = Path("outputs/data_check_report.txt")
# 定义需要检查缺失值和异常值的基本面字段。
FACTOR_COLUMNS = ["pe_ratio", "roe", "revenue_growth"]


def load_data(input_path: Path = INPUT_PATH) -> pd.DataFrame:
    """读取原始 CSV，并将调仓日期转换为日期类型。"""
    # 如果原始数据还没有下载，给出易懂的提示。
    if not input_path.exists():
        raise FileNotFoundError(f"未找到数据文件：{input_path}。请先运行 data_fetch.py。")
    # 读取 CSV 文件，同时把 trade_date 解析为日期。
    data = pd.read_csv(input_path, parse_dates=["trade_date"])
    # 定义本项目原始数据必须具备的列。
    required_columns = {"trade_date", "code", "close", *FACTOR_COLUMNS}
    # 找出缺失的必要列。
    missing_columns = required_columns - set(data.columns)
    # 如果列名不完整，则停止检查并提示问题。
    if missing_columns:
        raise ValueError(f"数据缺少必要列：{sorted(missing_columns)}")
    # 返回已读取并完成基础校验的数据。
    return data


def calculate_outliers(series: pd.Series) -> dict:
    """使用 1% 和 99% 分位数识别极端值，仅用于报告，不删除数据。"""
    # 删除缺失值，防止缺失值影响分位数计算。
    valid_values = series.dropna()
    # 当一列全部缺失时，返回空统计结果。
    if valid_values.empty:
        return {"lower_bound": float("nan"), "upper_bound": float("nan"), "count": 0, "ratio": float("nan")}
    # 计算较低的 1% 分位数。
    lower_bound = valid_values.quantile(0.01)
    # 计算较高的 99% 分位数。
    upper_bound = valid_values.quantile(0.99)
    # 统计落在两个分位数之外的观测数量。
    outlier_count = ((valid_values < lower_bound) | (valid_values > upper_bound)).sum()
    # 计算异常值在非缺失样本中的比例。
    outlier_ratio = outlier_count / len(valid_values)
    # 返回异常值判断所需的统计量。
    return {"lower_bound": lower_bound, "upper_bound": upper_bound, "count": int(outlier_count), "ratio": outlier_ratio}


def build_report(data: pd.DataFrame) -> str:
    """根据原始数据生成文本格式的数据质量检查报告。"""
    # 统计总记录数。
    total_rows = len(data)
    # 统计不同股票代码的数量。
    stock_count = data["code"].nunique()
    # 统计不同月末调仓日的数量。
    date_count = data["trade_date"].nunique()
    # 获取最早调仓日期。
    start_date = data["trade_date"].min()
    # 获取最晚调仓日期。
    end_date = data["trade_date"].max()
    # 检查同一股票在同一调仓日是否重复出现。
    duplicate_count = data.duplicated(subset=["trade_date", "code"]).sum()
    # 创建报告首部内容。
    report_lines = [
        "A股基本面多因子研究：原始数据检查报告",
        "=" * 45,
        f"总记录数：{total_rows}",
        f"股票数量：{stock_count}",
        f"调仓日期数量：{date_count}",
        f"日期范围：{start_date:%Y-%m-%d} 至 {end_date:%Y-%m-%d}",
        f"重复的 股票-日期 记录数：{duplicate_count}",
        "",
        "一、缺失值比例",
    ]
    # 逐列计算基本面因子的缺失数量和缺失比例。
    for column in FACTOR_COLUMNS:
        # 统计当前因子的缺失数量。
        missing_count = data[column].isna().sum()
        # 计算当前因子的缺失比例。
        missing_ratio = missing_count / total_rows if total_rows else 0
        # 将统计结果添加至报告。
        report_lines.append(f"{column}：{missing_count} 条，{missing_ratio:.2%}")
    # 增加异常值部分标题和说明。
    report_lines.extend(["", "二、异常值检查", "说明：基本面因子以非缺失样本的 1% 和 99% 分位数作为极端值参考。"])
    # 单独检查负 PE，因为亏损公司 PE 通常为负，不宜直接用于 EP 因子计算。
    negative_pe_count = (data["pe_ratio"] <= 0).sum()
    # 将负 PE 数量写入报告。
    report_lines.append(f"PE 小于等于 0 的记录数：{negative_pe_count}")
    # 逐列汇报分位数异常值情况。
    for column in FACTOR_COLUMNS:
        # 调用函数计算当前列的异常值统计量。
        outlier_info = calculate_outliers(data[column])
        # 以可读格式写入当前列的异常值结果。
        report_lines.append(
            f"{column}：低于 {outlier_info['lower_bound']:.4f} 或高于 {outlier_info['upper_bound']:.4f} "
            f"的记录共 {outlier_info['count']} 条，占非缺失值 {outlier_info['ratio']:.2%}"
        )
    # 增加解释，避免把统计极端值误认为已处理数据。
    report_lines.extend(["", "提示：本文件只报告异常值，不会删除或修改原始数据。", "后续在 factor_process.py 中进行 PE 筛选、去极值和标准化处理。"])
    # 用换行符将报告内容拼接成字符串。
    return "\n".join(report_lines)


def save_report(report: str, report_path: Path = REPORT_PATH) -> None:
    """保存检查报告到 outputs 文件夹。"""
    # 自动创建输出目录。
    report_path.parent.mkdir(parents=True, exist_ok=True)
    # 使用 UTF-8 编码写入文本报告。
    report_path.write_text(report, encoding="utf-8")


if __name__ == "__main__":
    # 读取原始月频数据。
    raw_data = load_data()
    # 生成数据质量检查报告。
    check_report = build_report(raw_data)
    # 将报告保存到本地。
    save_report(check_report)
    # 同时在控制台打印报告，方便在 PyCharm 中立即查看。
    print(check_report)
    # 提示报告保存位置。
    print(f"\n报告已保存至：{REPORT_PATH.resolve()}")
