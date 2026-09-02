import { ref } from 'vue'
import { THEME_VAR_MAP } from '../constants'
import { getFrontendConfig, whenPywebviewReady } from '../api/bridge'

export const frontendConfig = ref(null)

export function applyThemeColors(colors = {}) {
	Object.entries(THEME_VAR_MAP).forEach(([key, cssVar]) => {
		if (typeof colors[key] === 'string' && colors[key].trim()) {
			document.documentElement.style.setProperty(cssVar, colors[key].trim())
		}
	})
}

export async function loadFrontendConfig() {
	try {
		const config = await getFrontendConfig()
		if (!config) {
			return null
		}
		frontendConfig.value = config
		applyThemeColors(config.theme?.colors || {})
		return config
	} catch (error) {
		console.warn('前端配置读取失败，使用默认配色：', error)
		return null
	}
}

export function initThemeLoader() {
	async function tryLoad() {
		const config = await loadFrontendConfig()
		if (config) return
		// pywebview API 尚未就绪，500ms 后重试
		setTimeout(tryLoad, 500)
	}

	whenPywebviewReady(tryLoad)
}

export function getCurrentRoomBinding(config, roomIdOverride = null) {
	const roomId = String(roomIdOverride ?? (config?.LESSONROOMID || '')).trim()
	const bindings = config?.room_bindings || {}
	return bindings[roomId] || {}
}
