import { createRouter, createWebHashHistory } from 'vue-router'

import RoomsView from '../views/RoomsView.vue'
import ConsoleView from '../views/ConsoleView.vue'
import DatabaseView from '../views/DatabaseView.vue'
import GiftsView from '../views/GiftsView.vue'
import AnalyticsView from '../views/AnalyticsView.vue'
import AutoSpeakView from '../views/AutoSpeakView.vue'
import SettingsView from '../views/SettingsView.vue'

// hash 模式：兼容 pywebview file:// 加载与 web 模式 HTTP 服务
const router = createRouter({
	history: createWebHashHistory(),
	routes: [
		{ path: '/', redirect: '/rooms' },
		{
			path: '/rooms',
			name: 'rooms',
			component: RoomsView,
			meta: { title: '直播间', icon: 'broadcast' },
		},
		{
			path: '/console',
			name: 'console',
			component: ConsoleView,
			meta: { title: '控制台', icon: 'terminal' },
		},
		{
			path: '/database',
			name: 'database',
			component: DatabaseView,
			meta: { title: '弹幕数据库', icon: 'database' },
		},
		{
			path: '/gifts',
			name: 'gifts',
			component: GiftsView,
			meta: { title: '礼物数据库', icon: 'gift' },
		},
		{
			path: '/analytics',
			name: 'analytics',
			component: AnalyticsView,
			meta: { title: '数据分析', icon: 'chart' },
		},
		{
			path: '/auto-speak',
			name: 'auto-speak',
			component: AutoSpeakView,
			meta: { title: '自动发言', icon: 'comment' },
		},
		{
			path: '/settings',
			name: 'settings',
			component: SettingsView,
			meta: { title: '设置', icon: 'settings' },
		},
	],
})

export default router
