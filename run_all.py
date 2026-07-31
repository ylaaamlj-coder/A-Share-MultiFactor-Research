"""Windows + PyCharm 环境下一键运行完整研究流程。"""

# 导入 os，用于向子程序传递 JQData 环境变量。
import os
# 导入 subprocess，用于按顺序执行各个 Python 文件。
import subprocess
# 导入 sys，确保使用 PyCharm 当前配置的解释器。
import sys
# 导入 Path，确保所有路径都相对于本项目目录。
from pathlib import Path


# 获取本文件所在目录，即项目根目录，不依赖终端当前路径。
PROJECT_DIR = Path(__file__).resolve().parent
# 设置 .env 文件的相对位置。
ENV_PATH = PROJECT_DIR / ".env"
# main.py 已按完整顺序调用数据获取、检查、回测和基准分析，因此只需运行它一次。
SCRIPTS = ["main.py"]


def load_jqdata_environment() -> None:
    """从项目根目录的 .env 文件加载 JQData 账号配置。"""
    # 如果尚未创建 .env 文件，停止执行并给出中文操作提示。
    if not ENV_PATH.exists():
        raise FileNotFoundError(
            "未找到 .env 配置文件。请复制 .env.example 并重命名为 .env，"
            "然后填写 JQDATA_USERNAME 和 JQDATA_PASSWORD。"
        )
    # 延迟导入，便于在依赖未安装时提供更清楚的提示。
    try:
        from dotenv import load_dotenv
    except ModuleNotFoundError as error:
        raise ModuleNotFoundError(
            "缺少 python-dotenv 依赖。请在 PyCharm 终端执行：pip install -r requirements.txt"
        ) from error
    # 加载 .env 中的变量，并保留系统中已存在的同名变量。
    load_dotenv(ENV_PATH, override=False)
    # 检查账号变量是否已经成功读取。
    if not os.getenv("JQDATA_USERNAME") or not os.getenv("JQDATA_PASSWORD"):
        raise RuntimeError(".env 中缺少 JQDATA_USERNAME 或 JQDATA_PASSWORD，请填写后再运行。")


def run_script(script_name: str) -> None:
    """使用当前 PyCharm 解释器运行一个项目脚本。"""
    # 拼接脚本的绝对路径。
    script_path = PROJECT_DIR / script_name
    # 先检查脚本是否存在，避免出现不直观的 Python 报错。
    if not script_path.exists():
        raise FileNotFoundError(f"缺少脚本文件：{script_name}。请检查项目文件是否完整。")
    # 输出当前执行进度。
    print(f"\n{'=' * 60}\n正在运行：{script_name}\n{'=' * 60}")
    # 以项目根目录作为工作目录运行，保证所有相对路径都正确。
    result = subprocess.run([sys.executable, str(script_path)], cwd=PROJECT_DIR, env=os.environ.copy())
    # 子程序运行失败时立即停止，防止使用不完整数据继续回测。
    if result.returncode != 0:
        raise RuntimeError(f"{script_name} 运行失败，退出码为 {result.returncode}。请查看上方中文报错信息。")


def run_all() -> None:
    """加载账号配置后，依次完成下载、检查和研究回测。"""
    # 显示当前项目目录，方便确认 PyCharm 打开了正确项目。
    print(f"项目目录：{PROJECT_DIR}")
    # 加载 JQData 账号配置。
    load_jqdata_environment()
    # 逐个运行数据获取、数据检查和完整研究流程。
    for script_name in SCRIPTS:
        run_script(script_name)
    # 所有步骤成功时给出结果目录提示。
    print("\n全部流程已完成。请查看 data/processed、outputs 和 outputs/charts 文件夹。")


if __name__ == "__main__":
    # 捕获常见配置和运行错误，避免 PyCharm 只显示长堆栈而没有中文说明。
    try:
        run_all()
    except (FileNotFoundError, ModuleNotFoundError, RuntimeError) as error:
        print(f"\n运行终止：{error}")
        sys.exit(1)
