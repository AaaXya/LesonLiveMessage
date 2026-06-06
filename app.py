from bilibili_api import live, sync
import json
import webview
import os
from login import get_credential
from danmu_parser import parse_bilibili_danmu, parse_gift

class CloseApi:
    def closeWindow(self):
        global window
        if window:
            try:
                window.destroy()
            except Exception as e:
                print('关闭窗口失败：', e)

    def minimizeWindow(self):
        global window
        if window:
            try:
                window.minimize()
            except Exception as e:
                print('最小化窗口失败：', e)

    def toggleMaximizeWindow(self):
        global window
        if window:
            try:
                if hasattr(window, 'toggle_maximize'):
                    window.toggle_maximize()
                elif hasattr(window, 'toggle_fullscreen'):
                    window.toggle_fullscreen()
                else:
                    print('toggleMaximizeWindow: 未支持的最大化方法')
            except Exception as e:
                print('切换最大化失败：', e)

    def sendDanmu(self, message):
        global sender
        if not message:
            return {'ok': False, 'error': '弹幕内容不能为空'}

        if sender is None:
            return {'ok': False, 'error': '弹幕发送器未初始化'}

        try:
            if hasattr(sender, 'send_danmaku'):
                if hasattr(live, 'Danmaku'):
                    danmaku = live.Danmaku(message)
                    result = sync(sender.send_danmaku(danmaku))
                else:
                    result = sync(sender.send_danmaku(message))
            else:
                print('sendDanmu: 未找到可用的发送弹幕方法')
                return {'ok': False, 'error': '后端不支持发送弹幕'}

            print('发送弹幕：', message, '结果：', result)
            return {'ok': True, 'result': result}
        except Exception as e:
            print('发送弹幕失败：', e)
            return {'ok': False, 'error': str(e)}


window = None
room = None
sender = None
LESONROOMID = 1879006019

# 推送数据到前端
def send_to_frontend(data):
    if window and data:
        window.evaluate_js(f"addDanmu({json.dumps(data, ensure_ascii=False)})")

# 弹幕消息处理器
async def on_danmaku_handler(event):
    parsed = parse_bilibili_danmu(event)
    if isinstance(parsed, dict):
        parsed_to_log = {k: v for k, v in parsed.items() if k != 'avatar_url'}
    else:
        parsed_to_log = parsed
    print(parsed_to_log)
    send_to_frontend(parsed)

# 大航海续费处理器
async def on_guard_buy_handler(event): 
    print("大航海续费：", event)

# 礼物处理器
async def on_gift_handler(event):
    print("原始礼物事件：", event)
    parsed_gift = parse_gift(event)
    print("礼物：", parsed_gift)
    send_to_frontend(parsed_gift)

def on_window_ready():
    import threading
    if room:
        threading.Thread(target=lambda: sync(room.connect()), daemon=True).start()
    else:
        print('警告：直播间监听未初始化')

    if sender:
        threading.Thread(target=lambda: sync(sender.connect()), daemon=True).start()
    else:
        print('警告：弹幕发送器未初始化')

if __name__ == '__main__':
    # 获取有效的登录凭据
    COOKIES_FILE = os.path.join(os.path.dirname(__file__), 'cookies.json')
    credential = get_credential(COOKIES_FILE, LESONROOMID)
    
    # 初始化监听器和发送器（优先使用有效的 credential）
    if credential:
        try:
            room = live.LiveDanmaku(LESONROOMID, credential=credential)
            sender = live.LiveRoom(LESONROOMID, credential=credential)
            print('✓ 使用有效的凭据初始化 LiveDanmaku 和 LiveRoom')
        except Exception as e:
            print('✗ 初始化 LiveDanmaku/LiveRoom 失败：', e)
            room = live.LiveDanmaku(LESONROOMID)
            sender = live.LiveRoom(LESONROOMID)
    else:
        print('⚠ 无有效凭据，使用无凭据模式初始化 LiveDanmaku 和 LiveRoom')
        room = live.LiveDanmaku(LESONROOMID)
        sender = live.LiveRoom(LESONROOMID)
    
    # 注册事件处理器
    if room:
        room.on('DANMU_MSG')(on_danmaku_handler)
        room.on('GUARD_BUY')(on_guard_buy_handler)
        room.on('SEND_GIFT')(on_gift_handler)

    window = webview.create_window(
        title="B站弹幕姬",
        url="index.html",
        js_api=CloseApi(),
        width=500,
        height=800,
        frameless=True,
        on_top=True,
        transparent=True
    )
    window.events.loaded += on_window_ready
    webview.start(debug=True)
