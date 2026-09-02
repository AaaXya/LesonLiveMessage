<script setup>
import { computed, onMounted, ref } from 'vue'
import { FEATURE_KEYS, FEATURE_LABELS, OPEN_MODE_OPTIONS } from '../constants'
import { useSettings } from '../composables/useSettings'
import { frontendConfig } from '../composables/useTheme'
import { setWindowSize } from '../api/bridge'

const visible = ref(false)
const {
	status,
	roomId,
	roomFixed,
	theme,
	windowSize,
	features,
	themeOptions,
	windowSizeOptions,
	filterWords,
	save,
} = useSettings(visible)

const newFilter = ref('')

// d-select 的 options 需要 { name, value } 格式
const themeSelectOptions = computed(() =>
	themeOptions.value.map((opt) => ({ name: opt.label, value: opt.value })),
)
const openModeSelectOptions = OPEN_MODE_OPTIONS.map((opt) => ({
	name: opt.label,
	value: opt.value,
}))

// 复选框类功能项（open_mode 是下拉选择，单独处理）
const checkboxKeys = computed(() => FEATURE_KEYS.filter((k) => k !== 'open_mode'))

function setFeature(key, checked) {
	features.value[key] = checked
}

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

async function handleWindowSizeChange(value) {
	const res = await setWindowSize(value)
	status.value = res?.ok
		? '窗口大小已调整，保存后下次启动自动使用'
		: res?.error || '调整窗口大小失败'
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
				<d-editable-select
					v-model="roomId"
					:options="roomOptions"
					:disabled="roomFixed"
					placeholder="选择或输入直播间 ID"
				/>
			</label>
			<div class="settings-grid">
				<label>主题模式<d-select v-model="theme" :options="themeSelectOptions" /></label>
			</div>
			<div class="settings-grid">
				<label
					>运行模式<d-select
						v-model="features.open_mode"
						:options="openModeSelectOptions"
				/></label>
			</div>
			<div class="section-label">窗口大小</div>
			<div class="window-size">
				<d-radio-group
					v-model="windowSize"
					direction="row"
					@change="handleWindowSizeChange"
				>
					<d-radio v-for="opt in windowSizeOptions" :key="opt.value" :value="opt.value">
						{{ opt.label }}
					</d-radio>
				</d-radio-group>
				<span class="window-size-hint">选择后立即生效，保存后下次启动自动使用</span>
			</div>
			<div class="section-label">功能开关</div>
			<div class="checks">
				<d-checkbox
					v-for="key in checkboxKeys"
					:key="key"
					:model-value="Boolean(features[key])"
					@update:model-value="setFeature(key, $event)"
				>
					{{ FEATURE_LABELS[key] }}
				</d-checkbox>
			</div>

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
	display: flex;
	flex-direction: column;
	gap: 6px;
	color: var(--text-muted);
	font-size: 13px;
}
.settings-grid {
	display: grid;
	grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
	gap: 14px;
}
.settings-grid label {
	min-width: 0;
}
:deep(.devui-editable-select) {
	width: 100%;
	min-width: 0;
}
.window-size {
	display: grid;
	gap: 6px;
}
.window-size-hint {
	font-size: 12px;
	color: var(--text-muted);
}
:deep(.devui-select) {
	width: 100%;
	min-width: 0;
}
.section-label {
	font-weight: 650;
}
.checks {
	display: grid;
	grid-template-columns: repeat(2, minmax(0, 1fr));
	gap: 10px;
}
.checks :deep(.devui-checkbox) {
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
