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

    # ---- 获取登录凭据（所有房间共用） ----
    cookies_file = os.path.join(base_path, "cookies.json")
    credential = get_credential(cookies_file, ctx.lesson_room_id)

    def build_room_context(room_id_str):
        """为一个房间创建独立的 AppContext 并初始化连接"""
        room_ctx = AppContext(room_id=room_id_str)
        room_id = room_ctx.lesson_room_id

        def init_with_credential(use_credential):
            if use_credential:
                room_ctx.room = live.LiveDanmaku(room_id, credential=credential)
                room_ctx.sender = live.LiveRoom(room_id, credential=credential)
            else:
                room_ctx.room = live.LiveDanmaku(room_id)
                room_ctx.sender = live.LiveRoom(room_id)
            sync(init_room_info(room_ctx.sender, room_ctx))

        try:
            init_with_credential(bool(credential))
            print(f"✓ 房间 {room_id} 初始化 LiveDanmaku 和 LiveRoom 完成")
        except Exception as e:
            print(f"✗ 房间 {room_id} 凭据初始化失败，改用无凭据模式：{e}")
            try:
                init_with_credential(False)
            except Exception as e2:
                print(f"✗ 房间 {room_id} 初始化失败：{e2}")

        register_all_handlers(room_ctx.room, room_ctx)
        return room_ctx

    # ---- 根据 open_mode 分支运行 ----
    open_mode = ctx.features.get("open_mode", "webview")

    if open_mode == "web":
        # ===== Web 模式（单房间） =====
        print("🌐 运行模式：浏览器网页")
        room_ctx = build_room_context(str(ctx.lesson_room_id))
        start_room_connect(room_ctx.room, room_ctx)
        web_port = int(os.environ.get("WEB_PORT", 8080))
        start_web_server(room_ctx, port=web_port)

    else:
        # ===== Webview 模式（支持多窗口多房间） =====
        print("🪟 运行模式：桌面窗口 (webview)")
        room_id_list = [str(rid) for rid in ctx.room_ids]
        if not room_id_list:
            room_id_list = [str(ctx.lesson_room_id)]
        print(f"将创建 {len(room_id_list)} 个窗口：{room_id_list}")

        for rid in room_id_list:
            room_ctx = build_room_context(rid)
            title = f"B站弹幕姬 · {room_ctx.room_title or rid}"
            window = webview.create_window(
                title=title,
                url=resolve_frontend_index(base_path),
                js_api=CloseApi(room_ctx),
                width=400,
                height=700,
                frameless=True,
                on_top=True,
                transparent=True,
            )
            room_ctx.window = window

            def on_window_ready(rc=room_ctx, win=window):
                if rc.room_title:
                    try:
                        win.set_title(f"B站弹幕姬 · {rc.room_title}")
                    except Exception as e:
                        print("设置窗口标题失败：", e)
                start_room_connect(rc.room, rc)

            window.events.loaded += on_window_ready

        webview.start(debug=ctx.features.get("web_debug", False))
