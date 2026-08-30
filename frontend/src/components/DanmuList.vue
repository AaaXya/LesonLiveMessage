<script setup>
import { computed, ref, watch, nextTick, onMounted, onUnmounted } from 'vue'
import { getDanmuItems } from '../stores/danmu'
import DanmuItem from './DanmuItem.vue'
import GiftItem from './GiftItem.vue'
import GuardItem from './GuardItem.vue'
import SuperChatItem from './SuperChatItem.vue'

const props = defineProps({
	roomId: {
		type: [String, Number],
		default: '',
	},
})

// 按房间读取弹幕列表（无 roomId 时使用合并默认桶）
const items = computed(() => getDanmuItems(props.roomId))

const listRef = ref(null)
const showScrollButton = ref(false)
let userScrolled = false
let resumeTimer = null
const RESUME_DELAY = 3000

function isAtBottom() {
	const list = listRef.value
	if (!list) return true
	return list.scrollTop + list.clientHeight >= list.scrollHeight - 10
}

function checkScrollBottom() {
	showScrollButton.value = !isAtBottom()
}

function scrollToBottom() {
	const list = listRef.value
	if (!list) return
	list.scrollTop = list.scrollHeight
	showScrollButton.value = false
	userScrolled = false
	if (resumeTimer) {
		clearTimeout(resumeTimer)
		resumeTimer = null
	}
}

function onUserScroll() {
	if (isAtBottom()) {
		userScrolled = false
		return
	}
	// 用户上滚：标记暂停，3 秒后恢复自动滚动
	if (!userScrolled) {
		userScrolled = true
		if (resumeTimer) clearTimeout(resumeTimer)
		resumeTimer = setTimeout(() => {
			userScrolled = false
		}, RESUME_DELAY)
	}
	checkScrollBottom()
}

watch(
	items,
	async () => {
		await nextTick()
		if (!userScrolled) {
			scrollToBottom()
		}
		checkScrollBottom()
	},
	{ deep: true },
)

onMounted(async () => {
	await nextTick()
	scrollToBottom()
})

onUnmounted(() => {
	if (resumeTimer) clearTimeout(resumeTimer)
})

defineExpose({ scrollToBottom })
</script>

<template>
	<SuperChatItem :room-id="String(roomId || '') || undefined" />
	<div ref="listRef" class="danmu-list" @scroll="onUserScroll">
		<template v-for="(item, index) in items" :key="index">
			<DanmuItem v-if="item.type === 'danmu'" :data="item" />
			<GiftItem v-else-if="item.type === 'gift'" :data="item" />
			<GuardItem v-else-if="item.type === 'GUARD_BUY'" :data="item" />
		</template>
	</div>

	<button
		v-show="showScrollButton"
		class="scroll-btn"
		title="回到底部"
		type="button"
		@click="scrollToBottom"
	>
		↓
	</button>
</template>

<style scoped>
.danmu-list {
	margin-bottom: 0;
	flex: 1;
	overflow-y: auto;
	padding: 16px 5px 58px 4px;
	scrollbar-width: thin;
	scrollbar-color: var(--scrollbar-thumb) transparent;
}

.danmu-list::-webkit-scrollbar {
	width: 6px;
}

.danmu-list::-webkit-scrollbar-track {
	background: transparent;
}

.danmu-list::-webkit-scrollbar-thumb {
	background-color: var(--scrollbar-thumb);
	border-radius: 6px;
}

.scroll-btn {
	position: fixed;
	bottom: 64px;
	right: 12px;
	z-index: 1000;
	width: 34px;
	height: 34px;
	display: inline-flex;
	align-items: center;
	justify-content: center;
	border: 1px solid var(--border-strong);
	border-radius: 50%;
	background: var(--button-bg);
	color: var(--text-primary);
	cursor: pointer;
	font-size: 0.95rem;
	transition: background 0.2s ease;
}

.scroll-btn:hover {
	background: var(--surface-hover);
}
</style>
