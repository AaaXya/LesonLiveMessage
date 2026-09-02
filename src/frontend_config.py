import json
import os

from . import DATA_ROOT, RESOURCE_ROOT

CONFIG_PATH = os.path.join(DATA_ROOT, "config.json")
THEME_PATH = os.path.join(RESOURCE_ROOT, "theme.json")
FEATURE_KEYS = (
    "enable_danmaku",
    "enable_guard_buy",
    "enable_super_chat",
    "enable_gift",
    "enable_danmu_db",
    "web_debug",
    "open_mode",
)

# ---- 自动发言默认配置（全局配置，不按房间隔离） ----
DEFAULT_AUTO_SPEAK = {
    "enabled": False,
    "cycle_list": [],  # 定时循环：{interval(秒), text, enabled}
    "duration_list": [],  # 直播时长触发：{duration(秒), text, enabled}
    "keyword_replies": [],  # 关键词自动回复：{keyword, reply, enabled}
    "quick_sends": [],  # 常用弹幕快捷发送：{text, enabled}
}


def _normalize_auto_speak(raw):
    """规范化自动发言配置，确保各列表项字段完整、类型正确"""
    if not isinstance(raw, dict):
        raw = {}

    def _rows(items, numeric_keys=(), text_keys=()):
        result = []
        for it in items or []:
            if not isinstance(it, dict):
                continue
            row = {"enabled": bool(it.get("enabled", True))}
            for k in numeric_keys:
                try:
                    row[k] = max(0, int(float(str(it.get(k, 0)))))
                except (TypeError, ValueError):
                    row[k] = 0
            for k in text_keys:
                row[k] = str(it.get(k, "")).strip()
            result.append(row)
        return result

    return {
        "enabled": bool(raw.get("enabled", False)),
        "cycle_list": _rows(raw.get("cycle_list", []), ("interval",), ("text",)),
        "duration_list": _rows(raw.get("duration_list", []), ("duration",), ("text",)),
        "keyword_replies": _rows(
            raw.get("keyword_replies", []), (), ("keyword", "reply")
        ),
        "quick_sends": _rows(raw.get("quick_sends", []), (), ("text",)),
    }


def load_auto_speak(config):
    """读取自动发言配置，缺失或损坏时回退默认结构"""
    return _normalize_auto_speak(config.get("auto_speak", {}) or {})


# ---- webview 窗口大小预设 ----
WINDOW_SIZE_PRESETS = {
    "small": {"label": "小 (960×600)", "width": 960, "height": 600},
    "default": {"label": "标准 (1200×700)", "width": 1200, "height": 700},
    "large": {"label": "大 (1440×900)", "width": 1440, "height": 900},
    "wide": {"label": "超宽 (1600×1000)", "width": 1600, "height": 1000},
}
DEFAULT_WINDOW_SIZE = "default"


def get_window_size(config):
    """返回 webview 窗口 (width, height)，读取 frontend.window_size 预设"""
    frontend_config = config.get("frontend", {})
    preset = str(frontend_config.get("window_size") or DEFAULT_WINDOW_SIZE)
    size = WINDOW_SIZE_PRESETS.get(preset) or WINDOW_SIZE_PRESETS[DEFAULT_WINDOW_SIZE]
    return size["width"], size["height"]


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
    features["enable_local_notification"] = bool(
        binding.get("enable_local_notification", False)
    )
    next_config["features"] = features

    # 自动发言按房间独立保存/读取，兼容全局旧配置兜底
    next_config["auto_speak"] = _normalize_auto_speak(
        binding.get("auto_speak", next_config.get("auto_speak", {}))
    )
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
    # 原子写入：先写临时文件再替换，避免写入中断损坏配置
    tmp_path = CONFIG_PATH + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
        f.write("\n")
    os.replace(tmp_path, CONFIG_PATH)


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
                # 合并而非替换：设置页只编辑主房间，保存时保留其他已绑定的房间
                old_ids = [
                    str(i)
                    for i in next_config.get("room_ids", [])
                    if str(i).strip().isdigit()
                ]
                merged = []
                for x in [str(i) for i in clean_ids] + old_ids:
                    if x not in merged:
                        merged.append(x)
                next_config["room_ids"] = [int(x) for x in merged]
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
    if "window_size" in incoming_frontend:
        window_size = str(incoming_frontend.get("window_size") or "").strip()
        frontend["window_size"] = (
            window_size if window_size in WINDOW_SIZE_PRESETS else DEFAULT_WINDOW_SIZE
        )
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
    current_binding.pop("GROUPID", None)
    current_binding.pop("enable_qq_notification", None)
    current_binding["enable_local_notification"] = bool(
        update.get(
            "enable_local_notification",
            current_binding.get("enable_local_notification", False),
        )
    )
    # 自动发言配置（按房间绑定保存）
    if "auto_speak" in update:
        current_binding["auto_speak"] = _normalize_auto_speak(
            update.get("auto_speak", {}) or {}
        )
        next_config["auto_speak"] = current_binding["auto_speak"]
    bindings[room_id] = current_binding
    next_config["room_bindings"] = bindings
    next_config["features"].pop("enable_local_notification", None)

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
    frontend_config = config.get("frontend", {})
    return {
        "config": config,
        "theme": load_selected_theme(config, theme_config),
        "themeOptions": get_theme_options(theme_config),
        "windowSize": frontend_config.get("window_size") or DEFAULT_WINDOW_SIZE,
        "windowSizeOptions": [
            {"value": key, "label": item["label"]}
            for key, item in WINDOW_SIZE_PRESETS.items()
        ],
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

            # 保存配置时预建各房间数据库（新增房间立即创建 danmu/gift 表）
            from .danmu_db import init_db

            for rid in next_config.get("room_ids", []):
                try:
                    init_db(rid)
                except Exception:
                    pass

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
