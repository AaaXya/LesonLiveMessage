<script setup>
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import WindowControls from '../components/WindowControls.vue'

const route = useRoute()
const router = useRouter()
const isLight = ref(localStorage.getItem('color-mode') === 'light')
const menuItems = [
	{ name: 'rooms', label: '直播间', icon: '●' },
	{ name: 'console', label: '控制台', icon: '›_' },
	{ name: 'database', label: '弹幕数据库', icon: '□' },
	{ name: 'gifts', label: '礼物数据库', icon: '◇' },
	{ name: 'analytics', label: '数据分析', icon: '↗' },
	{ name: 'settings', label: '设置', icon: '⚙' },
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
					:type="button"
					:size="sm"
					:variant="activeName === item.name ? 'solid' : 'text'"
					:color="activeName === item.name ? 'primary' : 'secondary'"
					class="nav-item"
					:class="{ active: activeName === item.name }"
					@click="navigate(item.name)"
				>
					<span class="nav-icon">{{ item.icon }}</span>
					<span>{{ item.label }}</span>
				</d-button>
			</nav>
			<d-button
				class="mode-switch"
				variant="outline"
				color="secondary"
				@click="toggleColorMode"
			>
				{{ isLight ? '☾ 深色' : '☀ 浅色' }}
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
	background: transparent;
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
	background: linear-gradient(135deg, #6fb969 0%, #5eccc4 100%);
	box-shadow: 0 10px 18px rgba(111, 185, 105, 0.38);
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
	border-color: rgba(111, 185, 105, 0.14);
}
.nav-item.active {
	background: linear-gradient(135deg, rgba(111, 185, 105, 0.16), rgba(94, 204, 196, 0.08));
	color: var(--text-primary);
	border-color: rgba(111, 185, 105, 0.24);
	font-weight: 700;
}
.nav-icon {
	width: 18px;
	text-align: center;
	font-size: 16px;
	opacity: 0.9;
	line-height: 1;
}
.mode-switch {
	margin-top: auto;
	width: 100%;
	justify-content: flex-start;
	border-radius: 12px;
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
	background: linear-gradient(180deg, rgba(255, 255, 255, 0.18), rgba(255, 255, 255, 0.04));
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
