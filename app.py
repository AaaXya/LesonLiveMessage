from bilibili_api import live, sync
import json
import webview
import os
import asyncio
import threading
import http.server
import urllib.parse
import webbrowser
from login import get_credential
from danmu_parser import (
    parse_bilibili_danmu,
    parse_gift,
    parse_super_chat,
    parse_guard_buy,
)
from napcat_send import send_qq_group
from danmu_db import save_danmu
from frontend_config import FrontendConfigApi, apply_room_binding


def load_config():
    # 绝对路径，更稳定（避免运行目录变化导致找不到文件）
    base_path = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(base_path, "config.json")

    # 异常处理：文件不存在/格式错误/缺少键
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"配置文件不存在：{config_path}")

    with open(config_path, "r", encoding="utf-8") as f:
        try:
            return apply_room_binding(json.load(f))
        except json.JSONDecodeError:
            raise ValueError("config.json 格式错误，请检查语法")


def resolve_frontend_index(base_path):
    return os.path.join(base_path, "frontend", "dist", "index.html")


# ========== Web 模式：事件队列 + HTTP 服务器 ==========
_event_queue = []
_event_counter = 0
_event_lock = threading.Lock()
_base_path = os.path.dirname(os.path.abspath(__file__))
_static_dir = os.path.join(_base_path, "frontend", "dist")
_api_instance = None  # CloseApi 实例，web 模式下复用


def push_event(data):
    """推送事件到队列（web 模式使用）"""
    global _event_counter
    if data is None:
        return
    with _event_lock:
        _event_counter += 1
        _event_queue.append({"id": _event_counter, "data": data})
        # 保留最近 500 条
        if len(_event_queue) > 500:
            _event_queue.pop(0)


def _json_response(handler, data, status=200):
    body = json.dumps(data, ensure_ascii=False).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.send_header("Access-Control-Allow-Origin", "*")
    handler.end_headers()
    handler.wfile.write(body)


class _APIHandler(http.server.SimpleHTTPRequestHandler):
    """静态文件 + REST API"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=_static_dir, **kwargs)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == "/api/config":
            if _api_instance and hasattr(_api_instance, "getFrontendConfig"):
                result = _api_instance.getFrontendConfig()
            else:
                api = FrontendConfigApi()
                result = api.getFrontendConfig()
            _json_response(self, result)
            return

        if path == "/api/events":
            qs = urllib.parse.parse_qs(parsed.query)
            since = int(qs.get("since", [0])[0])
            with _event_lock:
                events = [e for e in _event_queue if e["id"] > since]
            _json_response(self, {"events": events})
            return

        # 静态文件：SPA fallback — 非 API 路径且非静态资源时返回 index.html
        if path.startswith("/api/"):
            _json_response(self, {"ok": False, "error": "未知接口"}, status=404)
            return

        if not os.path.splitext(path)[1] and path != "/":
            # 无扩展名 → 可能是前端路由，回退到 index.html
            self.path = "/index.html"

        super().do_GET()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        content_length = int(self.headers.get("Content-Length", 0))
        body_raw = self.rfile.read(content_length) if content_length > 0 else b"{}"
        try:
            body = json.loads(body_raw)
        except json.JSONDecodeError:
            body = {}

        if path == "/api/config":
            if _api_instance and hasattr(_api_instance, "saveFrontendConfig"):
                result = _api_instance.saveFrontendConfig(body)
            else:
                api = FrontendConfigApi()
                result = api.saveFrontendConfig(body)
            _json_response(self, result)
            return

        if path == "/api/danmu":
            if _api_instance and hasattr(_api_instance, "sendDanmu"):
                result = _api_instance.sendDanmu(body.get("message", ""))
            else:
                result = {"ok": False, "error": "弹幕发送器未初始化"}
            _json_response(self, result)
            return

        _json_response(self, {"ok": False, "error": "未知接口"}, status=404)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def log_message(self, format, *args):
        # 仅调试模式下打印请求日志
        if features.get("web_debug"):
            super().log_message(format, *args)


def start_web_server(port=8080):
    """启动 web 模式 HTTP 服务器"""
    global _api_instance
    _api_instance = CloseApi()

    server = http.server.HTTPServer(("127.0.0.1", port), _APIHandler)
    print(f"✓ Web 服务器已启动：http://127.0.0.1:{port}")
    webbrowser.open(f"http://127.0.0.1:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()


config = load_config()
LESSONROOMID = config["LESSONROOMID"]
features = config["features"]


class CloseApi(FrontendConfigApi):
    def saveFrontendConfig(self, update):
        result = super().saveFrontendConfig(update)
        if result.get("ok"):
            global config, LESSONROOMID, features
            old_room_id = LESSONROOMID
            config = load_config()
            new_room_id = config["LESSONROOMID"]
            LESSONROOMID = new_room_id
            features = config["features"]
            if new_room_id != old_room_id:
                result["restart_needed"] = True
                result["message"] = f"直播间已切换至 {new_room_id}，请重启应用以生效"
        return result

    def closeWindow(self):
        global window
        if window:
            try:
                window.destroy()
            except Exception as e:
                print("关闭窗口失败：", e)

    def minimizeWindow(self):
        global window
        if window:
            try:
                window.minimize()
            except Exception as e:
                print("最小化窗口失败：", e)

    def toggleMaximizeWindow(self):
        global window
        if window:
            try:
                if hasattr(window, "toggle_maximize"):
                    window.toggle_maximize()
                elif hasattr(window, "toggle_fullscreen"):
                    window.toggle_fullscreen()
                else:
                    print("toggleMaximizeWindow: 未支持的最大化方法")
            except Exception as e:
                print("切换最大化失败：", e)

    def sendDanmu(self, message):
        global sender
        if not message:
            return {"ok": False, "error": "弹幕内容不能为空"}

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


window = None
room = None
sender = None
room_title = None
room_cover = None


# 推送数据到前端
def send_to_frontend(data):
    if data is None:
        return
    if window:
        window.evaluate_js(f"addDanmu({json.dumps(data, ensure_ascii=False)})")
    else:
        # web 模式：推入事件队列
        push_event(data)


# 弹幕消息处理器
async def on_danmaku_handler(event):
    parsed = parse_bilibili_danmu(event)
    if isinstance(parsed, dict):
        parsed_to_log = {k: v for k, v in parsed.items() if k != "avatar_url"}
    else:
        parsed_to_log = parsed
    print(parsed_to_log)
    if features.get("enable_danmu_db"):
        save_danmu(parsed, LESSONROOMID)
    send_to_frontend(parsed)


# 大航海续费处理器
async def on_guard_buy_handler(event):
    parsed = parse_guard_buy(event)
    if parsed:
        print("大航海续费：", parsed)
        send_to_frontend(parsed)


# 事件格式示例：
# 大航海续费： {'room_display_id': 1879006019, 'room_real_id': 1879006019, 'type': 'GUARD_BUY', 'data': {'cmd': 'GUARD_BUY', 'data': {'uid': 44032453, 'username': '绯儿の锦依卫', 'guard_level': 3, 'num': 1, 'price': 198000, 'gift_id': 10003, 'gift_name': '舰长', 'start_time': 1781012304, 'end_time': 1781012304}}}


async def on_super_chat_handler(event):
    parsed = parse_super_chat(event)
    if parsed:
        print("超级留言：", {k: v for k, v in parsed.items() if k != "avatar_url"})
        if features.get("enable_danmu_db"):
            save_danmu(parsed, LESSONROOMID)
        send_to_frontend(parsed)


# 超级留言： {'room_display_id': 1879006019, 'room_real_id': 1879006019, 'type': 'SUPER_CHAT_MESSAGE', 'data': {'cmd': 'SUPER_CHAT_MESSAGE', 'data': {'background_bottom_color': '#2A60B2', 'background_color': '#EDF5FF', 'background_color_end': '#405D85', 'background_color_start': '#3171D2', 'background_icon': '', 'background_image': '', 'background_price_color': '#7497CD', 'color_point': 0.7, 'dmscore': 714, 'end_time': 1781012711, 'gift': {'gift_id': 12000, 'gift_name': '醒目留言', 'num': 1}, 'group_medal': {'is_lighted': 0, 'medal_id': 0, 'name': ''}, 'id': 16735005, 'is_mystery': False, 'is_ranked': 0, 'is_send_audit': 0, 'medal_info': {'anchor_roomid': 1879006019, 'anchor_uname': '酥柔柔', 'guard_level': 3, 'icon_id': 0, 'is_lighted': 1, 'medal_color': '#06154c', 'medal_color_border': 6809855, 'medal_color_end': 6850801, 'medal_color_start': 398668, 'medal_level': 27, 'medal_name': '粉丝团', 'special': '', 'target_id': 3546698381003418}, 'message': '测试', 'message_font_color': '#A3F6FF', 'message_trans': '', 'price': 2, 'rate': 1000, 'start_time': 1781012706, 'time': 5, 'token': '827B2131', 'trans_mark': 0, 'ts': 1781012706, 'uid': 388151398, 'uinfo': {'base': {'face': 'https://i1.hdslb.com/bfs/face/9dfc549c7d6809eafa93b15b97f9c05a7055752d.jpg', 'is_mystery': False, 'name': '安安安小雅w', 'name_color': 0, 'name_color_str': '#00D1F1', 'official_info': {'desc': '', 'role': 0, 'title': '', 'type': -1}, 'origin_info': {'face': 'https://i1.hdslb.com/bfs/face/9dfc549c7d6809eafa93b15b97f9c05a7055752d.jpg', 'name': '安安安小雅w'}, 'risk_ctrl_info': None}, 'guard': {'expired_str': '2026-06-24 23:59:59', 'level': 3}, 'guard_leader': None, 'medal': {'color': 398668, 'color_border': 6809855, 'color_end': 6850801, 'color_start': 398668, 'guard_icon': 'https://i0.hdslb.com/bfs/live/48360c8f3b7de8031e86ff1ef4a2dfc0ec2a61c2.png', 'guard_level': 3, 'honor_icon': '', 'id': 0, 'is_light': 1, 'level': 27, 'name': '粉丝团', 'ruid': 3546698381003418, 'score': 13918, 'typ': 0, 'user_receive_count': 0, 'v2_medal_color_border': '#5FC7F4', 'v2_medal_color_end': '#3FB4F699', 'v2_medal_color_level': '#3FB4F6E6', 'v2_medal_color_start': '#3FB4F699', 'v2_medal_color_text': '#FFFFFF'}, 'title': {'old_title_css_id': '', 'title_css_id': ''}, 'uhead_frame': None, 'uid': 388151398, 'wealth': None}, 'user_info': {'face': 'https://i1.hdslb.com/bfs/face/9dfc549c7d6809eafa93b15b97f9c05a7055752d.jpg', 'face_frame': 'https://i0.hdslb.com/bfs/live/80f732943cc3367029df65e267960d56736a82ee.png', 'guard_level': 3, 'is_main_vip': 0, 'is_svip': 0, 'is_vip': 0, 'level_color': '#61c05a', 'manager': 0, 'name_color': '#00D1F1', 'title': '', 'uname': '安安安小雅w', 'user_level': 20}}, 'is_report': True, 'msg_id': '96950106411035137:1000:1000', 'p_is_ack': True, 'p_msg_type': 1, 'send_time': 1781012706457}}
# 超级留言： {'room_display_id': 1879006019, 'room_real_id': 1879006019, 'type': 'SUPER_CHAT_MESSAGE', 'data': {'cmd': 'SUPER_CHAT_MESSAGE', 'data': {'background_bottom_color': '#2A60B2', 'background_color': '#EDF5FF', 'background_color_end': '#405D85', 'background_color_start': '#3171D2', 'background_icon': '', 'background_image': '', 'background_price_color': '#7497CD', 'color_point': 0.7, 'dmscore': 280, 'end_time': 1781095502, 'gift': {'gift_id': 12000, 'gift_name': '醒目留言', 'num': 1}, 'group_medal': {'is_lighted': 0, 'medal_id': 0, 'name': ''}, 'id': 16755420, 'is_mystery': False, 'is_ranked': 0, 'is_send_audit': 0, 'medal_info': {'anchor_roomid': 1879006019, 'anchor_uname': '酥柔柔', 'guard_level': 0, 'icon_id': 0, 'is_lighted': 1, 'medal_color': '#5c968e', 'medal_color_border': 6067854, 'medal_color_end': 6067854, 'medal_color_start': 6067854, 'medal_level': 1, 'medal_name': '粉丝团', 'special': '', 'target_id': 3546698381003418}, 'message': '为了你我怒充了3块', 'message_font_color': '#A3F6FF', 'message_trans': '', 'price': 2, 'rate': 1000, 'start_time': 1781095497, 'time': 5, 'token': 'EB002F5B', 'trans_mark': 0, 'ts': 1781095497, 'uid': 481939845, 'uinfo': {'base': {'face': 'https://i0.hdslb.com/bfs/face/e2aabe640e7b90675419bf9cccc71148433de9e4.jpg', 'is_mystery': False, 'name': '落迦行走', 'name_color': 0, 'name_color_str': '#666666', 'official_info': {'desc': '', 'role': 0, 'title': '', 'type': -1}, 'origin_info': {'face': 'https://i0.hdslb.com/bfs/face/e2aabe640e7b90675419bf9cccc71148433de9e4.jpg', 'name': '落迦行走'}, 'risk_ctrl_info': None}, 'guard': {'expired_str': '', 'level': 0}, 'guard_leader': None, 'medal': {'color': 6067854, 'color_border': 6067854, 'color_end': 6067854, 'color_start': 6067854, 'guard_icon': '', 'guard_level': 0, 'honor_icon': '', 'id': 0, 'is_light': 1, 'level': 1, 'name': '粉丝团', 'ruid': 3546698381003418, 'score': 1, 'typ': 0, 'user_receive_count': 0, 'v2_medal_color_border': '#5762A799', 'v2_medal_color_end': '#5762A799', 'v2_medal_color_level': '#5762A7E6', 'v2_medal_color_start': '#5762A799', 'v2_medal_color_text': '#FFFFFF'}, 'title': {'old_title_css_id': '', 'title_css_id': ''}, 'uhead_frame': None, 'uid': 481939845, 'wealth': None}, 'user_info': {'face': 'https://i0.hdslb.com/bfs/face/e2aabe640e7b90675419bf9cccc71148433de9e4.jpg', 'face_frame': '', 'guard_level': 0, 'is_main_vip': 0, 'is_svip': 0, 'is_vip': 0, 'level_color': '#61c05a', 'manager': 0, 'name_color': '#666666', 'title': '', 'uname': '落迦行走', 'user_level': 20}}, 'is_report': True, 'msg_id': '97036919205049344:1000:1000', 'p_is_ack': True, 'p_msg_type': 1, 'send_time': 1781095497589}}
state = 0


async def live_start_handler(event):
    global state  # ✅ 必须加这行，声明要修改全局变量state
    state += 1
    print("直播开始：", event)
    if (
        features["enable_qq_notification"] and state == 1
    ):  # 只在第一次直播开始时发送通知，避免重复通知
        from avatar_proxy import fetch_image_data_uri_uncompressed

        cover_data_uri = (
            fetch_image_data_uri_uncompressed(room_cover) if room_cover else None
        )
        send_qq_group(
            f"直播开始了：\n{room_title}\nhttps://live.bilibili.com/{str(LESSONROOMID)}",
            cover_data_uri,
            LESSONROOMID,
        )


# 礼物处理器
async def on_gift_handler(event):
    parsed_gift = parse_gift(event)
    print("礼物：", parsed_gift)
    send_to_frontend(parsed_gift)


def on_window_ready():
    import threading

    if room:
        threading.Thread(
            target=lambda: sync(room_connect_loop(room)), daemon=True
        ).start()
    else:
        print("警告：直播间监听未初始化")

    if sender:
        pass  # LiveRoom 无需持久连接，init_sender_and_get_info() 已在初始化时调用
    else:
        print("警告：弹幕发送器未初始化")


async def room_connect_loop(room_obj):
    """带自动重连的直播间连接循环"""
    retry_delay = 3
    max_delay = 60

    while True:
        try:
            print(f"[{LESSONROOMID}] 正在连接直播间...")
            await room_obj.connect()
        except Exception as e:
            print(f"[{LESSONROOMID}] 连接异常：{e}，{retry_delay} 秒后重连...")

        print(f"[{LESSONROOMID}] 连接已断开，{retry_delay} 秒后自动重连...")
        await asyncio.sleep(retry_delay)
        retry_delay = min(retry_delay * 2, max_delay)


async def init_sender_and_get_info():
    global sender, room_title, room_cover
    room_info = await sender.get_room_info()
    room_title = room_info["room_info"]["title"]
    room_cover = room_info["room_info"]["cover"]
    print("✓ 获取直播间信息成功", room_info["room_info"])
    print("直播间信息：", room_title, room_cover)


if __name__ == "__main__":
    base_path = os.path.dirname(os.path.abspath(__file__))
    # 获取有效的登录凭据
    COOKIES_FILE = os.path.join(base_path, "cookies.json")
    credential = get_credential(COOKIES_FILE, LESSONROOMID)

    # 初始化监听器和发送器（优先使用有效的 credential）
    if credential:
        try:
            room = live.LiveDanmaku(LESSONROOMID, credential=credential)
            sender = live.LiveRoom(LESSONROOMID, credential=credential)
            sync(init_sender_and_get_info())
            print("✓ 使用有效的凭据初始化 LiveDanmaku 和 LiveRoom")

        except Exception as e:
            print("✗ 初始化 LiveDanmaku/LiveRoom 失败：", e)
            room = live.LiveDanmaku(LESSONROOMID)
            sender = live.LiveRoom(LESSONROOMID)
            sync(init_sender_and_get_info())
    else:
        print("⚠ 无有效凭据，使用无凭据模式初始化 LiveDanmaku 和 LiveRoom")
        room = live.LiveDanmaku(LESSONROOMID)
        sender = live.LiveRoom(LESSONROOMID)

        sync(init_sender_and_get_info())
    # 注册事件处理器
    if room:
        if features["enable_live_start"]:
            room.on("LIVE")(live_start_handler)
        if features["enable_danmaku"]:
            room.on("DANMU_MSG")(on_danmaku_handler)
        if features["enable_guard_buy"]:
            room.on("GUARD_BUY")(on_guard_buy_handler)
        if features["enable_super_chat"]:
            room.on("SUPER_CHAT_MESSAGE")(on_super_chat_handler)
        if features["enable_gift"]:
            room.on("SEND_GIFT")(on_gift_handler)

    open_mode = features.get("open_mode", "webview")

    if open_mode == "web":
        # ===== Web 模式：启动 HTTP 服务器 =====
        print(f"🌐 运行模式：浏览器网页")
        # 在后台启动直播间连接
        if room:
            threading.Thread(
                target=lambda: sync(room_connect_loop(room)), daemon=True
            ).start()
        # 启动 web 服务器（阻塞）
        web_port = int(os.environ.get("WEB_PORT", 8080))
        start_web_server(port=web_port)
    else:
        # ===== Webview 模式：桌面窗口 =====
        print(f"🪟 运行模式：桌面窗口 (webview)")
        window = webview.create_window(
            title="B站弹幕姬",
            url=resolve_frontend_index(base_path),
            js_api=CloseApi(),
            width=400,
            height=700,
            frameless=True,
            on_top=True,
            transparent=True,
        )
        window.events.loaded += on_window_ready
        webview.start(debug=features["web_debug"])
