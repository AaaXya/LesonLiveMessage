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
from .local_notification import send_live_start_notification
from .danmu_db import save_danmu, save_gift
from .avatar_proxy import fetch_image_data_uri
from . import room_registry

# ==================== 事件处理器 ====================


async def on_danmaku_handler(event, ctx):
    """弹幕消息"""
    parsed = parse_bilibili_danmu(event)
    if isinstance(parsed, dict):
        face = parsed.get("avatar_url")
        if face:
            # 头像下载是阻塞网络请求，放线程池执行，避免卡住本房间事件循环
            parsed["avatar_url"] = await asyncio.to_thread(fetch_image_data_uri, face)
        log_data = {k: v for k, v in parsed.items() if k != "avatar_url"}
    else:
        log_data = parsed
    print(log_data)

    if ctx.features.get("enable_danmu_db"):
        save_danmu(parsed, ctx.lesson_room_id)
    room_registry.on_event(ctx.lesson_room_id, "danmu")
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
        face = parsed.get("avatar_url")
        if face:
            parsed["avatar_url"] = await asyncio.to_thread(fetch_image_data_uri, face)
        print("超级留言：", {k: v for k, v in parsed.items() if k != "avatar_url"})
        if ctx.features.get("enable_danmu_db"):
            save_danmu(parsed, ctx.lesson_room_id)
        ctx.send_to_frontend(parsed)


async def live_start_handler(event, ctx):
    """直播开始"""
    is_new_live = not ctx.live_started_notified
    ctx.is_live = True
    room_registry.set_live_state(ctx.lesson_room_id, 1)
    print("直播开始：", event)

    # 状态始终更新；通知与定时弹幕则遵循功能开关。
    if not ctx.features.get("enable_live_start"):
        return

    if ctx.features.get("enable_local_notification") and is_new_live:
        send_live_start_notification(ctx.room_title, ctx.lesson_room_id)

    # 定时弹幕：直接读取该房间的 live_timed_danmu_list，开播后逐条延迟发送
    if is_new_live:
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

    # 无论是否启用本地通知，LIVE 事件都代表一次新的开播周期。
    ctx.live_started_notified = True


async def live_end_handler(event, ctx):
    """直播结束，恢复未开播状态。"""
    ctx.is_live = False
    ctx.live_started_notified = False
    room_registry.set_live_state(ctx.lesson_room_id, 0)
    print("直播结束：", event)


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
    if isinstance(parsed, dict):
        if ctx.features.get("enable_danmu_db"):
            save_gift(parsed, ctx.lesson_room_id)
        room_registry.on_event(ctx.lesson_room_id, "gift")
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
    # 开播状态属于房间基础信息，不能随通知功能关闭而停止更新。
    room.on("LIVE")(_bind(live_start_handler, ctx))
    room.on("PREPARING")(_bind(live_end_handler, ctx))
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
    ctx.stop_flag.clear()

    def _run():
        try:
            sync(_room_connect_loop(room_obj, ctx))
        except Exception as e:
            print(f"[{ctx.lesson_room_id}] 连接线程异常退出：{e}", flush=True)
            room_registry.set_error(ctx.lesson_room_id, f"线程异常：{e}")

    threading.Thread(target=_run, daemon=True).start()


def stop_room_connect(ctx):
    """停止监听：设置停止标志并断开连接"""
    ctx.stop_flag.set()
    room_registry.set_connected(ctx.lesson_room_id, False)
    try:
        if ctx.room is not None:
            sync(ctx.room.disconnect())
    except Exception as e:
        print(f"断开房间 {ctx.lesson_room_id} 连接失败：", e)


async def _room_connect_loop(room_obj, ctx):
    """带自动重连的直播间连接循环（含连接建立超时监控）"""
    retry_delay = 3
    max_delay = 60
    connect_timeout = 8  # 建立连接的超时（秒），超时则重试

    while not ctx.stop_flag.is_set():
        print(f"[{ctx.lesson_room_id}] 正在连接直播间...", flush=True)
        room_registry.set_connected(ctx.lesson_room_id, False)
        room_registry.set_error(ctx.lesson_room_id, None)

        try:
            connect_task = asyncio.create_task(room_obj.connect())
            waited = 0
            established = False

            # 监控建立阶段：最多等 connect_timeout 秒
            while waited < connect_timeout and not ctx.stop_flag.is_set():
                await asyncio.sleep(1)
                waited += 1
                if connect_task.done():
                    break
                if room_obj.get_status() == live.LiveDanmaku.STATUS_ESTABLISHED:
                    established = True
                    break
                if waited % 3 == 0:
                    # 每 3 秒汇报一次连接进度，便于诊断
                    print(
                        f"[{ctx.lesson_room_id}] 连接建立中... 已等待 {waited}s"
                        f"（状态码 {room_obj.get_status()}）",
                        flush=True,
                    )

            if established:
                # 已建立连接：阻塞直到断开
                retry_delay = 3  # 成功连接后重置退避延迟
                room_registry.set_connected(ctx.lesson_room_id, True)
                print(f"[{ctx.lesson_room_id}] ✓ 连接成功，开始监听", flush=True)
                await connect_task
            elif connect_task.done():
                exc = connect_task.exception()
                if exc:
                    print(f"[{ctx.lesson_room_id}] 连接异常：{exc}", flush=True)
                    room_registry.set_error(ctx.lesson_room_id, str(exc))
                else:
                    print(f"[{ctx.lesson_room_id}] 连接已断开", flush=True)
            else:
                # 超时未建立连接：取消并重试
                print(
                    f"[{ctx.lesson_room_id}] ⏱ 连接超时（{connect_timeout}s 未建立），取消重试...",
                    flush=True,
                )
                connect_task.cancel()
                try:
                    await connect_task
                except (asyncio.CancelledError, Exception):
                    pass
                room_registry.set_error(
                    ctx.lesson_room_id, f"连接超时（{connect_timeout}s）"
                )
        except Exception as e:
            print(
                f"[{ctx.lesson_room_id}] 连接异常：{e}，" f"{retry_delay} 秒后重连...",
                flush=True,
            )
            room_registry.set_error(ctx.lesson_room_id, str(e))

        if ctx.stop_flag.is_set():
            break

        room_registry.set_connected(ctx.lesson_room_id, False)
        print(f"[{ctx.lesson_room_id}] 连接已断开，" f"{retry_delay} 秒后自动重连...")
        await asyncio.sleep(retry_delay)
        retry_delay = min(retry_delay * 2, max_delay)

    room_registry.set_connected(ctx.lesson_room_id, False)
    print(f"[{ctx.lesson_room_id}] 已停止监听")


async def init_room_info(sender, ctx):
    """获取直播间标题和封面"""
    room_info = await sender.get_room_info()
    ctx.room_title = room_info["room_info"]["title"]
    ctx.room_cover = room_info["room_info"]["cover"]
    # 监听开始时主播可能已经开播，不能只依赖之后才会推送的 LIVE 事件。
    ctx.is_live = bool(room_info["room_info"].get("live_status"))
    ctx.live_started_notified = ctx.is_live
    room_registry.ensure_room(
        ctx.lesson_room_id, room_title=ctx.room_title, room_cover=ctx.room_cover
    )
    room_registry.set_live_state(ctx.lesson_room_id, 1 if ctx.is_live else 0)
    print(
        f"✓ 获取直播间信息成功：{ctx.room_title}（{'直播中' if ctx.is_live else '未开播'}）"
    )
