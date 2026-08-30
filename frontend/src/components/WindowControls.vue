<script setup>
import { closeWindow, minimizeWindow, toggleMaximizeWindow } from '../api/bridge'

async function handleClose() {
	try {
		await closeWindow()
	} catch (error) {
		console.error('关闭窗口失败：', error)
	}
}
</script>

<template>
	<div class="window-controls">
		<d-button
			class="win-btn win-min"
			variant="text"
			color="secondary"
			native-type="button"
			title="最小化"
			@click="minimizeWindow"
		>
			<d-icon name="minus" :size="12" />
		</d-button>
		<d-button
			class="win-btn win-max"
			variant="text"
			color="secondary"
			native-type="button"
			title="最大化 / 还原"
			@click="toggleMaximizeWindow"
		>
			<d-icon name="copy" :size="12" />
		</d-button>
		<d-button
			class="win-btn win-close"
			variant="text"
			color="secondary"
			native-type="button"
			title="关闭"
			@click="handleClose"
		>
			<d-icon name="close" :size="12" />
		</d-button>
	</div>
</template>

<style scoped>
/* Windows 风格标题栏按钮 */
.window-controls {
	position: fixed;
	top: 0;
	right: 0;
	z-index: 1500;
	display: flex;
	height: 32px;
	-webkit-app-region: no-drag;
}

.win-btn {
	width: 46px;
	height: 32px;
	display: inline-flex;
	align-items: center;
	justify-content: center;
	border: none;
	border-radius: 0;
	background: transparent;
	color: var(--text-muted, #9aa5ad);
	cursor: pointer;
	padding: 0;
	min-width: 0;
	transition:
		background 0.12s ease,
		color 0.12s ease;
	outline: none;
}

/* 禁用 DevUI 按钮的波纹与按压缩放，避免透明窗口下的合成层问题 */
.win-btn :deep(.water-wave) {
	display: none;
}

.win-btn.mousedown:not(:disabled) {
	transform: none;
}

.win-min:hover,
.win-max:hover {
	background: rgba(255, 255, 255, 0.1);
	color: var(--text-primary, #e8f0f6);
}

.win-close:hover {
	background: #e81123;
	color: #ffffff;
}

.win-btn:active {
	filter: brightness(0.85);
}
</style>
