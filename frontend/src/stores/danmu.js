import { ref } from 'vue'
import { MAX_DANMU_ITEMS } from '../constants'

export const danmuItems = ref([])

export function pushDanmu(data) {
  if (!data) {
    return
  }
  console.log('addDanmu 接收到数据：', data)
  danmuItems.value.push(data)
  while (danmuItems.value.length > MAX_DANMU_ITEMS) {
    danmuItems.value.shift()
  }
}
