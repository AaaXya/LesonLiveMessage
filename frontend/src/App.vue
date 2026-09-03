<script setup>
import AppLayout from './layout/AppLayout.vue'
import DanmuList from './components/DanmuList.vue'
import LoginQr from './components/LoginQr.vue'

// OBS 浏览器源等纯弹幕悬浮场景：?overlay=1
const isOverlay = new URLSearchParams(location.search).get('overlay') === '1'
</script>

<template>
	<template v-if="!isOverlay">
		<AppLayout />
		<!-- 未登录/凭据失效时：在首页上内嵌扫码登录，不再弹外部浏览器页面 -->
		<LoginQr />
	</template>
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
