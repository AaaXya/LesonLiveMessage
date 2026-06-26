<script setup>
import { ref } from 'vue'
import WindowControls from './components/WindowControls.vue'
import SettingsPanel from './components/SettingsPanel.vue'
import DanmuList from './components/DanmuList.vue'
import DanmuInput from './components/DanmuInput.vue'

const settingsVisible = ref(false)

// URL 传参 ?mode=web 时仅展示弹幕流（OBS 浏览器源场景）
const isWebMode = new URLSearchParams(location.search).get('mode') === 'web'

function openSettings() {
	settingsVisible.value = true
}

function closeSettings() {
	settingsVisible.value = false
}
</script>

<template>
	<div class="app-root">
		<template v-if="!isWebMode">
			<WindowControls :on-open-settings="openSettings" />
			<SettingsPanel :visible="settingsVisible" @close="closeSettings" />
		</template>
		<DanmuList />
		<DanmuInput v-if="!isWebMode" />
	</div>
</template>

<style scoped>
.app-root {
	display: flex;
	flex-direction: column;
	height: 100vh;
	width: 100%;
	background: transparent;
}
</style>
