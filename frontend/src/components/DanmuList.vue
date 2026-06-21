<script setup>
import { ref, watch, nextTick, onMounted } from 'vue'
import { danmuItems } from '../stores/danmu'
import DanmuItem from './DanmuItem.vue'
import GiftItem from './GiftItem.vue'
import GuardItem from './GuardItem.vue'

const listRef = ref(null)
const showScrollButton = ref(false)

function isAtBottom() {
  const list = listRef.value
  if (!list) {
    return true
  }
  return list.scrollTop + list.clientHeight >= list.scrollHeight - 10
}

function checkScrollBottom() {
  showScrollButton.value = !isAtBottom()
}

function scrollToBottom() {
  const list = listRef.value
  if (!list) {
    return
  }
  list.scrollTop = list.scrollHeight
  showScrollButton.value = false
}

watch(
  danmuItems,
  async () => {
    await nextTick()
    const list = listRef.value
    if (list) {
      list.scrollTop = list.scrollHeight
    }
    checkScrollBottom()
  },
  { deep: true }
)

onMounted(async () => {
  await nextTick()
  scrollToBottom()
})

defineExpose({ scrollToBottom })
</script>

<template>
  <div ref="listRef" class="danmu-list" @scroll="checkScrollBottom">
    <template v-for="(item, index) in danmuItems" :key="index">
      <DanmuItem v-if="item.type === 'danmu'" :data="item" />
      <GiftItem v-else-if="item.type === 'gift'" :data="item" />
      <GuardItem v-else-if="item.type === 'GUARD_BUY'" :data="item" />
    </template>
  </div>

  <button
    v-show="showScrollButton"
    class="window-button scroll-to-bottom"
    title="回到底部"
    type="button"
    @click="scrollToBottom"
  >
    ↓
  </button>
</template>
