import { useEffect } from 'react'

function getDashboardHref() {
  if (typeof window !== 'undefined' && window.location.port === '5173') {
    return 'http://localhost:8000/'
  }
  return '/'
}

export default function PortalHomeRedirect() {
  useEffect(() => {
    window.location.replace(getDashboardHref())
  }, [])

  return (
    <div className="loading-screen">
      <div className="spinner" />
    </div>
  )
}
