"""读取研究结果并生成 IC、分组回测、组合净值和回撤图。"""

# 在导入 pyplot 前设置无界面绘图模式，适合在 PyCharm 脚本中运行。
import matplotlib
matplotlib.use("Agg")
# 导入绘图库。
import matplotlib.pyplot as plt
# 导入 Path 处理文件路径。
from pathlib import Path
# 导入 pandas 读取结果数据。
import pandas as pd


# 设置结果数据路径。
IC_PATH = Path("outputs/ic_monthly.csv")
GROUP_PATH = Path("outputs/group_return.csv")
PORTFOLIO_PATH = Path("outputs/portfolio_return.csv")
# 设置图表输出文件夹。
CHART_DIR = Path("outputs/charts")


def set_chinese_style() -> None:
    """设置常见中文字体候选，避免图表标题显示为方框。"""
    # 优先使用 Windows 常见中文字体；不同电脑缺少时 matplotlib 会自动回退。
    plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "Arial Unicode MS"]
    # 解决负号显示异常。
    plt.rcParams["axes.unicode_minus"] = False


def plot_ic_curve() -> Path:
    """绘制三个因子的逐月 Rank IC 曲线。"""
    # 读取逐月 IC 数据。
    ic_data = pd.read_csv(IC_PATH, parse_dates=["trade_date"])
    # 创建图和坐标轴。
    fig, ax = plt.subplots(figsize=(10, 5))
    # 按因子分别绘制 IC 曲线。
    for factor, factor_data in ic_data.groupby("factor"):
        ax.plot(factor_data["trade_date"], factor_data["rank_ic"], marker="o", label=factor)
    # 添加零轴作为正负 IC 的参考线。
    ax.axhline(0, color="black", linewidth=0.8)
    # 设置标题和坐标轴名称。
    ax.set(title="三个基本面因子的月度 Rank IC", xlabel="调仓日", ylabel="Rank IC")
    # 显示图例。
    ax.legend()
    # 自动调整布局。
    fig.tight_layout()
    # 定义输出文件路径。
    output_path = CHART_DIR / "ic_curve.png"
    # 保存图片。
    fig.savefig(output_path, dpi=150)
    # 关闭图片，防止重复运行时占用内存。
    plt.close(fig)
    # 返回图片路径。
    return output_path


def plot_group_curves() -> Path:
    """绘制每个单因子的五分组累计净值曲线。"""
    # 读取五分组结果。
    group_data = pd.read_csv(GROUP_PATH, parse_dates=["trade_date"])
    # 获取因子名称列表。
    factors = group_data["factor"].unique()
    # 创建三个纵向子图，每个因子一张图。
    fig, axes = plt.subplots(len(factors), 1, figsize=(10, 12), sharex=True)
    # 因子只有一个时，将单个坐标轴转为列表，统一后续写法。
    if len(factors) == 1:
        axes = [axes]
    # 逐个因子画五组净值曲线。
    for ax, factor in zip(axes, factors):
        factor_data = group_data[group_data["factor"] == factor]
        for group, one_group in factor_data.groupby("group"):
            ax.plot(one_group["trade_date"], one_group["net_value"], label=f"Group{group}")
        # 设置子图标题、纵轴和图例。
        ax.set(title=f"{factor} 五分组累计净值", ylabel="累计净值")
        ax.legend(ncol=5, fontsize=8)
    # 为最下方子图设置横轴名称。
    axes[-1].set_xlabel("调仓日")
    # 自动调整布局。
    fig.tight_layout()
    # 定义输出文件路径。
    output_path = CHART_DIR / "group_net_value.png"
    # 保存图片。
    fig.savefig(output_path, dpi=150)
    # 关闭图片。
    plt.close(fig)
    # 返回图片路径。
    return output_path


def plot_portfolio_curves() -> tuple:
    """绘制多因子组合累计净值和回撤曲线。"""
    # 读取组合回测结果。
    portfolio = pd.read_csv(PORTFOLIO_PATH, parse_dates=["trade_date"])
    # 定义净值和回撤的输出路径。
    net_value_path = CHART_DIR / "portfolio_net_value.png"
    drawdown_path = CHART_DIR / "portfolio_drawdown.png"
    # 单独创建净值图。
    net_fig, net_ax = plt.subplots(figsize=(10, 4))
    # 绘制累计净值。
    net_ax.plot(portfolio["trade_date"], portfolio["net_value"], color="tab:blue")
    # 设置净值图标题和坐标轴。
    net_ax.set(title="多因子组合累计净值", xlabel="调仓日", ylabel="累计净值")
    # 自动调整布局并保存净值图。
    net_fig.tight_layout()
    net_fig.savefig(net_value_path, dpi=150)
    # 关闭净值图。
    plt.close(net_fig)
    # 单独创建回撤图。
    drawdown_fig, drawdown_ax = plt.subplots(figsize=(10, 4))
    # 绘制回撤并填充阴影。
    drawdown_ax.plot(portfolio["trade_date"], portfolio["drawdown"], color="tab:red")
    drawdown_ax.fill_between(portfolio["trade_date"], portfolio["drawdown"], 0, color="tab:red", alpha=0.25)
    # 设置回撤图标题和坐标轴。
    drawdown_ax.set(title="多因子组合回撤", xlabel="调仓日", ylabel="回撤")
    # 自动调整布局并保存回撤图。
    drawdown_fig.tight_layout()
    drawdown_fig.savefig(drawdown_path, dpi=150)
    # 关闭回撤图。
    plt.close(drawdown_fig)
    # 返回两个路径。
    return net_value_path, drawdown_path


def create_all_charts() -> list:
    """检查结果文件并生成全部图表。"""
    # 确保图表目录存在。
    CHART_DIR.mkdir(parents=True, exist_ok=True)
    # 检查绘图需要的结果是否齐全。
    for file_path in [IC_PATH, GROUP_PATH, PORTFOLIO_PATH]:
        if not file_path.exists():
            raise FileNotFoundError(f"未找到绘图数据：{file_path}。请先运行 main.py 或对应分析模块。")
    # 设置中文绘图样式。
    set_chinese_style()
    # 生成 IC 图和五分组图。
    chart_paths = [plot_ic_curve(), plot_group_curves()]
    # 生成组合净值图和回撤图。
    chart_paths.extend(plot_portfolio_curves())
    # 返回全部图表路径。
    return chart_paths


if __name__ == "__main__":
    # 一键生成全部图表。
    generated_charts = create_all_charts()
    # 打印图表输出位置。
    for chart_path in generated_charts:
        print(f"已生成图表：{chart_path.resolve()}")
