# RunLiveTest — B站直播弹幕桌面客户端

一个基于 Python + Vue 3 的 Bilibili 直播弹幕查看与互动桌面应用，支持透明悬浮窗、QQ 群推送、多主题切换。

## ✨ 功能特性

- **弹幕实时显示** — 监听 Bilibili 直播间弹幕、礼物、舰队（大航海）、SC（醒目留言），以透明悬浮窗形式展示
- **弹幕发送** — 支持在桌面端直接发送弹幕到直播间
- **SC 醒目留言置顶** — SC 消息固定在页面顶部，带倒计时进度条，不随弹幕滚动
- **QQ 群推送** — 通过 [NapCat](https://github.com/NapNeko/NapCatQQ) 将直播事件（开播）实时转发到指定 QQ 群
- **自动重连** — 直播间连接断开后指数退避自动重连，无需手动重启
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

````
runlivetest/
├── app.py                  # 入口：初始化 → 凭据 → 分支运行（webview / web）
├── src/                    # 核心库
│   ├── __init__.py         # 包初始化 + PROJECT_ROOT 常量
│   ├── app_context.py      # 共享状态容器（config / room / sender / 事件队列）
│   ├── live_events.py      # B站直播间事件处理器 + 自动重连
│   ├── api.py              # CloseApi：前后端桥接层（webview JS + HTTP 共用）
│   ├── web_server.py       # Web 模式 HTTP 服务器（静态文件 + REST API）
│   ├── frontend_config.py  # 配置读写、主题管理、房间绑定
│   ├── login.py            # B站登录管理（扫码/Cookie）
│   ├── danmu_parser.py     # 弹幕/礼物/舰队/SC 数据解析
│   ├── danmu_db.py         # SQLite 弹幕存储（按房间分库）
│   ├── napcat_send.py      # QQ 群消息推送（NapCat）
│   └── avatar_proxy.py     # 头像拉取与压缩
├── scripts/                # 工具脚本
│   └── migrate_danmu_db.py # 弹幕数据库迁移工具
├── frontend/               # Vue 3 前端项目
│   ├── package.json
│   ├── vite.config.js
│   └── src/
│       ├── App.vue
│       ├── main.js
│       ├── constants.js
│       ├── api/bridge.js              # 前后端桥接通信
│       ├── components/
│       │   ├── DanmuList.vue          # 弹幕列表（含滚动按钮）
│       │   ├── DanmuItem.vue          # 单条弹幕
│       │   ├── DanmuInput.vue         # 弹幕输入框 + 发送按钮
│       │   ├── GiftItem.vue           # 礼物消息
│       │   ├── GuardItem.vue          # 舰队消息
│       │   ├── SuperChatItem.vue      # SC 醒目留言（置顶+倒计时）
│       │   ├── SettingsPanel.vue      # 设置面板
│       │   └── WindowControls.vue     # 窗口控制按钮
│       ├── composables/
│       │   ├── useSettings.js
│       │   └── useTheme.js
│       ├── stores/
│       │   └── danmu.js               # 弹幕/SC 状态管理
│       └── styles/
│           └── base.css               # 全局 CSS 变量 + 滚动条 + reset
├── data/                   # 弹幕数据库存放目录
├── config.json             # 主配置文件
├── theme.json              # 主题预设配色
├── cookies.json            # B站 Cookie（自动生成）
├── package.json            # 根构建脚本（npm run build）
└── README.md

## 🚀 快速开始

### 环境要求

- Python 3.9+
- Node.js 18+
- [NapCat](https://github.com/NapNeko/NapCatQQ)（可选，QQ 推送需要）

### 1. 克隆项目

```bash
git clone <your-repo-url>
cd runlivetest
````

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

> 后续只需在项目根目录运行 `npm run build` 即可构建前端。

### 4. 配置

编辑 `config.json`：

```json
{
	"room_ids": [1879006019, 另一个房间ID],
	"room_bindings": {
		"1879006019": {
			"GROUPID": "你的QQ群号",
			"enable_qq_notification": true
		},
		"另一个房间ID": {
			"GROUPID": "另一个QQ群号",
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
		"enable_danmu_db": true,
		"web_debug": false,
		"open_mode": "webview"
	}
}
```

| 字段                 | 说明                                                      |
| -------------------- | --------------------------------------------------------- |
| `room_ids`           | 监听的直播间 ID 数组，webview 模式下每个房间一个窗口      |
| `room_bindings`      | 房间 → QQ 群绑定，`GROUPID` 填写 QQ 群号                  |
| `frontend.theme`     | 主题名，可选 `default` / `ocean` / `sakura` 等            |
| `features`           | 功能开关，控制各类消息的显示和推送                        |
| `features.open_mode` | 运行模式：`"webview"`（桌面窗口）或 `"web"`（浏览器网页） |

### 多窗口多房间（webview 模式）

在 `room_ids` 中配置多个房间后，以 `"webview"` 模式启动应用，**每个房间会各自创建一个独立悬浮窗**，分别监听对应直播间，互不干扰。各窗口设置面板中的直播间 ID 为只读，QQ 群、开播通知、定时弹幕等配置仅对该窗口的房间生效。

| 字段                     | 说明                                                      |
| ------------------------ | --------------------------------------------------------- |
| `enable_qq_notification` | 开播后推送到该房间绑定的 QQ 群                            |
| `live_timed_danmu_list`  | 开播定时弹幕列表，每条含 `delay`（秒）、`text`、`enabled` |

### 5. 配置 NapCat（可选）

如需 QQ 群推送，在 `src/napcat_send.py` 中修改：

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

## 🏗 架构说明

所有前端样式均以 Vue `<style scoped>` 形式写入各自组件，不再使用全局 CSS 文件。仅 `base.css` 保留 CSS 变量定义和全局 reset。

后端事件处理器通过 `AppContext.send_to_frontend()` 向 WebView 注入 `addDanmu(data)` 调用（web 模式下通过事件队列轮询），前端 `stores/danmu.js` 根据 `data.type` 分流：

- `danmu` / `gift` / `GUARD_BUY` → 追加到滚动列表
- `super_chat` → 存入 `superChat` ref，由 `SuperChatItem.vue` 独立渲染在置顶位置

## 🗄 弹幕数据库

弹幕数据按房间存储在 `data/danmu_{room_id}.db` 中。如需迁移旧版数据库（`danmu.db` → 按房间分库），运行：

```bash
python scripts\migrate_danmu_db.py --room-id 1879006019
```

## 📄 许可证

MIT License
