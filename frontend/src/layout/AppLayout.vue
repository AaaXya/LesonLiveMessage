<script setup>
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import WindowControls from '../components/WindowControls.vue'

const route = useRoute()
const router = useRouter()
const isLight = ref(localStorage.getItem('color-mode') === 'light')
const menuItems = [
	{ name: 'rooms', label: '直播间', icon: 'op-home' },
	{ name: 'console', label: '控制台', icon: 'response-header' },
	{ name: 'database', label: '弹幕数据', icon: 'database' },
	{ name: 'gifts', label: '礼物数据', icon: 'buy' },
	{ name: 'analytics', label: '数据分析', icon: 'chart' },
	{ name: 'auto-speak', label: '自动发言', icon: 'comment' },
	{ name: 'settings', label: '设置', icon: 'setting' },
]
const activeName = computed(() => route.name)
function navigate(name) {
	router.push({ name })
}
function toggleColorMode() {
	isLight.value = !isLight.value
	document.documentElement.classList.toggle('light', isLight.value)
	document.documentElement.classList.toggle('dark', !isLight.value)
	localStorage.setItem('color-mode', isLight.value ? 'light' : 'dark')
}
document.documentElement.classList.toggle('light', isLight.value)
document.documentElement.classList.toggle('dark', !isLight.value)
</script>

<template>
	<div class="app-layout">
		<aside class="sidebar">
			<div class="brand"><span class="brand-mark">B</span><span>弹幕姬</span></div>
			<nav class="nav">
				<d-button
					v-for="item in menuItems"
					:key="item.name"
					type="button"
					size="sm"
					:variant="activeName === item.name ? 'solid' : 'text'"
					:color="activeName === item.name ? 'primary' : 'secondary'"
					class="nav-item"
					:class="{ active: activeName === item.name }"
					@click="navigate(item.name)"
				>
					<d-icon :name="item.icon" :size="16" class="nav-icon" />
					<span class="nav-label">{{ item.label }}</span>
				</d-button>
			</nav>
			<d-button
				class="mode-switch"
				variant="outline"
				color="secondary"
				@click="toggleColorMode"
			>
				<d-icon :name="isLight ? 'dark' : 'light'" :size="16" />
				{{ isLight ? '深色' : '浅色' }}
			</d-button>
		</aside>
		<div class="main">
			<header class="titlebar">
				<span class="page-title">{{ route.meta.title }}</span>
			</header>
			<main class="content"><router-view /></main>
		</div>
		<WindowControls />
	</div>
</template>

<style scoped>
.app-layout {
	display: flex;
	width: 100%;
	height: 100vh;
	background:
		radial-gradient(circle at top left, var(--accent-soft), transparent 26%),
		radial-gradient(circle at top right, var(--accent-ghost), transparent 28%), var(--page-bg);
}
.sidebar {
	display: flex;
	flex-direction: column;
	width: 220px;
	flex-shrink: 0;
	padding: 20px 14px 16px;
	background: linear-gradient(180deg, var(--surface-strong), var(--bg-elevated));
	border-right: 1px solid var(--border);
	backdrop-filter: blur(10px);
	color: var(--text-primary);
}
.brand {
	display: flex;
	align-items: center;
	gap: 12px;
	padding: 6px 10px 22px;
	font-size: 18px;
	font-weight: 700;
	letter-spacing: 0.06em;
	color: var(--text-primary);
}
.brand-mark {
	display: grid;
	place-items: center;
	width: 32px;
	height: 32px;
	border-radius: 10px;
	background: var(--bubble-gradient);
	box-shadow: 0 10px 18px var(--shadow);
	color: #fff;
	font-size: 13px;
	font-weight: 700;
}
.nav {
	display: grid;
	gap: 6px;
}
.nav-item {
	display: flex;
	align-items: center;
	justify-content: flex-start;
	gap: 10px;
	width: 100%;
	border: 1px solid transparent;
	border-radius: 12px;
	padding: 10px 12px;
	background: transparent;
	color: var(--text-muted);
	text-align: left;
	transition: all 0.2s ease;
}
.nav-item:hover {
	background: var(--surface-hover);
	color: var(--text-primary);
	border-color: var(--border);
}
.nav-item.active {
	background: var(--bubble-gradient);
	color: var(--text-primary);
	border-color: transparent;
	font-weight: 700;
}
.nav-icon {
	display: block;
	width: 18px;
	text-align: center;
	font-size: 16px;
	opacity: 0.9;
	line-height: 1;
}
.nav-item :deep(.button-content) {
	display: grid;
	grid-template-columns: 18px 1fr 18px;
	align-items: center;
	width: 100%;
}
.nav-label {
	grid-column: 2;
	text-align: center;
}
.mode-switch {
	margin-top: auto;
	width: 100%;
	justify-content: center;
	border-radius: 12px;
}
.mode-switch :deep(.button-content) {
	display: flex;
	align-items: center;
	gap: 8px;
}
.main {
	display: flex;
	min-width: 0;
	flex: 1;
	flex-direction: column;
}
.titlebar {
	display: flex;
	align-items: center;
	height: 58px;
	padding: 0 22px;
	border-bottom: 1px solid var(--border);
	background: linear-gradient(180deg, var(--surface-strong), var(--surface));
	backdrop-filter: blur(10px);
}
.page-title {
	font-size: 15px;
	font-weight: 700;
	letter-spacing: 0.04em;
	color: var(--text-primary);
}
.content {
	flex: 1;
	overflow: auto;
	padding: 22px;
}

/* 响应式设计 */
@media (max-width: 768px) {
	.sidebar {
		width: 200px;
		padding: 16px 10px 12px;
	}
	.brand {
		padding: 4px 8px 16px;
		font-size: 16px;
	}
	.content {
		padding: 16px;
	}
}
</style>
