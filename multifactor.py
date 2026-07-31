"""
Multi-Factor Portfolio Construction Module

Purpose:
Construct stock ranking score based on
multiple fundamental factors.

Method:
Composite Score =
PE Score
+
ROE Score
+
Revenue Growth Score

Portfolio:
- Rank stocks by score
- Select high-score stocks
- Equal-weight allocation
- Monthly rebalance

Author:
Ma Yanlong

构造 EP、ROE、营收增长率等权合成的多因子选股信号。
"""

# 导入 Path 处理文件路径。
from pathlib import Path
# 导入 pandas 处理表格数据。
import pandas as pd


# 设置因子收益数据路径。
INPUT_PATH = Path("data/processed/factor_return.csv")
# 设置多因子打分结果路径。
OUTPUT_PATH = Path("data/processed/multifactor_score.csv")


def build_multifactor_score(input_path=INPUT_PATH) -> pd.DataFrame:
    """计算等权综合得分，并标记每月得分最高的 20% 股票。"""
    # 确认输入文件存在。
    if not Path(input_path).exists():
        raise FileNotFoundError(f"未找到因子收益数据：{input_path}。请先运行 return_calculator.py。")
    # 读取因子和未来收益数据。
    data = pd.read_csv(input_path, parse_dates=["trade_date"])
    # 三个标准化因子方向已经统一，直接做简单等权平均。
    data["score"] = (data["ep_z"] + data["roe_z"] + data["revenue_growth_z"]) / 3
    # 在每个调仓日内计算得分百分位，数值越接近 1 表示得分越高。
    data["score_percentile"] = data.groupby("trade_date")["score"].rank(pct=True, method="first")
    # 标记每月综合得分最高的 20% 股票作为持仓候选。
    data["selected"] = data["score_percentile"] >= 0.8
    # 按日期和股票代码排序。
    return data.sort_values(["trade_date", "code"]).reset_index(drop=True)


def save_multifactor_score(data: pd.DataFrame, output_path=OUTPUT_PATH) -> Path:
    """保存多因子综合得分和选股结果。"""
    # 创建输出目录。
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    # 保存 CSV 文件。
    data.to_csv(output_path, index=False, encoding="utf-8-sig")
    # 返回输出路径。
    return output_path


if __name__ == "__main__":
    # 计算多因子综合得分。
    multifactor_data = build_multifactor_score()
    # 保存结果。
    saved_file = save_multifactor_score(multifactor_data)
    # 输出每期平均入选股票数量。
    average_selected = multifactor_data.groupby("trade_date")["selected"].sum().mean()
    print(f"多因子得分已保存至：{saved_file.resolve()}，每期平均选股数：{average_selected:.0f}")
