"""
src — 核心库
"""

import os
import sys

# 项目根目录（src/ 的父目录）
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# PyInstaller 打包后的只读资源目录：
# onefile 模式资源解压到临时目录 sys._MEIPASS，开发模式即 PROJECT_ROOT
RESOURCE_ROOT = getattr(sys, "_MEIPASS", None) or PROJECT_ROOT


def _resolve_data_root():
    """可写数据目录：
    - 开发模式：项目根目录
    - 打包模式：优先 exe 同目录（便携式）；若只读则回退 %APPDATA%\\RunLiveTest
    """
    if not getattr(sys, "frozen", False):
        return PROJECT_ROOT
    exe_dir = os.path.dirname(os.path.abspath(sys.executable))
    probe = os.path.join(exe_dir, ".write_test")
    try:
        with open(probe, "w") as f:
            f.write("")
        os.remove(probe)
        return exe_dir
    except OSError:
        appdata = os.environ.get("APPDATA") or os.path.expanduser("~")
        return os.path.join(appdata, "RunLiveTest")


DATA_ROOT = _resolve_data_root()
os.makedirs(DATA_ROOT, exist_ok=True)
