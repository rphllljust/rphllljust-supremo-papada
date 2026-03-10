import { useEffect } from 'react'

import { buildBackendUrl } from '@/utils/backendUrls'
import { navigateToBackendPath } from '@/utils/backendNavigation'

export default function BackendRouteRedirect({ path, title = 'Redirecionando para o modulo legado...' }) {
  const target = buildBackendUrl(path)

  useEffect(() => {
    navigateToBackendPath(path, { replace: true })
  }, [path, target])

  return (
    <div className="page-loader" role="status" aria-live="polite">
      <div className="spinner" />
      <span>{title}</span>
      <a href={target}>Abrir agora</a>
    </div>
  )
}