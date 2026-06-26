import argparse
import os
import sys
import sqlite3

# 确保项目根目录在 sys.path 中，以便直接运行此脚本
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.danmu_db import LEGACY_DB_FILE, get_room_db_file, init_db


def count_rows(db_file):
    if not os.path.exists(db_file):
        return 0

    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT COUNT(*) FROM danmu")
        return cursor.fetchone()[0]
    finally:
        conn.close()


def fetch_legacy_rows(source):
    conn = sqlite3.connect(source)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, content, send_time FROM danmu ORDER BY id ASC")
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows


def migrate(source, room_id, append=False, dry_run=False):
    if not os.path.exists(source):
        raise FileNotFoundError(f"旧数据库不存在：{source}")

    target = get_room_db_file(room_id, ensure_dir=not dry_run)
    if not dry_run:
        init_db(room_id)
    source_count = count_rows(source)
    target_count = count_rows(target)

    if target_count and not append:
        raise RuntimeError(
            f"Target database already has {target_count} rows: {target}. "
            "Use --append if you really want to append migrated rows."
        )

    print(f"Source: {source}")
    print(f"Target: {target}")
    print(f"Source rows: {source_count}")
    print(f"Target rows: {target_count}")

    if dry_run:
        print("dry-run: no data written")
        return

    rows = fetch_legacy_rows(source)
    conn = sqlite3.connect(target)
    cursor = conn.cursor()

    if target_count == 0:
        cursor.executemany(
            """
            INSERT INTO danmu (id, username, content, send_time)
            VALUES (?, ?, ?, ?)
            """,
            [
                (row["id"], row["username"], row["content"], row["send_time"])
                for row in rows
            ],
        )
    else:
        cursor.executemany(
            """
            INSERT INTO danmu (username, content, send_time)
            VALUES (?, ?, ?)
            """,
            [(row["username"], row["content"], row["send_time"]) for row in rows],
        )

    conn.commit()
    conn.close()
    print(f"Migration complete: wrote {len(rows)} rows")


def main():
    parser = argparse.ArgumentParser(
        description="Migrate old danmu.db to a room-specific database"
    )
    parser.add_argument("room_id", help="Room ID that the old rows belong to")
    parser.add_argument(
        "--source",
        default=LEGACY_DB_FILE,
        help="Old database path, defaults to ./danmu.db",
    )
    parser.add_argument(
        "--append",
        action="store_true",
        help="Append rows when target database is not empty",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show migration plan without writing data",
    )
    args = parser.parse_args()

    migrate(args.source, args.room_id, append=args.append, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
