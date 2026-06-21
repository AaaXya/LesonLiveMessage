# RunLiveTest — B站直播弹幕桌面客户端

一个基于 Python + Vue 3 的 Bilibili 直播弹幕查看与互动桌面应用，支持透明悬浮窗、QQ 群推送、多主题切换。

## ✨ 功能特性

- **弹幕实时显示** — 监听 Bilibili 直播间弹幕、礼物、舰队（大航海）、SC（醒目留言），以透明悬浮窗形式展示
- **弹幕发送** — 支持在桌面端直接发送弹幕到直播间
- **QQ 群推送** — 通过 [NapCat](https://github.com/NapNeko/NapCatQQ) 将直播事件（开播、弹幕、礼物等）实时转发到指定 QQ 群
- **多房间绑定** — 每个直播间可独立绑定不同的 QQ 群，互不干扰
- **头像代理压缩** — 自动拉取用户头像并压缩，减少前端渲染压力
- **主题系统** — 内置多套配色主题（默认亮彩、深海青蓝、樱粉等），支持自定义
- **弹幕持久化** — 使用 SQLite 本地存储弹幕记录，按房间分库
- **B站扫码登录** — 支持扫码登录获取 Cookie，持久化保存

## 🛠 技术栈

| 层级 | 技术                                  |
| ---- | ------------------------------------- |
| 后端 | Python 3, `bilibili-api`, `pywebview` |
| 前端 | Vue 3, Vite, 原生 CSS                 |
| 数据 | SQLite（弹幕存储）                    |
| 推送 | NapCat HTTP API                       |
| 图像 | Pillow（头像压缩）                    |

## 📁 项目结构

```
runlivetest/
├── app.py                  # 主入口，WebView 窗口 + 弹幕事件处理
├── login.py                # B站登录管理（扫码/Cookie）
├── danmu_parser.py         # 弹幕/礼物/舰队数据解析
├── danmu_db.py             # SQLite 弹幕存储
├── napcat_send.py          # QQ 群消息推送（NapCat）
├── avatar_proxy.py         # 头像拉取与压缩
├── frontend_config.py      # 前端配置 API（主题/房间绑定）
├── migrate_danmu_db.py     # 弹幕数据库迁移工具
├── config.json             # 主配置文件
├── theme.json              # 主题预设配色
├── cookies.json            # B站 Cookie（自动生成）
├── index.html              # 前端入口（开发回退用）
├── data/                   # 弹幕数据库存放目录
└── frontend/               # Vue 3 前端项目
    ├── package.json
    ├── vite.config.js
    └── src/
        ├── App.vue
        ├── main.js
        ├── constants.js
        ├── api/bridge.js           # 前后端桥接通信
        ├── components/
        │   ├── DanmuList.vue       # 弹幕列表
        │   ├── DanmuItem.vue       # 单条弹幕
        │   ├── DanmuInput.vue      # 弹幕输入框
        │   ├── GiftItem.vue        # 礼物消息
        │   ├── GuardItem.vue       # 舰队消息
        │   ├── SettingsPanel.vue   # 设置面板
        │   └── WindowControls.vue  # 窗口控制按钮
        ├── composables/
        │   ├── useSettings.js
        │   └── useTheme.js
        ├── stores/
        │   └── danmu.js            # 弹幕状态管理
        └── styles/
            ├── base.css
            ├── danmu.css
            └── settings.css
```

## 🚀 快速开始

### 环境要求

- Python 3.9+
- Node.js 18+
- [NapCat](https://github.com/NapNeko/NapCatQQ)（可选，QQ 推送需要）

### 1. 克隆项目

```bash
git clone <your-repo-url>
cd runlivetest
```

### 2. 安装 Python 依赖

```bash
pip install bilibili-api pywebview requests Pillow
```

### 3. 安装前端依赖并构建

```bash
cd frontend
npm install
npm run dev      # 浏览器预览（无 pywebview API）
npm run build    # 构建到 frontend/dist，供 app.py 加载
cd ..
```

### 4. 配置

编辑 `config.json`：

```json
{
	"LESSONROOMID": 1879006019,
	"room_bindings": {
		"1879006019": {
			"GROUPID": "你的QQ群号",
			"enable_qq_notification": true
		}
	},
	"frontend": {
		"theme": "sakura"
	},
	"features": {
		"enable_danmaku": true,
		"enable_guard_buy": true,
		"enable_super_chat": true,
		"enable_live_start": true,
		"enable_gift": true,
		"web_debug": false
	}
}
```

| 字段             | 说明                                           |
| ---------------- | ---------------------------------------------- |
| `LESSONROOMID`   | B站直播间 ID                                   |
| `room_bindings`  | 房间 → QQ 群绑定，`GROUPID` 填写 QQ 群号       |
| `frontend.theme` | 主题名，可选 `default` / `ocean` / `sakura` 等 |
| `features`       | 功能开关，控制各类消息的显示和推送             |

### 5. 配置 NapCat（可选）

如需 QQ 群推送，在 `napcat_send.py` 中修改：

```python
NAPCAT_URL = "http://127.0.0.1:3000/send_msg"
NAPCAT_TOKEN = "你的Token"
```

### 6. 运行

```bash
python app.py
```

首次运行会弹出 B站扫码登录窗口，登录后 Cookie 自动保存到 `cookies.json`。

## 🎨 主题配置

`theme.json` 中预设了多套主题，可在 `config.json` 的 `frontend.theme` 中切换。也可在 `theme.json` 的 `presets` 中添加自定义主题。

## 🗄 弹幕数据库

弹幕数据按房间存储在 `data/danmu_{room_id}.db` 中。如需迁移旧版数据库（`danmu.db` → 按房间分库），运行：

```bash
python migrate_danmu_db.py --room-id 1879006019
```

## 📄 许可证

MIT License
