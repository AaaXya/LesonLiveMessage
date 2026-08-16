import json
import os

from . import PROJECT_ROOT

CONFIG_PATH = os.path.join(PROJECT_ROOT, "config.json")
THEME_PATH = os.path.join(PROJECT_ROOT, "theme.json")
FEATURE_KEYS = (
    "enable_danmaku",
    "enable_guard_buy",
    "enable_super_chat",
    "enable_live_start",
    "enable_gift",
    "enable_danmu_db",
    "enable_live_timed_danmu",
    "web_debug",
    "open_mode",
)


def load_json(path, fallback):
    if not os.path.exists(path):
        return fallback

    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"读取配置失败：{path}", e)
        return fallback


def get_selected_theme_name(config):
    frontend_config = config.get("frontend", {})
    return frontend_config.get("theme") or config.get("theme") or "default"


def get_room_ids(config):
    """返回监听房间 ID 列表（新格式 room_ids，兼容旧 LESSONROOMID）"""
    ids = config.get("room_ids")
    if isinstance(ids, list):
        result = [str(i).strip() for i in ids if str(i).strip().isdigit()]
        if result:
            return result
    legacy = str(config.get("LESSONROOMID", "")).strip()
    return [legacy] if legacy.isdigit() else []


def get_room_id(config):
    """返回主房间 ID（列表首个）"""
    ids = get_room_ids(config)
    return ids[0] if ids else ""


def get_room_binding(config, room_id=None):
    room_id = room_id or get_room_id(config)
    bindings = config.get("room_bindings", {})
    return dict(bindings.get(str(room_id), {}))


def apply_room_binding(config, room_id=None):
    next_config = dict(config)
    features = dict(next_config.get("features", {}))
    binding = get_room_binding(next_config, room_id)
    group_id = str(binding.get("GROUPID", "")).strip()
    features["enable_qq_notification"] = bool(
        group_id and binding.get("enable_qq_notification", False)
    )
    # 定时弹幕
    features["live_timed_danmu_list"] = list(binding.get("live_timed_danmu_list", []))
    next_config["features"] = features
    return next_config


def load_theme_config():
    theme_config = load_json(THEME_PATH, {})
    if "presets" not in theme_config:
        theme_config = {
            "default": "default",
            "presets": {"default": theme_config},
        }
    return theme_config


def load_app_config(room_id=None):
    return apply_room_binding(load_json(CONFIG_PATH, {}), room_id)


def save_app_config(config):
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
        f.write("\n")


def get_theme_options(theme_config):
    options = []
    for key, value in theme_config.get("presets", {}).items():
        options.append(
            {
                "value": key,
                "label": value.get("name", key) if isinstance(value, dict) else key,
            }
        )
    return options


def load_selected_theme(config=None, theme_config=None):
    config = config or load_app_config()
    theme_config = theme_config or load_theme_config()
    selected_name = get_selected_theme_name(config)

    presets = theme_config.get("presets", {})
    fallback_name = theme_config.get("default", "default")
    selected = presets.get(selected_name) or presets.get(fallback_name) or {}
    resolved_name = selected_name if selected_name in presets else fallback_name

    if not selected:
        print(f"未找到主题预设：{selected_name}")

    return {
        "name": resolved_name,
        "colors": selected.get("colors", selected),
    }


def normalize_config_update(current_config, update, room_id=None):
    next_config = dict(current_config)

    # 固定房间模式（多窗口）：不修改全局房间列表
    if room_id is None:
        if "room_ids" in update and isinstance(update["room_ids"], list):
            clean_ids = [int(x) for x in update["room_ids"] if str(x).strip().isdigit()]
            if clean_ids:
                next_config["room_ids"] = clean_ids
        elif "LESSONROOMID" in update:
            # 兼容旧前端：单房间 ID
            room_id_str = str(update["LESSONROOMID"]).strip()
            if room_id_str.isdigit():
                next_config["room_ids"] = [int(room_id_str)]

    # 已迁移到 room_ids，移除磁盘上的旧字段
    next_config.pop("LESSONROOMID", None)

    frontend = dict(next_config.get("frontend", {}))
    incoming_frontend = update.get("frontend", {})
    if "theme" in incoming_frontend:
        theme_name = str(incoming_frontend["theme"]).strip() or "default"
        theme_config = load_theme_config()
        if theme_name not in theme_config.get("presets", {}):
            theme_name = theme_config.get("default", "default")
        frontend["theme"] = theme_name
    next_config["frontend"] = frontend

    features = dict(next_config.get("features", {}))
    incoming_features = update.get("features", {})
    for key in FEATURE_KEYS:
        if key in incoming_features:
            if key == "open_mode":
                features[key] = (
                    incoming_features[key]
                    if incoming_features[key] in ("webview", "web")
                    else "webview"
                )
            else:
                features[key] = bool(incoming_features[key])
    next_config["features"] = features

    room_id = room_id or get_room_id(next_config)
    bindings = dict(next_config.get("room_bindings", {}))
    current_binding = dict(bindings.get(room_id, {}))
    group_id = str(update.get("GROUPID", current_binding.get("GROUPID", ""))).strip()
    current_binding["GROUPID"] = group_id
    current_binding["enable_qq_notification"] = bool(
        group_id
        and update.get(
            "enable_qq_notification",
            current_binding.get("enable_qq_notification", False),
        )
    )
    # 定时弹幕列表
    if "live_timed_danmu_list" in update:
        raw_list = update["live_timed_danmu_list"]
        if isinstance(raw_list, list):
            current_binding["live_timed_danmu_list"] = [
                {
                    "delay": max(1, int(item.get("delay", 300))),
                    "text": str(item.get("text", "")).strip(),
                    "enabled": bool(item.get("enabled", True)),
                }
                for item in raw_list
                if isinstance(item, dict) and str(item.get("text", "")).strip()
            ]
    bindings[room_id] = current_binding
    next_config["room_bindings"] = bindings
    next_config["features"].pop("enable_qq_notification", None)
    # apply_room_binding 注入的运行时字段不写盘，避免与 room_bindings 重复
    next_config["features"].pop("live_timed_danmu_list", None)

    # 滤词列表
    if "filter_words" in update:
        next_config["filter_words"] = [
            str(w).strip() for w in update["filter_words"] if str(w).strip()
        ]

    return next_config


def build_frontend_config(room_id=None):
    config = load_app_config(room_id)
    theme_config = load_theme_config()
    effective_room = room_id or get_room_id(config)
    if effective_room:
        # 前端以 LESSONROOMID 读取当前窗口所属房间
        config["LESSONROOMID"] = int(effective_room)
    if room_id:
        # 多窗口模式：每个窗口固定显示自己的房间 ID
        config["roomFixed"] = True
    return {
        "config": config,
        "theme": load_selected_theme(config, theme_config),
        "themeOptions": get_theme_options(theme_config),
    }


class FrontendConfigApi:
    def __init__(self, room_id=None):
        self.room_id = str(room_id).strip() if room_id else None

    def getFrontendConfig(self):
        return build_frontend_config(self.room_id)

    def saveFrontendConfig(self, update):
        try:
            current_config = load_app_config(self.room_id)
            next_config = normalize_config_update(
                current_config, update or {}, self.room_id
            )
            save_app_config(next_config)

            # 用户滤词变更后刷新内存缓存
            from .danmu_db import reload_filter_words

            reload_filter_words()

            return {
                "ok": True,
                "frontendConfig": build_frontend_config(self.room_id),
            }
        except Exception as e:
            print("保存前端配置失败：", e)
            return {"ok": False, "error": str(e)}
