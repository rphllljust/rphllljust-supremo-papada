import { useEffect, useState } from 'react'
import { isDebugEnabled } from '@/utils/debug'

function readLogs() {
  if (typeof window === 'undefined') {
    return { logs: [], fatal: null }
  }

  return {
    logs: Array.isArray(window.__SUAP_DEBUG_LOGS__) ? window.__SUAP_DEBUG_LOGS__ : [],
    fatal: window.__SUAP_LAST_FATAL__ || null,
  }
}

export default function DevDiagnosticsPanel() {
  const [open, setOpen] = useState(false)
  const [snapshot, setSnapshot] = useState(() => readLogs())

  useEffect(() => {
    if (!isDebugEnabled) {
      return undefined
    }

    const interval = window.setInterval(() => {
      setSnapshot(readLogs())
    }, 700)

    return () => window.clearInterval(interval)
  }, [])

  if (!isDebugEnabled) {
    return null
  }

  const recentLogs = snapshot.logs.slice(-8).reverse()

  return (
    <div className={`dev-diagnostics ${open ? 'dev-diagnostics--open' : ''}`}>
      <button type="button" className="dev-diagnostics__toggle" onClick={() => setOpen((value) => !value)}>
        {open ? 'Ocultar logs' : 'Mostrar logs'}
      </button>

      {open ? (
        <div className="dev-diagnostics__panel">
          <div className="dev-diagnostics__section">
            <strong>Ultimo erro fatal</strong>
            <pre className="dev-diagnostics__pre">
              {snapshot.fatal ? JSON.stringify(snapshot.fatal, null, 2) : 'Nenhum erro fatal registrado.'}
            </pre>
          </div>

          <div className="dev-diagnostics__section">
            <strong>Ultimos eventos</strong>
            <pre className="dev-diagnostics__pre">
              {recentLogs.length > 0 ? JSON.stringify(recentLogs, null, 2) : 'Sem logs ainda.'}
            </pre>
          </div>
        </div>
      ) : null}
    </div>
  )
}