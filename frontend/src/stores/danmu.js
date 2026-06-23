import { ref } from 'vue'
import { MAX_DANMU_ITEMS } from '../constants'

export const danmuItems = ref([])
export const superChat = ref(null)

export function pushDanmu(data) {
	if (!data) {
		return
	}
	console.log('addDanmu 接收到数据：', data)

	if (data.type === 'super_chat') {
		console.log('[SC] 收到超级留言：', data.username, '¥' + data.price, data.message)
		superChat.value = { ...data, arrivedAt: Date.now() }
		return
	}

	danmuItems.value.push(data)
	while (danmuItems.value.length > MAX_DANMU_ITEMS) {
		danmuItems.value.shift()
	}
}
