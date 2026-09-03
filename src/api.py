"""
api.py — CloseApi：前后端桥接层
供 webview（JS API）和 web 模式（HTTP API）共用。
"""

import inspect

from bilibili_api import live, sync
from .frontend_config import FrontendConfigApi


class CloseApi(FrontendConfigApi):
    """前后端 API 桥接 — webview js_api / HTTP 端点共用"""

    def __init__(self, ctx, room_manager=None, login=None):
        super().__init__(room_id=ctx.fixed_room_id)
        self._ctx = ctx  # 下划线前缀：pywebview 不暴露给 JS，避免循环引用
        self._room_manager = room_manager
        self._login = login

    # ==================== 登录（应用内扫码） ====================

    def getLoginStatus(self):
        """前端登录浮层轮询：返回登录状态与二维码图片"""
        if not self._login:
            return {"ok": False, "error": "登录管理器未初始化"}
        return {"ok": True, **self._login.snapshot()}

    def startQrLogin(self):
        """开始/刷新应用内二维码登录"""
        if not self._login:
            return {"ok": False, "error": "登录管理器未初始化"}
        self._login.start_qr()
        return {"ok": True, "message": "已开始二维码登录"}

    # ==================== 配置 ====================

    def saveFrontendConfig(self, update):
        result = super().saveFrontendConfig(update)
        if result.get("ok"):
            room_changed = self._ctx.reload_config()
            if room_changed:
                result["restart_needed"] = True
                result["message"] = (
                    f"直播间已切换至 {self._ctx.lesson_room_id}，" "请重启应用以生效"
                )
        return result

    # ==================== 窗口控制（webview 专用） ====================

    def closeWindow(self):
        if self._ctx.window:
            try:
                self._ctx.window.destroy()
            except Exception as e:
                print("关闭窗口失败：", e)

    def minimizeWindow(self):
        if self._ctx.window:
            try:
                self._ctx.window.minimize()
            except Exception as e:
                print("最小化窗口失败：", e)

    def toggleMaximizeWindow(self):
        w = self._ctx.window
        if w:
            try:
                if hasattr(w, "toggle_maximize"):
                    w.toggle_maximize()
                elif hasattr(w, "toggle_fullscreen"):
                    w.toggle_fullscreen()
                else:
                    print("toggleMaximizeWindow: 未支持的最大化方法")
            except Exception as e:
                print("切换最大化失败：", e)

    def setWindowSize(self, preset):
        """按预设调整当前窗口大小（webview 模式，即时生效）"""
        from .frontend_config import WINDOW_SIZE_PRESETS

        preset = str(preset or "").strip()
        size = WINDOW_SIZE_PRESETS.get(preset)
        if size is None:
            return {"ok": False, "error": "未知的窗口大小预设"}

        w = self._ctx.window
        if w is not None:
            try:
                w.resize(size["width"], size["height"])
            except Exception as e:
                print("调整窗口大小失败：", e)
                return {"ok": False, "error": str(e)}
        return {"ok": True, "width": size["width"], "height": size["height"]}

    # ==================== 弹幕发送 ====================

    def sendDanmu(self, message, room_id=None):
        if not message:
            return {"ok": False, "error": "弹幕内容不能为空"}

        sender = None
        room_id_str = str(room_id).strip() if room_id is not None else ""

        if room_id_str and self._room_manager:
            room_ctx = self._room_manager._rooms.get(room_id_str)
            if room_ctx is not None:
                sender = room_ctx.sender

        if sender is None:
            sender = self._ctx.sender

        if sender is None:
            if room_id_str:
                return {"ok": False, "error": f"房间 {room_id_str} 发送器未初始化"}
            return {"ok": False, "error": "弹幕发送器未初始化"}

        try:
            if hasattr(sender, "send_danmaku"):
                if hasattr(live, "Danmaku"):
                    danmaku = live.Danmaku(message)
                    payload = sender.send_danmaku(danmaku)
                else:
                    payload = sender.send_danmaku(message)
                result = sync(payload) if inspect.isawaitable(payload) else payload
            else:
                print("sendDanmu: 未找到可用的发送弹幕方法")
                return {"ok": False, "error": "后端不支持发送弹幕"}

            print(
                f"发送弹幕到房间 {room_id_str or self._ctx.lesson_room_id}：",
                message,
                "结果：",
                result,
            )
            return {"ok": True, "result": result}
        except Exception as e:
            print("发送弹幕失败：", e)
            return {"ok": False, "error": str(e)}

    # ==================== 数据面板 ====================

    def getRoomsStatus(self):
        """返回所有绑定直播间的运行状态"""
        from .room_registry import get_all_rooms
        from .avatar_proxy import fetch_room_cover

        config = self._ctx.config
        bindings = config.get("room_bindings", {})
        room_ids = [str(r) for r in config.get("room_ids", [])]
        if not room_ids:
            room_ids = list(bindings.keys())
        listening_ids = self._room_manager.listening() if self._room_manager else set()
        current = get_all_rooms()
        by_id = {r["room_id"]: r for r in current}
        rooms = []
        for rid in room_ids:
            binding = bindings.get(str(rid), {})
            auto_speak = binding.get("auto_speak", {}) or {}
            auto_task_count = sum(
                len([i for i in auto_speak.get(k, []) or [] if i.get("enabled", True)])
                for k in ("cycle_list", "duration_list")
            )
            status = by_id.get(str(rid), {})
            # 封面：优先本地 JSON 缓存，未命中则下载并持久化
            cover_data = fetch_room_cover(rid, status.get("cover", ""))
            rooms.append(
                {
                    "room_id": str(rid),
                    "title": status.get("title", "") or f"房间 {rid}",
                    "cover": cover_data,
                    "connected": bool(status.get("connected", False)),
                    "live_state": int(status.get("live_state", 0)),
                    "is_live": bool(status.get("live_state", 0) > 0),
                    "danmu_count": int(status.get("danmu_count", 0)),
                    "last_event_at": status.get("last_event_at"),
                    "last_event_type": status.get("last_event_type"),
                    "local_notification": bool(
                        binding.get("enable_local_notification", False)
                    ),
                    "auto_task_count": auto_task_count,
                    "listening": str(rid) in listening_ids,
                    "last_error": status.get("last_error"),
                }
            )
        return {"ok": True, "rooms": rooms}

    def startRoomListen(self, roomId):
        """按需开始监听房间弹幕"""
        if not self._room_manager:
            return {"ok": False, "error": "监听管理器未初始化"}
        return self._room_manager.start(roomId)

    def stopRoomListen(self, roomId):
        """停止监听房间弹幕"""
        if not self._room_manager:
            return {"ok": False, "error": "监听管理器未初始化"}
        return self._room_manager.stop(roomId)

    def getConsoleLogs(self, sinceSeq=0, limit=200):
        """返回后端控制台日志（自 sinceSeq 之后）"""
        from .console_log import get_logs, clear as clear_logs

        try:
            if sinceSeq == -1:
                clear_logs()
                return {"ok": True, "logs": [], "nextSeq": 0}
            logs = get_logs(int(sinceSeq) if sinceSeq else 0, int(limit))
            next_seq = logs[-1]["seq"] if logs else int(sinceSeq)
            return {"ok": True, "logs": logs, "nextSeq": next_seq}
        except Exception as e:
            print("获取控制台日志失败：", e)
            return {"ok": False, "error": str(e), "logs": [], "nextSeq": 0}

    def getDanmuPage(
        self,
        roomId=None,
        page=1,
        pageSize=50,
        keyword=None,
        itemType=None,
        order="DESC",
    ):
        """弹幕数据库分页查询"""
        from .danmu_db import get_danmu_page, count_danmu

        room_id = str(roomId or self._ctx.lesson_room_id).strip()
        if not room_id.isdigit():
            return {"ok": False, "error": "无效的房间 ID"}
        try:
            limit = max(1, min(int(pageSize), 200))
            offset = max(0, (int(page) - 1)) * limit
            rows = get_danmu_page(room_id, limit, offset, keyword, itemType, order)
            total = count_danmu(room_id, keyword, itemType)
            return {"ok": True, "rows": rows, "total": total, "page": int(page)}
        except Exception as e:
            print("查询弹幕数据库失败：", e)
            return {"ok": False, "error": str(e)}

    def getGiftPage(
        self,
        roomId=None,
        page=1,
        pageSize=50,
        keyword=None,
        order="DESC",
    ):
        """礼物数据库分页查询"""
        from .danmu_db import get_gift_page, count_gifts

        room_id = str(roomId or self._ctx.lesson_room_id).strip()
        if not room_id.isdigit():
            return {"ok": False, "error": "无效的房间 ID"}
        try:
            limit = max(1, min(int(pageSize), 200))
            offset = max(0, (int(page) - 1)) * limit
            rows = get_gift_page(room_id, limit, offset, keyword, order)
            total = count_gifts(room_id, keyword)
            return {"ok": True, "rows": rows, "total": total, "page": int(page)}
        except Exception as e:
            print("查询礼物数据库失败：", e)
            return {"ok": False, "error": str(e)}
