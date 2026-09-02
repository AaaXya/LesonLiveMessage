<script setup>
import { toRef, computed, ref } from 'vue'
import { FEATURE_LABELS, OPEN_MODE_OPTIONS } from '../constants'
import { useSettings } from '../composables/useSettings'

const props = defineProps({
	visible: {
		type: Boolean,
		default: false,
	},
})

const emit = defineEmits(['close'])

const {
	status,
	roomId,
	roomFixed,
	theme,
	features,
	themeOptions,
	filterWords,
	liveTimedDanmuList,
	save,
} = useSettings(toRef(props, 'visible'))

const featuresBeforeLiveStart = ['enable_danmaku', 'enable_guard_buy', 'enable_super_chat']
const featuresAfterLiveStart = ['enable_gift', 'web_debug']

// open_mode 是下拉选择，单独处理
const openMode = computed({
	get: () => features.value.open_mode || 'webview',
	set: (val) => {
		features.value.open_mode = val
	},
})

// 滤词输入
const newFilterWord = ref('')

function addFilterWord() {
	const word = newFilterWord.value.trim()
	if (!word) return
	if (filterWords.value.includes(word)) return
	filterWords.value.push(word)
	newFilterWord.value = ''
}

function removeFilterWord(index) {
	filterWords.value.splice(index, 1)
}

// 定时弹幕列表操作
function addTimedDanmu() {
	liveTimedDanmuList.value.push({ delay: 300, text: '', enabled: true })
}

function removeTimedDanmu(index) {
	liveTimedDanmuList.value.splice(index, 1)
}

function handleOverlayClick(event) {
	if (event.target === event.currentTarget) {
		emit('close')
	}
}

async function handleSave() {
	await save()
}
</script>

<template>
	<div v-if="visible" class="settings-overlay" @click="handleOverlayClick">
		<div class="settings-panel" @click.stop>
			<div class="settings-title">设置</div>

			<div class="settings-section-required">
				<label class="settings-section-label" for="setting-room-id">
					直播间 ID
					<span class="settings-required-mark">*</span>
				</label>
				<input
					id="setting-room-id"
					v-model="roomId"
					type="number"
					inputmode="numeric"
					required
					:disabled="roomFixed"
					placeholder="例如 1879006019"
				/>
				<div class="settings-field-hint">
					{{
						roomFixed
							? '多开模式下此窗口固定监听该直播间。'
							: '必填。此房间的功能配置均关联到该 ID。'
					}}
				</div>
			</div>

			<label class="settings-field">
				主题
				<select id="setting-theme" v-model="theme">
					<option
						v-for="option in themeOptions"
						:key="option.value"
						:value="option.value"
					>
						{{ option.label }}
					</option>
				</select>
			</label>

			<label class="settings-field">
				{{ FEATURE_LABELS.open_mode }}
				<select id="setting-open-mode" v-model="openMode">
					<option
						v-for="option in OPEN_MODE_OPTIONS"
						:key="option.value"
						:value="option.value"
					>
						{{ option.label }}
					</option>
				</select>
				<div class="settings-field-hint">
					切换后需重启应用生效。网页模式可在浏览器中打开。
				</div>
			</label>

			<div class="settings-group-title">功能开关</div>

			<label v-for="key in featuresBeforeLiveStart" :key="key" class="settings-check">
				<input v-model="features[key]" type="checkbox" />
				{{ FEATURE_LABELS[key] }}
			</label>

			<label v-for="key in featuresAfterLiveStart" :key="key" class="settings-check">
				<input v-model="features[key]" type="checkbox" />
				{{ FEATURE_LABELS[key] }}
			</label>

			<div class="settings-feature-block">
				<div class="settings-group-title" style="margin-top: 0">开播定时弹幕</div>
				<div
					v-for="(item, idx) in liveTimedDanmuList"
					:key="idx"
					class="settings-timed-item"
				>
					<div class="settings-timed-item-header">
						<label class="settings-check" style="margin-bottom: 0">
							<input v-model="item.enabled" type="checkbox" />
							弹幕 #{{ idx + 1 }}
						</label>
						<button
							type="button"
							class="settings-timed-item-del"
							@click="removeTimedDanmu(idx)"
						>
							×
						</button>
					</div>
					<label class="settings-field settings-field-nested">
						延迟（秒）
						<input
							v-model.number="item.delay"
							type="number"
							inputmode="numeric"
							min="1"
							placeholder="300"
						/>
					</label>
					<label class="settings-field settings-field-nested">
						弹幕内容
						<input
							v-model="item.text"
							type="text"
							maxlength="30"
							placeholder="输入弹幕内容..."
						/>
					</label>
				</div>
				<button type="button" class="settings-timed-add-btn" @click="addTimedDanmu">
					+ 添加一条定时弹幕
				</button>
				<div v-if="liveTimedDanmuList.length === 0" class="settings-filter-words-empty">
					暂无定时弹幕，点击上方按钮添加
				</div>
			</div>

			<div class="settings-feature-block">
				<label class="settings-check">
					<input v-model="features.enable_danmu_db" type="checkbox" />
					{{ FEATURE_LABELS.enable_danmu_db }}
				</label>
				<div v-if="features.enable_danmu_db" class="settings-nested">
					<div class="settings-filter-words-hint">
						完全匹配（大小写敏感）的弹幕将不会存入数据库
					</div>
					<div class="settings-filter-words-input-row">
						<input
							v-model="newFilterWord"
							type="text"
							placeholder="输入滤词，回车添加"
							@keyup.enter="addFilterWord"
						/>
						<button
							type="button"
							class="settings-filter-add-btn"
							@click="addFilterWord"
						>
							添加
						</button>
					</div>
					<ul v-if="filterWords.length" class="settings-filter-words-list">
						<li
							v-for="(word, idx) in filterWords"
							:key="idx"
							class="settings-filter-word-item"
						>
							<span class="settings-filter-word-text">{{ word }}</span>
							<button
								type="button"
								class="settings-filter-word-del"
								@click="removeFilterWord(idx)"
							>
								×
							</button>
						</li>
					</ul>
					<div v-else class="settings-filter-words-empty">暂无滤词</div>
				</div>
			</div>

			<div class="settings-status">{{ status }}</div>
			<div class="settings-actions">
				<button class="settings-action" type="button" @click="emit('close')">取消</button>
				<button class="settings-action primary" type="button" @click="handleSave">
					保存
				</button>
			</div>
		</div>
	</div>
</template>

<style scoped>
.settings-overlay {
	position: fixed;
	inset: 0;
	z-index: 1200;
	display: flex;
	align-items: center;
	justify-content: center;
	padding: 18px;
	background: rgba(0, 0, 0, 0.28);
	backdrop-filter: blur(8px);
}

.settings-panel {
	width: min(360px, 100%);
	max-height: calc(100vh - 36px);
	overflow-y: auto;
	padding: 18px;
	border: 1px solid var(--border-strong);
	border-radius: 8px;
	background: var(--surface-strong);
	color: var(--text-primary);
	box-shadow: 0 18px 44px var(--shadow);
	scrollbar-width: thin;
	scrollbar-color: var(--scrollbar-thumb) transparent;
}

.settings-panel::-webkit-scrollbar {
	width: 6px;
}
.settings-panel::-webkit-scrollbar-track {
	background: transparent;
}
.settings-panel::-webkit-scrollbar-thumb {
	background-color: var(--scrollbar-thumb);
	border-radius: 6px;
}
.settings-panel::-webkit-scrollbar-thumb:hover {
	background-color: var(--surface-hover);
}

.settings-title {
	margin-bottom: 14px;
	font-size: 1rem;
	font-weight: 700;
}

.settings-field {
	display: flex;
	flex-direction: column;
	gap: 6px;
	margin-bottom: 12px;
	font-size: 0.85rem;
	color: var(--text-muted);
}

.settings-field input,
.settings-field select {
	width: 100%;
	padding: 10px 12px;
	border: 1px solid var(--border);
	border-radius: 8px;
	background: var(--surface-soft);
	color: var(--text-primary);
	outline: none;
	font-size: 0.9rem;
	transition:
		border-color 0.2s ease,
		box-shadow 0.2s ease;
}

.settings-field input:focus,
.settings-field select:focus {
	border-color: var(--name-text);
	box-shadow: 0 0 0 3px rgba(0, 234, 255, 0.15);
}

.settings-field input::placeholder {
	color: var(--text-placeholder);
}

.settings-field select {
	appearance: none;
	-webkit-appearance: none;
	-moz-appearance: none;
	background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='8' viewBox='0 0 12 8'%3E%3Cpath fill='rgba(255,255,255,0.6)' d='M1.41 0L6 4.58 10.59 0 12 1.41l-6 6-6-6z'/%3E%3C/svg%3E");
	background-repeat: no-repeat;
	background-position: right 12px center;
	padding-right: 36px;
	cursor: pointer;
}

.settings-field select option {
	background: var(--surface-strong);
	color: var(--text-primary);
	padding: 8px 12px;
}

.settings-section-required {
	margin-bottom: 16px;
	padding: 12px;
	border: 1px solid var(--border-strong);
	border-radius: 10px;
	background: var(--surface-soft);
}

.settings-section-required input {
	width: 100%;
	padding: 10px 12px;
	border: 1px solid var(--border);
	border-radius: 8px;
	background: var(--surface);
	color: var(--text-primary);
	outline: none;
	font-size: 0.9rem;
	transition:
		border-color 0.2s ease,
		box-shadow 0.2s ease;
}

.settings-section-required input:focus {
	border-color: var(--name-text);
	box-shadow: 0 0 0 3px rgba(0, 234, 255, 0.15);
}
.settings-section-required input::placeholder {
	color: var(--text-placeholder);
}

.settings-section-label {
	display: flex;
	align-items: center;
	gap: 4px;
	margin-bottom: 8px;
	font-size: 0.92rem;
	font-weight: 700;
	color: var(--text-primary);
}

.settings-required-mark {
	color: #ff6b6b;
	font-weight: 700;
}

.settings-field-hint {
	margin-top: 6px;
	font-size: 0.78rem;
	line-height: 1.4;
	color: var(--text-muted);
}

.settings-feature-block {
	margin-bottom: 4px;
}

.settings-nested {
	margin: 4px 0 10px 24px;
	padding: 10px 12px;
	border-left: 2px solid var(--border);
	border-radius: 0 8px 8px 0;
	background: var(--surface-soft);
}
.settings-nested.is-disabled {
	opacity: 0.45;
	pointer-events: none;
}

.settings-field-nested {
	margin-bottom: 0;
}
.settings-field-nested input:disabled,
.settings-check input:disabled {
	cursor: not-allowed;
}

.settings-group-title {
	margin: 16px 0 10px;
	font-size: 0.9rem;
	font-weight: 700;
}

.settings-check {
	display: flex;
	align-items: center;
	gap: 8px;
	margin-bottom: 9px;
	color: var(--text-primary);
	font-size: 0.9rem;
}
.settings-check input {
	width: 16px;
	height: 16px;
	accent-color: var(--name-text);
}

.settings-actions {
	display: flex;
	justify-content: flex-end;
	gap: 8px;
	margin-top: 16px;
}

.settings-action {
	border: 1px solid var(--border);
	border-radius: 999px;
	padding: 9px 14px;
	cursor: pointer;
	background: var(--surface-soft);
	color: var(--text-primary);
	font-weight: 700;
}
.settings-action.primary {
	border: none;
	background: var(--send-gradient);
	color: var(--send-text);
}

.settings-status {
	min-height: 18px;
	margin-top: 10px;
	color: var(--text-muted);
	font-size: 0.82rem;
}

/* ---- 滤词列表 ---- */
.settings-filter-words-hint {
	font-size: 0.75rem;
	color: var(--text-muted);
	margin-bottom: 8px;
}

.settings-filter-words-input-row {
	display: flex;
	gap: 6px;
	margin-bottom: 8px;
}

.settings-filter-words-input-row input {
	flex: 1;
	padding: 6px 10px;
	border: 1px solid var(--border);
	border-radius: 6px;
	background: var(--surface);
	color: var(--text-primary);
	outline: none;
	font-size: 0.82rem;
	transition: border-color 0.2s ease;
}

.settings-filter-words-input-row input:focus {
	border-color: var(--name-text);
	box-shadow: 0 0 0 2px rgba(0, 234, 255, 0.12);
}

.settings-filter-words-input-row input::placeholder {
	color: var(--text-placeholder);
}

.settings-filter-add-btn {
	padding: 6px 12px;
	border: 1px solid var(--border);
	border-radius: 6px;
	background: var(--surface-active);
	color: var(--text-primary);
	cursor: pointer;
	font-size: 0.82rem;
	font-weight: 600;
	white-space: nowrap;
	transition: background 0.15s ease;
}

.settings-filter-add-btn:hover {
	background: var(--surface-hover);
}

.settings-filter-words-list {
	list-style: none;
	margin: 0;
	padding: 0;
	max-height: 140px;
	overflow-y: auto;
	scrollbar-width: thin;
	scrollbar-color: var(--scrollbar-thumb) transparent;
}

.settings-filter-words-list::-webkit-scrollbar {
	width: 4px;
}

.settings-filter-words-list::-webkit-scrollbar-thumb {
	background-color: var(--scrollbar-thumb);
	border-radius: 4px;
}

.settings-filter-word-item {
	display: flex;
	align-items: center;
	justify-content: space-between;
	gap: 6px;
	padding: 4px 6px;
	border-radius: 4px;
	font-size: 0.82rem;
	color: var(--text-primary);
	transition: background 0.1s ease;
}

.settings-filter-word-item:hover {
	background: var(--surface-hover);
}

.settings-filter-word-text {
	flex: 1;
	overflow: hidden;
	text-overflow: ellipsis;
	white-space: nowrap;
}

.settings-filter-word-del {
	flex-shrink: 0;
	width: 20px;
	height: 20px;
	padding: 0;
	border: none;
	border-radius: 50%;
	background: transparent;
	color: var(--text-muted);
	font-size: 1rem;
	line-height: 1;
	cursor: pointer;
	transition:
		color 0.15s ease,
		background 0.15s ease;
}

.settings-filter-word-del:hover {
	color: #ff6b6b;
	background: rgba(255, 107, 107, 0.15);
}

.settings-filter-words-empty {
	font-size: 0.78rem;
	color: var(--text-muted);
	text-align: center;
	padding: 6px 0;
}

/* ---- 定时弹幕列表 ---- */
.settings-timed-item {
	border: 1px solid var(--border);
	border-radius: 6px;
	padding: 10px;
	margin-bottom: 10px;
	background: var(--surface);
}

.settings-timed-item-header {
	display: flex;
	align-items: center;
	justify-content: space-between;
	margin-bottom: 6px;
}

.settings-timed-item-label {
	font-size: 0.8rem;
	font-weight: 600;
	color: var(--text-muted);
}

.settings-timed-item-del {
	flex-shrink: 0;
	width: 22px;
	height: 22px;
	padding: 0;
	border: none;
	border-radius: 50%;
	background: transparent;
	color: var(--text-muted);
	font-size: 1.1rem;
	line-height: 1;
	cursor: pointer;
	transition:
		color 0.15s ease,
		background 0.15s ease;
}

.settings-timed-item-del:hover:not(:disabled) {
	color: #ff6b6b;
	background: rgba(255, 107, 107, 0.15);
}

.settings-timed-item-del:disabled {
	opacity: 0.35;
	cursor: not-allowed;
}

.settings-timed-add-btn {
	width: 100%;
	padding: 8px 0;
	border: 1px dashed var(--border);
	border-radius: 6px;
	background: transparent;
	color: var(--text-muted);
	cursor: pointer;
	font-size: 0.82rem;
	font-weight: 600;
	transition:
		border-color 0.15s ease,
		color 0.15s ease;
}

.settings-timed-add-btn:hover:not(:disabled) {
	border-color: var(--name-text);
	color: var(--name-text);
}

.settings-timed-add-btn:disabled {
	opacity: 0.35;
	cursor: not-allowed;
}
</style>
