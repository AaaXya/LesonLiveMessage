<script setup>
import { ref } from 'vue'

defineProps({
  data: {
    type: Object,
    required: true,
  },
})

const avatarVisible = ref(true)

function hideAvatar() {
  avatarVisible.value = false
}
</script>

<template>
  <div class="danmu-item">
    <img
      v-if="data.avatar_url && avatarVisible"
      class="danmu-avatar"
      :src="data.avatar_url"
      alt="头像"
      @error="hideAvatar"
    />
    <div class="danmu-body">
      <div class="danmu-header">
        <span class="medal">[{{ data.medal_name }}·{{ data.medal_level }}]</span>
        <span class="name">{{ data.username }}</span>
      </div>
      <div class="danmu-bubble">{{ data.content }}</div>
    </div>
  </div>
</template>
