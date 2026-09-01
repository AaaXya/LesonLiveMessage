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

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


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
    # 1. 前端构建（产物 frontend/dist）
    run(["npm", "run", "build"])
    # 2. PyInstaller 打包
    run([sys.executable, "-m", "PyInstaller", "runlivetest.spec", "--noconfirm"])
    print("\n✅ 打包完成：dist\\RunLiveTest\\RunLiveTest.exe")


if __name__ == "__main__":
    main()
