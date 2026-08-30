<script setup>
import { nextTick, onMounted, onUnmounted, ref } from 'vue'
import { getConsoleLogs, clearConsole } from '../api/bridge'

const logs = ref([])
const scrollEl = ref(null)
const paused = ref(false)
let nextSeq = 0
let timer = null

async function poll() {
	if (paused.value) return
	try {
		const res = await getConsoleLogs(nextSeq)
		if (res?.ok && res.logs?.length) {
			logs.value.push(...res.logs)
			if (logs.value.length > 800) {
				logs.value = logs.value.slice(-800)
			}
			nextSeq = res.nextSeq
			await nextTick()
			if (scrollEl.value) {
				scrollEl.value.scrollTop = scrollEl.value.scrollHeight
			}
		}
	} catch {
		// 忽略轮询错误
	}
}

async function handleClear() {
	await clearConsole()
	logs.value = []
	nextSeq = 0
}

onMounted(() => {
	poll()
	timer = setInterval(poll, 500)
})

onUnmounted(() => {
	if (timer) clearInterval(timer)
})
</script>

<template>
	<d-card class="console-view" title="后端控制台日志">
		<template #extra>
			<div class="console-actions">
				<d-button variant="outline" @click="paused = !paused">{{
					paused ? '继续' : '暂停'
				}}</d-button>
				<d-button color="danger" variant="outline" @click="handleClear">清空</d-button>
			</div>
		</template>
		<div ref="scrollEl" class="console-box">
			<div v-for="item in logs" :key="item.seq" class="console-line">
				<span class="console-seq">#{{ item.seq }}</span>
				<span class="console-text">{{ item.line }}</span>
			</div>
			<div v-if="logs.length === 0" class="console-empty">暂无日志输出</div>
		</div>
	</d-card>
</template>

<style scoped>
.console-view {
	display: flex;
	flex-direction: column;
	height: 100%;
}
.console-header {
	display: flex;
	align-items: center;
	justify-content: space-between;
	margin-bottom: 10px;
}
.console-title {
	font-weight: 600;
	font-size: 0.95rem;
}
.console-actions {
	display: flex;
	gap: 8px;
}
.console-box {
	height: calc(100vh - 140px);
	overflow-y: auto;
	padding: 12px 14px;
	border-radius: 8px;
	border: 1px solid var(--border);
	background: rgba(26, 24, 21, 0.45);
	font-family: Consolas, 'Courier New', monospace;
	font-size: 12px;
	line-height: 1.6;
	color: var(--text-primary);
}
.console-line {
	display: flex;
	gap: 10px;
	white-space: pre-wrap;
	word-break: break-all;
	margin-bottom: 2px;
}
.console-seq {
	flex-shrink: 0;
	color: var(--accent);
	user-select: none;
	font-weight: 600;
}
.console-text {
	color: var(--text-muted);
	flex: 1;
}
.console-empty {
	padding: 40px 0;
	text-align: center;
	color: var(--text-muted);
	font-style: italic;
}

/* 响应式设计 */
@media (max-width: 768px) {
	.console-box {
		height: calc(100vh - 160px);
	}
	.console-actions {
		flex-direction: column;
	}
}
</style>
