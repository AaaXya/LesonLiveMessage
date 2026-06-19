import sqlite3
import datetime

import os

# 关键：固定数据库文件和当前py文件同目录
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(SCRIPT_DIR, "danmu.db")


import re

# 预编译正则，性能更好
BRACKET_PATTERN = re.compile(r"^\[.*\]$")


def is_full_bracket_text(text: str) -> bool:
    """
    判断整条文本是否完整被一对中括号包裹
    :param text: 弹幕content字符串
    :return: 完全包裹返回True，否则False
    """
    return bool(BRACKET_PATTERN.fullmatch(text))


def init_db():
    """初始化数据库，建表（首次运行执行一次）"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS danmu (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            content TEXT,
            send_time TEXT
        )
    """)
    conn.commit()
    conn.close()
    print("✅ 数据库初始化完成")


def save_danmu(danmu_dict: dict):
    """
    存储一条弹幕，自动提取昵称和内容，忽略其他字段
    :param danmu_dict: 原始弹幕字典
    """
    now = datetime.datetime.now().isoformat()
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO danmu (username, content, send_time)
        VALUES (?, ?, ?)
    """,
        (danmu_dict["username"], danmu_dict["content"], now),
    )
    conn.commit()
    conn.close()


def get_today_danmu():
    """查询今日所有弹幕"""
    today = datetime.date.today().isoformat()
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM danmu WHERE send_time LIKE ? ORDER BY send_time ASC",
        (f"{today}%",),
    )
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows


def get_all_danmu():
    """查询全部历史弹幕"""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM danmu ORDER BY send_time ASC")
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows


if __name__ == "__main__":
    data = get_all_danmu()
    print(data)
