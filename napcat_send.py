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


def send_qq_group(msg: str):
    payload = json.dumps(
        {
            "message_type": "group",
            "group_id": GROUP_ID,
            "message": msg,  # 用参数传入，灵活修改
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
    send_qq_group("测试：函数封装成功！")
