import requests
import json
import datetime
import os


def load_config():
    config_path = os.path.join(os.path.dirname(__file__), "config.json")
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


config = load_config()

# 你的 NapCat 配置
NAPCAT_URL = "http://127.0.0.1:3000/send_msg"
NAPCAT_TOKEN = "4D7iSSwiD85HCl8h"
GROUP_ID = config["GROUPID"]


def send_qq_group(msg: str, image: str = None):
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
            "group_id": GROUP_ID,
            "message": message,  # 用参数传入，灵活修改
        }
    )
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {NAPCAT_TOKEN}",
    }

    response = requests.post(NAPCAT_URL, headers=headers, data=payload)
    print(f"[{datetime.datetime.now()}] 发送结果:", response.text)
    return response.json()


# 只有直接运行 send.py 才会执行测试
if __name__ == "__main__":
    # send_qq_group("测试：函数封装成功！")
    room_cover = "https://i0.hdslb.com/bfs/live/new_room_cover/46dc3b47198a994dc47d3b58b2cc6b908e6f4c7d.jpg"
    from avatar_proxy import fetch_image_data_uri_uncompressed

    cover_data_uri = (
        fetch_image_data_uri_uncompressed(room_cover) if room_cover else None
    )
    send_qq_group(f"直播开始了 ", cover_data_uri)
