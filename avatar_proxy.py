import base64
import io
import requests
from PIL import Image

avatar_cache = {}
MAX_AVATAR_DIMENSION = 80
JPEG_QUALITY = 75


def _compress_image_bytes(image_bytes, fallback_content_type):
    try:
        with Image.open(io.BytesIO(image_bytes)) as img:
            width, height = img.size
            max_side = max(width, height)
            if max_side > MAX_AVATAR_DIMENSION:
                scale = MAX_AVATAR_DIMENSION / max_side
                img = img.resize((int(width * scale), int(height * scale)), Image.LANCZOS)

            output = io.BytesIO()
            if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
                img.save(output, format='PNG', optimize=True)
                return output.getvalue(), 'image/png'

            rgb_image = img.convert('RGB')
            rgb_image.save(output, format='JPEG', quality=JPEG_QUALITY, optimize=True)
            return output.getvalue(), 'image/jpeg'
    except Exception as e:
        print('头像压缩失败:', e)
        return image_bytes, fallback_content_type


def fetch_image_data_uri(url):
    """Fetch remote avatar and return a compressed data URI for frontend rendering."""
    if not url or url.startswith('data:'):
        return url
    if url in avatar_cache:
        return avatar_cache[url]

    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
            'Referer': 'https://www.bilibili.com/',
            'Accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
        }
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        content_type = resp.headers.get('Content-Type', '')
        if not content_type.startswith('image/'):
            raise ValueError(f'非图片响应: {content_type}')

        image_bytes, mime_type = _compress_image_bytes(resp.content, content_type)
        data_uri = f"data:{mime_type};base64,{base64.b64encode(image_bytes).decode('ascii')}"
        avatar_cache[url] = data_uri
        return data_uri
    except Exception as e:
        print(f'头像代理请求失败: {url} -> {e}')
        avatar_cache[url] = None
        return None
