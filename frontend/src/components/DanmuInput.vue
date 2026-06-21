<script setup>
import { ref } from 'vue'
import { sendDanmu } from '../api/bridge'

const text = ref('')
const status = ref('')
let statusTimer = null

function showStatus(message, duration = 2400) {
  status.value = message
  if (statusTimer) {
    clearTimeout(statusTimer)
  }
  if (duration > 0) {
    statusTimer = setTimeout(() => {
      status.value = ''
    }, duration)
  }
}

async function handleSend() {
  const value = text.value.trim()
  if (!value) {
    showStatus('请输入弹幕内容')
    return
  }

  try {
    const result = await sendDanmu(value)
    if (result?.ok) {
      showStatus('弹幕已发送')
      text.value = ''
    } else {
      showStatus('发送失败：' + (result?.error || '未知错误'))
    }
  } catch (error) {
    console.error('sendDanmu 调用失败：', error)
    showStatus('发送失败：后端调用异常')
  }
}

function handleKeydown(event) {
  if (event.key === 'Enter') {
    event.preventDefault()
    handleSend()
  }
}
</script>

<template>
  <div class="danmu-box">
    <input
      v-model="text"
      class="danmu-input"
      type="text"
      placeholder="输入弹幕后按 Enter 发送"
      autocomplete="off"
      @keydown="handleKeydown"
    />
    <button class="danmu-send-btn" type="button" @click="handleSend">发送</button>
  </div>
  <div class="danmu-status">{{ status }}</div>
</template>
