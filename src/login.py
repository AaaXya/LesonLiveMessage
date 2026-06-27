"""B站登录管理模块"""

import os
import json
import time
import requests
from bilibili_api import login_v2, Credential, sync


def load_preset_from_env():
    """预设 cookies：优先从环境变量读取
    - 支持 `BILI_PRESET_COOKIES` 环境变量（JSON 字符串）
    - 或者使用逐项环境变量（例如 SESSDATA、bili_jct 等）
    """
    env_json = os.environ.get("BILI_PRESET_COOKIES")
    if env_json:
        try:
            return json.loads(env_json)
        except Exception as e:
            print("解析 BILI_PRESET_COOKIES 失败：", e)
            return None

    keys = [
        "SESSDATA",
        "buvid3",
        "buvid4",
        "bili_jct",
        "ac_time_value",
        "DedeUserID",
        "sessdata",
        "dedeuserid",
    ]
    cookies = {}
    for k in keys:
        v = os.environ.get(k)
        if v:
            cookies[k] = v
    return cookies if cookies else None


def normalize_cookies(raw):
    """Normalize cookies into dict{name: value}"""
    if not raw:
        return {}
    if isinstance(raw, dict):
        return raw
    # handle list of cookie dicts [{'name':..., 'value':...}, ...]
    if isinstance(raw, list):
        out = {}
        for item in raw:
            try:
                name = item.get("name") or item.get("key")
                value = item.get("value") or item.get("val")
                if name:
                    out[name] = value
            except Exception:
                continue
        return out
    return {}


def create_credential_from_cookies(cookies_dict):
    """Create Credential object from cookies dictionary"""
    if not cookies_dict:
        return None
    try:
        sessdata = cookies_dict.get("SESSDATA") or cookies_dict.get("sessdata")
        bili_jct = cookies_dict.get("bili_jct") or cookies_dict.get("BILI_JCT")
        buvid3 = cookies_dict.get("buvid3") or cookies_dict.get("BUVID3")
        credential = Credential(
            sessdata=sessdata or "", bili_jct=bili_jct or "", buvid3=buvid3 or ""
        )
        return credential
    except Exception as e:
        print("创建 Credential 失败：", e)
        return None


def check_login_with_cookies(cookies_dict) -> bool:
    """验证 cookies 是否有效"""
    if not cookies_dict:
        return False
    try:
        url = "https://api.bilibili.com/x/web-interface/nav"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": "https://www.bilibili.com/",
            "Accept": "application/json, text/javascript, */*; q=0.01",
        }
        resp = requests.get(url, cookies=cookies_dict, headers=headers, timeout=6)
        data = resp.json()
        if (
            isinstance(data, dict)
            and data.get("code") == 0
            and data.get("data", {}).get("mid")
        ):
            return True
        print("登录校验未通过，返回数据：", data)
    except Exception as e:
        print("验证 cookies 时出错：", e)
    return False


async def qrcode_login() -> dict:
    """二维码登录获取 cookies"""
    qr = login_v2.QrCodeLogin(platform=login_v2.QrCodeLoginChannel.WEB)
    await qr.generate_qrcode()
    print(qr.get_qrcode_terminal())
    while not qr.has_done():
        print(await qr.check_state())
        time.sleep(10)
    cookies = qr.get_credential().get_cookies()
    print(cookies)
    return cookies


def get_credential(cookies_file: str, roomid: int) -> Credential:
    """获取有效的 Credential 对象

    优先级：
    1. 本地 cookies.json
    2. 环境变量预设 cookies
    3. 二维码登录

    Args:
        cookies_file: cookies.json 文件路径
        roomid: 直播间ID，用于保存到 .env

    Returns:
        Credential 对象，若失败则返回 None
    """
    cookies = None
    try:
        if os.path.exists(cookies_file):
            with open(cookies_file, "r", encoding="utf-8") as f:
                cookies = json.load(f)
            print("Loaded local cookies from", cookies_file)
        elif load_preset_from_env():
            cookies = load_preset_from_env()
            with open(cookies_file, "w", encoding="utf-8") as f:
                json.dump(cookies, f, ensure_ascii=False)
            print("Saved preset cookies to", cookies_file)
        else:
            cookies = sync(qrcode_login())
            with open(cookies_file, "w", encoding="utf-8") as f:
                json.dump(cookies, f, ensure_ascii=False)
            print("Saved fetched cookies to", cookies_file)
    except Exception as e:
        print("处理 cookies 时出错：", e)
        return None

    # 规范化并验证 cookies
    norm = normalize_cookies(cookies)
    logged_in = check_login_with_cookies(norm)
    credential = create_credential_from_cookies(norm)

    if not logged_in:
        print("当前 cookies 无效，开始重新二维码登录获取 cookies")
        try:
            new_cookies = sync(qrcode_login())
            norm = normalize_cookies(new_cookies)
            if not check_login_with_cookies(norm):
                print("二维码登录后仍然无法验证登录，请检查 cookie 是否正确")
                return None
            with open(cookies_file, "w", encoding="utf-8") as f:
                json.dump(new_cookies, f, ensure_ascii=False)
            credential = create_credential_from_cookies(norm)
        except Exception as e:
            print("重新获取 cookies 失败：", e)
            return None

    return credential
