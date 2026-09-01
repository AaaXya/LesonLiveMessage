import datetime
import os
import re
import sqlite3
import threading

from . import DATA_ROOT
from .frontend_config import load_app_config

DATA_DIR = os.path.join(DATA_ROOT, "data")
LEGACY_DB_FILE = os.path.join(DATA_ROOT, "danmu.db")

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


# ---- 数据库连接复用 ----
# 每个线程为每个房间保持一个长连接，避免高弹幕量下频繁 open/close 连接。
# 写线程（直播间连接线程）与读线程（API 线程）互不干扰。
_conns_tls = threading.local()
# 已建表（含列迁移）的房间集合，避免每次写入都重复尝试 ALTER TABLE
_migrated = set()
_migrate_lock = threading.Lock()


def _get_conn(room_id):
    """获取当前线程的数据库连接（复用）"""
    conns = getattr(_conns_tls, "conns", None)
    if conns is None:
        conns = {}
        _conns_tls.conns = conns
    conn = conns.get(room_id)
    if conn is None:
        conn = sqlite3.connect(get_room_db_file(room_id), timeout=10)
        conn.execute("PRAGMA busy_timeout=5000")
        conn.row_factory = sqlite3.Row
        conns[room_id] = conn
    return conn


def get_room_db_file(room_id, ensure_dir=True) -> str:
    room_id_text = str(room_id).strip()
    if not room_id_text.isdigit():
        raise ValueError(f"无效的 room_id：{room_id}")

    if ensure_dir:
        os.makedirs(DATA_DIR, exist_ok=True)
    return os.path.join(DATA_DIR, f"danmu_{room_id_text}.db")


def init_db(room_id):
    room_id = str(room_id).strip()
    with _migrate_lock:
        if room_id in _migrated:
            return
        conn = _get_conn(room_id)
        cursor = conn.cursor()
        try:
            # WAL 模式：写入不阻塞读取（写线程 + API 读线程并发）
            cursor.execute("PRAGMA journal_mode=WAL")
        except sqlite3.DatabaseError:
            pass
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

        # 礼物表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS gift (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT,
                uid INTEGER,
                gift_name TEXT,
                gift_num INTEGER,
                total_coin INTEGER,
                paid_coin INTEGER,
                send_time TEXT,
                medal_name TEXT,
                medal_level INTEGER
            )
            """)
        conn.commit()
        _migrated.add(room_id)


def save_danmu(danmu_dict: dict, room_id):
    now = datetime.datetime.now().isoformat()
    # 确保直播间数据库与表存在（幂等）
    init_db(room_id)
    conn = _get_conn(room_id)
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
        return

    cursor.execute(
        """
        INSERT INTO danmu (username, content, send_time, uid, type)
        VALUES (?, ?, ?, ?, ?)
        """,
        (username, content, now, uid, item_type),
    )
    conn.commit()
    # 回填同名用户的历史 uid
    # backfill_uid(room_id, username, uid)


def backfill_uid(room_id, username, uid):
    """将同一房间内同名用户的历史 NULL uid 补全"""
    if not uid or not username:
        return
    conn = _get_conn(room_id)
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE danmu SET uid = ? WHERE username = ? AND uid IS NULL",
        (uid, username),
    )
    conn.commit()


def get_today_danmu(room_id):
    today = datetime.date.today().isoformat()
    init_db(room_id)
    conn = _get_conn(room_id)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM danmu WHERE send_time LIKE ? ORDER BY send_time ASC",
        (f"{today}%",),
    )
    return [dict(row) for row in cursor.fetchall()]


def get_all_danmu(room_id):
    init_db(room_id)
    conn = _get_conn(room_id)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM danmu ORDER BY send_time ASC")
    return [dict(row) for row in cursor.fetchall()]


def count_danmu(room_id, keyword=None, item_type=None):
    """统计条数（可选按关键词/类型过滤）"""
    init_db(room_id)
    conn = _get_conn(room_id)
    cursor = conn.cursor()
    where, params = _build_where(keyword, item_type)
    sql = f"SELECT COUNT(*) FROM danmu{where}"
    cursor.execute(sql, params)
    return cursor.fetchone()[0]


def _build_where(keyword=None, item_type=None):
    """构造 WHERE 子句"""
    clauses = []
    params = []
    if keyword:
        clauses.append("(content LIKE ? OR username LIKE ?)")
        like = f"%{keyword}%"
        params.extend([like, like])
    if item_type:
        clauses.append("type = ?")
        params.append(item_type)
    if not clauses:
        return "", []
    return " WHERE " + " AND ".join(clauses), params


def get_danmu_page(
    room_id, limit=50, offset=0, keyword=None, item_type=None, order="DESC"
):
    """分页查询弹幕（供前端「弹幕数据库」页面）"""
    init_db(room_id)
    conn = _get_conn(room_id)
    cursor = conn.cursor()
    where, params = _build_where(keyword, item_type)
    order_sql = "DESC" if order != "ASC" else "ASC"
    sql = (
        f"SELECT * FROM danmu{where} "
        f"ORDER BY send_time {order_sql}, id {order_sql} "
        f"LIMIT ? OFFSET ?"
    )
    cursor.execute(sql, [*params, int(limit), int(offset)])
    return [dict(row) for row in cursor.fetchall()]


def get_recent_danmu(room_id, limit=50):
    """最近 N 条弹幕"""
    return get_danmu_page(room_id, limit=limit, offset=0, order="DESC")


# ==================== 礼物数据库 ====================


def save_gift(gift_dict: dict, room_id):
    """保存礼物记录到 gift 表"""
    if not isinstance(gift_dict, dict):
        return
    init_db(room_id)
    now = datetime.datetime.now().isoformat()
    conn = _get_conn(room_id)
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO gift
            (username, uid, gift_name, gift_num, total_coin, paid_coin,
             send_time, medal_name, medal_level)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            gift_dict.get("username", ""),
            gift_dict.get("uid"),
            gift_dict.get("gift_name", "未知礼物"),
            int(gift_dict.get("gift_num", 1) or 1),
            int(gift_dict.get("total_coin", 0) or 0),
            int(gift_dict.get("paid_coin", 0) or 0),
            now,
            gift_dict.get("medal_name", ""),
            int(gift_dict.get("medal_level", 0) or 0),
        ),
    )
    conn.commit()


def count_gifts(room_id, keyword=None):
    """统计礼物条数（可选关键词过滤）"""
    init_db(room_id)
    conn = _get_conn(room_id)
    cursor = conn.cursor()
    if keyword:
        like = f"%{keyword}%"
        cursor.execute(
            "SELECT COUNT(*) FROM gift WHERE gift_name LIKE ? OR username LIKE ?",
            (like, like),
        )
    else:
        cursor.execute("SELECT COUNT(*) FROM gift")
    return cursor.fetchone()[0]


def get_gift_page(room_id, limit=50, offset=0, keyword=None, order="DESC"):
    """分页查询礼物（供前端「礼物数据库」页面）"""
    init_db(room_id)
    conn = _get_conn(room_id)
    cursor = conn.cursor()
    order_sql = "DESC" if order != "ASC" else "ASC"
    if keyword:
        like = f"%{keyword}%"
        cursor.execute(
            f"SELECT * FROM gift WHERE gift_name LIKE ? OR username LIKE ? "
            f"ORDER BY send_time {order_sql}, id {order_sql} LIMIT ? OFFSET ?",
            (like, like, int(limit), int(offset)),
        )
    else:
        cursor.execute(
            f"SELECT * FROM gift ORDER BY send_time {order_sql}, id {order_sql} "
            f"LIMIT ? OFFSET ?",
            (int(limit), int(offset)),
        )
    return [dict(row) for row in cursor.fetchall()]


if __name__ == "__main__":
    room_id = input("room_id: ").strip()
    print(get_all_danmu(room_id))
