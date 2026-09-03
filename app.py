"""
app.py — B站弹幕姬 入口
负责初始化 AppContext → 凭据 → LiveDanmaku/LiveRoom → 分支运行模式。
"""

import os
import sys
import webview

from src import DATA_ROOT, RESOURCE_ROOT
from src.app_context import AppContext
from src.login import LoginManager
from src.room_manager import RoomManager
from src.api import CloseApi
from src.web_server import start_web_server
from src.console_log import install as install_console_capture
from src.frontend_config import get_window_size


def resolve_frontend_index(base_path):
    return os.path.join(base_path, "frontend", "dist", "index.html")


def _enable_discrete_gpu_preference():
    """为当前 exe 设置 Windows“高性能 GPU（独显）”偏好。

    相当于在 系统设置→显示→图形 里把 RunLiveTest 设为“高性能”：
    写入 HKCU\\Software\\Microsoft\\DirectX\\UserGpuPreferences，
    值名=exe 路径，值=“GpuPreference=2;”（2 表示高性能/独显）。
    WebView2 使用 D3D，Windows 会据此优先把应用调度到独显。
    """
    if sys.platform != "win32" or not getattr(sys, "frozen", False):
        return
    exe = os.path.normcase(os.path.abspath(sys.executable))
    try:
        import winreg

        key_path = r"Software\Microsoft\DirectX\UserGpuPreferences"
        with winreg.CreateKeyEx(
            winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE
        ) as key:
            winreg.SetValueEx(key, exe, 0, winreg.REG_SZ, "GpuPreference=2;")
        print("⚙️ 已为 RunLiveTest 启用高性能 GPU（独显）偏好")
    except Exception as e:
        print("设置独显 GPU 偏好失败：", e)


if __name__ == "__main__":
    # 前端资源目录（打包后为只读解压目录）
    base_path = RESOURCE_ROOT

    # 控制台日志捕获：前端「控制台」页面展示后端输出
    install_console_capture()

    # 打包版：自动把本应用设为高性能 GPU（独显）偏好，避免被调度到核显导致黑屏
    _enable_discrete_gpu_preference()

    ctx = AppContext()

    # ---- 按需监听管理器：由前端点击房间开始/停止监听 ----
    cookies_file = os.path.join(DATA_ROOT, "cookies.json")
    room_manager = RoomManager(None)

    # ---- 登录协调器：有效凭据自动沿用；缺失/失效时由前端首页展示二维码 ----
    login_manager = LoginManager(cookies_file, on_success=room_manager.set_credential)

    # ---- 根据 open_mode 分支运行 ----
    open_mode = ctx.features.get("open_mode", "webview")

    if open_mode == "web":
        # ===== Web 模式（单实例，前端按需监听） =====
        print("🌐 运行模式：浏览器网页")
        # 监听房间的事件转投到主上下文的事件队列，供前端轮询
        room_manager.set_event_sink(ctx._push_event)
        # 后台探测登录状态（必要时自动进入二维码流程）
        login_manager.bootstrap()
        web_port = int(os.environ.get("WEB_PORT", 8080))
        start_web_server(
            ctx, port=web_port, room_manager=room_manager, login=login_manager
        )

    else:
        # ===== Webview 模式（单窗口，前端按需监听） =====
        print("🪟 运行模式：桌面窗口 (webview)")
        window_width, window_height = get_window_size(ctx.config)
        print(f"窗口大小：{window_width}×{window_height}")
        ctx.window = webview.create_window(
            title="B站弹幕姬",
            url=resolve_frontend_index(base_path),
            js_api=CloseApi(ctx, room_manager, login_manager),
            width=window_width,
            height=window_height,
            frameless=True,
            on_top=True,
            transparent=True,
        )

        # 监听房间的弹幕直接推送到主窗口
        room_manager.set_window(ctx.window)
        # 后台探测登录状态（必要时自动进入二维码流程）
        login_manager.bootstrap()

        webview.start(debug=ctx.features.get("web_debug", False))
