"""
app_context.py — 共享应用状态容器
替代全局变量，统一管理 config / room / sender / window / 事件队列。
"""

import json
import os
import threading
from collections import deque

from . import DATA_ROOT
from .frontend_config import apply_room_binding, get_room_ids, get_room_id


class AppContext:
    def __init__(self, room_id=None):
        # 固定房间 ID（多窗口模式）：该上下文只监听这一个房间
        self.fixed_room_id = str(room_id).strip() if room_id else None

        # ---- 配置 ----
        self.config = self._load_config()
        self.room_ids = get_room_ids(self.config)
        self.lesson_room_id = (
            int(self.fixed_room_id)
            if self.fixed_room_id
            else (int(get_room_id(self.config)) if get_room_id(self.config) else 0)
        )
        self.features = self.config["features"]

        # ---- B站连接 ----
        self.room = None  # LiveDanmaku
        self.sender = None  # LiveRoom
        self.room_title = None
        self.room_cover = None

        # ---- Webview 窗口 ----
        self.window = None

        # ---- 直播状态 ----
        self.is_live = False  # 当前直播状态，由房间信息与 LIVE/PREPARING 事件同步
        self.live_started_notified = False  # 本次监听周期内是否已发送开播通知
        self.stop_flag = threading.Event()  # 停止监听标志（按需监听用）

        # ---- 自动发言任务（生命周期跟随直播间开播/下播） ----
        self.auto_speak_tasks = (
            []
        )  # [(asyncio.Task, asyncio.Event)]：定时循环 + 时长触发
        self.live_started_at = None  # 本次开播时间戳（直播时长触发用）

        # ---- 事件外接（按需监听时把事件转给主队列） ----
        self._event_sink = None

        # ---- Web 模式事件队列 ----
        self._event_queue = deque()
        self._event_counter = 0
        self._event_lock = threading.Lock()

    # ==================== 配置 ====================

    def _load_config(self):
        config_path = os.path.join(DATA_ROOT, "config.json")
        if not os.path.exists(config_path):
            # 首次运行 / 打包后的全新目录：生成默认配置并落盘，避免 FileNotFoundError
            from .frontend_config import (
                DEFAULT_AUTO_SPEAK,
                FEATURE_KEYS,
                save_app_config,
            )

            default_config = {
                "room_ids": [],
                "room_bindings": {},
                "frontend": {"theme": "default", "window_size": "default"},
                "features": {
                    key: False if key == "web_debug" else True
                    for key in FEATURE_KEYS
                    if key != "open_mode"
                }
                | {"open_mode": "webview"},
                "filter_words": [],
                "auto_speak": dict(DEFAULT_AUTO_SPEAK),
            }
            save_app_config(default_config)
            print(f"已生成默认配置文件：{config_path}")
            return apply_room_binding(default_config, self.fixed_room_id)
        with open(config_path, "r", encoding="utf-8") as f:
            try:
                return apply_room_binding(json.load(f), self.fixed_room_id)
            except json.JSONDecodeError:
                raise ValueError("config.json 格式错误，请检查语法")

    def reload_config(self):
        """重新加载配置（前端保存后调用）"""
        old_room_id = self.lesson_room_id
        self.config = self._load_config()
        self.features = self.config["features"]
        self.room_ids = get_room_ids(self.config)
        if self.fixed_room_id:
            # 多窗口模式：房间固定，不随全局配置变化
            self.lesson_room_id = int(self.fixed_room_id)
            return False
        self.lesson_room_id = int(get_room_id(self.config) or self.lesson_room_id)
        return old_room_id != self.lesson_room_id

    # ==================== 前端推送 ====================

    def send_to_frontend(self, data):
        """推送到前端：优先外部 sink，其次 window JS，web 模式走事件队列"""
        if data is None:
            return
        # 附加房间 ID，前端按房间隔离弹幕列表
        if isinstance(data, dict) and data.get("room_id") is None:
            data = {**data, "room_id": str(self.lesson_room_id)}
        if self._event_sink:
            self._event_sink(data)
            return
        if self.window:
            self.window.evaluate_js(f"addDanmu({json.dumps(data, ensure_ascii=False)})")
        else:
            self._push_event(data)

    def _push_event(self, data):
        """推入事件队列（web 模式轮询用）"""
        with self._event_lock:
            self._event_counter += 1
            self._event_queue.append({"id": self._event_counter, "data": data})
            if len(self._event_queue) > 500:
                self._event_queue.popleft()

    def get_events_since(self, since_id):
        """获取自 since_id 以来的事件（web 模式 API）"""
        with self._event_lock:
            return [e for e in self._event_queue if e["id"] > since_id]
