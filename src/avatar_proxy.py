import atexit
import base64
import io
import json
import os
import threading
import time

import requests
from PIL import Image

from . import DATA_ROOT

# B 站图片防盗链：统一请求头（带 Referer 否则 403）
_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Referer": "https://www.bilibili.com/",
    "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
}
HTTP_TIMEOUT = 8  # 图片下载超时（秒）

avatar_cache = {}
MAX_AVATAR_DIMENSION = 80
JPEG_QUALITY = 75

cover_cache = {}
MAX_COVER_DIMENSION = 640
COVER_JPEG_QUALITY = 80

# 持久化缓存：data/image_cache/image_cache.json
CACHE_DIR = os.path.join(DATA_ROOT, "data", "image_cache")
CACHE_FILE = os.path.join(CACHE_DIR, "image_cache.json")

_cache_lock = threading.Lock()

# ---- 每线程一个 requests.Session（复用 TCP 连接池） ----
_tls = threading.local()


def _get_session():
    session = getattr(_tls, "session", None)
    if session is None:
        session = requests.Session()
        session.headers.update(_HEADERS)
        _tls.session = session
    return session


# ---- 并发去重：同一 URL 同一时刻只允许一个线程下载 ----
_url_locks = {}
_url_lock_usage = {}
_url_locks_guard = threading.Lock()


def _acquire_url_lock(url):
    with _url_locks_guard:
        lock = _url_locks.get(url)
        if lock is None:
            lock = threading.Lock()
            _url_locks[url] = lock
        _url_lock_usage[url] = _url_lock_usage.get(url, 0) + 1
        return lock


def _release_url_lock(url, lock):
    with _url_locks_guard:
        count = _url_lock_usage.get(url, 0) - 1
        if count <= 0:
            _url_locks.pop(url, None)
            _url_lock_usage.pop(url, None)
        else:
            _url_lock_usage[url] = count


# ---- 下载失败负缓存：短时间内不重复重试失败 URL ----
_failed_at = {}
NEGATIVE_CACHE_SECONDS = 60
MAX_FAILED_ENTRIES = 2000


def _remember_failure(url):
    with _cache_lock:
        if len(_failed_at) >= MAX_FAILED_ENTRIES:
            _failed_at.clear()
        _failed_at[url] = time.monotonic()


def _load_cache():
    """启动时从磁盘加载图片缓存"""
    try:
        if not os.path.isfile(CACHE_FILE):
            return
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        for k, v in (data.get("avatar") or {}).items():
            avatar_cache[k] = v
        for k, v in (data.get("cover") or {}).items():
            cover_cache[k] = v
        print(
            f"图片缓存已加载：头像 {len(avatar_cache)} 张，封面 {len(cover_cache)} 张"
        )
    except Exception as e:
        print("图片缓存加载失败:", e)


# ---- 写盘节流：合并短时间内的多次更新，避免弹幕高峰期频繁写大文件 ----
SAVE_INTERVAL = 5.0
_save_state_lock = threading.Lock()
_save_dirty = False


def _save_cache():
    """标记缓存有更新（由后台线程周期落盘）"""
    global _save_dirty
    with _save_state_lock:
        _save_dirty = True


def _flush_cache():
    """将内存缓存落盘（仅保存成功结果，失败的留待下次启动重试）"""
    global _save_dirty
    with _save_state_lock:
        if not _save_dirty:
            return
        with _cache_lock:
            data = {
                "avatar": {k: v for k, v in avatar_cache.items() if v},
                "cover": {k: v for k, v in cover_cache.items() if v},
            }
        _save_dirty = False
    try:
        os.makedirs(CACHE_DIR, exist_ok=True)
        tmp_file = CACHE_FILE + ".tmp"
        with open(tmp_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
        os.replace(tmp_file, CACHE_FILE)
    except Exception as e:
        print("图片缓存保存失败:", e)


def _start_cache_flusher():
    """后台线程周期性落盘；程序退出时由 atexit 兜底"""

    def _loop():
        while True:
            time.sleep(SAVE_INTERVAL)
            _flush_cache()

    threading.Thread(target=_loop, daemon=True, name="image-cache-flusher").start()


_start_cache_flusher()
atexit.register(_flush_cache)


def _compress_image(image_bytes, max_dimension, jpeg_quality, fallback_content_type):
    """压缩图片（长边缩放到 max_dimension），返回 (bytes, mime_type)；失败返回原图"""
    try:
        with Image.open(io.BytesIO(image_bytes)) as img:
            width, height = img.size
            max_side = max(width, height)
            if max_side > max_dimension:
                scale = max_dimension / max_side
                img = img.resize(
                    (int(width * scale), int(height * scale)), Image.LANCZOS
                )

            output = io.BytesIO()
            if img.mode in ("RGBA", "LA") or (
                img.mode == "P" and "transparency" in img.info
            ):
                img.save(output, format="PNG", optimize=True)
                return output.getvalue(), "image/png"

            img.convert("RGB").save(
                output, format="JPEG", quality=jpeg_quality, optimize=True
            )
            return output.getvalue(), "image/jpeg"
    except Exception as e:
        print("图片压缩失败:", e)
        return image_bytes, fallback_content_type


def _download_image(url):
    """下载图片，返回 (bytes, content_type)；失败返回 (None, None)"""
    try:
        resp = _get_session().get(url, timeout=HTTP_TIMEOUT)
        resp.raise_for_status()
        content_type = resp.headers.get("Content-Type", "").strip() or "image/jpeg"
        if not content_type.startswith("image/"):
            raise ValueError(f"非图片响应: {content_type}")
        return resp.content, content_type
    except Exception as e:
        print(f"图片下载失败: {url} -> {e}")
        return None, None


def fetch_image_data_uri(url):
    """拉取头像并压缩为 data URI（带缓存，线程安全，同一 URL 并发只下载一次）"""
    if not url or url.startswith("data:"):
        return url

    lock = _acquire_url_lock(url)
    try:
        with lock:
            with _cache_lock:
                cached = avatar_cache.get(url)
            if cached:
                return cached
            with _cache_lock:
                failed_at = _failed_at.get(url)
            if failed_at and time.monotonic() - failed_at < NEGATIVE_CACHE_SECONDS:
                return None

            image_bytes, content_type = _download_image(url)
            if image_bytes is None:
                _remember_failure(url)
                return None

            image_bytes, mime_type = _compress_image(
                image_bytes, MAX_AVATAR_DIMENSION, JPEG_QUALITY, content_type
            )
            data_uri = f"data:{mime_type};base64,{base64.b64encode(image_bytes).decode('ascii')}"
            with _cache_lock:
                avatar_cache[url] = data_uri
                _failed_at.pop(url, None)
            _save_cache()
            return data_uri
    finally:
        _release_url_lock(url, lock)


def fetch_image_data_uri_uncompressed(url):
    """Fetch remote image and return an uncompressed data URI."""
    if not url or url.startswith("data:"):
        return url

    image_bytes, content_type = _download_image(url)
    if image_bytes is None:
        return None
    return f"data:{content_type};base64,{base64.b64encode(image_bytes).decode('ascii')}"


def fetch_cover_data_uri(url):
    """获取直播间封面并压缩为 data URI（带缓存），供前端直接展示。"""
    if not url or url.startswith("data:"):
        return url or None

    lock = _acquire_url_lock(url)
    try:
        with lock:
            with _cache_lock:
                cached = cover_cache.get(url)
            if cached:
                return cached

            image_bytes, content_type = _download_image(url)
            if image_bytes is None:
                return None

            image_bytes, mime_type = _compress_image(
                image_bytes, MAX_COVER_DIMENSION, COVER_JPEG_QUALITY, content_type
            )
            data_uri = f"data:{mime_type};base64,{base64.b64encode(image_bytes).decode('ascii')}"
            with _cache_lock:
                cover_cache[url] = data_uri
            _save_cache()
            return data_uri
    finally:
        _release_url_lock(url, lock)


# 模块导入时加载磁盘缓存
_load_cache()


# 房间封面持久化：以 room_id 为键存 {url, data}，可直接手动编辑本地 JSON
COVERS_FILE = os.path.join(DATA_ROOT, "data", "room_covers.json")
room_cover_store = {}


def _load_room_covers():
    """启动时从 data/room_covers.json 加载房间封面"""
    try:
        if not os.path.isfile(COVERS_FILE):
            return
        with open(COVERS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            for k, v in data.items():
                k = str(k).strip()
                if not k:
                    continue
                if isinstance(v, dict):
                    # 新格式：{"url": ..., "data": ...}
                    data_uri = str(v.get("data", "") or "")
                    if data_uri.startswith("data:image"):
                        room_cover_store[k] = {
                            "url": str(v.get("url", "") or ""),
                            "data": data_uri,
                        }
                elif isinstance(v, str) and v.startswith("data:image"):
                    # 兼容旧格式：直接存 data URI（无 URL 记录）
                    room_cover_store[k] = {"url": "", "data": v}
        print(f"房间封面已加载：{len(room_cover_store)} 个")
    except Exception as e:
        print("房间封面缓存加载失败:", e)


def _save_room_covers():
    """持久化房间封面到 data/room_covers.json"""
    try:
        with _cache_lock:
            data = dict(room_cover_store)
        os.makedirs(os.path.dirname(COVERS_FILE), exist_ok=True)
        tmp_file = COVERS_FILE + ".tmp"
        with open(tmp_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(tmp_file, COVERS_FILE)
    except Exception as e:
        print("房间封面缓存保存失败:", e)


def fetch_room_cover(room_id, url):
    """获取房间封面 data URI。

    - 本地缓存的 URL 与当前 URL 一致（或无远程 URL）时直接读本地
    - URL 变化时重新下载并更新缓存
    """
    room_id = str(room_id).strip()
    if not room_id:
        return ""

    remote_url = str(url or "").strip()

    with _cache_lock:
        cached = room_cover_store.get(room_id)

    if cached:
        cached_url = cached.get("url", "")
        cached_data = cached.get("data", "")
        # 无远程 URL，或 URL 未变化 → 直接读本地
        if not remote_url or remote_url == cached_url:
            return cached_data
    elif not remote_url:
        return ""

    # 需要下载：新房间或 URL 已变化
    data_uri = fetch_cover_data_uri(remote_url)
    if data_uri:
        with _cache_lock:
            room_cover_store[room_id] = {"url": remote_url, "data": data_uri}
        _save_room_covers()
        return data_uri

    # 下载失败：保留旧图（若有）
    if cached:
        return cached.get("data", "")
    return ""


_load_room_covers()
