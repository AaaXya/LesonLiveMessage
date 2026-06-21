<script setup>
import { toRef } from 'vue'
import { FEATURE_LABELS } from '../constants'
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
	groupId,
	theme,
	features,
	enableQqNotification,
	themeOptions,
	liveStartEnabled,
	liveStartOptionsDisabled,
	groupIdDisabled,
	save,
} = useSettings(toRef(props, 'visible'))

const featuresBeforeLiveStart = ['enable_danmaku', 'enable_guard_buy', 'enable_super_chat']
const featuresAfterLiveStart = ['enable_gift', 'web_debug']

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
					placeholder="例如 1879006019"
				/>
				<div class="settings-field-hint">必填。QQ 群绑定等功能都关联到此房间 ID。</div>
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

			<div class="settings-group-title">功能开关</div>

			<label v-for="key in featuresBeforeLiveStart" :key="key" class="settings-check">
				<input v-model="features[key]" type="checkbox" />
				{{ FEATURE_LABELS[key] }}
			</label>

			<div class="settings-feature-block">
				<label class="settings-check">
					<input v-model="liveStartEnabled" type="checkbox" />
					{{ FEATURE_LABELS.enable_live_start }}
				</label>
				<div class="settings-nested" :class="{ 'is-disabled': liveStartOptionsDisabled }">
					<label class="settings-check">
						<input
							v-model="enableQqNotification"
							type="checkbox"
							:disabled="liveStartOptionsDisabled"
						/>
						推送到 QQ 群
					</label>
					<label class="settings-field settings-field-nested">
						QQ 群号
						<input
							v-model="groupId"
							type="text"
							inputmode="numeric"
							placeholder="例如 1093523827"
							:disabled="groupIdDisabled"
						/>
						<div class="settings-field-hint">
							仅对上方直播间 ID 生效，留空则不推送。
						</div>
					</label>
				</div>
			</div>

			<label v-for="key in featuresAfterLiveStart" :key="key" class="settings-check">
				<input v-model="features[key]" type="checkbox" />
				{{ FEATURE_LABELS[key] }}
			</label>

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
</style>
