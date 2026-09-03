"""B站登录管理模块"""

import os
import json
import time
import asyncio
import base64
import tempfile
import threading
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


def evaluate_login_with_cookies(cookies_dict):
    """评估 cookies 登录状态（三态，用于区分“失效”与“无法判定”）

    返回:
      True  - 已登录，cookies 有效
      False - 服务端明确未登录（凭据失效/过期）
      None  - 无法判定（网络异常等瞬时错误），不应据此判定失效而触发重登
    """
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
        # 服务端明确返回未登录等错误码：凭据确实失效
        print("登录校验未通过，返回数据：", data)
        return False
    except Exception as e:
        # 网络异常等：无法确认凭据失效，按“不确定”处理，避免误弹登录页
        print("验证 cookies 时出错：", e)
        return None


def check_login_with_cookies(cookies_dict) -> bool:
    """验证 cookies 是否有效（布尔版，供简单判断使用）"""
    return evaluate_login_with_cookies(cookies_dict) is True


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

    行为（兼顾“不打扰正常启动”与“不带失效凭据硬启动”）：
    1. 本地 cookies 仍有效 → 直接使用，不弹任何登录页
    2. 本地 cookies 明确失效（服务端返回未登录）→ 重新二维码登录拿到新凭据后再继续
    3. 本地 cookies 无法判定（网络异常等瞬时错误）→ 先沿用本地凭据继续，不弹登录页
    4. 无本地 cookies / 无预设 → 首次二维码登录

    Args:
        cookies_file: cookies.json 文件路径
        roomid: 直播间ID（预留，兼容旧签名）

    Returns:
        Credential 对象；登录失败且无法恢复时返回 None
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
            # 首次运行：直接二维码登录（登录成功即视为有效，无需再在线复核）
            cookies = sync(qrcode_login())
            with open(cookies_file, "w", encoding="utf-8") as f:
                json.dump(cookies, f, ensure_ascii=False)
            print("Saved fetched cookies to", cookies_file)
    except Exception as e:
        print("处理 cookies 时出错：", e)
        return None

    norm = normalize_cookies(cookies)
    login_state = evaluate_login_with_cookies(norm)

    if login_state is True:
        return create_credential_from_cookies(norm)

    if login_state is False:
        # cookies 已失效：不带无效凭据硬打开客户端，先重新扫码登录
        print("本地 cookies 已失效，开始二维码登录获取新凭据")
        try:
            new_cookies = sync(qrcode_login())
            with open(cookies_file, "w", encoding="utf-8") as f:
                json.dump(new_cookies, f, ensure_ascii=False)
            return create_credential_from_cookies(normalize_cookies(new_cookies))
        except Exception as e:
            print("重新二维码登录失败：", e)
            return None

    # login_state 为 None：网络异常等瞬时问题，先沿用本地凭据启动，不弹登录页
    print("cookies 在线校验暂不可用（网络异常？），先沿用本地凭据启动")
    return create_credential_from_cookies(norm)


class LoginManager:
    """应用内扫码登录协调器：后台线程轮询，二维码直接由前端展示。"""

    def __init__(self, cookies_file, on_success=None):
        self.cookies_file = cookies_file
        self._on_success = on_success
        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        self.credential = None
        self._state = {
            "status": "checking",  # checking | ok | scanning | timeout | error
            "message": "",
            "qr_data": None,
        }

    # ---------- 状态 ----------

    def snapshot(self):
        with self._lock:
            return dict(self._state)

    def _set(self, **kw):
        with self._lock:
            self._state.update(kw)

    def _notify(self):
        cb = self._on_success
        if cb is None:
            return
        try:
            cb(self.credential)
        except Exception as e:
            print("登录成功回调失败：", e)

    # ---------- 二维码登录 ----------

    def start_qr(self):
        """开始/刷新二维码登录：结束旧轮询并新开后台线程。"""
        self._stop_event.set()
        self._stop_event = threading.Event()
        self._set(
            status="scanning", message="请使用 B 站手机客户端扫码登录", qr_data=None
        )
        threading.Thread(target=self._run_qr, daemon=True).start()
        return True

    def _run_qr(self):
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self._qr_loop())
        except Exception as e:
            print("二维码登录出错：", e)
            self._set(status="error", message=f"登录出错：{e}")
        finally:
            try:
                asyncio.get_event_loop().close()
            except Exception:
                pass

    async def _qr_loop(self):
        qr = login_v2.QrCodeLogin(platform=login_v2.QrCodeLoginChannel.WEB)
        await qr.generate_qrcode()
        qrcode_path = os.path.join(tempfile.gettempdir(), "qrcode.png")
        try:
            with open(qrcode_path, "rb") as f:
                b64 = base64.b64encode(f.read()).decode("ascii")
        except Exception as e:
            self._set(status="error", message=f"读取二维码失败：{e}")
            return
        self._set(qr_data=f"data:image/png;base64,{b64}", status="scanning")

        stop = self._stop_event
        while not stop.is_set():
            try:
                state = await qr.check_state()
            except Exception as e:
                print("查询扫码状态失败：", e)
                await asyncio.sleep(3)
                continue
            print("Bilibili 扫码状态：", state)
            if state == login_v2.QrCodeLoginEvents.DONE:
                break
            if state == login_v2.QrCodeLoginEvents.TIMEOUT:
                self._set(status="timeout", message="二维码已过期，请点击刷新重试")
                return
            await asyncio.sleep(3)

        cookies = qr.get_credential().get_cookies()
        with open(self.cookies_file, "w", encoding="utf-8") as f:
            json.dump(cookies, f, ensure_ascii=False)
        self.credential = create_credential_from_cookies(normalize_cookies(cookies))
        self._set(status="ok", message="登录成功")
        self._notify()

    # ---------- 启动时的登录探测 ----------

    def bootstrap(self):
        """后台探测本地凭据：有效→直接 ok，缺失/失效→自动发起二维码登录。"""

        def _run():
            try:
                cred, state = resolve_existing_cookies(self.cookies_file)
            except Exception as e:
                print("登录探测失败：", e)
                self.start_qr()
                return
            if state is True:
                self.credential = cred
                self._set(status="ok", message="已登录")
                self._notify()
            elif state is False:
                self.start_qr()
            else:
                # state 为 None：网络异常等无法判定，先沿用本地凭据启动
                self.credential = cred
                self._set(status="ok", message="已登录（在线校验暂不可用）")
                self._notify()

        threading.Thread(target=_run, daemon=True).start()


def resolve_existing_cookies(cookies_file):
    """读取本地/预设 cookies 并在线校验。

    返回 (credential, state)：
      state True  - 有效
      state False - 无凭据或已失效（需要登录）
      state None  - 无法判定（网络异常），可先沿用本地凭据
    """
    cookies = None
    if os.path.exists(cookies_file):
        with open(cookies_file, "r", encoding="utf-8") as f:
            cookies = json.load(f)
        print("Loaded local cookies from", cookies_file)
    elif load_preset_from_env():
        cookies = load_preset_from_env()
        with open(cookies_file, "w", encoding="utf-8") as f:
            json.dump(cookies, f, ensure_ascii=False)
        print("Saved preset cookies to", cookies_file)
    norm = normalize_cookies(cookies or {})
    if not norm:
        return None, False
    state = evaluate_login_with_cookies(norm)
    return create_credential_from_cookies(norm), state
