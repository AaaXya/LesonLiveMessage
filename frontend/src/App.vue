<script setup>
import { ref } from 'vue'
import WindowControls from './components/WindowControls.vue'
import SettingsPanel from './components/SettingsPanel.vue'
import DanmuList from './components/DanmuList.vue'
import DanmuInput from './components/DanmuInput.vue'

const settingsVisible = ref(false)

function openSettings() {
	settingsVisible.value = true
}

function closeSettings() {
	settingsVisible.value = false
}
</script>

<template>
	<div class="app-root">
		<WindowControls :on-open-settings="openSettings" />
		<SettingsPanel :visible="settingsVisible" @close="closeSettings" />
		<DanmuList />
		<DanmuInput />
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
