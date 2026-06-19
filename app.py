from bilibili_api import live, sync
import json
import webview
import os
from login import get_credential
from danmu_parser import parse_bilibili_danmu, parse_gift
from napcat_send import send_qq_group


def load_config():
    # 绝对路径，更稳定（避免运行目录变化导致找不到文件）
    base_path = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(base_path, "config.json")

    # 异常处理：文件不存在/格式错误/缺少键
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"配置文件不存在：{config_path}")

    with open(config_path, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            raise ValueError("config.json 格式错误，请检查语法")


config = load_config()
LESSONROOMID = config["LESSONROOMID"]
GROUPID = config["GROUPID"]
features = config["features"]


class CloseApi:
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
    if window and data:
        window.evaluate_js(f"addDanmu({json.dumps(data, ensure_ascii=False)})")


# 弹幕消息处理器
async def on_danmaku_handler(event):
    if features["enable_danmaku"]:
        parsed = parse_bilibili_danmu(event)
        if isinstance(parsed, dict):
            parsed_to_log = {k: v for k, v in parsed.items() if k != "avatar_url"}
        else:
            parsed_to_log = parsed
        print(parsed_to_log)
        send_to_frontend(parsed)


# 大航海续费处理器
async def on_guard_buy_handler(event):
    if features["enable_guard_buy"]:
        print("大航海续费：", event)


# 事件格式示例：
# 大航海续费： {'room_display_id': 1879006019, 'room_real_id': 1879006019, 'type': 'GUARD_BUY', 'data': {'cmd': 'GUARD_BUY', 'data': {'uid': 44032453, 'username': '绯儿の锦依卫', 'guard_level': 3, 'num': 1, 'price': 198000, 'gift_id': 10003, 'gift_name': '舰长', 'start_time': 1781012304, 'end_time': 1781012304}}}


async def on_super_chat_handler(event):
    if features["enable_super_chat"]:
        print("超级留言：", event)


# 超级留言： {'room_display_id': 1879006019, 'room_real_id': 1879006019, 'type': 'SUPER_CHAT_MESSAGE', 'data': {'cmd': 'SUPER_CHAT_MESSAGE', 'data': {'background_bottom_color': '#2A60B2', 'background_color': '#EDF5FF', 'background_color_end': '#405D85', 'background_color_start': '#3171D2', 'background_icon': '', 'background_image': '', 'background_price_color': '#7497CD', 'color_point': 0.7, 'dmscore': 714, 'end_time': 1781012711, 'gift': {'gift_id': 12000, 'gift_name': '醒目留言', 'num': 1}, 'group_medal': {'is_lighted': 0, 'medal_id': 0, 'name': ''}, 'id': 16735005, 'is_mystery': False, 'is_ranked': 0, 'is_send_audit': 0, 'medal_info': {'anchor_roomid': 1879006019, 'anchor_uname': '酥柔柔', 'guard_level': 3, 'icon_id': 0, 'is_lighted': 1, 'medal_color': '#06154c', 'medal_color_border': 6809855, 'medal_color_end': 6850801, 'medal_color_start': 398668, 'medal_level': 27, 'medal_name': '粉丝团', 'special': '', 'target_id': 3546698381003418}, 'message': '测试', 'message_font_color': '#A3F6FF', 'message_trans': '', 'price': 2, 'rate': 1000, 'start_time': 1781012706, 'time': 5, 'token': '827B2131', 'trans_mark': 0, 'ts': 1781012706, 'uid': 388151398, 'uinfo': {'base': {'face': 'https://i1.hdslb.com/bfs/face/9dfc549c7d6809eafa93b15b97f9c05a7055752d.jpg', 'is_mystery': False, 'name': '安安安小雅w', 'name_color': 0, 'name_color_str': '#00D1F1', 'official_info': {'desc': '', 'role': 0, 'title': '', 'type': -1}, 'origin_info': {'face': 'https://i1.hdslb.com/bfs/face/9dfc549c7d6809eafa93b15b97f9c05a7055752d.jpg', 'name': '安安安小雅w'}, 'risk_ctrl_info': None}, 'guard': {'expired_str': '2026-06-24 23:59:59', 'level': 3}, 'guard_leader': None, 'medal': {'color': 398668, 'color_border': 6809855, 'color_end': 6850801, 'color_start': 398668, 'guard_icon': 'https://i0.hdslb.com/bfs/live/48360c8f3b7de8031e86ff1ef4a2dfc0ec2a61c2.png', 'guard_level': 3, 'honor_icon': '', 'id': 0, 'is_light': 1, 'level': 27, 'name': '粉丝团', 'ruid': 3546698381003418, 'score': 13918, 'typ': 0, 'user_receive_count': 0, 'v2_medal_color_border': '#5FC7F4', 'v2_medal_color_end': '#3FB4F699', 'v2_medal_color_level': '#3FB4F6E6', 'v2_medal_color_start': '#3FB4F699', 'v2_medal_color_text': '#FFFFFF'}, 'title': {'old_title_css_id': '', 'title_css_id': ''}, 'uhead_frame': None, 'uid': 388151398, 'wealth': None}, 'user_info': {'face': 'https://i1.hdslb.com/bfs/face/9dfc549c7d6809eafa93b15b97f9c05a7055752d.jpg', 'face_frame': 'https://i0.hdslb.com/bfs/live/80f732943cc3367029df65e267960d56736a82ee.png', 'guard_level': 3, 'is_main_vip': 0, 'is_svip': 0, 'is_vip': 0, 'level_color': '#61c05a', 'manager': 0, 'name_color': '#00D1F1', 'title': '', 'uname': '安安安小雅w', 'user_level': 20}}, 'is_report': True, 'msg_id': '96950106411035137:1000:1000', 'p_is_ack': True, 'p_msg_type': 1, 'send_time': 1781012706457}}
# 超级留言： {'room_display_id': 1879006019, 'room_real_id': 1879006019, 'type': 'SUPER_CHAT_MESSAGE', 'data': {'cmd': 'SUPER_CHAT_MESSAGE', 'data': {'background_bottom_color': '#2A60B2', 'background_color': '#EDF5FF', 'background_color_end': '#405D85', 'background_color_start': '#3171D2', 'background_icon': '', 'background_image': '', 'background_price_color': '#7497CD', 'color_point': 0.7, 'dmscore': 280, 'end_time': 1781095502, 'gift': {'gift_id': 12000, 'gift_name': '醒目留言', 'num': 1}, 'group_medal': {'is_lighted': 0, 'medal_id': 0, 'name': ''}, 'id': 16755420, 'is_mystery': False, 'is_ranked': 0, 'is_send_audit': 0, 'medal_info': {'anchor_roomid': 1879006019, 'anchor_uname': '酥柔柔', 'guard_level': 0, 'icon_id': 0, 'is_lighted': 1, 'medal_color': '#5c968e', 'medal_color_border': 6067854, 'medal_color_end': 6067854, 'medal_color_start': 6067854, 'medal_level': 1, 'medal_name': '粉丝团', 'special': '', 'target_id': 3546698381003418}, 'message': '为了你我怒充了3块', 'message_font_color': '#A3F6FF', 'message_trans': '', 'price': 2, 'rate': 1000, 'start_time': 1781095497, 'time': 5, 'token': 'EB002F5B', 'trans_mark': 0, 'ts': 1781095497, 'uid': 481939845, 'uinfo': {'base': {'face': 'https://i0.hdslb.com/bfs/face/e2aabe640e7b90675419bf9cccc71148433de9e4.jpg', 'is_mystery': False, 'name': '落迦行走', 'name_color': 0, 'name_color_str': '#666666', 'official_info': {'desc': '', 'role': 0, 'title': '', 'type': -1}, 'origin_info': {'face': 'https://i0.hdslb.com/bfs/face/e2aabe640e7b90675419bf9cccc71148433de9e4.jpg', 'name': '落迦行走'}, 'risk_ctrl_info': None}, 'guard': {'expired_str': '', 'level': 0}, 'guard_leader': None, 'medal': {'color': 6067854, 'color_border': 6067854, 'color_end': 6067854, 'color_start': 6067854, 'guard_icon': '', 'guard_level': 0, 'honor_icon': '', 'id': 0, 'is_light': 1, 'level': 1, 'name': '粉丝团', 'ruid': 3546698381003418, 'score': 1, 'typ': 0, 'user_receive_count': 0, 'v2_medal_color_border': '#5762A799', 'v2_medal_color_end': '#5762A799', 'v2_medal_color_level': '#5762A7E6', 'v2_medal_color_start': '#5762A799', 'v2_medal_color_text': '#FFFFFF'}, 'title': {'old_title_css_id': '', 'title_css_id': ''}, 'uhead_frame': None, 'uid': 481939845, 'wealth': None}, 'user_info': {'face': 'https://i0.hdslb.com/bfs/face/e2aabe640e7b90675419bf9cccc71148433de9e4.jpg', 'face_frame': '', 'guard_level': 0, 'is_main_vip': 0, 'is_svip': 0, 'is_vip': 0, 'level_color': '#61c05a', 'manager': 0, 'name_color': '#666666', 'title': '', 'uname': '落迦行走', 'user_level': 20}}, 'is_report': True, 'msg_id': '97036919205049344:1000:1000', 'p_is_ack': True, 'p_msg_type': 1, 'send_time': 1781095497589}}
state = 0


async def live_start_handler(event):
    global state  # ✅ 必须加这行，声明要修改全局变量state
    if features["enable_live_start"]:
        state += 1
        print("直播开始：", event)
        if features["enable_qq_notification"]:
            if state == 1:  # 只在第一次直播开始时发送通知，避免重复通知
                from avatar_proxy import fetch_image_data_uri_uncompressed

                cover_data_uri = (
                    fetch_image_data_uri_uncompressed(room_cover)
                    if room_cover
                    else None
                )
                send_qq_group(
                    f"直播开始了：\n{room_title}\nhttps://live.bilibili.com/{str(LESSONROOMID)}",
                    cover_data_uri,
                )


# 礼物处理器
async def on_gift_handler(event):
    if features["enable_gift"]:
        parsed_gift = parse_gift(event)
        print("礼物：", parsed_gift)
        send_to_frontend(parsed_gift)


def on_window_ready():
    import threading

    if room:
        threading.Thread(target=lambda: sync(room.connect()), daemon=True).start()
    else:
        print("警告：直播间监听未初始化")

    if sender:
        threading.Thread(target=lambda: sync(sender.connect()), daemon=True).start()
    else:
        print("警告：弹幕发送器未初始化")


async def init_sender_and_get_info():
    global sender, room_title, room_cover
    room_info = await sender.get_room_info()
    room_title = room_info["room_info"]["title"]
    room_cover = room_info["room_info"]["cover"]
    print("✓ 获取直播间信息成功", room_info["room_info"])
    print("直播间信息：", room_title, room_cover)


if __name__ == "__main__":
    # 获取有效的登录凭据
    COOKIES_FILE = os.path.join(os.path.dirname(__file__), "cookies.json")
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

    window = webview.create_window(
        title="B站弹幕姬",
        url="index.html",
        js_api=CloseApi(),
        width=400,
        height=700,
        frameless=True,
        on_top=True,
        transparent=True,
    )
    window.events.loaded += on_window_ready
    webview.start(debug=features["web_debug"])
