from bilibili_api import login_v2,live, sync
import json
import webview
import time

window = None
LESONROOMID = 510
# 弹幕解析
def parse_bilibili_danmu(raw_data):
    try:
        room_id = raw_data.get('room_display_id', '未知房间')
        data = raw_data.get('data', {})
        info = data.get('info', [])

        def safe_list(lst, index, default):
            if isinstance(lst, list) and len(lst) > index:
                return lst[index]
            return default

        content = safe_list(info, 1, "无内容")
        user_info = info[2] if len(info) > 2 else []
        medal_info = info[3] if len(info) > 3 else []
        extra_info = info[15] if len(info) > 15 else {}

        extra = {}
        try:
            extra_str = extra_info.get('extra', '{}') if isinstance(extra_info, dict) else '{}'
            extra = json.loads(extra_str)
        except:
            extra = {}

        danmu = {
            "type": "danmu",
            "username": safe_list(user_info, 1, "匿名用户"),
            "content": content,
            "medal_level": safe_list(medal_info, 0, 0),
            "medal_name": safe_list(medal_info, 1, "无粉丝牌"),
        }
        return danmu
    except Exception as e:
        print(f"弹幕解析失败: {e}")
        return None

# ====== 新增礼物解析函数 ======
def parse_gift(raw_data):
    try:
        body = raw_data.get("data", {})
        gift_data = body.get("data", {})  # 关键：内层data才是礼物核心数据
        sender_info = body.get("sender_uinfo", {})
        medal = sender_info.get("medal", {})
        user_base = sender_info.get("base", {})

        # 1. 用户名双兜底：先取脱敏名，再取完整名
        username = gift_data.get("uname", user_base.get("name", "匿名用户"))
        
        # 2. 礼物金额多来源优先级：total_coin > combo_total_coin > price × num
        total_coin = gift_data.get("total_coin", 0)
        if total_coin == 0:
            total_coin = gift_data.get("combo_total_coin", 0)
        if total_coin == 0:
            price = gift_data.get("price", 0)
            num = gift_data.get("num", 1)
            total_coin = price * num

        gift_info = {
            "type": "gift",
            "username": username,
            "gift_name": gift_data.get("giftName", "未知礼物"),
            "gift_num": gift_data.get("num", 1),
            "total_coin": total_coin,  # 现在能正确取到金额了
            "medal_name": medal.get("name", "无粉丝牌"),
            "medal_level": medal.get("level", 0),
        }
        return gift_info
    except Exception as e:
        print(f"礼物解析失败:{e}")
        return None

# 推送数据到前端
def send_to_frontend(data):
    if window and data:
        window.evaluate_js(f"addDanmu({json.dumps(data, ensure_ascii=False)})")

# 直播间监听
room = live.LiveDanmaku(LESONROOMID)

@room.on('DANMU_MSG')
async def on_danmaku(event):
    parsed = parse_bilibili_danmu(event)
    print(parsed)
    send_to_frontend(parsed)

@room.on('GUARD_BUY')
async def on_guard_buy(event): 
    print("大航海续费：", event)  
@room.on('SEND_GIFT')
async def on_gift(event):
    parsed_gift = parse_gift(event)
    print("礼物：", parsed_gift)
    send_to_frontend(parsed_gift)

def on_window_ready():
    import threading
    threading.Thread(target=lambda: sync(room.connect()), daemon=True).start()

if __name__ == '__main__':
    window = webview.create_window(
        title="B站弹幕姬",
        url="index.html",
        width=500,
        height=800,
        frameless=True,
        on_top=True,
        transparent=True
    )
    window.events.loaded += on_window_ready
    webview.start()

async def main() -> None:
    qr = login_v2.QrCodeLogin(platform=login_v2.QrCodeLoginChannel.WEB) # 生成二维码登录实例，平台选择网页端
    await qr.generate_qrcode()                                          # 生成二维码
    print(qr.get_qrcode_terminal())                                     # 生成终端二维码文本，打印
    while not qr.has_done():                                            # 在完成扫描前轮询
        print(await qr.check_state())                                   # 检查状态
        time.sleep(1)                                                   # 轮训间隔建议 >=1s
    print(qr.get_credential().get_cookies())                            # 获取 Credential 类，打印其 Cookies 信息

if __name__ == '__main__':
    sync(main())