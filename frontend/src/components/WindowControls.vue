<script setup>
import { closeWindow, minimizeWindow } from '../api/bridge'

defineProps({
  onOpenSettings: {
    type: Function,
    required: true,
  },
})

async function handleClose() {
  try {
    await closeWindow()
  } catch (error) {
    console.error('关闭窗口失败：', error)
  }
}
</script>

<template>
  <div class="window-controls">
    <button class="window-button" title="最小化" type="button" @click="minimizeWindow">─</button>
    <button class="window-button" title="设置" type="button" @click="onOpenSettings">⚙</button>
    <button class="window-button close" title="关闭" type="button" @click="handleClose">×</button>
  </div>
</template>

<style scoped>
.window-controls {
  position: fixed;
  top: 10px;
  right: 10px;
  z-index: 1000;
  display: flex;
  gap: 6px;
}
</style>
