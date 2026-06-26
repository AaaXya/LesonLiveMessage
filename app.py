"""
app.py — B站弹幕姬 入口
负责初始化 AppContext → 凭据 → LiveDanmaku/LiveRoom → 分支运行模式。
"""

import os
import webview
from bilibili_api import live, sync

from src.app_context import AppContext
from src.login import get_credential
from src.live_events import (
    register_all_handlers,
    start_room_connect,
    init_room_info,
)
from src.api import CloseApi
from src.web_server import start_web_server


def resolve_frontend_index(base_path):
    return os.path.join(base_path, "frontend", "dist", "index.html")


if __name__ == "__main__":
    base_path = os.path.dirname(os.path.abspath(__file__))
    ctx = AppContext()

    # ---- 获取登录凭据 ----
    cookies_file = os.path.join(base_path, "cookies.json")
    credential = get_credential(cookies_file, ctx.lesson_room_id)

    # ---- 初始化 LiveDanmaku / LiveRoom ----
    room_id = ctx.lesson_room_id
    if credential:
        try:
            ctx.room = live.LiveDanmaku(room_id, credential=credential)
            ctx.sender = live.LiveRoom(room_id, credential=credential)
            sync(init_room_info(ctx.sender, ctx))
            print("✓ 使用有效的凭据初始化 LiveDanmaku 和 LiveRoom")
        except Exception as e:
            print("✗ 初始化 LiveDanmaku/LiveRoom 失败：", e)
            ctx.room = live.LiveDanmaku(room_id)
            ctx.sender = live.LiveRoom(room_id)
            sync(init_room_info(ctx.sender, ctx))
    else:
        print("⚠ 无有效凭据，使用无凭据模式初始化 LiveDanmaku 和 LiveRoom")
        ctx.room = live.LiveDanmaku(room_id)
        ctx.sender = live.LiveRoom(room_id)
        sync(init_room_info(ctx.sender, ctx))

    # ---- 注册事件处理器 ----
    register_all_handlers(ctx.room, ctx)

    # ---- 根据 open_mode 分支运行 ----
    open_mode = ctx.features.get("open_mode", "webview")

    if open_mode == "web":
        # ===== Web 模式 =====
        print("🌐 运行模式：浏览器网页")
        start_room_connect(ctx.room, ctx)
        web_port = int(os.environ.get("WEB_PORT", 8080))
        start_web_server(ctx, port=web_port)

    else:
        # ===== Webview 模式 =====
        print("🪟 运行模式：桌面窗口 (webview)")
        ctx.window = webview.create_window(
            title="B站弹幕姬",
            url=resolve_frontend_index(base_path),
            js_api=CloseApi(ctx),
            width=400,
            height=700,
            frameless=True,
            on_top=True,
            transparent=True,
        )

        def on_window_ready():
            start_room_connect(ctx.room, ctx)

        ctx.window.events.loaded += on_window_ready
        webview.start(debug=ctx.features.get("web_debug", False))
