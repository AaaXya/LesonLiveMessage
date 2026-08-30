import { ref } from 'vue'
import { MAX_DANMU_ITEMS } from '../constants'

// 默认桶：无 room_id 的数据 + 所有房间的合并视图（供 overlay / 全局场景）
export const DEFAULT_ROOM_KEY = '__default__'

// { roomId: items[] } 按房间隔离的弹幕列表
export const roomDanmuItems = ref({})
// { roomId: sc } 按房间隔离的超级留言
export const roomSuperChats = ref({})

function getBucket(map, key) {
	let bucket = map.value[key]
	if (!bucket) {
		bucket = []
		map.value[key] = bucket
	}
	return bucket
}

function appendLimited(bucket, data) {
	bucket.push(data)
	while (bucket.length > MAX_DANMU_ITEMS) {
		bucket.shift()
	}
}

export function pushDanmu(data) {
	if (!data) {
		return
	}
	console.log('addDanmu 接收到数据：', data)

	const roomId = data.room_id != null ? String(data.room_id) : DEFAULT_ROOM_KEY

	if (data.type === 'super_chat') {
		console.log('[SC] 收到超级留言：', data.username, '¥' + data.price, data.message)
		const sc = { ...data, arrivedAt: Date.now() }
		roomSuperChats.value[roomId] = sc
		if (roomId !== DEFAULT_ROOM_KEY) {
			roomSuperChats.value[DEFAULT_ROOM_KEY] = sc
		}
		return
	}

	const bucket = getBucket(roomDanmuItems, roomId)
	appendLimited(bucket, data)

	// 合并视图同步一份到默认桶（供无房间概念的场景）
	if (roomId !== DEFAULT_ROOM_KEY) {
		appendLimited(getBucket(roomDanmuItems, DEFAULT_ROOM_KEY), data)
	}
}

/** 读取房间弹幕列表（不存在时返回空数组） */
export function getDanmuItems(roomId) {
	const key = roomId != null && String(roomId) !== '' ? String(roomId) : DEFAULT_ROOM_KEY
	return roomDanmuItems.value[key] || []
}

/** 读取房间当前超级留言（不存在返回 null） */
export function getSuperChat(roomId) {
	const key = roomId != null && String(roomId) !== '' ? String(roomId) : DEFAULT_ROOM_KEY
	return roomSuperChats.value[key] || null
}

/** 清理房间数据（停止监听时调用，避免残留旧弹幕） */
export function clearRoom(roomId) {
	if (roomId == null || roomId === '') return
	const key = String(roomId)
	delete roomDanmuItems.value[key]
	delete roomSuperChats.value[key]
}
