<script setup>
import { ref } from 'vue'
import { sendDanmu } from '../api/bridge'

const text = ref('')
const status = ref('')
let statusTimer = null

function showStatus(message, duration = 2400) {
	status.value = message
	if (statusTimer) {
		clearTimeout(statusTimer)
	}
	if (duration > 0) {
		statusTimer = setTimeout(() => {
			status.value = ''
		}, duration)
	}
}

async function handleSend() {
	const value = text.value.trim()
	if (!value) {
		showStatus('请输入弹幕内容')
		return
	}

	try {
		const result = await sendDanmu(value)
		if (result?.ok) {
			showStatus('弹幕已发送')
			text.value = ''
		} else {
			showStatus('发送失败：' + (result?.error || '未知错误'))
		}
	} catch (error) {
		console.error('sendDanmu 调用失败：', error)
		showStatus('发送失败：后端调用异常')
	}
}

function handleKeydown(event) {
	if (event.key === 'Enter') {
		event.preventDefault()
		handleSend()
	}
}
</script>

<template>
	<div class="danmu-box">
		<input
			v-model="text"
			class="danmu-input"
			type="text"
			placeholder="输入弹幕后按 Enter 发送"
			autocomplete="off"
			@keydown="handleKeydown"
		/>
		<button class="danmu-send-btn" type="button" @click="handleSend">发送</button>
	</div>
	<div class="danmu-status">{{ status }}</div>
</template>

<style scoped>
.danmu-box {
	position: fixed;
	left: 0;
	right: 0;
	bottom: 0;
	z-index: 999;
	display: flex;
	gap: 8px;
	align-items: center;
	padding: 10px 12px;
	background: var(--surface);
	border: 1px solid var(--border);
	border-radius: 12px 12px 0 0;
	backdrop-filter: blur(12px);
}

.danmu-input {
	flex: 1;
	min-width: 0;
	padding: 12px 14px;
	border: 1px solid var(--border);
	border-radius: 999px;
	background: var(--surface-soft);
	color: var(--text-primary);
	outline: none;
	font-size: 0.95rem;
}

.danmu-input::placeholder {
	color: var(--text-placeholder);
}

.danmu-send-btn {
	border: none;
	background: var(--send-gradient);
	color: var(--send-text);
	border-radius: 999px;
	padding: 10px 18px;
	cursor: pointer;
	font-weight: 700;
	box-shadow: 0 10px 24px var(--shadow);
}

.danmu-send-btn:hover {
	opacity: 0.95;
}

.danmu-status {
	position: fixed;
	left: 0;
	right: 0;
	bottom: 58px;
	z-index: 998;
	text-align: center;
	color: var(--text-muted);
	font-size: 0.85rem;
	pointer-events: none;
}
</style>
