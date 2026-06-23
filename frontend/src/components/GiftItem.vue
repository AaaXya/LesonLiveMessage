<script setup>
import { computed } from 'vue'

const props = defineProps({
	data: { type: Object, required: true },
})

const giftIcon = computed(() => {
	const price = (props.data.paid_coin || 0) / 1000
	if (price >= 100) return '💎'
	if (price >= 10) return '🌟'
	return '🎁'
})

const priceText = computed(() => {
	const paid = (props.data.paid_coin || 0) / 1000
	if (!paid) return ''
	const total = (props.data.total_coin || 0) / 1000
	if (paid !== total && total) {
		return `¥${paid.toFixed(1)} (原价 ¥${total.toFixed(1)})`
	}
	return `¥${paid.toFixed(1)}`
})
</script>

<template>
	<div class="gift-item">
		<span class="gift-icon">{{ giftIcon }}</span>
		<div class="gift-body">
			<div class="gift-header">
				<span v-if="data.medal_name" class="gift-medal"
					>[{{ data.medal_name }}·{{ data.medal_level }}]</span
				>
				<span class="name">{{ data.username }}</span>
				<span class="gift-tag">礼物</span>
			</div>
			<div class="gift-content">
				赠送 <strong>×{{ data.gift_num }}</strong> 【{{ data.gift_name }}】
				<span v-if="priceText" class="gift-price">{{ priceText }}</span>
			</div>
		</div>
	</div>
</template>

<style scoped>
.gift-item {
	display: flex;
	align-items: flex-start;
	gap: 10px;
	padding: 10px 12px;
	border-radius: 10px;
	margin-bottom: 8px;
	background: linear-gradient(135deg, rgba(255, 180, 30, 0.16), rgba(255, 140, 20, 0.1));
	border: 1px solid rgba(255, 180, 40, 0.2);
	color: var(--text-primary);
	animation: giftIn 0.35s ease;
}

.gift-icon {
	font-size: 1.4rem;
	flex-shrink: 0;
	margin-top: 2px;
}

.gift-body {
	flex: 1;
	min-width: 0;
}

.gift-header {
	display: flex;
	align-items: center;
	gap: 6px;
	flex-wrap: wrap;
	margin-bottom: 4px;
	font-size: 0.85rem;
}

.gift-medal {
	color: var(--gift-medal-text);
	font-weight: 600;
}

.name {
	color: var(--name-text);
	font-weight: 600;
}

.gift-tag {
	font-size: 0.75rem;
	padding: 1px 7px;
	border-radius: 999px;
	background: rgba(255, 190, 50, 0.25);
	color: #ffb830;
	font-weight: 600;
}

.gift-content {
	font-size: 0.9rem;
	line-height: 1.6;
	color: var(--text-primary);
}

.gift-content strong {
	color: #ffcc33;
}

.gift-price {
	margin-left: 6px;
	font-size: 0.82rem;
	color: var(--text-muted);
}

@keyframes giftIn {
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
