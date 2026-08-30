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
		<button class="win-btn win-min" title="最小化" type="button" @click="minimizeWindow">
			<svg width="10" height="10" viewBox="0 0 10 10">
				<line x1="0" y1="5" x2="10" y2="5" stroke="currentColor" stroke-width="1" />
			</svg>
		</button>
		<button
			class="win-btn win-max"
			title="最大化 / 还原"
			type="button"
			@click="toggleMaximizeWindow"
		>
			<svg width="10" height="10" viewBox="0 0 10 10">
				<rect
					x="0.5"
					y="0.5"
					width="9"
					height="9"
					fill="none"
					stroke="currentColor"
					stroke-width="1"
				/>
			</svg>
		</button>
		<button class="win-btn win-close" title="关闭" type="button" @click="handleClose">
			<svg width="10" height="10" viewBox="0 0 10 10">
				<line x1="0" y1="0" x2="10" y2="10" stroke="currentColor" stroke-width="1" />
				<line x1="10" y1="0" x2="0" y2="10" stroke="currentColor" stroke-width="1" />
			</svg>
		</button>
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
	background: transparent;
	color: var(--text-muted, #9aa5ad);
	cursor: pointer;
	padding: 0;
	transition:
		background 0.12s ease,
		color 0.12s ease;
	outline: none;
}

.win-btn svg {
	display: block;
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
