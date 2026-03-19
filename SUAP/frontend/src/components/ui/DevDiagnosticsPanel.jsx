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
  const [level, setLevel] = useState(() => {
    try {
      return window.__SUAP_DEBUG_LEVEL__ || localStorage.getItem('suap_debug_level') || 'debug'
    } catch (e) {
      return 'debug'
    }
  })

  const levelPriority = (lvl) => {
    if (!lvl) return 10
    const v = String(lvl).toLowerCase()
    if (v === 'debug') return 10
    if (v === 'info') return 20
    if (v === 'error') return 30
    return 10
  }

  function applyLevel(lvl) {
    try {
      window.__SUAP_DEBUG_LEVEL__ = lvl
      localStorage.setItem('suap_debug_level', lvl)
    } catch (e) {}
    setLevel(lvl)
  }

  function colorForLevel(lvl) {
    const v = String(lvl || '').toLowerCase()
    if (v === 'debug') return '#0f766e'
    if (v === 'info') return '#0ea5e9'
    if (v === 'error') return '#dc2626'
    return '#6b7280'
  }

  function injectSample() {
    try {
      const sample = {
        timestamp: '2026-03-19T18:00:59.097Z',
        level: 'error',
        event: 'react_query.mutation_error',
        meta: {
          variables: {
            params: [
              {
                id: 65,
                name: 'dshafkjashksdkjfksdkfsdh',
                description: '',
                parent: 0,
              },
            ],
          },
          error: {
            name: 'AxiosError',
            message: 'Request failed with status code 500',
            stack: "_AxiosError@http://127.0.0.1:5175/node_modules/.vite/deps/axios.js?v=7c093ff6:463:5\nsettle@http://127.0.0.1:5175/node_modules/.vite/deps/axios.js?v=7c093ff6:1319:7\nonloadend@http://127.0.0.1:5175/node_modules/.vite/deps/axios.js?v=7c093ff6:1682:13\n",
          },
        },
      }

      if (typeof window !== 'undefined') {
        if (!Array.isArray(window.__SUAP_DEBUG_LOGS__)) window.__SUAP_DEBUG_LOGS__ = []
        window.__SUAP_DEBUG_LOGS__.push(sample)
        setSnapshot(readLogs())
        toast.success('Exemplo injetado nos logs')
      }
    } catch (e) {
      toast.error('Falha ao injetar exemplo')
    }
  }

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
  // apply filter according to selected `level`
  const filteredLogs = snapshot.logs.filter((l) => {
    try {
      return levelPriority(l.level) >= levelPriority(level)
    } catch (e) {
      return true
    }
  })
  const visibleRecent = filteredLogs.slice(-8).reverse()

  async function copyEvents() {
    const data = JSON.stringify(filteredLogs || [], null, 2)
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

  function clearLogs() {
    if (typeof window === 'undefined') return
    if (!window.confirm('Tem certeza que deseja limpar os logs? Esta ação não pode ser desfeita.')) return
    try {
      window.__SUAP_DEBUG_LOGS__ = []
      window.__SUAP_LAST_FATAL__ = null
      setSnapshot({ logs: [], fatal: null })
      toast.success('Logs limpos')
    } catch (err) {
      toast.error('Falha ao limpar logs')
    }
  }

  return (
    <div className={`dev-diagnostics ${open ? 'dev-diagnostics--open' : ''}`}>
      <button type="button" className="dev-diagnostics__toggle" onClick={() => setOpen((value) => !value)}>
        {open ? 'Ocultar logs' : 'Mostrar logs'}
      </button>

      {open ? (
        <div className="dev-diagnostics__panel">
          <div style={{display: 'flex', gap: 8, marginBottom: 8, alignItems: 'center'}}>
            <div style={{fontWeight:700}}>Nível:</div>
            <div style={{display:'flex', gap:6}}>
              <button type="button" className="dev-diagnostics__button" onClick={() => applyLevel('debug')} style={{background: level === 'debug' ? '#222' : undefined, color: level === 'debug' ? '#fff' : undefined}}>Debug</button>
              <button type="button" className="dev-diagnostics__button" onClick={() => applyLevel('info')} style={{background: level === 'info' ? '#222' : undefined, color: level === 'info' ? '#fff' : undefined}}>Info</button>
              <button type="button" className="dev-diagnostics__button" onClick={() => applyLevel('error')} style={{background: level === 'error' ? '#b91c1c' : undefined, color: level === 'error' ? '#fff' : undefined}}>Error</button>
            </div>
            <div style={{marginLeft: 'auto'}}>
              <button type="button" className="dev-diagnostics__button" onClick={() => injectSample()} style={{background: '#111827', color: '#fff'}}>Injetar exemplo</button>
            </div>
          </div>
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
                <button type="button" className="dev-diagnostics__button" onClick={clearLogs} style={{marginLeft:8}}>Limpar logs</button>
              </div>
            </div>
            <div style={{display: 'flex', flexDirection: 'column', gap: 8, marginTop: 8}}>
              {visibleRecent.length > 0 ? (
                visibleRecent.map((log, i) => {
                  const ts = log.timestamp ? new Date(log.timestamp).toLocaleString() : ''
                  return (
                    <div key={`${log.event}-${i}`} style={{display: 'flex', gap: 12, alignItems: 'flex-start', padding: 8, border: '1px solid rgba(0,0,0,0.06)', borderRadius: 6, background: '#fff'}}>
                      <div style={{minWidth: 140, color: '#444', fontSize: 12}}>{ts}</div>
                      <div style={{minWidth: 86}}>
                        <span style={{display: 'inline-block', padding: '4px 8px', borderRadius: 6, background: colorForLevel(log.level), color: '#fff', fontWeight: 700, fontSize: 12}}>{String(log.level || '').toUpperCase()}</span>
                      </div>
                      <div style={{flex: 1, fontSize: 13}}>
                        <div style={{fontWeight: 700, marginBottom: 4}}>{log.event}</div>
                        {log.meta && log.meta.error ? (
                          <div style={{fontFamily: 'monospace', fontSize: 12, color: '#111'}}>
                            <div style={{fontWeight:700, marginBottom:4}}>{log.meta.error.name || 'Error'}: {log.meta.error.message}</div>
                            <pre style={{whiteSpace: 'pre-wrap', margin: 0, color: '#333'}}>{log.meta.error.stack}</pre>
                          </div>
                        ) : log.meta ? (
                          <pre style={{whiteSpace: 'pre-wrap', margin: 0, fontFamily: 'monospace', fontSize: 12}}>{JSON.stringify(log.meta, null, 2)}</pre>
                        ) : null}
                      </div>
                    </div>
                  )
                })
              ) : (
                <div style={{color: '#666'}}>Sem logs ainda.</div>
              )}
            </div>
          </div>
        </div>
      ) : null}
    </div>
  )
}