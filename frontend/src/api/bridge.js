function getApi() {
	return window.pywebview?.api
}

function hasMethod(name) {
	return typeof getApi()?.[name] === 'function'
}

function isWebMode() {
	// URL 参数 ?mode=web 才是真正 web 模式；pywebview 未就绪 ≠ web 模式
	if (window.pywebview) return false
	return new URLSearchParams(location.search).get('mode') === 'web'
}

// pywebview API 就绪 Promise：pywebview 在 pywebviewready 事件后才创建 api 方法
let apiReadyPromise = null
export function ensureApiReady() {
	if (isWebMode()) return Promise.resolve()
	if (window.__pywebviewApiReady) return Promise.resolve()
	if (!apiReadyPromise) {
		apiReadyPromise = new Promise((resolve) => {
			window.addEventListener(
				'pywebviewready',
				() => {
					window.__pywebviewApiReady = true
					resolve()
				},
				{ once: true },
			)
			// 兜底：10 秒后放弃等待
			setTimeout(resolve, 10000)
		})
	}
	return apiReadyPromise
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

export async function getLoginStatus() {
	if (isWebMode()) {
		return fetchApi('/login/status')
	}
	return callApi('getLoginStatus')
}

export async function startQrLogin() {
	if (isWebMode()) {
		return fetchApi('/login/start', { method: 'POST' })
	}
	return callApi('startQrLogin')
}

export async function sendDanmu(text, roomId = null) {
	if (isWebMode()) {
		return fetchApi('/danmu', {
			method: 'POST',
			body: JSON.stringify({ message: text, room_id: roomId ?? null }),
		})
	}
	if (!hasMethod('sendDanmu')) {
		return { ok: false, error: '后端发送接口不可用' }
	}
	return getApi().sendDanmu(text, roomId)
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

export function toggleMaximizeWindow() {
	if (isWebMode()) {
		return
	}
	if (hasMethod('toggleMaximizeWindow')) {
		getApi().toggleMaximizeWindow()
	}
}

export async function setWindowSize(preset) {
	if (isWebMode()) {
		return { ok: false, error: '网页模式不支持调整窗口大小' }
	}
	return callApi('setWindowSize', preset)
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

// ---- 数据面板 API（webview / web 通用） ----

// pywebview 模式：等待 API 就绪并带重试地调用后端方法
async function callApi(name, ...args) {
	await ensureApiReady()
	for (let i = 0; i < 20; i++) {
		if (hasMethod(name)) {
			return getApi()[name](...args)
		}
		await new Promise((resolve) => setTimeout(resolve, 300))
	}
	return { ok: false, error: `后端接口 ${name} 不可用` }
}

export async function getRoomsStatus() {
	if (isWebMode()) {
		return fetchApi('/rooms')
	}
	return callApi('getRoomsStatus')
}

export async function getConsoleLogs(sinceSeq = 0) {
	if (isWebMode()) {
		return fetchApi(`/console?since=${sinceSeq}`)
	}
	return callApi('getConsoleLogs', sinceSeq, 200)
}

export async function clearConsole() {
	if (isWebMode()) {
		return fetchApi('/console?since=-1')
	}
	return callApi('getConsoleLogs', -1, 0)
}

export async function startRoomListen(roomId) {
	if (isWebMode()) {
		return fetchApi('/listen', {
			method: 'POST',
			body: JSON.stringify({ action: 'start', room: roomId }),
		})
	}
	return callApi('startRoomListen', roomId)
}

export async function stopRoomListen(roomId) {
	if (isWebMode()) {
		return fetchApi('/listen', {
			method: 'POST',
			body: JSON.stringify({ action: 'stop', room: roomId }),
		})
	}
	return callApi('stopRoomListen', roomId)
}

export async function getDanmuPage({
	roomId,
	page = 1,
	pageSize = 50,
	keyword,
	itemType,
	order = 'DESC',
}) {
	if (isWebMode()) {
		const params = new URLSearchParams({
			room: roomId || '',
			page: String(page),
			pageSize: String(pageSize),
			order,
		})
		if (keyword) params.set('keyword', keyword)
		if (itemType) params.set('type', itemType)
		return fetchApi(`/danmu_db?${params.toString()}`)
	}
	return callApi('getDanmuPage', roomId, page, pageSize, keyword, itemType, order)
}

export async function getGiftPage({ roomId, page = 1, pageSize = 50, keyword, order = 'DESC' }) {
	if (isWebMode()) {
		const params = new URLSearchParams({
			room: roomId || '',
			page: String(page),
			pageSize: String(pageSize),
			order,
		})
		if (keyword) params.set('keyword', keyword)
		return fetchApi(`/gift_db?${params.toString()}`)
	}
	return callApi('getGiftPage', roomId, page, pageSize, keyword, order)
}
