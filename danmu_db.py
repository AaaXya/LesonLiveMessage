import datetime
import os
import re
import sqlite3


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(SCRIPT_DIR, "data")
LEGACY_DB_FILE = os.path.join(SCRIPT_DIR, "danmu.db")
BRACKET_PATTERN = re.compile(r"^\[.*\]$")


def is_full_bracket_text(text: str) -> bool:
    return bool(BRACKET_PATTERN.fullmatch(text))


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
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS danmu (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            content TEXT,
            send_time TEXT
        )
        """
    )
    conn.commit()
    conn.close()


def save_danmu(danmu_dict: dict, room_id):
    now = datetime.datetime.now().isoformat()
    init_db(room_id)
    conn = sqlite3.connect(get_room_db_file(room_id))
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
