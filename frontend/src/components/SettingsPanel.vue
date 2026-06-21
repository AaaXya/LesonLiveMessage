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

const featuresBeforeLiveStart = [
  'enable_danmaku',
  'enable_guard_buy',
  'enable_super_chat',
]
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
          <option v-for="option in themeOptions" :key="option.value" :value="option.value">
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
            <div class="settings-field-hint">仅对上方直播间 ID 生效，留空则不推送。</div>
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
        <button class="settings-action primary" type="button" @click="handleSave">保存</button>
      </div>
    </div>
  </div>
</template>
