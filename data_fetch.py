"""使用 JQData 下载沪深300月频行情与基本面数据。"""

# 导入 os，用于从系统环境变量读取 JQData 账号，避免把密码写进代码。
import os
# 导入 Path，用于创建跨平台的数据保存路径。
from pathlib import Path
# 导入 pandas，用于整理并保存表格数据。
import pandas as pd
# 从 JQData SDK 导入本模块需要使用的接口和数据表。
from jqdatasdk import auth, get_fundamentals, get_index_stocks, get_price, get_trade_days, indicator, is_auth, query, valuation


# 设置沪深300指数代码，后续股票池统一由此代码获取。
CSI_300 = "000300.XSHG"
# 设置默认开始日期；请改为自己试用账号实际允许查询的日期范围。
DEFAULT_START_DATE = "2025-05-01"
# 设置默认结束日期；试用账号通常不能查询最近约三个月的数据。
DEFAULT_END_DATE = "2026-04-29"
# 设置原始数据的默认保存文件夹。
DEFAULT_OUTPUT_DIR = Path("data/raw")


def login_jqdata() -> None:
    """使用环境变量中的 JQData 账号登录。"""
    # 从环境变量读取手机号或用户名。
    username = os.getenv("JQDATA_USERNAME")
    # 从环境变量读取密码。
    password = os.getenv("JQDATA_PASSWORD")
    # 如果账号或密码没有配置，就停止并给出明确提示。
    if not username or not password:
        raise RuntimeError(
            "未找到 JQData 账号。请先在 PyCharm 运行配置中设置 "
            "JQDATA_USERNAME 和 JQDATA_PASSWORD 环境变量。"
        )
    # 调用 JQData 登录接口；该接口本身不适合作为布尔值判断。
    auth(username, password)
    # 通过 is_auth() 读取 SDK 当前真实登录状态。
    if not is_auth():
        raise RuntimeError("JQData 登录失败，请检查账号、密码和网络连接。")
    # 登录成功时给出清楚提示。
    print("JQData 登录成功。")


def get_month_end_trade_days(start_date: str, end_date: str) -> list[pd.Timestamp]:
    """返回给定区间内每个月最后一个交易日。"""
    # 从交易所日历获取区间内全部交易日。
    trade_days = pd.to_datetime(get_trade_days(start_date=start_date, end_date=end_date))
    # 把交易日转换为一列，方便按月份分组。
    trade_day_series = pd.Series(trade_days, name="trade_date")
    # 每月取日期最大的交易日，即月末调仓日。
    month_end_days = trade_day_series.groupby(trade_day_series.dt.to_period("M")).max()
    # 转为列表，便于后续逐月循环。
    return month_end_days.tolist()


def get_csi300_members(trade_date: pd.Timestamp) -> list[str]:
    """获取某一调仓日当天的沪深300成分股，避免用当前成分股代替历史股票池。"""
    # 按指定历史日期查询指数成分股。
    stocks = get_index_stocks(CSI_300, date=trade_date.strftime("%Y-%m-%d"))
    # 返回 JQData 股票代码列表，例如 000001.XSHE。
    return stocks


def get_month_end_prices(stocks: list[str], trade_date: pd.Timestamp) -> pd.DataFrame:
    """获取股票在调仓日的前复权收盘价，并返回长表格式。"""
    # 批量查询所有股票在指定调仓日的日线收盘价。
    prices = get_price(
        security=stocks,
        start_date=trade_date.strftime("%Y-%m-%d"),
        end_date=trade_date.strftime("%Y-%m-%d"),
        frequency="daily",
        fields=["close"],
        fq="pre",
        panel=False,
    )
    # 将接口可能返回的 time 字段统一改名为 trade_date。
    prices = prices.rename(columns={"time": "trade_date"})
    # 明确保留后续计算需要的三列，并复制为独立对象。
    prices = prices.loc[:, ["trade_date", "code", "close"]].copy()
    # 统一日期类型，方便后续按日期合并。
    prices["trade_date"] = pd.to_datetime(prices["trade_date"])
    # 返回月末价格长表。
    return prices


def get_fundamental_data(stocks: list[str], trade_date: pd.Timestamp) -> pd.DataFrame:
    """获取某日可查询到的 PE、ROE 与营业收入同比增长率。"""
    # 指定需要提取的估值和财务字段；date 参数使数据按该日可得状态查询。
    fundamental_query = query(
        valuation.code,
        valuation.pe_ratio,
        indicator.roe,
        indicator.inc_revenue_year_on_year,
    ).filter(valuation.code.in_(stocks))
    # 使用调仓日查询横截面基本面数据，JQData 会返回当时已披露的数据。
    fundamentals = get_fundamentals(
        fundamental_query,
        date=trade_date.strftime("%Y-%m-%d"),
    )
    # 给结果增加调仓日期，便于与价格数据按股票和日期连接。
    fundamentals["trade_date"] = pd.Timestamp(trade_date)
    # 将接口字段改为研究中更容易理解的列名。
    fundamentals = fundamentals.rename(
        columns={
            "pe_ratio": "pe_ratio",
            "roe": "roe",
            "inc_revenue_year_on_year": "revenue_growth",
        }
    )
    # 返回标准长表格式的基本面数据。
    return fundamentals.loc[:, ["trade_date", "code", "pe_ratio", "roe", "revenue_growth"]]


def fetch_monthly_dataset(start_date: str, end_date: str) -> pd.DataFrame:
    """逐月下载历史成分股、月末价格和三个原始因子，并合并为一张长表。"""
    # 获取全部月末调仓日。
    month_end_days = get_month_end_trade_days(start_date, end_date)
    # 创建列表，用于收集每个月的数据表。
    monthly_frames = []
    # 逐个调仓日下载数据，避免一次请求过大而超过试用账号限制。
    for trade_date in month_end_days:
        # 获取该历史日期的沪深300成分股。
        stocks = get_csi300_members(trade_date)
        # 获取这些股票的月末价格。
        prices = get_month_end_prices(stocks, trade_date)
        # 获取这些股票的估值和财务指标。
        fundamentals = get_fundamental_data(stocks, trade_date)
        # 以股票代码和调仓日为键合并价格与基本面数据。
        monthly_data = prices.merge(fundamentals, on=["trade_date", "code"], how="inner")
        # 将当月结果加入总列表。
        monthly_frames.append(monthly_data)
        # 打印进度，方便观察下载是否正常进行。
        print(f"已获取 {trade_date:%Y-%m-%d}：{len(monthly_data)} 只股票")
    # 将各月数据纵向拼接成完整研究样本。
    dataset = pd.concat(monthly_frames, ignore_index=True)
    # 按日期和股票代码排序，保证保存结果稳定且易于查看。
    dataset = dataset.sort_values(["trade_date", "code"]).reset_index(drop=True)
    # 返回供后续因子模块使用的 DataFrame。
    return dataset


def save_dataset(dataset: pd.DataFrame, output_dir: Path = DEFAULT_OUTPUT_DIR) -> Path:
    """将原始月频数据保存为 UTF-8 编码的 CSV 文件。"""
    # 自动创建数据目录；目录已经存在时不会报错。
    output_dir.mkdir(parents=True, exist_ok=True)
    # 定义输出文件名。
    output_path = output_dir / "csi300_monthly_raw.csv"
    # 使用 utf-8-sig 保存，使 Excel 直接打开中文列名时不乱码。
    dataset.to_csv(output_path, index=False, encoding="utf-8-sig")
    # 返回文件路径，方便主程序打印结果。
    return output_path


if __name__ == "__main__":
    # 登录 JQData。
    login_jqdata()
    # 下载默认可用区间内的月频原始数据。
    raw_dataset = fetch_monthly_dataset(DEFAULT_START_DATE, DEFAULT_END_DATE)
    # 将数据保存到本地。
    saved_path = save_dataset(raw_dataset)
    # 输出保存结果和表格前五行，供首次运行时检查。
    print(f"数据已保存至：{saved_path.resolve()}")
    print(raw_dataset.head())
