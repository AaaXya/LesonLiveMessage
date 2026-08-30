"""
room_manager.py — 按需监听房间管理器
单窗口模式下，由前端点击房间开始/停止监听弹幕。
"""

import asyncio
import threading

from bilibili_api import live, sync

from .app_context import AppContext
from .live_events import (
    register_all_handlers,
    start_room_connect,
    stop_room_connect,
    init_room_info,
)


class RoomManager:
    def __init__(self, credential=None):
        self.credential = credential
        self._lock = threading.Lock()
        self._rooms = {}  # rid_str -> AppContext
        self._window = None
        self._event_sink = None

    def set_window(self, window):
        """webview 模式：弹幕直接推送到主窗口"""
        self._window = window

    def set_event_sink(self, sink):
        """web 模式：弹幕推送到主上下文的事件队列"""
        self._event_sink = sink

    def _init_room(self, rid_str):
        ctx = AppContext(room_id=rid_str)
        room_id = ctx.lesson_room_id

        try:
            if self.credential:
                ctx.room = live.LiveDanmaku(room_id, credential=self.credential)
                ctx.sender = live.LiveRoom(room_id, credential=self.credential)
            else:
                ctx.room = live.LiveDanmaku(room_id)
                ctx.sender = live.LiveRoom(room_id)
        except Exception as e:
            print(f"✗ 房间 {room_id} 凭据初始化失败，改用无凭据模式：{e}")
            try:
                ctx.room = live.LiveDanmaku(room_id)
                ctx.sender = live.LiveRoom(room_id)
            except Exception as e2:
                raise RuntimeError(f"房间 {room_id} 初始化失败：{e2}")

        # 获取房间信息（带超时，失败不影响监听）
        try:

            async def _fetch_info():
                await asyncio.wait_for(init_room_info(ctx.sender, ctx), timeout=10)

            sync(_fetch_info())
        except Exception as e:
            print(f"⚠ 获取房间 {room_id} 信息失败（不影响监听）：{e}")

        # 事件出口：webview 走主窗口，web 模式走主队列
        if self._window is not None:
            ctx.window = self._window
        elif self._event_sink is not None:
            ctx._event_sink = self._event_sink

        register_all_handlers(ctx.room, ctx)
        return ctx

    def start(self, rid):
        """开始监听一个房间"""
        rid_str = str(rid).strip()
        with self._lock:
            if rid_str in self._rooms:
                return {"ok": False, "error": "该房间已在监听中"}
            try:
                ctx = self._init_room(rid_str)
            except Exception as e:
                return {"ok": False, "error": str(e)}
            self._rooms[rid_str] = ctx

        start_room_connect(ctx.room, ctx)
        print(f"✓ 开始监听房间 {ctx.lesson_room_id}")
        return {"ok": True, "room_id": ctx.lesson_room_id}

    def stop(self, rid):
        """停止监听一个房间"""
        rid_str = str(rid).strip()
        with self._lock:
            ctx = self._rooms.pop(rid_str, None)
        if ctx is None:
            return {"ok": False, "error": "该房间未在监听"}
        stop_room_connect(ctx)
        print(f"✓ 停止监听房间 {ctx.lesson_room_id}")
        return {"ok": True, "room_id": ctx.lesson_room_id}

    def stop_all(self):
        for rid in list(self.listening()):
            self.stop(rid)

    def listening(self):
        """返回正在监听的房间 ID 集合"""
        with self._lock:
            return set(self._rooms.keys())
