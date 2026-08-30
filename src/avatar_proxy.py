import base64
import io
import json
import os
import threading

import requests
from PIL import Image

from . import PROJECT_ROOT

avatar_cache = {}
MAX_AVATAR_DIMENSION = 80
JPEG_QUALITY = 75

cover_cache = {}
MAX_COVER_DIMENSION = 640
COVER_JPEG_QUALITY = 80

# 持久化缓存：data/image_cache/image_cache.json
CACHE_DIR = os.path.join(PROJECT_ROOT, "data", "image_cache")
CACHE_FILE = os.path.join(CACHE_DIR, "image_cache.json")

_cache_lock = threading.Lock()


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


def _save_cache():
    """持久化图片缓存到磁盘（仅保存成功结果，失败的留待下次启动重试）"""
    try:
        with _cache_lock:
            data = {
                "avatar": {k: v for k, v in avatar_cache.items() if v},
                "cover": {k: v for k, v in cover_cache.items() if v},
            }
        os.makedirs(CACHE_DIR, exist_ok=True)
        tmp_file = CACHE_FILE + ".tmp"
        with open(tmp_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
        os.replace(tmp_file, CACHE_FILE)
    except Exception as e:
        print("图片缓存保存失败:", e)


def _compress_image_bytes(image_bytes, fallback_content_type):
    try:
        with Image.open(io.BytesIO(image_bytes)) as img:
            width, height = img.size
            max_side = max(width, height)
            if max_side > MAX_AVATAR_DIMENSION:
                scale = MAX_AVATAR_DIMENSION / max_side
                img = img.resize(
                    (int(width * scale), int(height * scale)), Image.LANCZOS
                )

            output = io.BytesIO()
            if img.mode in ("RGBA", "LA") or (
                img.mode == "P" and "transparency" in img.info
            ):
                img.save(output, format="PNG", optimize=True)
                return output.getvalue(), "image/png"

            rgb_image = img.convert("RGB")
            rgb_image.save(output, format="JPEG", quality=JPEG_QUALITY, optimize=True)
            return output.getvalue(), "image/jpeg"
    except Exception as e:
        print("头像压缩失败:", e)
        return image_bytes, fallback_content_type


def fetch_image_data_uri(url):
    """Fetch remote avatar and return a compressed data URI for frontend rendering."""
    if not url or url.startswith("data:"):
        return url
    with _cache_lock:
        if url in avatar_cache:
            return avatar_cache[url]

    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
            "Referer": "https://www.bilibili.com/",
            "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
        }
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        content_type = resp.headers.get("Content-Type", "")
        if not content_type.startswith("image/"):
            raise ValueError(f"非图片响应: {content_type}")

        image_bytes, mime_type = _compress_image_bytes(resp.content, content_type)
        data_uri = (
            f"data:{mime_type};base64,{base64.b64encode(image_bytes).decode('ascii')}"
        )
        with _cache_lock:
            avatar_cache[url] = data_uri
        _save_cache()
        return data_uri
    except Exception as e:
        print(f"头像代理请求失败: {url} -> {e}")
        with _cache_lock:
            avatar_cache[url] = None
        return None


def fetch_image_data_uri_uncompressed(url):
    """Fetch remote image and return an uncompressed data URI."""
    if not url or url.startswith("data:"):
        return url

    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
            "Referer": "https://www.bilibili.com/",
        }
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        content_type = resp.headers.get("Content-Type", "image/jpeg")
        data_uri = f"data:{content_type};base64,{base64.b64encode(resp.content).decode('ascii')}"
        return data_uri
    except Exception as e:
        print(f"获取图片失败: {url} -> {e}")
        return None


cover_cache = {}
MAX_COVER_DIMENSION = 640
COVER_JPEG_QUALITY = 80


def fetch_cover_data_uri(url):
    """获取直播间封面并压缩为 data URI（带缓存），供前端直接展示。"""
    if not url or url.startswith("data:"):
        return url or None
    with _cache_lock:
        if url in cover_cache:
            return cover_cache[url]

    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
            "Referer": "https://www.bilibili.com/",
            "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
        }
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        content_type = resp.headers.get("Content-Type", "")
        if not content_type.startswith("image/"):
            raise ValueError(f"非图片响应: {content_type}")

        with Image.open(io.BytesIO(resp.content)) as img:
            width, height = img.size
            max_side = max(width, height)
            if max_side > MAX_COVER_DIMENSION:
                scale = MAX_COVER_DIMENSION / max_side
                img = img.resize(
                    (int(width * scale), int(height * scale)), Image.LANCZOS
                )
            output = io.BytesIO()
            if img.mode in ("RGBA", "LA") or (
                img.mode == "P" and "transparency" in img.info
            ):
                img.save(output, format="PNG", optimize=True)
                mime_type = "image/png"
            else:
                img.convert("RGB").save(
                    output, format="JPEG", quality=COVER_JPEG_QUALITY, optimize=True
                )
                mime_type = "image/jpeg"

        data_uri = f"data:{mime_type};base64,{base64.b64encode(output.getvalue()).decode('ascii')}"
        with _cache_lock:
            cover_cache[url] = data_uri
        _save_cache()
        return data_uri
    except Exception as e:
        print(f"封面代理请求失败: {url} -> {e}")
        with _cache_lock:
            cover_cache[url] = None
        return None


# 模块导入时加载磁盘缓存
_load_cache()


# 房间封面持久化：以 room_id 为键存 {url, data}，可直接手动编辑本地 JSON
COVERS_FILE = os.path.join(PROJECT_ROOT, "data", "room_covers.json")
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
