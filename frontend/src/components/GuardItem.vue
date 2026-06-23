<script setup>
import { computed } from 'vue'

const props = defineProps({
	data: { type: Object, required: true },
})

const guardIcon = computed(() => {
	const level = props.data.guard_level
	if (level === 1) return '👑'
	if (level === 2) return '💍'
	return '⚓'
})

const guardLabel = computed(() => {
	return props.data.guard_name || '大航海'
})

const priceText = computed(() => {
	const price = (props.data.price || 0) / 1000
	if (!price) return ''
	return `¥${price.toFixed(1)}`
})
</script>

<template>
	<div class="guard-item">
		<span class="guard-icon">{{ guardIcon }}</span>
		<div class="guard-body">
			<div class="guard-header">
				<span class="name">{{ data.username }}</span>
				<span class="guard-tag">{{ guardLabel }}</span>
			</div>
			<div class="guard-content">
				开通 <strong>{{ guardLabel }}</strong>
				<span v-if="data.num > 1"> ×{{ data.num }}</span>
				<span v-if="priceText" class="guard-price">{{ priceText }}</span>
			</div>
		</div>
	</div>
</template>

<style scoped>
.guard-item {
	display: flex;
	align-items: flex-start;
	gap: 10px;
	padding: 10px 12px;
	border-radius: 10px;
	margin-bottom: 8px;
	background: linear-gradient(135deg, rgba(60, 140, 255, 0.18), rgba(80, 100, 255, 0.1));
	border: 1px solid rgba(80, 140, 255, 0.25);
	color: var(--text-primary);
	animation: guardIn 0.35s ease;
}

.guard-icon {
	font-size: 1.4rem;
	flex-shrink: 0;
	margin-top: 2px;
}

.guard-body {
	flex: 1;
	min-width: 0;
}

.guard-header {
	display: flex;
	align-items: center;
	gap: 6px;
	flex-wrap: wrap;
	margin-bottom: 4px;
	font-size: 0.85rem;
}

.name {
	color: var(--name-text);
	font-weight: 600;
}

.guard-tag {
	font-size: 0.75rem;
	padding: 1px 8px;
	border-radius: 999px;
	background: rgba(60, 160, 255, 0.3);
	color: #6cb8ff;
	font-weight: 700;
}

.guard-content {
	font-size: 0.9rem;
	line-height: 1.6;
	color: var(--text-primary);
}

.guard-content strong {
	color: #6cb8ff;
}

.guard-price {
	margin-left: 6px;
	font-size: 0.82rem;
	color: var(--text-muted);
}

@keyframes guardIn {
	from {
		opacity: 0;
		transform: translateX(8px);
	}
	to {
		opacity: 1;
		transform: translateX(0);
	}
}
</style>
