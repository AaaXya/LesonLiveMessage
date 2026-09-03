"""B站登录管理模块"""

import os
import json
import time
import asyncio
import base64
import tempfile
import webbrowser
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


def _open_qrcode_guide(qrcode_path: str) -> None:
    """打开带分步说明的二维码登录页面，兼容无控制台的打包版。"""
    with open(qrcode_path, "rb") as f:
        qrcode_data = base64.b64encode(f.read()).decode("ascii")
    guide_path = os.path.join(tempfile.gettempdir(), "runlivetest_qrcode_login.html")
    html = f"""<!doctype html>
<html lang="zh-CN">
<meta charset="utf-8">
<title>RunLiveTest - Bilibili 扫码登录</title>
<style>
body {{ font-family: sans-serif; margin: 32px; color: #242424; }}
h1 {{ font-size: 22px; margin-bottom: 8px; }}
p {{ color: #666; }}
ol {{ line-height: 1.9; padding-left: 28px; }}
img {{ display: block; width: 280px; height: 280px; margin: 20px 0; }}
strong {{ color: #d95f02; }}
</style>
<h1>Bilibili 账号扫码登录</h1>
<p>首次运行需要使用你的 <strong>Bilibili 账号</strong> 完成登录。</p>
<ol>
  <li>打开手机上的 Bilibili 客户端。</li>
  <li>进入“我的” → 扫一扫，扫描下方二维码。</li>
  <li>手机显示登录确认后，点击确认登录。</li>
  <li>登录成功后窗口会自动继续启动。</li>
</ol>
<img src="data:image/png;base64,{qrcode_data}" alt="Bilibili 登录二维码">
</html>
"""
    with open(guide_path, "w", encoding="utf-8") as f:
        f.write(html)
    webbrowser.open(f"file://{guide_path}")


async def qrcode_login() -> dict:
    """二维码登录获取 cookies"""
    qr = login_v2.QrCodeLogin(platform=login_v2.QrCodeLoginChannel.WEB)
    await qr.generate_qrcode()
    qrcode_path = os.path.join(tempfile.gettempdir(), "qrcode.png")
    try:
        _open_qrcode_guide(qrcode_path)
    except Exception as e:
        print("打开二维码引导页失败：", e)
        print(qr.get_qrcode_terminal())
    while not qr.has_done():
        state = await qr.check_state()
        print(f"Bilibili 扫码登录状态：{state}")
        if state == login_v2.QrCodeLoginEvents.DONE:
            break
        await asyncio.sleep(10)
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
    obtained_from_qrcode = False
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
            obtained_from_qrcode = True
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

    if not logged_in and obtained_from_qrcode:
        # 二维码登录本身已取得 Credential；在线校验偶发失败时不要阻断主窗口启动。
        print("二维码登录已完成，但在线校验未通过，继续使用刚获取的凭据启动")
    elif not logged_in:
        print("当前 cookies 无效，开始重新二维码登录获取 cookies")
        try:
            new_cookies = sync(qrcode_login())
            norm = normalize_cookies(new_cookies)
            if not check_login_with_cookies(norm):
                print("二维码登录已完成，但在线校验未通过，继续使用刚获取的凭据启动")
            with open(cookies_file, "w", encoding="utf-8") as f:
                json.dump(new_cookies, f, ensure_ascii=False)
            credential = create_credential_from_cookies(norm)
        except Exception as e:
            print("重新获取 cookies 失败：", e)
            return None

    return credential
