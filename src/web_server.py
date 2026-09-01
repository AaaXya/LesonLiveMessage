"""
web_server.py — Web 模式 HTTP 服务器
提供静态文件服务 + REST API，供浏览器端使用。
"""

import json
import os
import http.server
import urllib.parse
import webbrowser

from . import RESOURCE_ROOT
from .api import CloseApi

STATIC_DIR = os.path.join(RESOURCE_ROOT, "frontend", "dist")

# ---- 抑制 HTTP 200 日志（仅异常时打印） ----
_original_log_message = http.server.BaseHTTPRequestHandler.log_message


def _quiet_log_message(self, format, *args):
    # format: '"%s" %s %s' / args: (requestline, code, size)
    try:
        if len(args) >= 2 and int(args[1]) < 400:
            return  # 2xx/3xx 静默
    except (ValueError, TypeError):
        pass
    _original_log_message(self, format, *args)


http.server.BaseHTTPRequestHandler.log_message = _quiet_log_message


def _json_response(handler, data, status=200):
    body = json.dumps(data, ensure_ascii=False).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.send_header("Access-Control-Allow-Origin", "*")
    handler.end_headers()
    try:
        handler.wfile.write(body)
    except (ConnectionAbortedError, ConnectionResetError, BrokenPipeError):
        pass  # 客户端已断开（刷新/关闭），静默忽略


class APIHandler(http.server.SimpleHTTPRequestHandler):
    """静态文件 + REST API 处理器"""

    # 类属性：由 start_web_server 在启动前设置
    ctx = None
    api = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=STATIC_DIR, **kwargs)

    # ---- GET ----

    def do_GET(self):
        try:
            self._do_GET()
        except (ConnectionAbortedError, ConnectionResetError, BrokenPipeError):
            pass  # 客户端断开，静默忽略

    def _do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == "/api/config":
            result = self.api.getFrontendConfig()
            _json_response(self, result)
            return

        if path == "/api/events":
            qs = urllib.parse.parse_qs(parsed.query)
            since = int(qs.get("since", [0])[0])
            events = self.ctx.get_events_since(since)
            _json_response(self, {"events": events})
            return

        if path == "/api/rooms":
            result = self.api.getRoomsStatus()
            _json_response(self, result)
            return

        if path == "/api/console":
            qs = urllib.parse.parse_qs(parsed.query)
            since = int(qs.get("since", [0])[0])
            result = self.api.getConsoleLogs(sinceSeq=since)
            _json_response(self, result)
            return

        if path == "/api/danmu_db":
            qs = urllib.parse.parse_qs(parsed.query)
            result = self.api.getDanmuPage(
                roomId=qs.get("room", [None])[0],
                page=int(qs.get("page", [1])[0]),
                pageSize=int(qs.get("pageSize", [50])[0]),
                keyword=qs.get("keyword", [None])[0],
                itemType=qs.get("type", [None])[0],
                order=qs.get("order", ["DESC"])[0],
            )
            _json_response(self, result)
            return

        if path == "/api/gift_db":
            qs = urllib.parse.parse_qs(parsed.query)
            result = self.api.getGiftPage(
                roomId=qs.get("room", [None])[0],
                page=int(qs.get("page", [1])[0]),
                pageSize=int(qs.get("pageSize", [50])[0]),
                keyword=qs.get("keyword", [None])[0],
                order=qs.get("order", ["DESC"])[0],
            )
            _json_response(self, result)
            return

        if path.startswith("/api/"):
            _json_response(self, {"ok": False, "error": "未知接口"}, status=404)
            return

        # SPA fallback：无扩展名路径返回 index.html
        if not os.path.splitext(path)[1] and path != "/":
            self.path = "/index.html"

        super().do_GET()

    # ---- POST ----

    def do_POST(self):
        try:
            self._do_POST()
        except (ConnectionAbortedError, ConnectionResetError, BrokenPipeError):
            pass

    def _do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        content_length = int(self.headers.get("Content-Length", 0))
        body_raw = self.rfile.read(content_length) if content_length > 0 else b"{}"
        try:
            body = json.loads(body_raw)
        except json.JSONDecodeError:
            body = {}

        if path == "/api/config":
            result = self.api.saveFrontendConfig(body)
            _json_response(self, result)
            return

        if path == "/api/danmu":
            result = self.api.sendDanmu(body.get("message", ""))
            _json_response(self, result)
            return

        if path == "/api/listen":
            action = body.get("action")
            room = body.get("room")
            if action == "start":
                result = self.api.startRoomListen(room)
            elif action == "stop":
                result = self.api.stopRoomListen(room)
            else:
                result = {"ok": False, "error": "未知操作"}
            _json_response(self, result)
            return

        _json_response(self, {"ok": False, "error": "未知接口"}, status=404)

    # ---- CORS ----

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()


def start_web_server(ctx, port=8080, room_manager=None):
    """启动 web 模式 HTTP 服务器（阻塞）"""

    # 设置类属性，每个请求的 handler 实例自动继承
    APIHandler.ctx = ctx
    APIHandler.api = CloseApi(ctx, room_manager)

    server = http.server.HTTPServer(("127.0.0.1", port), APIHandler)
    url = f"http://127.0.0.1:{port}?mode=web"
    print(f"✓ Web 服务器已启动：{url}")
    webbrowser.open(url)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()
