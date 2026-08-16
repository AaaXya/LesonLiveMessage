import { ref, computed, watch } from 'vue'
import { FEATURE_KEYS } from '../constants'
import {
	frontendConfig,
	getCurrentRoomBinding,
	applyThemeColors,
	loadFrontendConfig,
} from './useTheme'
import { saveFrontendConfig } from '../api/bridge'

export function useSettings(visible) {
	const status = ref('')
	const roomId = ref('')
	const roomFixed = ref(false)
	const groupId = ref('')
	const theme = ref('default')
	const enableQqNotification = ref(false)
	const features = ref(createDefaultFeatures())
	const filterWords = ref([])
	const liveTimedDanmuList = ref([])

	const themeOptions = computed(() => frontendConfig.value?.themeOptions || [])

	const liveStartEnabled = computed({
		get: () => features.value.enable_live_start,
		set: (value) => {
			features.value.enable_live_start = value
			if (!value) {
				enableQqNotification.value = false
			}
		},
	})

	const liveStartOptionsDisabled = computed(() => !liveStartEnabled.value)
	const groupIdDisabled = computed(() => !liveStartEnabled.value || !enableQqNotification.value)

	watch(visible, async (isVisible) => {
		if (!isVisible) {
			return
		}
		status.value = ''
		if (!frontendConfig.value) {
			await loadFrontendConfig()
		}
		hydrateFromConfig(frontendConfig.value || {})
	})

	watch(liveStartEnabled, (enabled) => {
		if (!enabled) {
			enableQqNotification.value = false
		}
	})

	function createDefaultFeatures() {
		return FEATURE_KEYS.reduce((acc, key) => {
			acc[key] = false
			return acc
		}, {})
	}

	function hydrateFromConfig(configPayload) {
		const config = configPayload.config || {}
		const configFeatures = config.features || {}
		const roomBinding = getCurrentRoomBinding(config)

		roomId.value = config.LESSONROOMID ? String(config.LESSONROOMID) : ''
		roomFixed.value = Boolean(config.roomFixed)
		groupId.value = roomBinding.GROUPID || ''
		theme.value = config.frontend?.theme || configPayload.theme?.name || 'default'
		enableQqNotification.value = Boolean(
			roomBinding.enable_qq_notification ?? configFeatures.enable_qq_notification,
		)

		FEATURE_KEYS.forEach((key) => {
			features.value[key] = Boolean(configFeatures[key])
		})

		const rawList =
			roomBinding.live_timed_danmu_list ?? configFeatures.live_timed_danmu_list ?? []
		liveTimedDanmuList.value = Array.isArray(rawList)
			? rawList.map((item) => ({
					delay: Number(item.delay) || 300,
					text: String(item.text || ''),
					enabled: item.enabled !== false,
				}))
			: []

		filterWords.value = Array.isArray(config.filter_words) ? [...config.filter_words] : []
	}

	function collectUpdate() {
		const qqNotificationEnabled = liveStartEnabled.value && enableQqNotification.value

		return {
			room_ids: [String(roomId.value || '').trim()].filter(Boolean),
			GROUPID: qqNotificationEnabled ? String(groupId.value || '').trim() : '',
			frontend: { theme: theme.value },
			enable_qq_notification: qqNotificationEnabled,
			live_timed_danmu_list: liveTimedDanmuList.value
				.filter((item) => item.text.trim())
				.map((item) => ({
					delay: Number(item.delay) || 300,
					text: String(item.text).trim(),
					enabled: item.enabled !== false,
				})),
			features: { ...features.value },
			filter_words: [...filterWords.value],
		}
	}

	function validate() {
		if (!String(roomId.value || '').trim()) {
			status.value = '请先填写直播间 ID'
			return false
		}

		if (
			liveStartEnabled.value &&
			enableQqNotification.value &&
			!String(groupId.value || '').trim()
		) {
			status.value = '开启 QQ 推送时请填写群号'
			return false
		}

		return true
	}

	async function save() {
		if (!validate()) {
			return false
		}

		status.value = '保存中...'

		try {
			const result = await saveFrontendConfig(collectUpdate())
			if (!result?.ok) {
				status.value = '保存失败：' + (result?.error ? result.error : '未知错误')
				return false
			}

			frontendConfig.value = result.frontendConfig
			applyThemeColors(result.frontendConfig?.theme?.colors || {})
			hydrateFromConfig(result.frontendConfig || {})
			status.value = result.restart_needed
				? result.message || '直播间 ID 已变更，请重启应用以生效'
				: '已保存，部分监听配置重启后完全生效'
			return true
		} catch (error) {
			console.error('保存配置失败：', error)
			status.value = '保存失败：后端调用异常'
			return false
		}
	}

	return {
		status,
		roomId,
		roomFixed,
		groupId,
		theme,
		features,
		enableQqNotification,
		themeOptions,
		liveStartEnabled,
		liveStartOptionsDisabled,
		groupIdDisabled,
		filterWords,
		liveTimedDanmuList,
		save,
	}
}
