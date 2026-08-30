<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { getDanmuPage, getRoomsStatus } from '../api/bridge'
const rooms = ref([]),
	selectedRoom = ref(''),
	keyword = ref(''),
	itemType = ref(''),
	page = ref(1),
	pageSize = ref(20),
	total = ref(0),
	rows = ref([]),
	loading = ref(false),
	notice = ref('')
const pages = computed(() => Math.max(1, Math.ceil(total.value / pageSize.value)))
async function loadRooms() {
	const res = await getRoomsStatus()
	if (res?.ok) {
		rooms.value = res.rooms || []
		selectedRoom.value ||= rooms.value[0]?.room_id || ''
	}
}
async function load() {
	if (!selectedRoom.value) return
	loading.value = true
	try {
		const res = await getDanmuPage({
			roomId: selectedRoom.value,
			page: page.value,
			pageSize: pageSize.value,
			keyword: keyword.value || null,
			itemType: itemType.value || null,
		})
		if (res?.ok) {
			rows.value = res.rows || []
			total.value = res.total || 0
		} else notice.value = res?.error || '查询失败'
	} catch {
		notice.value = '查询失败'
	} finally {
		loading.value = false
	}
}
function search() {
	page.value = 1
	load()
}
onMounted(async () => {
	await loadRooms()
	load()
})
watch([page, pageSize], load)
</script>
<template>
	<d-card class="data-card" :title="`弹幕数据库（${total} 条记录）`">
		<div class="toolbar">
			<select v-model="selectedRoom" class="control" @change="search">
				<option v-for="room in rooms" :key="room.room_id" :value="room.room_id">
					{{ room.title }} ({{ room.room_id }})
				</option>
			</select>
			<select v-model="itemType" class="control" @change="search">
				<option value="">全部类型</option>
				<option value="danmu">弹幕</option>
				<option value="super_chat">超级留言</option>
			</select>
			<input
				v-model="keyword"
				class="control"
				placeholder="内容或用户"
				@keyup.enter="search"
			/>
			<d-button color="primary" @click="search">搜索</d-button>
		</div>
		<p v-if="notice" class="notice">{{ notice }}</p>
		<div class="table-wrap">
			<table class="data-table">
				<thead>
					<tr>
						<th>时间</th>
						<th>用户</th>
						<th>类型</th>
						<th>内容</th>
					</tr>
				</thead>
				<tbody>
					<tr v-if="loading">
						<td colspan="4">加载中…</td>
					</tr>
					<tr v-for="row in rows" :key="row.id">
						<td>{{ row.send_time }}</td>
						<td>{{ row.username }}</td>
						<td>
							<span class="badge">{{
								row.type === 'super_chat' ? 'SC' : '弹幕'
							}}</span>
						</td>
						<td>{{ row.content }}</td>
					</tr>
				</tbody>
			</table>
		</div>
		<div class="pager">
			<d-button :disabled="page <= 1" @click="page--">上一页</d-button
			><span>{{ page }} / {{ pages }}</span
			><select v-model.number="pageSize" class="control">
				<option :value="10">10</option>
				<option :value="20">20</option>
				<option :value="50">50</option></select
			><d-button :disabled="page >= pages" @click="page++">下一页</d-button>
		</div>
	</d-card>
</template>
<style scoped>
.count {
	font-size: 12px;
	font-weight: 400;
	color: var(--text-muted);
}
.toolbar,
.pager {
	display: flex;
	align-items: center;
	gap: 8px;
	flex-wrap: wrap;
}
.toolbar {
	margin-bottom: 14px;
}
.toolbar input {
	min-width: 200px;
}
.pager {
	justify-content: flex-end;
	margin-top: 12px;
	color: var(--text-muted);
	font-size: 13px;
}
</style>
