import requests
import json
import datetime
import os

from . import PROJECT_ROOT


def load_config():
    config_path = os.path.join(PROJECT_ROOT, "config.json")
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


# 你的 NapCat 配置
NAPCAT_URL = "http://127.0.0.1:3000/send_msg"
NAPCAT_TOKEN = "4D7iSSwiD85HCl8h"


def get_group_id(room_id=None):
    config = load_config()
    if room_id is None:
        room_id = config.get("LESSONROOMID")
    binding = config.get("room_bindings", {}).get(str(room_id), {})
    return str(binding.get("GROUPID", "")).strip()


def send_qq_group(msg: str, image: str = None, room_id=None):
    group_id = get_group_id(room_id)
    if not group_id:
        print(f"[{datetime.datetime.now()}] 未配置 QQ 群号，跳过发送")
        return None
    # 动态构造消息内容（核心修改点）
    if image and image.strip():
        # 有图片：构造消息段数组
        message_segments = []
        # 先加文字（文字为空则跳过）
        if msg.strip():
            message_segments.append({"type": "text", "data": {"text": msg}})
        # 再加图片
        message_segments.append({"type": "image", "data": {"file": image}})
        message = message_segments
    else:
        # 无图片：保持原有纯文字格式（完全兼容历史调用）
        message = msg
    payload = json.dumps(
        {
            "message_type": "group",
            "group_id": group_id,
            "message": message,  # 用参数传入，灵活修改
        }
    )
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {NAPCAT_TOKEN}",
    }

    try:
        response = requests.post(NAPCAT_URL, headers=headers, data=payload, timeout=10)
        print(f"[{datetime.datetime.now()}] 发送结果:", response.text)
        return response.json()
    except requests.exceptions.ConnectionError:
        print(f"[{datetime.datetime.now()}] NapCat 服务未启动，跳过 QQ 推送")
        return None
    except requests.exceptions.Timeout:
        print(f"[{datetime.datetime.now()}] NapCat 请求超时，跳过 QQ 推送")
        return None
    except Exception as e:
        print(f"[{datetime.datetime.now()}] QQ 推送失败：{e}")
        return None


# 只有直接运行 send.py 才会执行测试
if __name__ == "__main__":
    # send_qq_group("测试：函数封装成功！")
    room_cover = "https://i0.hdslb.com/bfs/live/new_room_cover/46dc3b47198a994dc47d3b58b2cc6b908e6f4c7d.jpg"
    from avatar_proxy import fetch_image_data_uri_uncompressed

    cover_data_uri = (
        fetch_image_data_uri_uncompressed(room_cover) if room_cover else None
    )
    send_qq_group(f"直播开始了 ", cover_data_uri)
