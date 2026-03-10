import { authApi } from '@/api/endpoints'
import { buildBackendUrl } from '@/utils/backendUrls'
import { debugLog, normalizeError } from '@/utils/debug'

function hasJwtSession() {
  return Boolean(localStorage.getItem('access_token'))
}

export async function navigateToBackendPath(path, options = {}) {
  const { replace = false } = options
  const target = buildBackendUrl(path)

  if (hasJwtSession()) {
    try {
      await authApi.syncSession()
      debugLog('info', 'navigation.backend_session_synced', { path, target })
    } catch (error) {
      debugLog('warn', 'navigation.backend_session_sync_failed', {
        path,
        target,
        error: normalizeError(error),
      })
    }
  }

  if (replace) {
    window.location.replace(target)
    return
  }

  window.location.assign(target)
}