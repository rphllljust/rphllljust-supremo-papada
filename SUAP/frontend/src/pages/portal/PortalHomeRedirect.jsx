import { useEffect } from 'react'
import { buildBackendUrl } from '@/utils/backendUrls'

export default function PortalHomeRedirect() {
  useEffect(() => {
    window.location.replace(buildBackendUrl('/'))
  }, [])

  return (
    <div className="loading-screen">
      <div className="spinner" />
    </div>
  )
}
