<script setup>
import { onMounted, ref, watch } from 'vue'
import { getRoomsStatus, saveFrontendConfig } from '../api/bridge'
import { frontendConfig, getCurrentRoomBinding, loadFrontendConfig } from '../composables/useTheme'

const autoSpeak = ref(createDefaultAutoSpeak())
const status = ref('')
const selectedRoomId = ref('')
const rooms = ref([])

function createDefaultAutoSpeak() {
	return {
		enabled: false,
		cycle_list: [],
		duration_list: [],
		keyword_replies: [],
		quick_sends: [],
	}
}

// 规范化列表行：数字字段取默认值，文本字段转字符串
function normalizeRows(items, keys, defaults = {}) {
	return Array.isArray(items)
		? items
				.filter((it) => it && typeof it === 'object')
				.map((it) => {
					const row = { enabled: it.enabled !== false }
					keys.forEach((k) => {
						row[k] = k in defaults ? Number(it[k]) || defaults[k] : String(it[k] ?? '')
					})
					return row
				})
		: []
}

function hydrateFromConfig(config) {
	const currentBinding = getCurrentRoomBinding(config, selectedRoomId.value)
	const rawAuto = currentBinding.auto_speak || config.auto_speak || {}
	autoSpeak.value = {
		enabled: Boolean(rawAuto.enabled),
		cycle_list: normalizeRows(rawAuto.cycle_list, ['interval', 'text'], {
			interval: 300,
		}),
		duration_list: normalizeRows(rawAuto.duration_list, ['duration', 'text'], {
			duration: 3600,
		}),
		keyword_replies: normalizeRows(rawAuto.keyword_replies, ['keyword', 'reply']),
		quick_sends: normalizeRows(rawAuto.quick_sends, ['text']),
	}
}

function addRow(listKey, defaults) {
	autoSpeak.value[listKey].push({ ...defaults, enabled: true })
}

function removeRow(listKey, index) {
	autoSpeak.value[listKey].splice(index, 1)
}

async function save() {
	status.value = '保存中...'
	try {
		const roomId = Number(selectedRoomId.value)
		const result = await saveFrontendConfig({
			room_ids: Number.isFinite(roomId) ? [roomId] : [],
			LESSONROOMID: Number.isFinite(roomId) ? roomId : undefined,
			auto_speak: {
				enabled: Boolean(autoSpeak.value.enabled),
				cycle_list: autoSpeak.value.cycle_list
					.filter((it) => String(it.text || '').trim())
					.map((it) => ({
						interval: Number(it.interval) || 300,
						text: String(it.text).trim(),
						enabled: it.enabled !== false,
					})),
				duration_list: autoSpeak.value.duration_list
					.filter((it) => String(it.text || '').trim())
					.map((it) => ({
						duration: Number(it.duration) || 3600,
						text: String(it.text).trim(),
						enabled: it.enabled !== false,
					})),
				keyword_replies: autoSpeak.value.keyword_replies
					.filter(
						(it) => String(it.keyword || '').trim() && String(it.reply || '').trim(),
					)
					.map((it) => ({
						keyword: String(it.keyword).trim(),
						reply: String(it.reply).trim(),
						enabled: it.enabled !== false,
					})),
				quick_sends: autoSpeak.value.quick_sends
					.filter((it) => String(it.text || '').trim())
					.map((it) => ({
						text: String(it.text).trim(),
						enabled: it.enabled !== false,
					})),
			},
		})
		if (result?.ok) {
			status.value = '已保存，下次开播时生效'
			// 刷新共享配置，让「直播间」页的快捷弹幕立即读取最新列表
			frontendConfig.value = result.frontendConfig || frontendConfig.value
		} else {
			status.value = '保存失败：' + (result?.error || '未知错误')
		}
	} catch (error) {
		console.error('保存自动发言配置失败：', error)
		status.value = '保存失败：后端调用异常'
	}
}

async function loadRooms() {
	const res = await getRoomsStatus()
	if (!res?.ok) return
	rooms.value = res.rooms || []
	if (!selectedRoomId.value) {
		selectedRoomId.value = String(
			frontendConfig.value?.config?.LESSONROOMID || rooms.value[0]?.room_id || '',
		)
	}
	if (!rooms.value.some((room) => String(room.room_id) === String(selectedRoomId.value))) {
		selectedRoomId.value = rooms.value[0]?.room_id ? String(rooms.value[0].room_id) : ''
	}
	hydrateFromConfig(frontendConfig.value?.config || {})
}

watch(selectedRoomId, () => {
	if (!frontendConfig.value) return
	hydrateFromConfig(frontendConfig.value.config || {})
})

onMounted(async () => {
	if (!frontendConfig.value) {
		await loadFrontendConfig()
	}
	await loadRooms()
})
</script>

<template>
	<d-card title="自动发言" class="auto-speak-card">
		<div class="form">
			<div class="toolbar-row">
				<label class="room-select-wrap">
					<span class="section-label">当前房间</span>
					<select v-model="selectedRoomId" class="room-select">
						<option
							v-for="room in rooms"
							:key="room.room_id"
							:value="String(room.room_id)"
						>
							{{ room.title }}（{{ room.room_id }}）
						</option>
					</select>
				</label>
			</div>
			<div class="section-label auto-speak-title">
				autoSpeak
				<d-switch v-model="autoSpeak.enabled" />
			</div>
			<p class="auto-speak-hint">
				开启后按下列规则自动发送弹幕；如需直播开始通知，可在“直播时长触发”中新增 0
				分钟规则（保存后，下次开播时生效）
			</p>

			<div class="auto-speak-group">
				<div class="auto-speak-group-title">
					定时循环发言
					<d-button
						variant="text"
						size="sm"
						@click="addRow('cycle_list', { interval: 300, text: '' })"
						>+ 添加</d-button
					>
				</div>
				<div
					v-for="(item, i) in autoSpeak.cycle_list"
					:key="'c' + i"
					class="auto-speak-row"
				>
					<d-checkbox v-model="item.enabled" />
					<d-input-number
						v-model="item.interval"
						:min="1"
						:max="86400"
						:step="60"
						class="num"
					/>
					<span class="unit">秒</span>
					<d-input v-model="item.text" placeholder="循环发送的弹幕内容" maxlength="50" />
					<d-button
						variant="text"
						size="sm"
						class="row-del"
						@click="removeRow('cycle_list', i)"
						>删除</d-button
					>
				</div>
				<div v-if="autoSpeak.cycle_list.length === 0" class="auto-speak-empty">
					暂无，点击「+ 添加」创建
				</div>
			</div>

			<div class="auto-speak-group">
				<div class="auto-speak-group-title">
					直播时长触发
					<d-button
						variant="text"
						size="sm"
						@click="addRow('duration_list', { duration: 3600, text: '' })"
						>+ 添加</d-button
					>
				</div>
				<div
					v-for="(item, i) in autoSpeak.duration_list"
					:key="'d' + i"
					class="auto-speak-row"
				>
					<d-checkbox v-model="item.enabled" />
					<d-input-number
						v-model="item.duration"
						:min="1"
						:max="1440"
						:step="60"
						class="num"
					/>
					<span class="unit">分钟</span>
					<d-input
						v-model="item.text"
						placeholder="达到该时长后发送的弹幕"
						maxlength="50"
					/>
					<d-button
						variant="text"
						size="sm"
						class="row-del"
						@click="removeRow('duration_list', i)"
						>删除</d-button
					>
				</div>
				<div v-if="autoSpeak.duration_list.length === 0" class="auto-speak-empty">
					暂无，点击「+ 添加」创建
				</div>
			</div>

			<div class="auto-speak-group">
				<div class="auto-speak-group-title">
					关键词自动回复
					<d-button
						variant="text"
						size="sm"
						@click="addRow('keyword_replies', { keyword: '', reply: '' })"
						>+ 添加</d-button
					>
				</div>
				<div
					v-for="(item, i) in autoSpeak.keyword_replies"
					:key="'k' + i"
					class="auto-speak-row"
				>
					<d-checkbox v-model="item.enabled" />
					<d-input
						v-model="item.keyword"
						placeholder="命中关键词"
						maxlength="20"
						class="keyword"
					/>
					<d-input v-model="item.reply" placeholder="自动回复内容" maxlength="50" />
					<d-button
						variant="text"
						size="sm"
						class="row-del"
						@click="removeRow('keyword_replies', i)"
						>删除</d-button
					>
				</div>
				<div v-if="autoSpeak.keyword_replies.length === 0" class="auto-speak-empty">
					暂无，点击「+ 添加」创建
				</div>
			</div>

			<div class="auto-speak-group">
				<div class="auto-speak-group-title">
					常用弹幕快捷发送
					<d-button variant="text" size="sm" @click="addRow('quick_sends', { text: '' })"
						>+ 添加</d-button
					>
				</div>
				<div
					v-for="(item, i) in autoSpeak.quick_sends"
					:key="'q' + i"
					class="auto-speak-row"
				>
					<d-checkbox v-model="item.enabled" />
					<d-input
						v-model="item.text"
						placeholder="点击即发送的常用弹幕"
						maxlength="50"
					/>
					<d-button
						variant="text"
						size="sm"
						class="row-del"
						@click="removeRow('quick_sends', i)"
						>删除</d-button
					>
				</div>
				<div v-if="autoSpeak.quick_sends.length === 0" class="auto-speak-empty">
					暂无，点击「+ 添加」创建
				</div>
			</div>

			<p v-if="status" class="notice">{{ status }}</p>
			<d-button class="save" variant="solid" color="primary" @click="save">保存设置</d-button>
		</div>
	</d-card>
</template>

<style scoped>
.auto-speak-card {
	max-width: 780px;
}
.form {
	display: grid;
	gap: 16px;
}
.toolbar-row {
	display: flex;
	justify-content: flex-start;
}
.room-select-wrap {
	display: grid;
	gap: 6px;
	width: min(100%, 360px);
}
.room-select {
	width: 100%;
	padding: 8px 10px;
	border: 1px solid var(--border);
	border-radius: 8px;
	background: var(--surface);
	color: var(--text-primary);
}
.section-label {
	font-weight: 650;
	color: var(--text-primary);
}
.auto-speak-title {
	display: flex;
	align-items: center;
	justify-content: space-between;
}
.auto-speak-hint {
	margin: 0;
	font-size: 12px;
	color: var(--text-muted);
}
.auto-speak-group {
	display: grid;
	gap: 8px;
	padding: 12px;
	border: 1px solid var(--border);
	border-radius: 10px;
	background: var(--surface-soft);
}
.auto-speak-group-title {
	display: flex;
	align-items: center;
	justify-content: space-between;
	font-weight: 600;
	color: var(--text-primary);
}
.auto-speak-row {
	display: flex;
	align-items: center;
	gap: 8px;
}
.auto-speak-row :deep(.devui-input-number) {
	width: 120px;
	flex-shrink: 0;
}
.auto-speak-row :deep(.devui-input) {
	flex: 1;
	min-width: 0;
}
.auto-speak-row .keyword {
	flex: 0 0 140px;
	width: 140px;
}
.auto-speak-row .unit {
	flex-shrink: 0;
	font-size: 12px;
	color: var(--text-muted);
}
.auto-speak-row .row-del {
	flex-shrink: 0;
}
.auto-speak-empty {
	font-size: 12px;
	color: var(--text-muted);
}
.notice {
	margin: 0;
	padding: 8px 12px;
	border-radius: 8px;
	background: var(--surface-hover);
	color: var(--text-primary);
	font-size: 13px;
}
</style>
