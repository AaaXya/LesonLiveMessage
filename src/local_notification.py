"""本机桌面通知。"""

from plyer import notification


def send_live_start_notification(room_title: str, room_id: str) -> None:
    """显示直播间开播的本机桌面通知。"""
    title = room_title or f"直播间 {room_id}"
    message = f"{title} 已开播\nhttps://live.bilibili.com/{room_id}"
    try:
        notification.notify(
            title="Bilibili 直播开始",
            message=message,
            app_name="RunLiveTest",
            timeout=10,
        )
    except Exception as e:
        print(f"本地通知发送失败：{e}")
