"""临时诊断脚本：验证 RoomManager 连接是否成功"""

import sys
import json
import time

sys.path.insert(0, ".")

from src.room_manager import RoomManager
from src.login import normalize_cookies, create_credential_from_cookies
from src import room_registry

cookies = json.load(open("cookies.json", encoding="utf-8"))
cred = create_credential_from_cookies(normalize_cookies(cookies))
print("[1] credential:", "有" if cred else "无")

mgr = RoomManager(cred)
result = mgr.start("1879006019")
print("[2] start result:", result)

time.sleep(6)
status = room_registry.get_room("1879006019")
print(
    "[3] 6秒后状态: connected =",
    status.get("connected"),
    "| live_state =",
    status.get("live_state"),
    "| error =",
    status.get("last_error"),
)

mgr.stop("1879006019")
time.sleep(2)
status = room_registry.get_room("1879006019")
print("[4] 停止后: connected =", status.get("connected"))
print("DONE")
