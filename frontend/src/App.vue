<script setup>
import AppLayout from './layout/AppLayout.vue'
import DanmuList from './components/DanmuList.vue'

// OBS 浏览器源等纯弹幕悬浮场景：?overlay=1
const isOverlay = new URLSearchParams(location.search).get('overlay') === '1'
</script>

<template>
	<AppLayout v-if="!isOverlay" />
	<DanmuList v-else />
</template>

<style>
html,
body,
#app {
	height: 100%;
	margin: 0;
	background: transparent;
}
</style>
