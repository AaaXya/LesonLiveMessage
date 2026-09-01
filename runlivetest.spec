# -*- mode: python ; coding: utf-8 -*-
"""
RunLiveTest 打包配置（PyInstaller onedir）
用法：
  1. 先构建前端：npm run build
  2. 打包：python -m PyInstaller runlivetest.spec --noconfirm
产物：dist/RunLiveTest/RunLiveTest.exe
"""

from PyInstaller.utils.hooks import collect_all

# 只读资源：前端构建产物 + 主题预设（打包后位于 _internal/ 下，经 RESOURCE_ROOT 读取）
datas = [
    ("frontend/dist", "frontend/dist"),
    ("theme.json", "."),
]
binaries = []
hiddenimports = []

# pywebview：收集平台后端与数据文件
wv_datas, wv_binaries, wv_hidden = collect_all("webview")
datas += wv_datas
binaries += wv_binaries
hiddenimports += wv_hidden

# aiohttp：bilibili-api 运行时懒加载，静态分析抓不到；
# 需显式收集本体及其 C 扩展依赖（multidict/yarl/frozenlist/aiosignal 带 .pyd）
for _mod in ("aiohttp", "multidict", "yarl", "frozenlist", "aiosignal"):
    try:
        _d, _b, _h = collect_all(_mod)
        datas += _d
        binaries += _b
        hiddenimports += _h
    except Exception:
        pass

# bilibili_api 用 importlib 字符串动态导入请求客户端，PyInstaller 看不到，
# 显式加入 hiddenimports
hiddenimports += [
    "bilibili_api.clients.AioHTTPClient",
    "bilibili_api.clients.HTTPXClient",
    "bilibili_api.clients.CurlCFFIClient",
]


a = Analysis(
    ["app.py"],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tkinter", "matplotlib", "numpy", "pandas"],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="RunLiveTest",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="RunLiveTest",
)
