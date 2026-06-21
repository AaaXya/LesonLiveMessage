<script setup>
defineProps({
  data: {
    type: Object,
    required: true,
  },
})
</script>

<template>
  <div class="guard-item">
    <div class="guard-header">
      <span class="gift-medal">[{{ data.medal_name }}·{{ data.medal_level }}]</span>
      <span class="name">{{ data.username }}</span>
      <span class="type-label">续费</span>
    </div>
    <div class="content">
      续费大航海 {{ data.guard_level || '' }}
      <template v-if="data.guard_name"> {{ data.guard_name }}</template>
    </div>
  </div>
</template>
