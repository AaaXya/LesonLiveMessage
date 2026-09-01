# RunLiveTest — B站直播弹幕桌面客户端

一个基于 Python + Vue 3 的 Bilibili 直播弹幕查看与互动桌面应用，支持透明悬浮窗、本机开播通知、多主题切换。

## ✨ 功能特性

- **弹幕实时显示** — 监听 Bilibili 直播间弹幕、礼物、舰队（大航海）、SC（醒目留言），以透明悬浮窗形式展示
- **弹幕发送** — 支持在桌面端直接发送弹幕到直播间
- **SC 醒目留言置顶** — SC 消息固定在页面顶部，带倒计时进度条，不随弹幕滚动
- **本机开播通知** — 通过 `plyer` 在直播开始时显示系统桌面通知
- **开播定时弹幕** — 开播后按房间配置在指定时间自动发送弹幕（可多条、可单独开关）
- **自动重连** — 直播间连接断开后指数退避自动重连，无需手动重启
- **多房间配置** — 每个直播间可独立配置开播通知与定时弹幕
- **头像代理压缩** — 自动拉取用户头像并压缩，减少前端渲染压力
- **主题系统** — 内置 10 套配色主题（5 套场景主题 + 5 套主题色预设），统一在「主题模式」中切换
- **明暗模式** — 侧边栏一键切换深色 / 浅色，浅色模式使用独立浅色变量
- **窗口大小预设** — 小 / 标准 / 大 / 超宽四档窗口尺寸，设置页即时生效并持久化
- **弹幕持久化** — 使用 SQLite 本地存储弹幕记录，按房间分库
- **B站扫码登录** — 支持扫码登录获取 Cookie，持久化保存

## 🛠 技术栈

| 层级 | 技术                                            |
| ---- | ----------------------------------------------- |
| 后端 | Python 3, `bilibili-api`, `pywebview`           |
| 前端 | Vue 3, Vite, vue-devui（DevUI 组件 + 图标字体） |
| 数据 | SQLite（弹幕存储）                              |
| 通知 | plyer 本机桌面通知                              |
| 图像 | Pillow（头像压缩）                              |

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
│   ├── local_notification.py # 本机桌面通知
│   └── avatar_proxy.py     # 头像拉取与压缩
├── scripts/                # 工具脚本
│   ├── migrate_danmu_db.py    # 弹幕数据库迁移工具
│   ├── update_theme_presets.py # 主题预设升级/合并工具
│   └── diag_connect.py        # 连接诊断工具
├── frontend/               # Vue 3 前端项目
│   ├── package.json
│   ├── vite.config.js
│   └── src/
│       ├── App.vue
│       ├── main.js
│       ├── constants.js
│       ├── api/bridge.js              # 前后端桥接通信
│       ├── layout/AppLayout.vue       # 侧边栏 + 标题栏布局（明暗切换）
│       ├── views/                     # 各路由页面（直播间/控制台/数据库/礼物/分析/设置）
│       ├── router/                    # 前端路由
│       ├── components/
│       │   ├── DanmuList.vue          # 弹幕列表（含滚动按钮）
│       │   ├── DanmuItem.vue          # 单条弹幕
│       │   ├── DanmuInput.vue         # 弹幕输入框 + 发送按钮
│       │   ├── GiftItem.vue           # 礼物消息
│       │   ├── GuardItem.vue          # 舰队消息
│       │   ├── SuperChatItem.vue      # SC 醒目留言（置顶+倒计时）
│       │   ├── SettingsPanel.vue      # 设置面板
│       │   └── WindowControls.vue     # 窗口控制按钮（d-button + d-icon）
│       ├── composables/
│       │   ├── useSettings.js         # 设置页状态
│       │   └── useTheme.js            # 主题配置加载与应用
│       ├── stores/
│       │   └── danmu.js               # 弹幕/SC 状态管理（按房间隔离）
│       └── styles/
│           ├── base.css               # 全局 CSS 变量 + 明暗模式 + reset
│           └── devui-theme.css        # DevUI 令牌映射与组件微调
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

### 1. 克隆项目

```bash
git clone <your-repo-url>
cd runlivetest
````

### 2. 安装 Python 依赖

```bash
pip install -r requirements.txt
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
			"enable_local_notification": true,
			"live_timed_danmu_list": [
				{ "delay": 30, "text": "直播开始啦，欢迎各位观众~", "enabled": true },
				{ "delay": 10800, "text": "已经开播三小时啦！", "enabled": true }
			]
		},
		"另一个房间ID": {
			"enable_local_notification": true
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

| 字段                   | 说明                                                                                                            |
| ---------------------- | --------------------------------------------------------------------------------------------------------------- |
| `room_ids`             | 监听的直播间 ID 数组，webview 模式下每个房间一个窗口                                                            |
| `room_bindings`        | 房间级设置，保存本机通知与定时弹幕配置                                                                          |
| `frontend.theme`       | 主题名，可选 `default` / `ocean` / `sakura` / `forest` / `dark` / `green` / `blue` / `purple` / `pink` / `teal` |
| `frontend.window_size` | 窗口大小预设：`small` / `default` / `large` / `wide`                                                            |
| `features`             | 功能开关，控制各类消息的显示和推送                                                                              |
| `features.open_mode`   | 运行模式：`"webview"`（桌面窗口）或 `"web"`（浏览器网页）                                                       |

### 单窗口多房间按需监听

webview 模式为**单窗口**：在 `room_ids` 中配置多个房间后，在「直播间」页面点击房间卡片即可按需开始/停止监听，弹幕流按房间隔离显示。开播通知和定时弹幕等配置通过 `room_bindings` 按房间独立生效。

| 字段                        | 说明                                                                                     |
| --------------------------- | ---------------------------------------------------------------------------------------- |
| `enable_local_notification` | 开播后显示本机桌面通知                                                                   |
| `live_timed_danmu_list`     | 开播定时弹幕列表，每条含 `delay`（秒）、`text`、`enabled`；`enabled: false` 的条目不发送 |

### 开播定时弹幕

- 配置完全按房间隔离，直接读取该房间的 `live_timed_danmu_list`，无全局开关
- 每次启动应用后的**首次开播**才调度定时弹幕，中途下播再开播不会重复发送
- 每条弹幕独立倒计时：开播后 `delay` 秒发送 `text`；`text` 为空或 `enabled: false` 的条目跳过
- 即使中途下播，已创建的定时任务到点仍会尝试发送（直播间关闭时发送会失败）

### 5. 运行

```bash
python app.py
```

首次运行会弹出 B站扫码登录窗口，登录后 Cookie 自动保存到 `cookies.json`。

## 🎨 主题配置

`theme.json` 内置 10 套预设：

- 场景主题：`default` 默认亮彩 / `ocean` 深海青蓝 / `sakura` 樱粉夜色 / `forest` 森林暖光 / `dark` 极暗之夜
- 主题色预设：`green` 翠绿 / `blue` 海蓝 / `purple` 薰衣草 / `pink` 樱花粉 / `teal` 孔雀青

在设置页「主题模式」中选择并保存后写入 `config.json` 的 `frontend.theme`，下次启动自动应用。每套预设的颜色会同时映射到自定义 CSS 变量与 DevUI 设计令牌（`--devui-brand`、`--devui-base-bg` 等），DevUI 组件自动跟随主题。新增主题色时可用脚本同步生成完整预设：

```bash
python scripts\update_theme_presets.py
```

## 🏗 架构说明

组件样式以 Vue `<style scoped>` 为主；全局仅保留 `base.css`（CSS 变量、明暗模式、reset）与 `devui-theme.css`（`--devui-*` 令牌映射、DevUI 组件微调）。主题预设颜色在启动/保存时由 `applyThemeColors` 写入根元素，DevUI 组件通过 `--devui-brand` 等令牌自动跟随主题。

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
