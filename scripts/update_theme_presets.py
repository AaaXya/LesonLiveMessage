# -*- coding: utf-8 -*-
"""为每套主题预设补充不透明 pageBg、强调色与 DevUI token（可重复执行）。"""

import json

PATH = "theme.json"

EXT = {
    "default": dict(
        pageBg="#101722",
        accent="#4a9eff",
        accentStrong="#7c9cff",
        accentSoft="rgba(74, 158, 255, 0.14)",
        devuiBrand="#4a9eff",
        devuiBrandHover="#6fb2ff",
        devuiBrandActive="#3a8aef",
        devuiBaseBg="#171e2b",
        devuiGlobalBg="#101722",
    ),
    "ocean": dict(
        pageBg="#061720",
        accent="#2ed6cc",
        accentStrong="#7cc7ff",
        accentSoft="rgba(46, 214, 204, 0.14)",
        devuiBrand="#2ed6cc",
        devuiBrandHover="#55e0d8",
        devuiBrandActive="#25b8b0",
        devuiBaseBg="#08232f",
        devuiGlobalBg="#061720",
    ),
    "sakura": dict(
        pageBg="#1d0d18",
        accent="#ff7fb5",
        accentStrong="#d98cff",
        accentSoft="rgba(255, 127, 181, 0.14)",
        devuiBrand="#ff7fb5",
        devuiBrandHover="#ff9ec6",
        devuiBrandActive="#ed6ba3",
        devuiBaseBg="#291221",
        devuiGlobalBg="#1d0d18",
    ),
    "forest": dict(
        pageBg="#0c1f14",
        accent="#8fd685",
        accentStrong="#c5e88a",
        accentSoft="rgba(143, 214, 133, 0.14)",
        devuiBrand="#8fd685",
        devuiBrandHover="#a5e39a",
        devuiBrandActive="#7ac96e",
        devuiBaseBg="#12291b",
        devuiGlobalBg="#0c1f14",
    ),
    "dark": dict(
        pageBg="#0b0b0e",
        accent="#9aa5b8",
        accentStrong="#7d899c",
        accentSoft="rgba(154, 165, 184, 0.14)",
        devuiBrand="#9aa5b8",
        devuiBrandHover="#b0bac9",
        devuiBrandActive="#8792a5",
        devuiBaseBg="#15151a",
        devuiGlobalBg="#0b0b0e",
    ),
}


def rgba(hex_color, alpha):
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r}, {g}, {b}, {alpha})"


def palette_preset(name, accent, accent_strong, accent_soft):
    return {
        "name": name,
        "colors": {
            "pageBg": "#11151b",
            "textPrimary": "#f5f2ed",
            "textMuted": "rgba(245, 242, 237, 0.75)",
            "textPlaceholder": "rgba(245, 242, 237, 0.5)",
            "surface": "rgba(20, 24, 32, 0.72)",
            "surfaceStrong": "rgba(17, 21, 28, 0.9)",
            "surfaceActive": "rgba(28, 33, 43, 0.85)",
            "surfaceHover": "rgba(255, 255, 255, 0.08)",
            "surfaceSoft": "rgba(255, 255, 255, 0.05)",
            "border": "rgba(255, 255, 255, 0.1)",
            "borderStrong": "rgba(255, 255, 255, 0.14)",
            "scrollbarThumb": "rgba(255, 255, 255, 0.16)",
            "buttonBg": "rgba(20, 24, 32, 0.6)",
            "closeBg": "rgba(229, 80, 80, 0.9)",
            "closeHoverBg": "#e55050",
            "sendGradient": f"linear-gradient(135deg, {accent}, {accent_strong})",
            "sendText": "#0d1117",
            "bubbleGradient": f"linear-gradient(135deg, {rgba(accent, 0.96)}, {rgba(accent_strong, 0.94)})",
            "giftBg": "rgba(212, 160, 0, 0.75)",
            "giftText": "#000000",
            "guardBg": "rgba(0, 116, 204, 0.8)",
            "guardText": "#ffffff",
            "medalText": "#ffcc00",
            "nameText": "#8fb1d5",
            "giftMedalText": "#ffd740",
            "shadow": "rgba(0, 0, 0, 0.25)",
            "bubbleShadow": "rgba(0, 0, 0, 0.18)",
            "accent": accent,
            "accentStrong": accent_strong,
            "accentSoft": accent_soft,
            "devuiBrand": accent,
            "devuiBrandHover": accent_strong,
            "devuiBrandActive": accent_strong,
            "devuiBaseBg": "#141a22",
            "devuiGlobalBg": "#11151b",
        },
    }


# 前端 THEME_PALETTES 的 5 套主题色，转成完整预设
PALETTE_PRESETS = {
    "green": palette_preset("翠绿", "#6fb969", "#5eccc4", "rgba(111, 185, 105, 0.12)"),
    "blue": palette_preset("海蓝", "#5a8dd8", "#4a9fd8", "rgba(90, 141, 216, 0.12)"),
    "purple": palette_preset(
        "薰衣草", "#9b7dd8", "#a89dd8", "rgba(155, 125, 216, 0.12)"
    ),
    "pink": palette_preset("樱花粉", "#d97b9a", "#e89dae", "rgba(217, 123, 154, 0.12)"),
    "teal": palette_preset("孔雀青", "#4db8a8", "#3eccc4", "rgba(77, 184, 168, 0.12)"),
}


def main():
    with open(PATH, encoding="utf-8") as f:
        data = json.load(f)
    for key, values in EXT.items():
        colors = data["presets"][key]["colors"]
        colors["pageBg"] = values.pop("pageBg")
        colors.update(values)
    # 合并主题色预设（幂等：同名 key 直接覆盖）
    for key, preset in PALETTE_PRESETS.items():
        data["presets"][key] = preset
    with open(PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print("ok:", ", ".join(list(EXT) + list(PALETTE_PRESETS)))


if __name__ == "__main__":
    main()
