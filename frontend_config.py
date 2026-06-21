import json
import os


BASE_PATH = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_PATH, "config.json")
THEME_PATH = os.path.join(BASE_PATH, "theme.json")
FEATURE_KEYS = (
    "enable_danmaku",
    "enable_guard_buy",
    "enable_super_chat",
    "enable_live_start",
    "enable_gift",
    "web_debug",
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


def get_room_id(config):
    return str(config.get("LESSONROOMID", "")).strip()


def get_room_binding(config, room_id=None):
    room_id = room_id or get_room_id(config)
    bindings = config.get("room_bindings", {})
    return dict(bindings.get(str(room_id), {}))


def apply_room_binding(config):
    next_config = dict(config)
    features = dict(next_config.get("features", {}))
    binding = get_room_binding(next_config)
    group_id = str(binding.get("GROUPID", "")).strip()
    features["enable_qq_notification"] = bool(
        group_id and binding.get("enable_qq_notification", False)
    )
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


def load_app_config():
    return apply_room_binding(load_json(CONFIG_PATH, {}))


def save_app_config(config):
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
        f.write("\n")


def get_theme_options(theme_config):
    options = []
    for key, value in theme_config.get("presets", {}).items():
        options.append({
            "value": key,
            "label": value.get("name", key) if isinstance(value, dict) else key,
        })
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


def normalize_config_update(current_config, update):
    next_config = dict(current_config)

    if "LESSONROOMID" in update:
        next_config["LESSONROOMID"] = int(update["LESSONROOMID"])

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
            features[key] = bool(incoming_features[key])
    next_config["features"] = features

    room_id = get_room_id(next_config)
    bindings = dict(next_config.get("room_bindings", {}))
    current_binding = dict(bindings.get(room_id, {}))
    group_id = str(update.get("GROUPID", current_binding.get("GROUPID", ""))).strip()
    current_binding["GROUPID"] = group_id
    current_binding["enable_qq_notification"] = bool(
        group_id and update.get("enable_qq_notification", current_binding.get("enable_qq_notification", False))
    )
    bindings[room_id] = current_binding
    next_config["room_bindings"] = bindings
    next_config["features"].pop("enable_qq_notification", None)

    return next_config


def build_frontend_config():
    config = load_app_config()
    theme_config = load_theme_config()
    return {
        "config": config,
        "theme": load_selected_theme(config, theme_config),
        "themeOptions": get_theme_options(theme_config),
    }


class FrontendConfigApi:
    def getFrontendConfig(self):
        return build_frontend_config()

    def saveFrontendConfig(self, update):
        try:
            current_config = load_app_config()
            next_config = normalize_config_update(current_config, update or {})
            save_app_config(next_config)
            return {
                "ok": True,
                "frontendConfig": build_frontend_config(),
            }
        except Exception as e:
            print("保存前端配置失败：", e)
            return {"ok": False, "error": str(e)}
