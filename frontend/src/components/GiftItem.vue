<script setup>
defineProps({
  data: {
    type: Object,
    required: true,
  },
})
</script>

<template>
  <div class="gift-item">
    <div class="gift-header">
      <span class="gift-medal">[{{ data.medal_name }}·{{ data.medal_level }}]</span>
      <span class="name">{{ data.username }}</span>
      <span class="type-label">礼物</span>
    </div>
    <div class="content">
      赠送 ×{{ data.gift_num }}【{{ data.gift_name }}】 · {{ data.paid_coin / 1000 }} 元
      <template v-if="data.paid_coin && data.paid_coin !== data.total_coin">
        （花费 {{ data.total_coin / 1000 }} 元）
      </template>
    </div>
  </div>
</template>
