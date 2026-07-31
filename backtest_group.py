"""对 EP、ROE、营收增长率分别进行月频五分组回测。"""

# 导入 Path 处理文件路径。
from pathlib import Path
# 导入 pandas 处理表格数据。
import pandas as pd


# 设置因子收益数据路径。
INPUT_PATH = Path("data/processed/factor_return.csv")
# 设置五分组回测结果路径。
OUTPUT_PATH = Path("outputs/group_return.csv")
# 设置待检验的标准化因子。
FACTOR_COLUMNS = ["ep_z", "roe_z", "revenue_growth_z"]


def assign_five_groups(series: pd.Series) -> pd.Series:
    """按因子从低到高分为五组；Group5 表示因子值最高的一组。"""
    # 先用 first 方法打破并列值，确保 qcut 在样本充足时能稳定分组。
    ranks = series.rank(method="first")
    # 将排名切分为五个尽量等数量的组，并从 1 开始编号。
    return pd.qcut(ranks, q=5, labels=[1, 2, 3, 4, 5]).astype(int)


def run_group_backtest(input_path=INPUT_PATH) -> pd.DataFrame:
    """计算每个因子的五组月收益和累计净值。"""
    # 确认输入文件存在。
    if not Path(input_path).exists():
        raise FileNotFoundError(f"未找到因子收益数据：{input_path}。请先运行 return_calculator.py。")
    # 读取因子收益数据。
    data = pd.read_csv(input_path, parse_dates=["trade_date"])
    # 删除没有未来收益的最后一期记录。
    data = data.dropna(subset=["future_return"]).copy()
    # 创建列表保存各因子的分组结果。
    all_results = []
    # 逐个因子进行回测。
    for factor in FACTOR_COLUMNS:
        # 复制当期因子和未来收益。
        factor_data = data[["trade_date", factor, "future_return"]].dropna().copy()
        # 每个月独立排序分组，保证是横截面回测。
        factor_data["group"] = factor_data.groupby("trade_date")[factor].transform(assign_five_groups)
        # 计算每个月、每个组内股票的等权平均收益。
        group_result = factor_data.groupby(["trade_date", "group"], as_index=False)["future_return"].mean()
        # 改名为月收益，避免与个股未来收益混淆。
        group_result = group_result.rename(columns={"future_return": "monthly_return"})
        # 添加因子名称。
        group_result["factor"] = factor
        # 按组内时间顺序计算累计净值，初始净值为 1。
        group_result = group_result.sort_values(["group", "trade_date"])
        group_result["net_value"] = group_result.groupby("group")["monthly_return"].transform(lambda values: (1 + values).cumprod())
        # 收集当前因子结果。
        all_results.append(group_result)
    # 合并三类因子的回测结果。
    result = pd.concat(all_results, ignore_index=True)
    # 按因子、日期和组别排序。
    return result.sort_values(["factor", "trade_date", "group"]).reset_index(drop=True)


def save_group_results(data: pd.DataFrame, output_path=OUTPUT_PATH) -> Path:
    """保存五分组回测结果。"""
    # 创建输出目录。
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    # 保存回测长表。
    data.to_csv(output_path, index=False, encoding="utf-8-sig")
    # 返回输出路径。
    return output_path


if __name__ == "__main__":
    # 执行五分组回测。
    group_returns = run_group_backtest()
    # 保存结果。
    saved_file = save_group_results(group_returns)
    # 打印前几行方便检查。
    print(group_returns.head())
    print(f"分组回测结果已保存至：{saved_file.resolve()}")
