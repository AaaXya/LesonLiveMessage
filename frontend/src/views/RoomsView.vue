<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import {
	getRoomsStatus,
	startRoomListen,
	stopRoomListen,
	sendDanmu,
	saveFrontendConfig,
} from '../api/bridge'
import { clearRoom } from '../stores/danmu'
import { frontendConfig, getCurrentRoomBinding } from '../composables/useTheme'
import DanmuList from '../components/DanmuList.vue'

const rooms = ref([])
const notice = ref('')
const togglingIds = ref(new Set())
const notificationTogglingIds = ref(new Set())
const selectedRoom = ref(null)
const quickStatus = ref('')
let timer = null

// 常用弹幕快捷发送：按当前选中房间读取自动发言配置中的 quick_sends
const quickSends = computed(() => {
	const config = frontendConfig.value?.config || {}
	const roomId = selectedRoom.value?.room_id || config.LESSONROOMID
	const binding = getCurrentRoomBinding(config, roomId)
	const cfg = binding.auto_speak || config.auto_speak || {}
	if (!cfg?.enabled) return []
	return (cfg.quick_sends || []).filter((q) => q.enabled !== false && String(q.text || '').trim())
})

async function quickSend(text) {
	if (!selectedRoom.value || !selectedRoom.value.listening) {
		quickStatus.value = '请先开始监听该房间，再发送快捷弹幕'
		return
	}
	quickStatus.value = ''
	try {
		const res = await sendDanmu(text, String(selectedRoom.value.room_id))
		quickStatus.value = res?.ok ? `已发送：${text}` : res?.error || '发送失败'
	} catch {
		quickStatus.value = '发送失败'
	}
}
async function refresh() {
	try {
		const res = await getRoomsStatus()
		if (res?.ok) {
			rooms.value = res.rooms || []
			// 同步更新 selectedRoom 的数据（找不到时保留旧对象，避免视图闪回列表）
			if (selectedRoom.value) {
				const found = rooms.value.find((r) => r.room_id === selectedRoom.value.room_id)
				if (found) selectedRoom.value = found
			}
		}
	} catch {
		notice.value = '无法获取直播间状态'
	}
}
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
async function toggleListen(room) {
	if (togglingIds.value.has(room.room_id)) return
	togglingIds.value = new Set([...togglingIds.value, room.room_id])
	try {
		if (room.listening) {
			// 停止监听
			const res = await stopRoomListen(room.room_id)
			if (!res?.ok) notice.value = res?.error || '操作失败'
			await refresh()
			// 清理该房间的弹幕缓存，重新监听时从空白开始
			clearRoom(room.room_id)
			// 如果停止的是当前选中的房间，返回列表
			if (selectedRoom.value?.room_id === room.room_id) {
				selectedRoom.value = null
			}
		} else {
			// 开始监听
			const res = await startRoomListen(room.room_id)
			if (!res?.ok) {
				notice.value = res?.error || '操作失败'
			} else {
				// 选中房间，显示弹幕流
				await refresh()
				selectedRoom.value = rooms.value.find((r) => r.room_id === room.room_id)
			}
		}
	} catch {
		notice.value = '操作失败，请检查后端日志'
	} finally {
		const next = new Set(togglingIds.value)
		next.delete(room.room_id)
		togglingIds.value = next
	}
}

async function toggleLocalNotification(room) {
	if (notificationTogglingIds.value.has(room.room_id)) return
	notificationTogglingIds.value = new Set([...notificationTogglingIds.value, room.room_id])
	try {
		const enabled = Boolean(room.local_notification)
		const res = await saveFrontendConfig({
			room_ids: [Number(room.room_id)],
			LESSONROOMID: Number(room.room_id),
			enable_local_notification: enabled,
		})
		if (!res?.ok) {
			notice.value = res?.error || '设置失败'
			return
		}
		await refresh()
		notice.value = ''
	} catch {
		notice.value = '设置失败，请检查后端日志'
	} finally {
		const next = new Set(notificationTogglingIds.value)
		next.delete(room.room_id)
		notificationTogglingIds.value = next
	}
}

function handleBack() {
	selectedRoom.value = null
}

function openStream(room) {
	// 点击房间卡片进入弹幕流视图（未监听时显示提示）
	selectedRoom.value = room
}

function onCoverError(room) {
	// 加载失败时清空封面显示占位图；下次刷新后端返回新封面时自动重试
	room.cover = ''
}
onMounted(() => {
	refresh()
	timer = setInterval(refresh, 3000)
})
onUnmounted(() => clearInterval(timer))
</script>

<template>
	<div class="rooms-view">
		<!-- 弹幕流视图 -->
		<div v-if="selectedRoom" class="stream-view">
			<div class="page-header">
				<div class="header-left">
					<button class="back-btn" @click="handleBack" title="返回">←</button>
					<div class="room-info">
						<h1>{{ selectedRoom.title }}</h1>
						<span class="room-id">房间号 {{ selectedRoom.room_id }}</span>
					</div>
				</div>
				<span class="badge" :class="liveClass(selectedRoom)">
					{{ liveText(selectedRoom) }}
				</span>
			</div>
			<div class="stream-container">
				<DanmuList v-if="selectedRoom.listening" :room-id="selectedRoom.room_id" />
				<div v-else class="stream-empty">
					<div class="stream-empty-icon">📡</div>
					<div>该房间未在监听中，暂无弹幕流</div>
					<div class="stream-empty-hint">返回列表点击「开始监听」</div>
				</div>
			</div>
			<div v-if="selectedRoom && quickSends.length" class="quick-bar">
				<span class="quick-bar-label">快捷弹幕</span>
				<d-button
					v-for="(q, i) in quickSends"
					:key="'q' + i"
					variant="outline"
					size="sm"
					:disabled="!selectedRoom.listening"
					@click="quickSend(String(q.text).trim())"
					>{{ q.text }}</d-button
				>
				<span v-if="quickStatus" class="quick-status">{{ quickStatus }}</span>
			</div>
		</div>

		<!-- 房间列表视图 -->
		<div v-else class="list-view">
			<p v-if="notice" class="notice">{{ notice }}</p>
			<div v-if="rooms.length" class="room-grid">
				<d-card
					v-for="room in rooms"
					:key="room.room_id"
					class="room-card clickable"
					@click="openStream(room)"
				>
					<template #default>
						<div v-if="room.cover" class="room-cover-wrapper">
							<img
								class="room-cover"
								:src="room.cover"
								:alt="room.title"
								loading="lazy"
								@error="onCoverError(room)"
							/>
						</div>
						<div v-else class="room-cover-placeholder">
							<span class="placeholder-icon">🖼️</span>
						</div>
						<div class="room-body">
							<div class="room-title-row">
								<div>
									<h2>{{ room.title }}</h2>
									<span>房间号 {{ room.room_id }}</span>
								</div>
								<span class="badge" :class="liveClass(room)">{{
									liveText(room)
								}}</span>
							</div>
							<div class="stats">
								<div>
									<b>{{ room.danmu_count }}</b
									><span>弹幕</span>
								</div>
								<div>
									<b>{{ room.is_live ? '开播' : '离线' }}</b
									><span>当前状态</span>
								</div>
								<div>
									<b>{{ room.auto_task_count }}</b
									><span>自动任务</span>
								</div>
							</div>
							<p v-if="room.last_error" class="room-error">{{ room.last_error }}</p>
							<div class="room-actions">
								<div class="notification-toggle" @click.stop>
									<span class="muted">本地通知</span>
									<d-switch
										v-model="room.local_notification"
										:disabled="notificationTogglingIds.has(room.room_id)"
										@change="toggleLocalNotification(room)"
									/>
								</div>
								<d-button
									:color="room.listening ? 'secondary' : 'primary'"
									:variant="room.listening ? 'outline' : 'solid'"
									:disabled="togglingIds.has(room.room_id)"
									@click.stop="toggleListen(room)"
									>{{ room.listening ? '停止监听' : '开始监听' }}</d-button
								>
							</div>
						</div>
					</template>
				</d-card>
			</div>
			<d-card v-else class="empty">暂无绑定直播间，请在设置中添加。</d-card>
		</div>
	</div>
</template>

<style scoped>
.rooms-view {
	display: flex;
	flex-direction: column;
	height: 100%;
}

/* 列表视图 */
.list-view {
	flex: 1;
	overflow: auto;
}

.notice {
	padding: 12px 20px;
	margin: 0;
	background: var(--color-warn-bg);
	color: var(--color-warn-text);
	font-size: 14px;
	border-bottom: 1px solid var(--border-color);
}

.room-grid {
	display: grid;
	grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
	gap: 14px;
	padding: 16px;
}

.room-card {
	overflow: hidden;
}

.room-card.clickable {
	cursor: pointer;
	transition:
		border-color 0.2s ease,
		box-shadow 0.2s ease;
}

.room-card.clickable:hover {
	border-color: var(--accent);
	box-shadow: 0 6px 18px var(--shadow);
}

.room-cover-wrapper {
	display: block;
	width: 100%;
	height: 126px;
	overflow: hidden;
	background: var(--bg-elevated);
}

.room-cover {
	display: block;
	width: 100%;
	height: 100%;
	object-fit: cover;
}

.room-cover-placeholder {
	display: flex;
	align-items: center;
	justify-content: center;
	width: 100%;
	height: 126px;
	background: var(--bg-elevated);
	color: var(--text-muted);
	font-size: 48px;
}

.placeholder-icon {
	opacity: 0.5;
}

.room-body {
	padding: 15px;
}

.room-title-row {
	display: flex;
	justify-content: space-between;
	gap: 8px;
}

.room-title-row h2 {
	margin: 0;
	font-size: 15px;
}

.room-title-row span,
.muted {
	color: var(--text-muted);
	font-size: 12px;
}

.stats {
	display: grid;
	grid-template-columns: repeat(3, 1fr);
	margin: 16px 0;
	padding: 10px 0;
	border-block: 1px solid var(--border);
}

.stats div {
	display: grid;
	gap: 2px;
}

.stats div + div {
	padding-left: 10px;
	border-left: 1px solid var(--border);
}

.stats b {
	font-size: 15px;
}

.stats span {
	color: var(--text-muted);
	font-size: 12px;
}

.room-actions {
	display: flex;
	align-items: center;
	justify-content: space-between;
	gap: 10px;
}

.notification-toggle {
	display: inline-flex;
	align-items: center;
	gap: 8px;
}

.room-error {
	margin: 0 0 10px;
	color: var(--danger);
	font-size: 12px;
}

.empty {
	padding: 36px;
	text-align: center;
	color: var(--text-muted);
}

/* 弹幕流视图 */
.stream-view {
	display: flex;
	flex-direction: column;
	height: 100%;
}

.page-header {
	display: flex;
	justify-content: space-between;
	align-items: center;
	padding: 12px 20px;
	border-bottom: 1px solid var(--border-color);
	background: var(--bg-base);
	gap: 20px;
}

.header-left {
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
	flex-shrink: 0;
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

.badge {
	display: inline-block;
	padding: 4px 12px;
	border-radius: 4px;
	font-size: 12px;
	font-weight: 500;
	white-space: nowrap;
	flex-shrink: 0;
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

.stream-container {
	flex: 1;
	overflow: auto;
}

.stream-empty {
	display: flex;
	flex-direction: column;
	align-items: center;
	justify-content: center;
	gap: 8px;
	height: 100%;
	color: var(--text-muted);
	font-size: 14px;
	text-align: center;
}

.stream-empty-icon {
	font-size: 40px;
	opacity: 0.6;
}

.stream-empty-hint {
	font-size: 12px;
	opacity: 0.8;
}

.quick-bar {
	display: flex;
	flex-wrap: wrap;
	align-items: center;
	gap: 8px;
	padding: 10px 14px;
	border-top: 1px solid var(--border);
	background: var(--surface);
}
.quick-bar-label {
	flex-shrink: 0;
	font-size: 12px;
	color: var(--text-muted);
}
.quick-status {
	font-size: 12px;
	color: var(--text-muted);
}
</style>
