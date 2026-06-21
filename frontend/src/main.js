import { createApp } from 'vue'
import App from './App.vue'
import { pushDanmu } from './stores/danmu'
import { initThemeLoader } from './composables/useTheme'
import './styles/base.css'
import './styles/danmu.css'
import './styles/settings.css'

window.addDanmu = pushDanmu

window.onerror = function (message, source, lineno, colno, error) {
  console.error('前端错误：', message, source, lineno, colno, error)
}

initThemeLoader()

createApp(App).mount('#app')
