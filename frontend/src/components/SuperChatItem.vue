<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { superChat } from '../stores/danmu'

const remaining = ref(0)
const visible = ref(false)
let timer = null

function clearTimer() {
	if (timer) {
		clearInterval(timer)
		timer = null
	}
}

function startCountdown(sc) {
	clearTimer()
	visible.value = true

	const update = () => {
		const now = Date.now()
		const end = sc.end_time * 1000
		const left = Math.max(0, Math.ceil((end - now) / 1000))
		remaining.value = left
		if (left <= 0) {
			clearTimer()
			visible.value = false
			superChat.value = null
		}
	}
	update()
	timer = setInterval(update, 500)
}

watch(
	superChat,
	(sc) => {
		if (sc) {
			startCountdown(sc)
		}
	},
	{ immediate: true },
)

const progressPercent = computed(() => {
	if (!superChat.value) return 100
	const total = (superChat.value.end_time - superChat.value.start_time) / 60
	if (total <= 0) return 0
	const elapsed = (Date.now() - superChat.value.arrivedAt) / 60000
	return Math.max(0, Math.min(100, 100 - (elapsed / total) * 100))
})

const medalLabel = computed(() => {
	if (!superChat.value) return ''
	const sc = superChat.value
	return sc.medal_name ? `[${sc.medal_name}·${sc.medal_level}]` : ''
})

onUnmounted(clearTimer)
</script>

<template>
	<div v-if="visible && superChat" class="sc-banner">
		<div class="sc-progress" :style="{ width: progressPercent + '%' }" />
		<div class="sc-body">
			<img
				v-if="superChat.avatar_url"
				class="sc-avatar"
				:src="superChat.avatar_url"
				alt="头像"
			/>
			<div class="sc-info">
				<div class="sc-header">
					<span v-if="medalLabel" class="sc-medal">{{ medalLabel }}</span>
					<span class="sc-name">{{ superChat.username }}</span>
					<span class="sc-price">¥{{ superChat.price }}</span>
					<span class="sc-countdown">{{ remaining }}s</span>
				</div>
				<div class="sc-message">{{ superChat.message }}</div>
			</div>
		</div>
	</div>
</template>

<style scoped>
.sc-banner {
	position: relative;
	z-index: 900;
	flex-shrink: 0;
	margin: 4px 8px;
	border-radius: 10px;
	overflow: hidden;
	background: linear-gradient(135deg, rgba(0, 200, 255, 0.18), rgba(255, 180, 60, 0.15));
	border: 1px solid rgba(255, 200, 60, 0.35);
	box-shadow: 0 4px 16px rgba(0, 160, 220, 0.15);
	animation: scSlideIn 0.3s ease;
}

.sc-progress {
	position: absolute;
	top: 0;
	left: 0;
	height: 3px;
	background: linear-gradient(90deg, #ffcc33, #ff6b6b);
	border-radius: 0 2px 2px 0;
	transition: width 0.5s linear;
}

.sc-body {
	display: flex;
	align-items: center;
	gap: 10px;
	padding: 10px 12px;
}

.sc-avatar {
	width: 36px;
	height: 36px;
	border-radius: 50%;
	object-fit: cover;
	border: 1px solid rgba(255, 255, 255, 0.25);
	flex-shrink: 0;
}

.sc-info {
	flex: 1;
	min-width: 0;
	display: flex;
	flex-direction: column;
	gap: 4px;
}

.sc-header {
	display: flex;
	align-items: center;
	gap: 6px;
	flex-wrap: wrap;
	font-size: 0.85rem;
}

.sc-medal {
	color: var(--gift-medal-text);
}

.sc-name {
	color: var(--name-text);
	font-weight: 600;
}

.sc-price {
	color: #ffcc33;
	font-weight: 700;
	font-size: 0.9rem;
}

.sc-countdown {
	margin-left: auto;
	color: var(--text-muted);
	font-size: 0.8rem;
	font-variant-numeric: tabular-nums;
}

.sc-message {
	color: var(--text-primary);
	font-size: 0.92rem;
	line-height: 1.5;
	word-break: break-word;
}

@keyframes scSlideIn {
	from {
		opacity: 0;
		transform: translateY(-10px);
	}
	to {
		opacity: 1;
		transform: translateY(0);
	}
}
</style>
