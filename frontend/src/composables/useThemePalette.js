// 主题色配置方案
export const THEME_PALETTES = {
	// 绿色主题（原生态治愈系）
	green: {
		name: '翠绿',
		accent: '#6fb969',
		accentStrong: '#5eccc4',
		accentSoft: 'rgba(111, 185, 105, 0.12)',
		warning: '#d8937d',
		danger: '#d97676',
	},
	// 蓝色主题（清爽现代）
	blue: {
		name: '海蓝',
		accent: '#5a8dd8',
		accentStrong: '#4a9fd8',
		accentSoft: 'rgba(90, 141, 216, 0.12)',
		warning: '#e8b451',
		danger: '#e85959',
	},
	// 紫色主题（优雅温和）
	purple: {
		name: '薰衣草',
		accent: '#9b7dd8',
		accentStrong: '#a89dd8',
		accentSoft: 'rgba(155, 125, 216, 0.12)',
		warning: '#d8a96b',
		danger: '#d97676',
	},
	// 粉色主题（温暖柔和）
	pink: {
		name: '樱花粉',
		accent: '#d97b9a',
		accentStrong: '#e89dae',
		accentSoft: 'rgba(217, 123, 154, 0.12)',
		warning: '#d8a374',
		danger: '#d97676',
	},
	// 青色主题（沉静深邃）
	teal: {
		name: '孔雀青',
		accent: '#4db8a8',
		accentStrong: '#3eccc4',
		accentSoft: 'rgba(77, 184, 168, 0.12)',
		warning: '#d8b374',
		danger: '#d97676',
	},
}

export const THEME_PALETTE_OPTIONS = Object.entries(THEME_PALETTES).map(([key, palette]) => ({
	value: key,
	label: palette.name,
}))

// 应用主题色到CSS变量
export function applyThemePalette(paletteKey = 'green') {
	const palette = THEME_PALETTES[paletteKey] || THEME_PALETTES.green
	const root = document.documentElement

	root.style.setProperty('--accent', palette.accent)
	root.style.setProperty('--accent-strong', palette.accentStrong)
	root.style.setProperty('--accent-soft', palette.accentSoft)
	root.style.setProperty('--warning', palette.warning)
	root.style.setProperty('--danger', palette.danger)

	// 同步 DevUI token，让 DevUI 组件跟随主题色
	root.style.setProperty('--devui-brand', palette.accent)
	root.style.setProperty('--devui-brand-hover', palette.accentStrong)
	root.style.setProperty('--devui-brand-active', palette.accentStrong)
	root.style.setProperty('--devui-primary', palette.accent)

	// 更新相关的渐变和阴影
	root.style.setProperty(
		'--send-gradient',
		`linear-gradient(135deg, ${palette.accent} 0%, ${palette.accentStrong} 100%)`,
	)
	root.style.setProperty(
		'--bubble-gradient',
		`linear-gradient(135deg, ${palette.accentSoft}, rgba(94, 204, 196, 0.08))`,
	)

	// 保存用户偏好
	localStorage.setItem('theme-palette', paletteKey)
}

// 获取保存的主题色，如果没有则返回默认值
export function getSavedThemePalette() {
	return localStorage.getItem('theme-palette') || 'green'
}

// 在应用启动时恢复主题色
export function restoreThemePalette() {
	const saved = getSavedThemePalette()
	applyThemePalette(saved)
}
