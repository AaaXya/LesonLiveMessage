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
	background: linear-gradient(135deg, rgba(255, 180, 30, 0.28), rgba(255, 140, 20, 0.18));
	border: 1px solid rgba(255, 180, 40, 0.35);
	color: #ffffff;
	text-shadow: 0 1px 3px rgba(0, 0, 0, 0.5);
	animation: giftIn 0.35s ease;
}

.gift-icon {
	font-size: 1.4rem;
	flex-shrink: 0;
	margin-top: 2px;
	filter: drop-shadow(0 1px 2px rgba(0, 0, 0, 0.4));
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
	color: #ffcc00;
	font-weight: 700;
	text-shadow: 0 1px 2px rgba(0, 0, 0, 0.6);
}

.name {
	color: var(--name-text);
	font-weight: 700;
	text-shadow: 0 1px 2px rgba(0, 0, 0, 0.5);
}

.gift-tag {
	font-size: 0.75rem;
	padding: 1px 7px;
	border-radius: 999px;
	background: rgba(255, 190, 50, 0.35);
	color: #fff3c4;
	font-weight: 700;
	text-shadow: 0 1px 2px rgba(0, 0, 0, 0.4);
}

.gift-content {
	font-size: 0.9rem;
	line-height: 1.6;
	color: #ffffff;
	text-shadow: 0 1px 2px rgba(0, 0, 0, 0.45);
}

.gift-content strong {
	color: #fff3c4;
	font-weight: 700;
}

.gift-price {
	margin-left: 6px;
	font-size: 0.82rem;
	color: rgba(255, 255, 255, 0.9);
	text-shadow: 0 1px 2px rgba(0, 0, 0, 0.5);
}

@keyframes giftIn {
	from {
		opacity: 0;
	}
	to {
		opacity: 1;
	}
}
</style>
