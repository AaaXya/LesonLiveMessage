# -*- coding: utf-8 -*-
"""一键打包：先构建前端 → 再 PyInstaller 打包（onedir）。

用法：
    python scripts\\build_exe.py
产物：dist\\RunLiveTest\\RunLiveTest.exe
"""

import os
import shutil
import subprocess
import sys
import time

# 保证中文提示在任意代码页（cp936/cp1252）终端都能正常输出
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def stop_running_app():
    """打包前自动结束仍在运行的 RunLiveTest 进程，
    避免 exe 被占用导致 PyInstaller 清理 dist 时报 PermissionError。
    """
    if sys.platform != "win32":
        return
    image = "RunLiveTest.exe"
    try:
        result = subprocess.run(
            ["taskkill", "/IM", image, "/T", "/F"],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            print(f"已结束正在运行的 {image}（含子进程），继续打包", flush=True)
            # 等待句柄真正释放，避免立刻删除仍被占用的文件
            for _ in range(20):
                try:
                    check = subprocess.run(
                        ["tasklist", "/FI", f"IMAGENAME eq {image}", "/NH"],
                        capture_output=True,
                        text=True,
                    )
                    if image.lower() not in (check.stdout or "").lower():
                        break
                except Exception:
                    break
                time.sleep(0.25)
        else:
            print(f"未发现正在运行的 {image}，跳过结束进程", flush=True)
    except Exception as e:
        # 结束失败不应阻断打包：仅提示后继续
        print(f"结束 {image} 进程时出错（忽略，继续打包）：{e}", flush=True)


def get_packaging_python():
    """选择包含 PyInstaller 的 Python，优先当前环境，回退项目 conda 环境。"""
    try:
        import importlib.util

        if importlib.util.find_spec("PyInstaller"):
            return [sys.executable]
    except Exception:
        pass

    conda = shutil.which("conda")
    if conda:
        print("当前 Python 未安装 PyInstaller，切换到 conda 环境 learnpy", flush=True)
        return [conda, "run", "-n", "learnpy", "python"]

    raise RuntimeError("当前 Python 未安装 PyInstaller，且未找到 conda 环境 learnpy。")


def run(cmd, cwd=None):
    cwd = cwd or ROOT
    # Windows 下 npm 是 npm.cmd，CreateProcess 直接跑会报 WinError 2，
    # 这里用 cmd.exe 解析（shell=True）执行命令
    if sys.platform == "win32":
        exe = shutil.which(cmd[0]) or cmd[0]
        print("$", " ".join([exe, *cmd[1:]]), flush=True)
        subprocess.run([exe, *cmd[1:]], cwd=cwd, check=True, shell=True)
        return
    print("$", " ".join(cmd), flush=True)
    subprocess.run(cmd, cwd=cwd, check=True)


def main():
    os.chdir(ROOT)
    # 0. 自动结束仍在运行的 RunLiveTest，避免 exe 文件占用导致打包失败
    stop_running_app()
    # 1. 前端构建（产物 frontend/dist）
    run(["npm", "run", "build"])
    # 2. PyInstaller 打包
    python_cmd = get_packaging_python()
    run(python_cmd + ["-m", "PyInstaller", "runlivetest.spec", "--noconfirm"])
    print("\n✅ 打包完成：dist\\RunLiveTest\\RunLiveTest.exe")


if __name__ == "__main__":
    main()
