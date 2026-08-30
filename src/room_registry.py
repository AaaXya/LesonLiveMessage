"""
room_registry.py — 多房间状态注册表
所有房间上下文共享的全局状态，供前端「直播间」页面展示各项数据。
"""

import threading
import time

# 状态更新函数会在已持锁时调用 ensure_room；使用可重入锁避免自身再次
# 获取同一把锁时死锁，从而阻塞直播间连接线程。
_lock = threading.RLock()

# room_id(str) -> status dict
_rooms = {}


def _new_status(room_id):
    return {
        "room_id": room_id,
        "title": "",
        "cover": "",
        "connected": False,
        "live_state": 0,
        "danmu_count": 0,
        "last_event_at": None,
        "last_event_type": None,
        "last_error": None,
    }


def ensure_room(room_id, room_title=None, room_cover=None):
    """获取房间状态（返回内部引用，必须在 _lock 内修改）"""
    room_id = str(room_id).strip()
    with _lock:
        status = _rooms.setdefault(room_id, _new_status(room_id))
        if room_title:
            status["title"] = room_title
        if room_cover:
            status["cover"] = room_cover
        return status


def set_connected(room_id, connected: bool):
    with _lock:
        status = ensure_room(room_id)
        status["connected"] = connected
        if connected:
            status["last_error"] = None
        return dict(status)


def set_live_state(room_id, live_state: int):
    with _lock:
        status = ensure_room(room_id)
        status["live_state"] = live_state
        return dict(status)


def set_error(room_id, error: str):
    with _lock:
        status = ensure_room(room_id)
        status["last_error"] = str(error)[:200] if error else None
        return dict(status)


def on_event(room_id, event_type: str):
    """统计事件（弹幕/礼物等），更新计数与最后事件时间"""
    with _lock:
        status = ensure_room(room_id)
        if event_type == "danmu":
            status["danmu_count"] += 1
        status["last_event_at"] = time.time()
        status["last_event_type"] = event_type
        return dict(status)


def get_all_rooms():
    with _lock:
        return [dict(status) for status in _rooms.values()]


def get_room(room_id):
    room_id = str(room_id).strip()
    with _lock:
        status = _rooms.get(room_id)
        return dict(status) if status else None
