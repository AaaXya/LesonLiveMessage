export const THEME_VAR_MAP = {
	pageBg: '--theme-page-bg',
	textPrimary: '--theme-text-primary',
	textMuted: '--theme-text-muted',
	textPlaceholder: '--theme-text-placeholder',
	surface: '--theme-surface',
	surfaceStrong: '--theme-surface-strong',
	surfaceActive: '--theme-surface-active',
	surfaceHover: '--theme-surface-hover',
	surfaceSoft: '--theme-surface-soft',
	border: '--theme-border',
	borderStrong: '--theme-border-strong',
	scrollbarThumb: '--theme-scrollbar-thumb',
	buttonBg: '--theme-button-bg',
	closeBg: '--close-bg',
	closeHoverBg: '--close-hover-bg',
	sendGradient: '--send-gradient',
	sendText: '--send-text',
	bubbleGradient: '--bubble-gradient',
	giftBg: '--gift-bg',
	giftText: '--gift-text',
	guardBg: '--guard-bg',
	guardText: '--guard-text',
	medalText: '--medal-text',
	nameText: '--name-text',
	giftMedalText: '--gift-medal-text',
	shadow: '--theme-shadow',
	bubbleShadow: '--bubble-shadow',
	accent: '--accent',
	accentStrong: '--accent-strong',
	accentSoft: '--accent-soft',
	devuiBrand: '--devui-brand',
	devuiBrandHover: '--devui-brand-hover',
	devuiBrandActive: '--devui-brand-active',
	devuiBaseBg: '--theme-devui-base-bg',
	devuiGlobalBg: '--theme-devui-global-bg',
}

export const FEATURE_KEYS = [
	'enable_danmaku',
	'enable_guard_buy',
	'enable_super_chat',
	'enable_live_start',
	'enable_gift',
	'enable_danmu_db',
	'web_debug',
	'open_mode',
]

export const FEATURE_LABELS = {
	enable_danmaku: '弹幕监听',
	enable_guard_buy: '大航海续费',
	enable_super_chat: '超级留言',
	enable_live_start: '开播通知',
	enable_gift: '礼物消息',
	enable_danmu_db: '弹幕数据库',
	web_debug: 'Web 调试',
	open_mode: '运行模式',
}

export const OPEN_MODE_OPTIONS = [
	{ value: 'webview', label: '桌面窗口 (webview)' },
	{ value: 'web', label: '浏览器网页' },
]

export const MAX_DANMU_ITEMS = 100
