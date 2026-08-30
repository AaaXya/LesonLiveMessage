<script setup>
import { onMounted, onUnmounted, ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { getRoomsStatus, stopRoomListen } from '../api/bridge'
import DanmuList from '../components/DanmuList.vue'

const router = useRouter()
const route = useRoute()

const roomId = ref(null)
const room = ref(null)
const notice = ref('')
const isStopping = ref(false)
let statusTimer = null

async function loadRoomStatus() {
	try {
		const res = await getRoomsStatus()
		if (res?.ok) {
			const targetRoom = res.rooms?.find((r) => r.room_id === roomId.value)
			if (targetRoom) {
				room.value = targetRoom
			}
		}
	} catch {
		notice.value = '无法获取房间状态'
	}
}

async function handleStop() {
	if (isStopping.value) return
	isStopping.value = true
	try {
		const res = await stopRoomListen(roomId.value)
		if (!res?.ok) {
			notice.value = res?.error || '停止监听失败'
			isStopping.value = false
			return
		}
		// 停止监听成功，返回主页面
		router.back()
	} catch {
		notice.value = '操作失败，请检查后端日志'
		isStopping.value = false
	}
}

function goBack() {
	router.back()
}

onMounted(() => {
	roomId.value = parseInt(route.params.roomId)
	if (!roomId.value) {
		notice.value = '房间ID无效'
		return
	}
	loadRoomStatus()
	statusTimer = setInterval(loadRoomStatus, 3000)
})

onUnmounted(() => clearInterval(statusTimer))
</script>

<template>
	<div class="danmu-stream-view">
		<div class="header">
			<div class="header-content">
				<button class="back-btn" @click="goBack" title="返回">
					<span>←</span>
				</button>
				<div class="room-info">
					<h1 v-if="room">{{ room.title }}</h1>
					<span v-if="room" class="room-id">房间号 {{ room.room_id }}</span>
					<span v-else class="room-id">加载中...</span>
				</div>
				<div class="header-actions">
					<span v-if="room" class="badge" :class="liveClass(room)">
						{{ liveText(room) }}
					</span>
				</div>
			</div>
			<div class="header-actions-right">
				<d-button
					color="secondary"
					variant="outline"
					:disabled="isStopping"
					@click="handleStop"
				>
					{{ isStopping ? '停止中...' : '停止监听' }}
				</d-button>
			</div>
		</div>

		<p v-if="notice" class="notice">{{ notice }}</p>

		<div class="stream-container">
			<DanmuList />
		</div>
	</div>
</template>

<script>
function liveText(room) {
	return !room.listening
		? '未监听'
		: !room.connected
			? room.last_error
				? '重连中'
				: '连接中'
			: room.is_live
				? '直播中'
				: '未开播'
}

function liveClass(room) {
	return room.connected && room.is_live
		? 'success'
		: room.last_error
			? 'danger'
			: room.listening
				? 'warn'
				: ''
}
</script>

<style scoped>
.danmu-stream-view {
	display: flex;
	flex-direction: column;
	height: 100%;
}

.header {
	display: flex;
	justify-content: space-between;
	align-items: center;
	padding: 12px 20px;
	border-bottom: 1px solid var(--border-color);
	background: var(--bg-base);
	gap: 20px;
}

.header-content {
	display: flex;
	align-items: center;
	gap: 16px;
	flex: 1;
	min-width: 0;
}

.back-btn {
	display: flex;
	align-items: center;
	justify-content: center;
	width: 36px;
	height: 36px;
	border: none;
	background: var(--bg-elevated);
	border-radius: 6px;
	cursor: pointer;
	font-size: 18px;
	color: var(--text-primary);
	transition: background 0.2s;
}

.back-btn:hover {
	background: var(--bg-hover);
}

.back-btn:active {
	background: var(--bg-pressed);
}

.room-info {
	display: flex;
	flex-direction: column;
	gap: 4px;
	min-width: 0;
}

.room-info h1 {
	margin: 0;
	font-size: 18px;
	font-weight: 600;
	white-space: nowrap;
	overflow: hidden;
	text-overflow: ellipsis;
}

.room-id {
	font-size: 12px;
	color: var(--text-muted);
}

.header-actions {
	display: flex;
	align-items: center;
	gap: 12px;
}

.header-actions-right {
	display: flex;
	align-items: center;
	gap: 12px;
}

.badge {
	display: inline-block;
	padding: 4px 12px;
	border-radius: 4px;
	font-size: 12px;
	font-weight: 500;
	white-space: nowrap;
}

.badge.success {
	background: var(--color-success-bg);
	color: var(--color-success-text);
}

.badge.danger {
	background: var(--color-danger-bg);
	color: var(--color-danger-text);
}

.badge.warn {
	background: var(--color-warn-bg);
	color: var(--color-warn-text);
}

.notice {
	padding: 12px 20px;
	margin: 0;
	background: var(--color-warn-bg);
	color: var(--color-warn-text);
	font-size: 14px;
	border-bottom: 1px solid var(--border-color);
}

.stream-container {
	flex: 1;
	overflow: auto;
}
</style>
