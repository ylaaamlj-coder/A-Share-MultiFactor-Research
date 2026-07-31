"""计算每只股票从当前月末到下月月末的前瞻一个月收益率。"""

# 导入 Path 处理文件路径。
from pathlib import Path
# 导入 pandas 处理表格数据。
import pandas as pd


# 设置因子处理结果路径。
INPUT_PATH = Path("data/processed/factor_processed.csv")
# 设置原始价格数据路径，用于取得下一期价格而不受下一期因子缺失影响。
RAW_PRICE_PATH = Path("data/raw/csi300_monthly_raw.csv")
# 设置因子与未来收益合并后的输出路径。
OUTPUT_PATH = Path("data/processed/factor_return.csv")


def calculate_future_returns(input_path=INPUT_PATH) -> pd.DataFrame:
    """按照股票代码计算下个月月末价格和未来一个月收益率。"""
    # 检查输入文件是否存在。
    if not Path(input_path).exists():
        raise FileNotFoundError(f"未找到因子数据：{input_path}。请先运行 factor_process.py。")
    # 读取当前期可用于选股的因子数据。
    data = pd.read_csv(input_path, parse_dates=["trade_date"])
    # 检查原始价格文件是否存在。
    if not RAW_PRICE_PATH.exists():
        raise FileNotFoundError(f"未找到原始价格数据：{RAW_PRICE_PATH}。请先运行 data_fetch.py。")
    # 读取原始月末价格；即使下期因子缺失，仍尽量保留真实的下期价格。
    raw_prices = pd.read_csv(RAW_PRICE_PATH, parse_dates=["trade_date"])
    # 获取完整月末交易日序列。
    trade_dates = sorted(raw_prices["trade_date"].drop_duplicates())
    # 为每个调仓日建立下一月末调仓日映射。
    next_date_map = dict(zip(trade_dates[:-1], trade_dates[1:]))
    # 给当前期因子数据添加下一个月末日期。
    data["next_trade_date"] = data["trade_date"].map(next_date_map)
    # 准备下一期价格表，并将日期列改名以便合并。
    next_prices = raw_prices[["trade_date", "code", "close"]].rename(columns={"trade_date": "next_trade_date", "close": "next_close"})
    # 按股票代码和下期日期合并真实下期月末价格。
    data = data.merge(next_prices, on=["next_trade_date", "code"], how="left")
    # 计算未来一个月收益率；最后一个调仓日会自然为空。
    data["future_return"] = data["next_close"] / data["close"] - 1
    # 重新按日期和代码排序，便于后续横截面分析。
    data = data.sort_values(["trade_date", "code"]).reset_index(drop=True)
    # 返回包含未来收益的数据。
    return data


def save_future_returns(data: pd.DataFrame, output_path=OUTPUT_PATH) -> Path:
    """保存因子和未来收益数据。"""
    # 创建输出文件夹。
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    # 保存 CSV 文件。
    data.to_csv(output_path, index=False, encoding="utf-8-sig")
    # 返回保存路径。
    return output_path


if __name__ == "__main__":
    # 计算未来收益率。
    factor_return_data = calculate_future_returns()
    # 保存结果。
    saved_file = save_future_returns(factor_return_data)
    # 输出可用于回测的样本数。
    valid_count = factor_return_data["future_return"].notna().sum()
    print(f"未来收益数据已保存至：{saved_file.resolve()}，可回测记录数：{valid_count}")
