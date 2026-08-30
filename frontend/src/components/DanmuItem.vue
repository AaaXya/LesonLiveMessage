<script setup>
import { ref } from 'vue'

defineProps({
	data: {
		type: Object,
		required: true,
	},
})

const avatarVisible = ref(true)

function hideAvatar() {
	avatarVisible.value = false
}
</script>

<template>
	<div class="danmu-item">
		<img
			v-if="data.avatar_url && avatarVisible"
			class="danmu-avatar"
			:src="data.avatar_url"
			alt="头像"
			@error="hideAvatar"
		/>
		<div class="danmu-body">
			<div class="danmu-header">
				<span class="medal">[{{ data.medal_name }}·{{ data.medal_level }}]</span>
				<span class="name">{{ data.username }}</span>
			</div>
			<div class="danmu-bubble">{{ data.content }}</div>
		</div>
	</div>
</template>

<style scoped>
.danmu-item {
	display: flex;
	align-items: center;
	gap: 12px;
	padding: 4px 0;
	margin-bottom: 10px;
	animation: fadeIn 0.25s ease;
	color: var(--theme-text-primary, var(--text-primary));
}

.danmu-avatar {
	width: 40px;
	height: 40px;
	border-radius: 50%;
	object-fit: cover;
	border: 1px solid var(--border-strong);
	flex-shrink: 0;
	background: var(--surface-soft);
}

.danmu-body {
	flex: 1;
	min-width: 0;
	display: flex;
	flex-direction: column;
	gap: 6px;
}

.danmu-header {
	display: flex;
	align-items: center;
	flex-wrap: wrap;
	gap: 8px;
	margin: 0;
	font-size: 0.95rem;
}

.danmu-bubble {
	background: var(--bubble-gradient);
	border-radius: 18px;
	padding: 10px 14px;
	word-break: break-word;
	line-height: 1.5;
	box-shadow: 0 10px 24px var(--bubble-shadow);
	background-clip: padding-box;
	-webkit-font-smoothing: antialiased;
}

.medal {
	color: var(--medal-text);
	margin-right: 6px;
}

.name {
	color: var(--name-text);
	margin-right: 6px;
}

@keyframes fadeIn {
	from {
		opacity: 0;
	}
	to {
		opacity: 1;
	}
}
</style>
