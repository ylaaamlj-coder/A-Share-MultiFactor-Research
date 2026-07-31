"""
Factor Processing Module

Functions:
- Fundamental factor cleaning
- Outlier treatment
- Factor normalization
- Factor score calculation

Factors:
- PE Ratio
- ROE
- Revenue Growth

Processing:
1% - 99% quantile based winsorization
and standardization.

Author:
Ma Yanlong

构造 EP、ROE、营收增长率因子，并按月进行去极值和标准化。
"""

# 导入 Path 处理文件路径。
from pathlib import Path
# 导入 numpy 处理标准差为零等数值问题。
import numpy as np
# 导入 pandas 处理表格数据。
import pandas as pd


# 设置清洗后数据路径。
INPUT_PATH = Path("data/processed/factor_clean.csv")
# 设置因子处理结果路径。
OUTPUT_PATH = Path("data/processed/factor_processed.csv")
# 设置需要横截面处理的原始因子。
RAW_FACTOR_COLUMNS = ["ep", "roe", "revenue_growth"]


def mad_winsorize(series: pd.Series, n=5.0) -> pd.Series:
    """使用 MAD 方法截断极端值，默认阈值为 5 倍 MAD。"""
    # 计算当前截面因子的中位数。
    median = series.median()
    # 计算中位数绝对偏差 MAD。
    mad = (series - median).abs().median()
    # 如果整列数值相同，直接返回原始值，避免除零或无意义截断。
    if pd.isna(mad) or mad == 0:
        return series
    # 根据常用正态一致性系数计算稳健标准差。
    robust_std = 1.4826 * mad
    # 计算下界。
    lower_bound = median - n * robust_std
    # 计算上界。
    upper_bound = median + n * robust_std
    # 将超过上下界的值截断，而不是删除股票。
    return series.clip(lower=lower_bound, upper=upper_bound)


def zscore(series: pd.Series) -> pd.Series:
    """在单个调仓日的横截面内进行 Z-score 标准化。"""
    # 计算截面均值。
    mean_value = series.mean()
    # 计算样本标准差。
    std_value = series.std(ddof=0)
    # 标准差为零时，所有股票没有横截面差异，统一赋值为零。
    if pd.isna(std_value) or np.isclose(std_value, 0):
        return pd.Series(0.0, index=series.index)
    # 返回均值为零、标准差为一的因子值。
    return (series - mean_value) / std_value


def process_factors(input_path=INPUT_PATH) -> pd.DataFrame:
    """计算三个原始因子，并逐月完成 MAD 去极值和 Z-score 标准化。"""
    # 检查清洗后数据是否存在。
    if not Path(input_path).exists():
        raise FileNotFoundError(f"未找到清洗后数据：{input_path}。请先运行 data_cleaner.py。")
    # 读取清洗后数据。
    data = pd.read_csv(input_path, parse_dates=["trade_date"])
    # 计算价值因子 EP；PE 已在清洗模块中保证大于零。
    data["ep"] = 1.0 / data["pe_ratio"]
    # ROE 和营收增长率数值越大通常代表质量和成长越好，方向无需反转。
    # 对每个调仓日分别做 MAD 去极值，避免跨期分布变化影响结果。
    for column in RAW_FACTOR_COLUMNS:
        data[f"{column}_mad"] = data.groupby("trade_date")[column].transform(mad_winsorize)
        # 对去极值后的因子做当期横截面 Z-score 标准化。
        data[f"{column}_z"] = data.groupby("trade_date")[f"{column}_mad"].transform(zscore)
    # 按日期和代码排序。
    data = data.sort_values(["trade_date", "code"]).reset_index(drop=True)
    # 返回处理后的因子数据。
    return data


def save_processed_factors(data: pd.DataFrame, output_path=OUTPUT_PATH) -> Path:
    """保存处理后的因子数据。"""
    # 创建输出目录。
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    # 保存 CSV 文件。
    data.to_csv(output_path, index=False, encoding="utf-8-sig")
    # 返回文件路径。
    return output_path


if __name__ == "__main__":
    # 执行因子构建和处理。
    processed_data = process_factors()
    # 保存结果。
    saved_file = save_processed_factors(processed_data)
    # 打印结果位置和关键列样例。
    print(f"处理后因子已保存至：{saved_file.resolve()}")
    print(processed_data[["trade_date", "code", "ep_z", "roe_z", "revenue_growth_z"]].head())
