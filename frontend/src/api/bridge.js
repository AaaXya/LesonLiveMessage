function getApi() {
	return window.pywebview?.api
}

function hasMethod(name) {
	return typeof getApi()?.[name] === 'function'
}

function isWebMode() {
	return !window.pywebview
}

async function fetchApi(path, options = {}) {
	const res = await fetch(`/api${path}`, {
		headers: { 'Content-Type': 'application/json' },
		...options,
	})
	return res.json()
}

export function whenPywebviewReady(callback) {
	if (window.pywebview) {
		callback()
		return
	}
	// web 模式下直接回调
	if (isWebMode()) {
		callback()
		return
	}
	window.addEventListener('pywebviewready', callback, { once: true })
}

export async function getFrontendConfig() {
	if (isWebMode()) {
		return fetchApi('/config')
	}
	if (!hasMethod('getFrontendConfig')) {
		return null
	}
	return getApi().getFrontendConfig()
}

export async function saveFrontendConfig(update) {
	if (isWebMode()) {
		return fetchApi('/config', {
			method: 'POST',
			body: JSON.stringify(update),
		})
	}
	if (!hasMethod('saveFrontendConfig')) {
		return { ok: false, error: '后端配置接口不可用' }
	}
	return getApi().saveFrontendConfig(update)
}

export async function sendDanmu(text) {
	if (isWebMode()) {
		return fetchApi('/danmu', {
			method: 'POST',
			body: JSON.stringify({ message: text }),
		})
	}
	if (!hasMethod('sendDanmu')) {
		return { ok: false, error: '后端发送接口不可用' }
	}
	return getApi().sendDanmu(text)
}

export function closeWindow() {
	if (isWebMode()) {
		return
	}
	if (hasMethod('closeWindow')) {
		return getApi().closeWindow()
	}
	window.close()
}

export function minimizeWindow() {
	if (isWebMode()) {
		return
	}
	if (hasMethod('minimizeWindow')) {
		getApi().minimizeWindow()
	}
}

// 轮询获取弹幕事件（web 模式使用）
let lastEventId = 0
export async function pollEvents() {
	if (!isWebMode()) return []
	try {
		const res = await fetch(`/api/events?since=${lastEventId}`)
		const data = await res.json()
		if (data.events && data.events.length > 0) {
			lastEventId = data.events[data.events.length - 1].id
		}
		return data.events || []
	} catch {
		return []
	}
}
