"""使用 JQData 获取沪深300指数的月末收盘价基准数据。"""

# 导入 os 读取 .env 加载后的 JQData 账号。
import os
# 导入 Path 处理项目相对路径。
from pathlib import Path
# 导入 pandas 处理交易日和指数价格。
import pandas as pd
# 导入 JQData 登录和行情接口。
from jqdatasdk import auth, get_price, is_auth


# 设置沪深300指数代码。
HS300_CODE = "000300.XSHG"
# 按用户要求优先使用复数形式的策略收益文件。
PRIMARY_PORTFOLIO_PATH = Path("outputs/portfolio_returns.csv")
# 兼容项目现有的单数形式策略收益文件，不修改既有回测模块。
FALLBACK_PORTFOLIO_PATH = Path("outputs/portfolio_return.csv")
# 现有股票原始数据保留最后一个月末价格，供基准收益计算最后一期使用。
RAW_STOCK_PATH = Path("data/raw/csi300_monthly_raw.csv")
# 设置沪深300月末收盘价保存路径。
OUTPUT_PATH = Path("data/raw/hs300_monthly.csv")


def login_jqdata() -> None:
    """使用环境变量中的 JQData 账号登录。"""
    # 定位项目根目录中的 .env，支持直接运行 benchmark.py。
    env_path = Path(__file__).resolve().parent / ".env"
    # .env 存在时加载账号配置。
    if env_path.exists():
        try:
            from dotenv import load_dotenv
        except ModuleNotFoundError as error:
            raise ModuleNotFoundError("缺少 python-dotenv。请执行：python -m pip install -r requirements.txt") from error
        load_dotenv(env_path, override=False)
    # 读取账号和密码。
    username = os.getenv("JQDATA_USERNAME")
    password = os.getenv("JQDATA_PASSWORD")
    # 未配置账号时给出明确提示。
    if not username or not password:
        raise RuntimeError("未找到 JQData 账号。请先配置 .env 中的 JQDATA_USERNAME 和 JQDATA_PASSWORD。")
    # 调用 JQData 登录接口。
    auth(username, password)
    # 验证当前 SDK 的登录状态。
    if not is_auth():
        raise RuntimeError("JQData 登录失败，无法下载沪深300基准数据。请检查账号、密码和网络。")


def get_research_month_end_dates() -> pd.DatetimeIndex:
    """读取策略调仓日，并补充最后一个月末作为最后一期基准收益终点。"""
    # 优先使用用户要求的 portfolio_returns.csv，兼容现有单数文件名。
    portfolio_path = PRIMARY_PORTFOLIO_PATH if PRIMARY_PORTFOLIO_PATH.exists() else FALLBACK_PORTFOLIO_PATH
    # 没有策略收益文件时无法确定回测区间。
    if not portfolio_path.exists():
        raise FileNotFoundError("未找到 outputs/portfolio_returns.csv 或 outputs/portfolio_return.csv。请先完成组合回测。")
    # 读取策略调仓日。
    portfolio_data = pd.read_csv(portfolio_path, parse_dates=["trade_date"])
    # 检查策略日期字段。
    if "trade_date" not in portfolio_data.columns:
        raise ValueError("策略收益文件缺少 trade_date 字段，无法匹配沪深300基准日期。")
    # 获取策略真实使用的调仓日。
    strategy_dates = pd.DatetimeIndex(sorted(portfolio_data["trade_date"].drop_duplicates()))
    # 原始股票数据存在时，补充其最后一个月末价格作为最后一期收益的结束日。
    if RAW_STOCK_PATH.exists():
        raw_dates = pd.read_csv(RAW_STOCK_PATH, usecols=["trade_date"], parse_dates=["trade_date"])
        last_raw_date = pd.to_datetime(raw_dates["trade_date"]).max()
        # 仅在最后原始日期晚于策略最后调仓日时才加入。
        if pd.notna(last_raw_date) and last_raw_date > strategy_dates.max():
            strategy_dates = strategy_dates.append(pd.DatetimeIndex([last_raw_date]))
    # 返回已排序、去重后的指数价格匹配日期。
    return pd.DatetimeIndex(sorted(strategy_dates.unique()))


def standardize_price_data(df: pd.DataFrame) -> pd.DataFrame:
    """兼容 JQData 的列日期、time 列和日期索引三种返回格式。"""
    # 直接存在 date 列时无需重置索引。
    if "date" not in df.columns:
        # 日期不在列中时，将索引转为普通列以便识别。
        df = df.reset_index()
    # 按常见 JQData 返回字段顺序寻找日期列。
    date_candidates = ["date", "time", "datetime", "index"]
    date_column = next((column for column in date_candidates if column in df.columns), None)
    # 无法识别日期列时给出实际列名，方便排查。
    if date_column is None:
        raise ValueError(f"JQData 返回的沪深300数据无法识别日期字段，实际列为：{list(df.columns)}")
    # 收盘价字段不存在时停止，避免生成错误基准。
    if "close" not in df.columns:
        raise ValueError(f"JQData 返回的沪深300数据缺少 close 字段，实际列为：{list(df.columns)}")
    # 统一日期字段和收盘价字段。
    normalized = df[[date_column, "close"]].rename(columns={date_column: "date"}).copy()
    # 统一为不含时分秒的日期。
    normalized["date"] = pd.to_datetime(normalized["date"], errors="coerce").dt.normalize()
    # 统一收盘价为浮点数。
    normalized["close"] = pd.to_numeric(normalized["close"], errors="coerce").astype(float)
    # 出现无法解析的日期或价格时不使用不完整结果。
    if normalized[["date", "close"]].isna().any().any():
        raise ValueError("JQData 返回的沪深300数据存在无法解析的日期或 close 值。")
    # 返回按日期排序、去重后的标准格式。
    return normalized.sort_values("date").drop_duplicates("date").reset_index(drop=True)


def fetch_hs300_monthly() -> pd.DataFrame:
    """下载研究期间每日指数收盘价，并筛选出项目月末调仓日收盘价。"""
    # 获取项目中实际使用的月末调仓日。
    month_end_dates = get_research_month_end_dates()
    # 日期为空时停止，避免请求无意义区间。
    if month_end_dates.empty:
        raise ValueError("原始股票数据中没有可用调仓日，无法获取沪深300基准。")
    # 登录 JQData。
    login_jqdata()
    # 一次获取研究区间内的指数日线收盘价，减少接口调用次数。
    df = get_price(
        security=HS300_CODE,
        start_date=month_end_dates.min().strftime("%Y-%m-%d"),
        end_date=month_end_dates.max().strftime("%Y-%m-%d"),
        frequency="daily",
        fields=["close"],
        panel=False,
    )
    # 输出真实返回格式，便于首次运行时定位 JQData 版本差异。
    print(df.columns)
    print(df.head())
    print(df.index)
    # 返回为空时说明账号权限不足、日期不允许或接口未返回数据。
    if df is None or df.empty:
        raise RuntimeError("JQData未返回沪深300数据，请检查账号权限或日期范围")
    # 将不同 JQData 返回格式统一为 date 和 close 两列。
    price_data = standardize_price_data(df)
    # 将项目月末调仓日也统一为不带时分秒的日期。
    target_dates = pd.Series(month_end_dates).dt.normalize()
    # 只保留项目回测所需的月末收盘价。
    monthly_data = price_data.loc[price_data["date"].isin(target_dates), ["date", "close"]].copy()
    # 按日期排序并去重。
    monthly_data = monthly_data.sort_values("date").drop_duplicates("date").reset_index(drop=True)
    # 若任一月末日期未返回，直接报错，避免用不完整数据计算基准。
    missing_dates = set(target_dates.dt.strftime("%Y-%m-%d")) - set(monthly_data["date"].dt.strftime("%Y-%m-%d"))
    if missing_dates:
        missing_text = "、".join(sorted(missing_dates))
        raise RuntimeError(f"沪深300基准缺少以下月末收盘价：{missing_text}。请检查 JQData 权限或日期范围。")
    # 按要求将日期格式固定为 YYYY-MM-DD。
    monthly_data["date"] = monthly_data["date"].dt.strftime("%Y-%m-%d")
    # 返回仅包含 date 和 float 类型 close 的标准基准数据。
    return monthly_data[["date", "close"]]


def save_hs300_monthly(data: pd.DataFrame, output_path=OUTPUT_PATH) -> Path:
    """保存沪深300月末收盘价。"""
    # 创建输出目录。
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    # 保存为 CSV，便于后续分析读取。
    data.to_csv(output_path, index=False, encoding="utf-8-sig")
    # 返回保存路径。
    return output_path


if __name__ == "__main__":
    # 单独运行时下载沪深300基准数据。
    hs300_data = fetch_hs300_monthly()
    saved_file = save_hs300_monthly(hs300_data)
    # 输出保存结果。
    print(f"沪深300月末数据已保存至：{saved_file.resolve()}，共 {len(hs300_data)} 个调仓日。")
