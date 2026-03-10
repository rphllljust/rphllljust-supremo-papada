const DEBUG_NAMESPACE = 'SUAP-Frontend'
const MAX_BUFFER_SIZE = 200

export const isDebugEnabled = import.meta.env.DEV || import.meta.env.VITE_DEBUG_LOGS === 'true'

function getLogMethod(level) {
  if (level === 'error') return console.error
  if (level === 'warn') return console.warn
  if (level === 'info') return console.info
  return console.log
}

export function normalizeError(error) {
  if (!error) {
    return null
  }

  if (error instanceof Error) {
    return {
      name: error.name,
      message: error.message,
      stack: error.stack,
    }
  }

  if (typeof error === 'object') {
    return {
      ...error,
      message: error.message || String(error),
    }
  }

  return {
    message: String(error),
  }
}

function pushToBuffer(entry) {
  if (typeof window === 'undefined') {
    return
  }

  const current = Array.isArray(window.__SUAP_DEBUG_LOGS__) ? window.__SUAP_DEBUG_LOGS__ : []
  current.push(entry)
  if (current.length > MAX_BUFFER_SIZE) {
    current.splice(0, current.length - MAX_BUFFER_SIZE)
  }
  window.__SUAP_DEBUG_LOGS__ = current
  if (entry.level === 'error') {
    window.__SUAP_LAST_FATAL__ = entry
  }
}

export function debugLog(level, event, meta) {
  if (!isDebugEnabled) {
    return
  }

  const entry = {
    timestamp: new Date().toISOString(),
    level,
    event,
    meta,
  }

  pushToBuffer(entry)
  getLogMethod(level)(`[${DEBUG_NAMESPACE}] ${entry.timestamp} ${event}`, meta || '')
}

export function installGlobalDebugHandlers() {
  if (!isDebugEnabled || typeof window === 'undefined' || window.__SUAP_DEBUG_HANDLERS__) {
    return
  }

  window.__SUAP_DEBUG_HANDLERS__ = true

  window.addEventListener('error', (event) => {
    debugLog('error', 'window.error', {
      message: event.message,
      filename: event.filename,
      lineno: event.lineno,
      colno: event.colno,
      error: normalizeError(event.error),
    })
  })

  window.addEventListener('unhandledrejection', (event) => {
    debugLog('error', 'window.unhandledrejection', {
      reason: normalizeError(event.reason),
    })
  })

  debugLog('info', 'debug.handlers.ready')
}

export function instrumentAxiosClient(instance, name) {
  if (!isDebugEnabled || !instance || instance.__suapDebugInstrumented) {
    return instance
  }

  instance.__suapDebugInstrumented = true

  instance.interceptors.request.use(
    (config) => {
      debugLog('info', `${name}.request`, {
        method: config.method?.toUpperCase(),
        url: `${config.baseURL || ''}${config.url || ''}`,
        params: config.params,
        data: config.data,
      })
      return config
    },
    (error) => {
      debugLog('error', `${name}.request_error`, {
        error: normalizeError(error),
      })
      return Promise.reject(error)
    }
  )

  instance.interceptors.response.use(
    (response) => {
      debugLog('info', `${name}.response`, {
        status: response.status,
        method: response.config?.method?.toUpperCase(),
        url: `${response.config?.baseURL || ''}${response.config?.url || ''}`,
      })
      return response
    },
    (error) => {
      debugLog('error', `${name}.response_error`, {
        status: error.response?.status,
        method: error.config?.method?.toUpperCase(),
        url: `${error.config?.baseURL || ''}${error.config?.url || ''}`,
        response: error.response?.data,
        error: normalizeError(error),
      })
      return Promise.reject(error)
    }
  )

  return instance
}