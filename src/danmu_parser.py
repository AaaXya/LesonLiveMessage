import json

from .avatar_proxy import fetch_image_data_uri


def _safe_list(lst, index, default):
    if isinstance(lst, list) and len(lst) > index:
        return lst[index]
    return default


def _find_face(obj):
    if isinstance(obj, dict):
        if "base" in obj and isinstance(obj["base"], dict):
            face = obj["base"].get("face") or obj["base"].get("origin_info", {}).get(
                "face"
            )
            if face:
                return face
        if "user" in obj and isinstance(obj["user"], dict):
            face = obj["user"].get("base", {}).get("face") or obj["user"].get(
                "base", {}
            ).get("origin_info", {}).get("face")
            if face:
                return face
        for v in obj.values():
            result = _find_face(v)
            if result:
                return result
    elif isinstance(obj, list):
        for item in obj:
            result = _find_face(item)
            if result:
                return result
    return None


def parse_bilibili_danmu(raw_data):
    try:
        data = raw_data.get("data", {})
        info = data.get("info", [])

        content = _safe_list(info, 1, "无内容")
        user_info = info[2] if len(info) > 2 else []
        medal_info = info[3] if len(info) > 3 else []
        extra_info = info[15] if len(info) > 15 else {}

        extra = {}
        try:
            extra_str = (
                extra_info.get("extra", "{}") if isinstance(extra_info, dict) else "{}"
            )
            extra = json.loads(extra_str)
        except Exception:
            extra = {}

        avatar_url = _find_face(data) or _find_face(info)
        avatar_url = fetch_image_data_uri(avatar_url)

        return {
            "type": "danmu",
            "uid": _safe_list(user_info, 0, 0),
            "username": _safe_list(user_info, 1, "匿名用户"),
            "content": content,
            "avatar_url": avatar_url,
            "medal_level": _safe_list(medal_info, 0, 0),
            "medal_name": _safe_list(medal_info, 1, "无粉丝牌"),
        }
    except Exception as e:
        print(f"弹幕解析失败: {e}")
        return None


def parse_gift(raw_data):
    try:
        body = raw_data.get("data", {})
        gift_data = body.get("data", {})
        sender_info = body.get("sender_uinfo", {})
        user_base = sender_info.get("base", {})

        def choose_medal():
            candidates = [
                gift_data.get("medal_info"),
                gift_data.get("medal"),
                body.get("medal_info"),
                body.get("medal"),
                sender_info.get("medal"),
                sender_info.get("medal_info"),
            ]
            for item in candidates:
                if isinstance(item, dict) and (
                    item.get("medal_name") or item.get("name")
                ):
                    return item
            for item in candidates:
                if isinstance(item, dict):
                    return item
            return {}

        medal = choose_medal()

        username = (
            gift_data.get("uname")
            or sender_info.get("uname")
            or user_base.get("name", "匿名用户")
        )
        uid = (
            sender_info.get("uid")
            or gift_data.get("uid")
            or user_base.get("uid")
            or body.get("uid")
        )

        actual_coin = gift_data.get("total_coin", 0)
        if actual_coin == 0:
            actual_coin = gift_data.get("combo_total_coin", 0)
        if actual_coin == 0:
            actual_coin = gift_data.get("original_gift_price", 0) or gift_data.get(
                "price", 0
            ) * gift_data.get("num", 1)

        paid_coin = gift_data.get("discount_price")
        if paid_coin is None:
            paid_coin = gift_data.get("price", 0)
        if paid_coin == 0:
            paid_coin = gift_data.get("price", 0)

        num = gift_data.get("num", 1)
        if num and paid_coin != 0 and gift_data.get("price") not in (None, 0):
            # paid_coin may already be per item or total
            if paid_coin == gift_data.get("price"):
                paid_coin = paid_coin * num

        return {
            "type": "gift",
            "username": username,
            "uid": uid,
            "gift_name": gift_data.get(
                "giftName", gift_data.get("gift_name", "未知礼物")
            ),
            "gift_num": num,
            "total_coin": actual_coin,
            "paid_coin": paid_coin,
            "medal_name": medal.get("medal_name", medal.get("name", "无粉丝牌")),
            "medal_level": medal.get("medal_level", medal.get("level", 0)),
        }
    except Exception as e:
        print(f"礼物解析失败: {e}")
        return None


def parse_super_chat(raw_data):
    """解析 SUPER_CHAT_MESSAGE（醒目留言）"""
    try:
        body = raw_data.get("data", {})
        data = body.get("data", {})

        message = data.get("message", "")
        price = data.get("price", 0)  # 金额（元）
        start_time = data.get("start_time", 0)
        end_time = data.get("end_time", 0)

        uinfo = data.get("uinfo", {})
        user_base = uinfo.get("base", {})
        username = user_base.get("name", "匿名用户")
        face_url = user_base.get("face", "") or user_base.get("origin_info", {}).get(
            "face", ""
        )

        medal_info = data.get("medal_info", {})
        medal_name = medal_info.get("medal_name", "")
        medal_level = medal_info.get("medal_level", 0)

        avatar = fetch_image_data_uri(face_url) if face_url else None

        return {
            "type": "super_chat",
            "username": username,
            "message": message,
            "price": price,
            "end_time": end_time,
            "start_time": start_time,
            "avatar_url": avatar,
            "medal_name": medal_name,
            "medal_level": medal_level,
        }
    except Exception as e:
        print(f"超级留言解析失败: {e}")
        return None


def parse_guard_buy(raw_data):
    """解析 GUARD_BUY（大航海续费/开通）"""
    try:
        body = raw_data.get("data", {})
        data = body.get("data", {})

        username = data.get("username", "匿名用户")
        guard_level = data.get("guard_level", 0)  # 1=总督, 2=提督, 3=舰长
        guard_name = data.get("gift_name", "")
        price = data.get("price", 0)  # 分
        num = data.get("num", 1)

        guard_level_map = {1: "总督", 2: "提督", 3: "舰长"}
        guard_label = guard_name or guard_level_map.get(guard_level, "大航海")

        return {
            "type": "GUARD_BUY",
            "username": username,
            "guard_level": guard_level,
            "guard_name": guard_label,
            "price": price,
            "num": num,
            "medal_name": "",
            "medal_level": 0,
        }
    except Exception as e:
        print(f"大航海解析失败: {e}")
        return None
