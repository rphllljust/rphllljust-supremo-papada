export const AUTH_REDIRECT_EVENT = 'suap:auth-redirect'

function getCurrentAppPath() {
  if (typeof window === 'undefined') {
    return '/dashboard'
  }

  const { pathname, search, hash } = window.location
  return `${pathname || ''}${search || ''}${hash || ''}` || '/dashboard'
}

export function buildLoginPath(nextPath = getCurrentAppPath()) {
  const safeNextPath = nextPath && nextPath !== '/login' ? nextPath : '/dashboard'
  return `/login?next=${encodeURIComponent(safeNextPath)}`
}

export function requestAuthRedirect(reason = 'session-expired', nextPath = getCurrentAppPath()) {
  const target = buildLoginPath(nextPath)

  window.dispatchEvent(
    new CustomEvent(AUTH_REDIRECT_EVENT, {
      detail: {
        reason,
        nextPath,
        target,
      },
    })
  )

  return target
}