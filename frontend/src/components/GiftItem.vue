<script setup>
defineProps({
	data: {
		type: Object,
		required: true,
	},
})
</script>

<template>
	<div class="gift-item">
		<div class="gift-header">
			<span class="gift-medal">[{{ data.medal_name }}·{{ data.medal_level }}]</span>
			<span class="name">{{ data.username }}</span>
			<span class="type-label">礼物</span>
		</div>
		<div class="content">
			赠送 ×{{ data.gift_num }}【{{ data.gift_name }}】 · {{ data.paid_coin / 1000 }} 元
			<template v-if="data.paid_coin && data.paid_coin !== data.total_coin">
				（花费 {{ data.total_coin / 1000 }} 元）
			</template>
		</div>
	</div>
</template>

<style scoped>
.gift-item {
	background: var(--gift-bg);
	color: var(--gift-text);
	padding: 8px 12px;
	border-radius: 8px;
	margin-bottom: 8px;
	animation: fadeIn 0.3s ease;
}

.gift-header {
	margin-bottom: 4px;
}

.gift-medal {
	color: var(--gift-medal-text);
	margin-right: 6px;
}

.name {
	color: var(--name-text);
	margin-right: 6px;
}

.content {
	line-height: 1.5;
}

@keyframes fadeIn {
	from {
		opacity: 0;
		transform: translateY(10px);
	}
	to {
		opacity: 1;
		transform: translateY(0);
	}
}
</style>
