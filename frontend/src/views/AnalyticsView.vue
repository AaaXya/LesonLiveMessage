<script setup>
const modules = [
	{ name: '弹幕频率分析', desc: '按小时和分钟查看互动密度' },
	{ name: '用户活跃度排行', desc: '识别高互动观众与粉丝牌分布' },
	{ name: '礼物价值统计', desc: '汇总礼物和超级留言价值' },
	{ name: '关键词聚类', desc: '提取高频词与热点话题' },
]
</script>
<template>
	<div class="analytics">
		<d-card title="数据分析工作台">
			<div class="muted">分析模块已预留，后续可在此接入图表和报表。</div>
		</d-card>
		<div class="grid">
			<d-card v-for="module in modules" :key="module.name" class="module">
				<div class="card-content">
					<span class="badge">规划中</span>
					<h2>{{ module.name }}</h2>
					<p>{{ module.desc }}</p>
				</div>
			</d-card>
		</div>
	</div>
</template>
<style scoped>
.analytics .grid {
	display: grid;
	grid-template-columns: repeat(auto-fill, minmax(20rem, 1fr));
	gap: 1.125rem;
	margin-top: 1.125rem;
	align-items: stretch;
	letter-spacing: normal;
	word-spacing: normal;
}
.analytics .module {
	padding: 0;
	min-height: 10.625rem;
	width: 100%;
	min-width: 0;
	overflow: visible;
	flex-shrink: 0;
}
.analytics .card-content {
	display: flex;
	flex-direction: column;
	align-items: flex-start;
	gap: 0.75rem;
	width: 100%;
	padding: 1.375rem 1.25rem 1.25rem;
	letter-spacing: normal;
	word-spacing: normal;
}
.analytics .module .badge {
	align-self: flex-start;
	margin: 0;
	flex-shrink: 0;
	white-space: nowrap;
	font-size: 0.75rem;
	padding: 0.25rem 0.625rem;
}
.analytics .module h2 {
	margin: 0;
	font-size: 1rem;
	font-weight: 700;
	line-height: 1.5;
	letter-spacing: 0.02em;
	color: var(--text-primary);
	word-break: break-word;
	overflow-wrap: anywhere;
	min-width: 0;
	width: 100%;
}
.analytics .module p,
.analytics .muted {
	margin: 0;
	color: var(--text-muted);
	font-size: 0.875rem;
	line-height: 1.7;
	word-break: break-word;
	overflow-wrap: anywhere;
	white-space: normal;
	display: block;
	max-width: 100%;
	min-width: 0;
	width: 100%;
}
</style>
