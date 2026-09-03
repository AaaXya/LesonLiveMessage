<script setup>
import { onMounted, onUnmounted, ref } from 'vue'
import { getLoginStatus, startQrLogin } from '../api/bridge'

const state = ref(null) // 后端登录状态快照
const visible = ref(false)
let prevStatus = ''
let timer = null

async function refresh() {
	try {
		const res = await getLoginStatus()
		if (!res?.ok) return
		state.value = res
		const status = String(res.status || '')
		// 仅在明确“需要登录/扫码/出错”时展示浮层；checking/ok 不遮住界面
		visible.value = status === 'scanning' || status === 'timeout' || status === 'error'

		// 登录成功后刷新整个页面，让后端注入的凭据全面生效
		if (status === 'ok' && prevStatus && prevStatus !== 'ok') {
			setTimeout(() => location.reload(), 600)
		}
		prevStatus = status || prevStatus
	} catch {
		// 桥接尚未就绪，等下一次轮询
	}
}

async function handleRefreshQr() {
	state.value = null
	await startQrLogin()
	refresh()
}

onMounted(() => {
	refresh()
	timer = setInterval(refresh, 2000)
})

onUnmounted(() => clearInterval(timer))
</script>

<template>
	<transition name="login-fade">
		<div v-if="visible" class="login-mask">
			<div class="login-card">
				<h2 class="title">Bilibili 扫码登录</h2>
				<p class="hint">
					{{ state?.message || '请使用 B 站手机客户端扫码登录' }}
				</p>

				<div v-if="state?.status === 'scanning'" class="qr-area">
					<img
						v-if="state?.qr_data"
						:src="state.qr_data"
						class="qr"
						alt="Bilibili 登录二维码"
					/>
					<div v-else class="qr-loading">
						<span class="spinner"></span>
						<span>正在获取二维码...</span>
					</div>
					<div class="steps">
						<p>1. 打开手机 Bilibili 客户端</p>
						<p>2. 进入「我的」→ 扫一扫</p>
						<p>3. 扫描二维码并确认登录</p>
					</div>
					<button class="btn" type="button" @click="handleRefreshQr">刷新二维码</button>
				</div>

				<div v-else class="qr-area">
					<p class="error-text">{{ state?.message || '登录状态异常' }}</p>
					<button class="btn" type="button" @click="handleRefreshQr">重新扫码登录</button>
				</div>
			</div>
		</div>
	</transition>
</template>

<style scoped>
.login-mask {
	position: fixed;
	inset: 0;
	z-index: 3000;
	display: grid;
	place-items: center;
	background: rgba(20, 18, 16, 0.72);
	backdrop-filter: blur(6px);
}
.login-card {
	width: 360px;
	max-width: calc(100vw - 48px);
	padding: 28px 26px 26px;
	background: var(--surface-strong, #2a2420);
	border: 1px solid var(--border, rgba(61, 55, 47, 0.6));
	border-radius: 16px;
	box-shadow: 0 18px 40px rgba(0, 0, 0, 0.45);
	color: var(--text-primary, #f5f2ed);
	text-align: center;
}
.title {
	margin: 0 0 6px;
	font-size: 20px;
	letter-spacing: 0.04em;
}
.hint {
	margin: 0 0 16px;
	font-size: 13px;
	color: var(--text-muted, #b8b1a8);
	min-height: 18px;
}
.qr-area {
	display: grid;
	justify-items: center;
	gap: 14px;
}
.qr {
	width: 220px;
	height: 220px;
	border-radius: 10px;
	background: #fff;
	padding: 8px;
}
.qr-loading {
	display: flex;
	flex-direction: column;
	align-items: center;
	gap: 12px;
	width: 220px;
	height: 220px;
	justify-content: center;
	color: var(--text-muted, #b8b1a8);
	font-size: 13px;
}
.spinner {
	width: 30px;
	height: 30px;
	border: 3px solid var(--accent-soft, rgba(123, 198, 123, 0.25));
	border-top-color: var(--accent, #7bc67b);
	border-radius: 50%;
	animation: spin 0.9s linear infinite;
}
@keyframes spin {
	to {
		transform: rotate(360deg);
	}
}
.steps {
	display: grid;
	gap: 2px;
	margin: 2px 0 0;
	font-size: 12.5px;
	color: var(--text-muted, #b8b1a8);
	line-height: 1.8;
}
.error-text {
	color: var(--danger, #d97676);
	font-size: 14px;
}
.btn {
	width: 180px;
	border: 0;
	border-radius: 10px;
	padding: 9px 14px;
	font-size: 14px;
	cursor: pointer;
	color: #f5f2ed;
	background: var(--send-gradient, linear-gradient(135deg, #7bc67b, #5eccc4));
	box-shadow: 0 6px 14px rgba(123, 198, 123, 0.25);
	transition:
		transform 0.15s ease,
		opacity 0.15s ease;
}
.btn:hover {
	transform: translateY(-1px);
	opacity: 0.94;
}
.login-fade-enter-active,
.login-fade-leave-active {
	transition: opacity 0.25s ease;
}
.login-fade-enter-from,
.login-fade-leave-to {
	opacity: 0;
}
</style>
