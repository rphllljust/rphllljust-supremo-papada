function stripTrailingSlash(value) {
  return value.replace(/\/$/, '')
}

function normalizePath(path = '/') {
  if (!path || path === '/') {
    return '/'
  }

  return `/${String(path).replace(/^\/+|\/+$/g, '')}/`
}

function extractOriginFromApiUrl() {
  const apiUrl = import.meta.env.VITE_API_URL

  if (!apiUrl) {
    return ''
  }

  try {
    return new URL(apiUrl).origin
  } catch {
    return ''
  }
}

export function getBackendOrigin() {
  const configuredOrigin = import.meta.env.VITE_BACKEND_ORIGIN?.trim()
  if (configuredOrigin) {
    return stripTrailingSlash(configuredOrigin)
  }

  const derivedOrigin = extractOriginFromApiUrl()
  if (derivedOrigin) {
    return stripTrailingSlash(derivedOrigin)
  }

  if (import.meta.env.DEV) {
    return 'http://127.0.0.1:8000'
  }

  return ''
}

export function buildBackendUrl(path = '/') {
  const normalizedPath = normalizePath(path)
  const origin = getBackendOrigin()

  return origin ? `${origin}${normalizedPath}` : normalizedPath
}

export function getBackendPrefix(path = '/') {
  const normalizedPath = normalizePath(path)

  if (normalizedPath === '/') {
    return '/'
  }

  return normalizedPath.slice(0, -1)
}