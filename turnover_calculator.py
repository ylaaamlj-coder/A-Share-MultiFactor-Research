"""计算等权多因子组合在相邻调仓日之间的目标权重换手率。"""

# 导入 Path 处理项目相对路径。
from pathlib import Path
# 导入 pandas 处理股票权重表。
import pandas as pd


# 设置多因子选股结果路径。
INPUT_PATH = Path("data/processed/multifactor_score.csv")
# 设置换手率结果路径。
OUTPUT_PATH = Path("outputs/tables/turnover.csv")


def _to_bool(series: pd.Series) -> pd.Series:
    """兼容 CSV 中的 True/False 字符串和布尔值。"""
    # 统一转换为小写字符串后判断是否为 true。
    return series.astype(str).str.lower().eq("true")


def calculate_turnover(input_path=INPUT_PATH) -> pd.DataFrame:
    """按“权重绝对变化之和除以二”计算每月目标权重换手率。"""
    # 检查多因子打分文件是否存在。
    if not Path(input_path).exists():
        raise FileNotFoundError(f"未找到多因子得分文件：{input_path}。请先运行 multifactor.py。")
    # 读取每期股票是否入选的结果。
    data = pd.read_csv(input_path, parse_dates=["trade_date"])
    # 只保留综合得分最高 20% 的目标持仓股票。
    selected = data.loc[_to_bool(data["selected"]), ["trade_date", "code"]].copy()
    # 创建列表保存每期换手率。
    records = []
    # 初始化上一期的目标权重；第一期默认从现金建仓。
    previous_weights = {}
    # 按调仓日依次计算换手。
    for trade_date, monthly_data in selected.groupby("trade_date", sort=True):
        # 获取本期入选股票代码。
        codes = monthly_data["code"].tolist()
        # 本项目使用等权配置，因此每只股票权重相同。
        current_weights = {code: 1.0 / len(codes) for code in codes}
        # 第一期从空仓建仓，按包含现金头寸的标准将换手率记为 1。
        if not previous_weights:
            turnover = 1.0
        else:
            # 取本期和上期所有股票的并集，未持有时权重视为零。
            all_codes = set(previous_weights) | set(current_weights)
            # 计算买卖两侧权重变化绝对值之和的一半。
            turnover = sum(abs(current_weights.get(code, 0.0) - previous_weights.get(code, 0.0)) for code in all_codes) / 2
        # 保存本期调仓日、持仓数和换手率。
        records.append({"trade_date": trade_date, "selected_count": len(codes), "turnover": turnover})
        # 将本期权重保存为下一期的上一期权重。
        previous_weights = current_weights
    # 返回按日期排序的换手率表。
    return pd.DataFrame(records).sort_values("trade_date").reset_index(drop=True)


def save_turnover(turnover_data: pd.DataFrame, output_path=OUTPUT_PATH) -> Path:
    """保存换手率结果。"""
    # 创建输出目录。
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    # 保存为 CSV。
    turnover_data.to_csv(output_path, index=False, encoding="utf-8-sig")
    # 返回输出路径。
    return output_path


if __name__ == "__main__":
    # 计算换手率。
    turnover_result = calculate_turnover()
    # 保存换手率。
    saved_file = save_turnover(turnover_result)
    # 输出平均换手率，方便快速检查。
    print(f"换手率已保存至：{saved_file.resolve()}，平均月换手率：{turnover_result['turnover'].mean():.2%}")
