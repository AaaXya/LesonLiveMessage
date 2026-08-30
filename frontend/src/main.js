import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import DevUI from 'vue-devui'
import 'vue-devui/style.css'
import { pushDanmu } from './stores/danmu'
import { initThemeLoader } from './composables/useTheme'
import { restoreThemePalette } from './composables/useThemePalette'
import { pollEvents } from './api/bridge'
import './styles/base.css'
import './styles/devui-theme.css'

// 默认深色；布局栏可在运行时切换。
document.documentElement.classList.add('dark')

// 恢复用户保存的主题色
restoreThemePalette()

window.addDanmu = pushDanmu

window.onerror = function (message, source, lineno, colno, error) {
	console.error('前端错误：', message, source, lineno, colno, error)
}

initThemeLoader()

const app = createApp(App)
app.use(router)
app.use(DevUI)
app.mount('#app')

// ===== Web 模式（?mode=web）：轮询后端事件 =====
if (new URLSearchParams(location.search).get('mode') === 'web') {
	console.log('[web mode] 启动事件轮询...')
	function poll() {
		pollEvents()
			.then((events) => {
				if (events && events.length > 0) {
					events.forEach((e) => pushDanmu(e.data))
				}
			})
			.catch(() => {})
			.finally(() => {
				setTimeout(poll, 500)
			})
	}
	poll()
}
