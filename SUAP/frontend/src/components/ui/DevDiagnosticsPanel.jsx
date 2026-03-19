import { useEffect, useState } from 'react'
import { isDebugEnabled } from '@/utils/debug'
import toast from 'react-hot-toast'

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

  // Only render the diagnostics UI in development builds
  if (!import.meta.env.DEV) {
    return null
  }

  const recentLogs = snapshot.logs.slice(-8).reverse()

  async function copyEvents() {
    const data = JSON.stringify(snapshot.logs || [], null, 2)
    try {
      if (navigator.clipboard && navigator.clipboard.writeText) {
        await navigator.clipboard.writeText(data)
      } else {
        const ta = document.createElement('textarea')
        ta.value = data
        document.body.appendChild(ta)
        ta.select()
        document.execCommand('copy')
        document.body.removeChild(ta)
      }
      toast.success('Eventos copiados para a área de transferência.')
    } catch (err) {
      toast.error('Falha ao copiar eventos.')
    }
  }

  async function copyFatal() {
    if (!snapshot.fatal) {
      toast.error('Nenhum erro fatal para copiar.')
      return
    }

    const data = JSON.stringify(snapshot.fatal, null, 2)
    try {
      if (navigator.clipboard && navigator.clipboard.writeText) {
        await navigator.clipboard.writeText(data)
      } else {
        const ta = document.createElement('textarea')
        ta.value = data
        document.body.appendChild(ta)
        ta.select()
        document.execCommand('copy')
        document.body.removeChild(ta)
      }
      toast.success('Erro fatal copiado para a área de transferência.')
    } catch (err) {
      toast.error('Falha ao copiar erro fatal.')
    }
  }

  return (
    <div className={`dev-diagnostics ${open ? 'dev-diagnostics--open' : ''}`}>
      <button type="button" className="dev-diagnostics__toggle" onClick={() => setOpen((value) => !value)}>
        {open ? 'Ocultar logs' : 'Mostrar logs'}
      </button>

      {open ? (
        <div className="dev-diagnostics__panel">
          <div className="dev-diagnostics__section">
            <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center'}}>
              <strong>Ultimo erro fatal</strong>
              <div>
                <button type="button" className="dev-diagnostics__button" onClick={copyFatal}>Copiar erro fatal</button>
              </div>
            </div>
            <pre className="dev-diagnostics__pre">
              {snapshot.fatal ? JSON.stringify(snapshot.fatal, null, 2) : 'Nenhum erro fatal registrado.'}
            </pre>
          </div>

          <div className="dev-diagnostics__section">
            <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center'}}>
              <strong>Ultimos eventos</strong>
              <div>
                <button type="button" className="dev-diagnostics__button" onClick={copyEvents}>Copiar eventos</button>
              </div>
            </div>
            <pre className="dev-diagnostics__pre">
              {recentLogs.length > 0 ? JSON.stringify(recentLogs, null, 2) : 'Sem logs ainda.'}
            </pre>
          </div>
        </div>
      ) : null}
    </div>
  )
}