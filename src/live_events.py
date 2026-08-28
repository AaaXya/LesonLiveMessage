"""
live_events.py — B站直播间事件处理器 + 连接管理
所有函数接收 AppContext 实例，不再使用全局变量。
"""

import asyncio
import threading
from bilibili_api import live, sync
from .danmu_parser import (
    parse_bilibili_danmu,
    parse_gift,
    parse_super_chat,
    parse_guard_buy,
)
from .napcat_send import send_qq_group
from .danmu_db import save_danmu
from .avatar_proxy import fetch_image_data_uri_uncompressed

# ==================== 事件处理器 ====================


async def on_danmaku_handler(event, ctx):
    """弹幕消息"""
    parsed = parse_bilibili_danmu(event)
    if isinstance(parsed, dict):
        log_data = {k: v for k, v in parsed.items() if k != "avatar_url"}
    else:
        log_data = parsed
    print(log_data)

    if ctx.features.get("enable_danmu_db"):
        save_danmu(parsed, ctx.lesson_room_id)
    ctx.send_to_frontend(parsed)


async def on_guard_buy_handler(event, ctx):
    """大航海续费"""
    parsed = parse_guard_buy(event)
    if parsed:
        print("大航海续费：", parsed)
        ctx.send_to_frontend(parsed)


async def on_super_chat_handler(event, ctx):
    """超级留言"""
    parsed = parse_super_chat(event)
    if parsed:
        print("超级留言：", {k: v for k, v in parsed.items() if k != "avatar_url"})
        if ctx.features.get("enable_danmu_db"):
            save_danmu(parsed, ctx.lesson_room_id)
        ctx.send_to_frontend(parsed)


async def live_start_handler(event, ctx):
    """直播开始"""
    ctx.live_state += 1
    print("直播开始：", event)

    if ctx.features.get("enable_qq_notification") and ctx.live_state == 1:
        cover_uri = (
            fetch_image_data_uri_uncompressed(ctx.room_cover)
            if ctx.room_cover
            else None
        )
        send_qq_group(
            f"直播开始了：\n{ctx.room_title}\n"
            f"https://live.bilibili.com/{ctx.lesson_room_id}",
            cover_uri,
            ctx.lesson_room_id,
        )

    # 定时弹幕：直接读取该房间的 live_timed_danmu_list，开播后逐条延迟发送
    if ctx.live_state == 1:
        danmu_list = ctx.features.get("live_timed_danmu_list", [])
        if isinstance(danmu_list, list):
            for item in danmu_list:
                if not isinstance(item, dict):
                    continue
                delay = max(1, int(item.get("delay", 300)))
                text = str(item.get("text", "")).strip()
                if not text:
                    continue
                if not item.get("enabled", True):
                    continue
                print(f"定时弹幕已安排：{delay} 秒后发送「{text}」")
                asyncio.create_task(_send_timed_danmu(delay, text, ctx))


async def _send_timed_danmu(delay_seconds: int, message: str, ctx):
    """延迟指定秒数后发送弹幕到直播间"""
    try:
        await asyncio.sleep(delay_seconds)
        if ctx.sender is None:
            print("定时弹幕发送失败：sender 未初始化")
            return
        if hasattr(live, "Danmaku"):
            danmaku = live.Danmaku(message)
            result = await ctx.sender.send_danmaku(danmaku)
        else:
            result = await ctx.sender.send_danmaku(message)
        print(f"定时弹幕发送成功：「{message}」结果：{result}")
    except asyncio.CancelledError:
        print("定时弹幕任务已取消")
    except Exception as e:
        print(f"定时弹幕发送失败：{e}")


async def on_gift_handler(event, ctx):
    """礼物消息"""
    parsed = parse_gift(event)
    print("礼物：", parsed)
    ctx.send_to_frontend(parsed)


# ==================== 注册 & 连接 ====================


def _bind(async_fn, ctx):
    """将 ctx 绑定到 async 事件处理器，返回一个 async 回调"""

    async def wrapper(event):
        await async_fn(event, ctx)

    return wrapper


def register_all_handlers(room, ctx):
    """根据 features 配置注册事件处理器"""
    if not room:
        return
    if ctx.features.get("enable_live_start"):
        room.on("LIVE")(_bind(live_start_handler, ctx))
    if ctx.features.get("enable_danmaku"):
        room.on("DANMU_MSG")(_bind(on_danmaku_handler, ctx))
    if ctx.features.get("enable_guard_buy"):
        room.on("GUARD_BUY")(_bind(on_guard_buy_handler, ctx))
    if ctx.features.get("enable_super_chat"):
        room.on("SUPER_CHAT_MESSAGE")(_bind(on_super_chat_handler, ctx))
    if ctx.features.get("enable_gift"):
        room.on("SEND_GIFT")(_bind(on_gift_handler, ctx))


def start_room_connect(room_obj, ctx):
    """在后台线程启动直播间连接循环"""
    if not room_obj:
        print("警告：直播间监听未初始化")
        return
    threading.Thread(
        target=lambda: sync(_room_connect_loop(room_obj, ctx)),
        daemon=True,
    ).start()


async def _room_connect_loop(room_obj, ctx):
    """带自动重连的直播间连接循环"""
    retry_delay = 3
    max_delay = 60

    while True:
        try:
            print(f"[{ctx.lesson_room_id}] 正在连接直播间...")
            await room_obj.connect()
        except Exception as e:
            print(
                f"[{ctx.lesson_room_id}] 连接异常：{e}，" f"{retry_delay} 秒后重连..."
            )

        print(f"[{ctx.lesson_room_id}] 连接已断开，" f"{retry_delay} 秒后自动重连...")
        await asyncio.sleep(retry_delay)
        retry_delay = min(retry_delay * 2, max_delay)


async def init_room_info(sender, ctx):
    """获取直播间标题和封面"""
    room_info = await sender.get_room_info()
    ctx.room_title = room_info["room_info"]["title"]
    ctx.room_cover = room_info["room_info"]["cover"]
    print("✓ 获取直播间信息成功", room_info["room_info"])
    print("直播间信息：", ctx.room_title, ctx.room_cover)
