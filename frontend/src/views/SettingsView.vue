<script setup>
import { computed, onMounted, ref } from 'vue'
import { FEATURE_KEYS, FEATURE_LABELS, OPEN_MODE_OPTIONS } from '../constants'
import { useSettings } from '../composables/useSettings'
import { frontendConfig } from '../composables/useTheme'
import {
	THEME_PALETTE_OPTIONS,
	applyThemePalette,
	getSavedThemePalette,
} from '../composables/useThemePalette'

const visible = ref(false)
const themePalette = ref(getSavedThemePalette())
const {
	status,
	roomId,
	roomFixed,
	groupId,
	theme,
	features,
	enableQqNotification,
	themeOptions,
	liveStartEnabled,
	filterWords,
	save,
} = useSettings(visible)

const newFilter = ref('')

const roomOptions = computed(() => {
	const ids = new Set()
	const config = frontendConfig.value?.config || {}
	for (const id of config.room_ids || []) {
		if (String(id).trim()) ids.add(String(id).trim())
	}
	for (const key of Object.keys(config.room_bindings || {})) {
		if (String(key).trim()) ids.add(String(key).trim())
	}
	if (String(roomId.value || '').trim()) {
		ids.add(String(roomId.value).trim())
	}
	return [...ids]
		.filter((id) => id && /^\d+$/.test(id))
		.map((id) => ({ value: id, label: `房间 ${id}` }))
})

function addFilter() {
	const word = newFilter.value.trim()
	if (word && !filterWords.value.includes(word)) filterWords.value.push(word)
	newFilter.value = ''
}

function handleThemePaletteChange(palette) {
	applyThemePalette(palette)
}

onMounted(() => {
	visible.value = true
})
</script>
<template>
	<d-card title="应用设置" class="settings-card">
		<div class="form">
			<label>
				直播间 ID
				<div class="room-picker">
					<select v-model="roomId" class="control" :disabled="roomFixed">
						<option value="">请选择房间号</option>
						<option v-for="item in roomOptions" :key="item.value" :value="item.value">
							{{ item.label }}
						</option>
					</select>
					<input
						v-model="roomId"
						class="control"
						:disabled="roomFixed"
						placeholder="手动输入直播间 ID"
					/>
				</div>
			</label>
			<div class="grid">
				<label
					>主题模式<select v-model="theme" class="control">
						<option v-for="item in themeOptions" :key="item.value" :value="item.value">
							{{ item.label }}
						</option>
					</select></label
				>
				<label
					>主题色<select
						v-model="themePalette"
						class="control"
						@change="handleThemePaletteChange"
					>
						<option
							v-for="item in THEME_PALETTE_OPTIONS"
							:key="item.value"
							:value="item.value"
						>
							{{ item.label }}
						</option>
					</select></label
				>
			</div>
			<div class="grid">
				<label
					>运行模式<select v-model="features.open_mode" class="control">
						<option
							v-for="item in OPEN_MODE_OPTIONS"
							:key="item.value"
							:value="item.value"
						>
							{{ item.label }}
						</option>
					</select></label
				>
			</div>
			<div class="section-label">功能开关</div>
			<div class="checks">
				<label
					v-for="key in FEATURE_KEYS.filter(
						(k) => !['open_mode', 'enable_live_start'].includes(k),
					)"
					:key="key"
					><input v-model="features[key]" type="checkbox" />
					{{ FEATURE_LABELS[key] }}</label
				>
				<label
					><input v-model="liveStartEnabled" type="checkbox" />
					{{ FEATURE_LABELS.enable_live_start }}</label
				>
				<label
					><input
						v-model="enableQqNotification"
						type="checkbox"
						:disabled="!liveStartEnabled"
					/>
					推送到 QQ 群</label
				>
			</div>
			<label
				>QQ 群号<input
					v-model="groupId"
					class="control"
					:disabled="!liveStartEnabled || !enableQqNotification"
			/></label>
			<div class="section-label">弹幕过滤词</div>
			<div class="filter">
				<input
					v-model="newFilter"
					class="control"
					placeholder="输入后回车添加"
					@keyup.enter="addFilter"
				/>
				<d-button variant="outline" @click="addFilter">添加</d-button>
			</div>
			<div class="words">
				<span v-for="(word, i) in filterWords" :key="word" class="badge"
					>{{ word }} <button @click="filterWords.splice(i, 1)">×</button></span
				>
			</div>
			<p v-if="status" class="notice">{{ status }}</p>
			<d-button class="save" variant="solid" color="primary" @click="save">保存设置</d-button>
		</div>
	</d-card>
</template>
<style scoped>
.settings-card {
	max-width: 780px;
}
.form {
	display: grid;
	gap: 16px;
}
.form label {
	display: grid;
	gap: 6px;
	color: var(--text-muted);
	font-size: 13px;
}
.room-picker {
	display: grid;
	grid-template-columns: minmax(170px, 1fr) minmax(180px, 1.2fr);
	gap: 8px;
}
.grid {
	display: grid;
	grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
	gap: 14px;
}
.section-label {
	font-weight: 650;
}
.checks {
	display: grid;
	grid-template-columns: repeat(2, minmax(0, 1fr));
	gap: 10px;
}
.checks label {
	display: block;
	color: var(--text-primary);
}
.filter {
	display: flex;
	gap: 8px;
}
.filter input {
	flex: 1;
}
.words {
	display: flex;
	flex-wrap: wrap;
	gap: 6px;
}
.words button {
	border: 0;
	background: transparent;
	color: inherit;
	cursor: pointer;
}
.save {
	justify-self: start;
}
</style>
