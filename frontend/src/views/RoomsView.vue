<script setup>
import { onMounted, onUnmounted, ref } from 'vue'
import { getRoomsStatus, startRoomListen, stopRoomListen } from '../api/bridge'
import DanmuList from '../components/DanmuList.vue'

const rooms = ref([])
const notice = ref('')
const togglingIds = ref(new Set())
const selectedRoom = ref(null)
let timer = null
async function refresh() {
	try {
		const res = await getRoomsStatus()
		if (res?.ok) {
			rooms.value = res.rooms || []
			// 同步更新 selectedRoom 的数据
			if (selectedRoom.value) {
				selectedRoom.value = rooms.value.find(
					(r) => r.room_id === selectedRoom.value.room_id,
				)
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

function handleBack() {
	selectedRoom.value = null
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
				<DanmuList />
			</div>
		</div>

		<!-- 房间列表视图 -->
		<div v-else class="list-view">
			<p v-if="notice" class="notice">{{ notice }}</p>
			<div v-if="rooms.length" class="room-grid">
				<d-card v-for="room in rooms" :key="room.room_id" class="room-card">
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
									<b>{{ room.timed_danmu_count }}</b
									><span>定时任务</span>
								</div>
							</div>
							<p v-if="room.last_error" class="room-error">{{ room.last_error }}</p>
							<div class="room-actions">
								<span class="muted"
									>QQ {{ room.qq_notification ? '已开启' : '未开启' }}</span
								><d-button
									:color="room.listening ? 'secondary' : 'primary'"
									:variant="room.listening ? 'outline' : 'solid'"
									:disabled="togglingIds.has(room.room_id)"
									@click="toggleListen(room)"
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
</style>
