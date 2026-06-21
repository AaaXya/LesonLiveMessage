function getApi() {
  return window.pywebview?.api
}

function hasMethod(name) {
  return typeof getApi()?.[name] === 'function'
}

export function whenPywebviewReady(callback) {
  if (window.pywebview) {
    callback()
    return
  }
  window.addEventListener('pywebviewready', callback, { once: true })
}

export async function getFrontendConfig() {
  if (!hasMethod('getFrontendConfig')) {
    return null
  }
  return getApi().getFrontendConfig()
}

export async function saveFrontendConfig(update) {
  if (!hasMethod('saveFrontendConfig')) {
    return { ok: false, error: '后端配置接口不可用' }
  }
  return getApi().saveFrontendConfig(update)
}

export async function sendDanmu(text) {
  if (!hasMethod('sendDanmu')) {
    return { ok: false, error: '后端发送接口不可用' }
  }
  return getApi().sendDanmu(text)
}

export function closeWindow() {
  if (hasMethod('closeWindow')) {
    return getApi().closeWindow()
  }
  window.close()
}

export function minimizeWindow() {
  if (hasMethod('minimizeWindow')) {
    getApi().minimizeWindow()
  }
}
