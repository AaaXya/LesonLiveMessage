<script setup>
defineProps({
	data: {
		type: Object,
		required: true,
	},
})
</script>

<template>
	<div class="guard-item">
		<div class="guard-header">
			<span class="gift-medal">[{{ data.medal_name }}·{{ data.medal_level }}]</span>
			<span class="name">{{ data.username }}</span>
			<span class="type-label">续费</span>
		</div>
		<div class="content">
			续费大航海 {{ data.guard_level || '' }}
			<template v-if="data.guard_name"> {{ data.guard_name }}</template>
		</div>
	</div>
</template>

<style scoped>
.guard-item {
	background: var(--guard-bg);
	color: var(--guard-text);
	padding: 8px 12px;
	border-radius: 8px;
	margin-bottom: 8px;
	animation: fadeIn 0.3s ease;
}

.guard-header {
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
