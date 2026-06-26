import { createApp } from 'vue'
import App from './App.vue'
import { pushDanmu } from './stores/danmu'
import { initThemeLoader } from './composables/useTheme'
import { pollEvents } from './api/bridge'
import './styles/base.css'

window.addDanmu = pushDanmu

window.onerror = function (message, source, lineno, colno, error) {
	console.error('前端错误：', message, source, lineno, colno, error)
}

initThemeLoader()

createApp(App).mount('#app')

// ===== Web 模式：轮询后端事件 =====
if (!window.pywebview) {
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
