"""
app.py — B站弹幕姬 入口
负责初始化 AppContext → 凭据 → LiveDanmaku/LiveRoom → 分支运行模式。
"""

import os
import webview

from src.app_context import AppContext
from src.login import get_credential
from src.room_manager import RoomManager
from src.api import CloseApi
from src.web_server import start_web_server
from src.console_log import install as install_console_capture


def resolve_frontend_index(base_path):
    return os.path.join(base_path, "frontend", "dist", "index.html")


if __name__ == "__main__":
    base_path = os.path.dirname(os.path.abspath(__file__))

    # 控制台日志捕获：前端「控制台」页面展示后端输出
    install_console_capture()

    ctx = AppContext()

    # ---- 获取登录凭据（所有房间共用） ----
    cookies_file = os.path.join(base_path, "cookies.json")
    credential = get_credential(cookies_file, ctx.lesson_room_id)

    # ---- 按需监听管理器：由前端点击房间开始/停止监听 ----
    room_manager = RoomManager(credential)

    # ---- 根据 open_mode 分支运行 ----
    open_mode = ctx.features.get("open_mode", "webview")

    if open_mode == "web":
        # ===== Web 模式（单实例，前端按需监听） =====
        print("🌐 运行模式：浏览器网页")
        # 监听房间的事件转投到主上下文的事件队列，供前端轮询
        room_manager.set_event_sink(ctx._push_event)
        web_port = int(os.environ.get("WEB_PORT", 8080))
        start_web_server(ctx, port=web_port, room_manager=room_manager)

    else:
        # ===== Webview 模式（单窗口，前端按需监听） =====
        print("🪟 运行模式：桌面窗口 (webview)")
        ctx.window = webview.create_window(
            title="B站弹幕姬",
            url=resolve_frontend_index(base_path),
            js_api=CloseApi(ctx, room_manager),
            width=1200,
            height=700,
            frameless=True,
            on_top=True,
            transparent=True,
        )

        # 监听房间的弹幕直接推送到主窗口
        room_manager.set_window(ctx.window)

        webview.start(debug=ctx.features.get("web_debug", False))
