"""清洗原始沪深300月频数据，为因子计算准备可用样本。"""

# 导入 Path 处理文件路径。
from pathlib import Path
# 导入 pandas 处理表格数据。
import pandas as pd


# 设置原始数据路径。
RAW_PATH = Path("data/raw/csi300_monthly_raw.csv")
# 设置清洗后数据路径。
OUTPUT_PATH = Path("data/processed/factor_clean.csv")
# 设置计算因子必须存在的字段。
REQUIRED_COLUMNS = ["trade_date", "code", "close", "pe_ratio", "roe", "revenue_growth"]


def clean_data(raw_path=RAW_PATH) -> pd.DataFrame:
    """读取原始数据，处理无效 PE 和缺失值，返回清洗后数据。"""
    # 确认原始文件存在，避免后续出现难理解的读取错误。
    if not Path(raw_path).exists():
        raise FileNotFoundError(f"未找到原始数据：{raw_path}。请先运行 data_fetch.py。")
    # 读取原始数据，并将调仓日解析为日期。
    data = pd.read_csv(raw_path, parse_dates=["trade_date"])
    # 检查必要字段是否完整。
    missing_columns = set(REQUIRED_COLUMNS) - set(data.columns)
    if missing_columns:
        raise ValueError(f"原始数据缺少字段：{sorted(missing_columns)}")
    # 输出清洗前各必要字段的缺失数量，便于定位数据质量问题。
    print("清洗前缺失值数量：")
    print(data[REQUIRED_COLUMNS].isna().sum().to_string())
    # 将 PE 小于等于零的记录设为缺失值；亏损公司的 PE 不适合计算 EP。
    data.loc[data["pe_ratio"] <= 0, "pe_ratio"] = pd.NA
    # 记录清洗前样本数，便于运行时检查。
    before_rows = len(data)
    # 删除任一必要字段缺失的记录，保证后续三个因子都可计算。
    data = data.dropna(subset=REQUIRED_COLUMNS).copy()
    # 删除同一股票、同一日期的重复记录，保留第一条。
    data = data.drop_duplicates(subset=["trade_date", "code"], keep="first")
    # 按日期和股票代码排序，便于人工查看与后续计算。
    data = data.sort_values(["trade_date", "code"]).reset_index(drop=True)
    # 打印本次实际删除的记录数。
    print(f"清洗完成：原始 {before_rows} 条，保留 {len(data)} 条，删除 {before_rows - len(data)} 条。")
    # 返回清洗后的数据。
    return data


def save_clean_data(data: pd.DataFrame, output_path=OUTPUT_PATH) -> Path:
    """保存清洗后的数据。"""
    # 创建处理后数据所在文件夹。
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    # 使用 utf-8-sig 编码，方便 Excel 打开。
    data.to_csv(output_path, index=False, encoding="utf-8-sig")
    # 返回输出路径。
    return output_path


if __name__ == "__main__":
    # 执行清洗。
    clean_dataset = clean_data()
    # 保存清洗结果。
    saved_file = save_clean_data(clean_dataset)
    # 打印结果位置和样例。
    print(f"清洗后数据已保存至：{saved_file.resolve()}")
    print(clean_dataset.head())
