"""
api.py — CloseApi：前后端桥接层
供 webview（JS API）和 web 模式（HTTP API）共用。
"""

from bilibili_api import live, sync
from .frontend_config import FrontendConfigApi


class CloseApi(FrontendConfigApi):
    """前后端 API 桥接 — webview js_api / HTTP 端点共用"""

    def __init__(self, ctx):
        super().__init__(room_id=ctx.fixed_room_id)
        self._ctx = ctx  # 下划线前缀：pywebview 不暴露给 JS，避免循环引用

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

    # ==================== 弹幕发送 ====================

    def sendDanmu(self, message):
        if not message:
            return {"ok": False, "error": "弹幕内容不能为空"}

        sender = self._ctx.sender
        if sender is None:
            return {"ok": False, "error": "弹幕发送器未初始化"}

        try:
            if hasattr(sender, "send_danmaku"):
                if hasattr(live, "Danmaku"):
                    danmaku = live.Danmaku(message)
                    result = sync(sender.send_danmaku(danmaku))
                else:
                    result = sync(sender.send_danmaku(message))
            else:
                print("sendDanmu: 未找到可用的发送弹幕方法")
                return {"ok": False, "error": "后端不支持发送弹幕"}

            print("发送弹幕：", message, "结果：", result)
            return {"ok": True, "result": result}
        except Exception as e:
            print("发送弹幕失败：", e)
            return {"ok": False, "error": str(e)}
