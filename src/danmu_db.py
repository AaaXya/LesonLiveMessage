import datetime
import os
import re
import sqlite3

from . import PROJECT_ROOT
from .frontend_config import load_app_config

DATA_DIR = os.path.join(PROJECT_ROOT, "data")
LEGACY_DB_FILE = os.path.join(PROJECT_ROOT, "danmu.db")

# 系统级过滤正则（不可由前端修改）
_SYSTEM_FILTER_PATTERNS = [
    re.compile(r"^\[.*\]$"),  # 纯括号文本
]

# 用户自定义滤词（运行时从 config.json 加载）
_user_filter_words = []


def _load_user_filter_words():
    """从 config.json 读取用户滤词列表"""
    global _user_filter_words
    try:
        config = load_app_config()
        _user_filter_words = [
            str(w).strip() for w in config.get("filter_words", []) if str(w).strip()
        ]
    except Exception:
        _user_filter_words = []


def reload_filter_words():
    """供外部（保存配置后）调用，刷新滤词缓存"""
    _load_user_filter_words()


def _should_filter_danmu(content: str) -> bool:
    """检查弹幕内容是否应被过滤（系统正则 + 用户滤词完全匹配）"""
    # 系统正则
    for pattern in _SYSTEM_FILTER_PATTERNS:
        if pattern.fullmatch(content):
            return True
    # 用户滤词（完全匹配，大小写敏感）
    if _user_filter_words:
        for word in _user_filter_words:
            if word == content:
                return True
    return False


# 模块加载时读取一次滤词
_load_user_filter_words()


def get_room_db_file(room_id, ensure_dir=True) -> str:
    room_id_text = str(room_id).strip()
    if not room_id_text.isdigit():
        raise ValueError(f"无效的 room_id：{room_id}")

    if ensure_dir:
        os.makedirs(DATA_DIR, exist_ok=True)
    return os.path.join(DATA_DIR, f"danmu_{room_id_text}.db")


def init_db(room_id):
    conn = sqlite3.connect(get_room_db_file(room_id))
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS danmu (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            content TEXT,
            send_time TEXT,
            uid INTEGER,
            type TEXT DEFAULT 'danmu'
        )
        """)
    # 兼容旧表：没有 type 列则补上
    try:
        cursor.execute("ALTER TABLE danmu ADD COLUMN type TEXT DEFAULT 'danmu'")
    except sqlite3.OperationalError:
        pass
    # 兼容旧表：没有 uid 列则补上
    try:
        cursor.execute("ALTER TABLE danmu ADD COLUMN uid INTEGER")
    except sqlite3.OperationalError:
        pass  # 列已存在
    conn.commit()
    conn.close()


def save_danmu(danmu_dict: dict, room_id):
    now = datetime.datetime.now().isoformat()
    # 直播间不存在则创建
    # init_db(room_id)
    conn = sqlite3.connect(get_room_db_file(room_id))
    cursor = conn.cursor()

    item_type = danmu_dict.get("type", "danmu")
    username = danmu_dict.get("username", "")
    uid = danmu_dict.get("uid")

    if item_type == "super_chat":
        content = (
            f"SC | ¥{danmu_dict.get('price', 0)} | {danmu_dict.get('message', '')}"
        )
    else:
        content = danmu_dict.get("content", "")

    # 过滤：括号纯文本 或 命中过滤词
    if _should_filter_danmu(content):
        conn.close()
        return

    cursor.execute(
        """
        INSERT INTO danmu (username, content, send_time, uid, type)
        VALUES (?, ?, ?, ?, ?)
        """,
        (username, content, now, uid, item_type),
    )
    conn.commit()
    conn.close()
    # 回填同名用户的历史 uid
    # backfill_uid(room_id, username, uid)


def backfill_uid(room_id, username, uid):
    """将同一房间内同名用户的历史 NULL uid 补全"""
    if not uid or not username:
        return
    conn = sqlite3.connect(get_room_db_file(room_id, ensure_dir=False))
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE danmu SET uid = ? WHERE username = ? AND uid IS NULL",
        (uid, username),
    )
    conn.commit()
    conn.close()


def get_today_danmu(room_id):
    today = datetime.date.today().isoformat()
    init_db(room_id)
    conn = sqlite3.connect(get_room_db_file(room_id))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM danmu WHERE send_time LIKE ? ORDER BY send_time ASC",
        (f"{today}%",),
    )
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows


def get_all_danmu(room_id):
    init_db(room_id)
    conn = sqlite3.connect(get_room_db_file(room_id))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM danmu ORDER BY send_time ASC")
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows


if __name__ == "__main__":
    room_id = input("room_id: ").strip()
    print(get_all_danmu(room_id))
