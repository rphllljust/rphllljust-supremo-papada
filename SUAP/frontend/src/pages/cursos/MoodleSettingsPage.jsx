import { useState, useEffect } from 'react'
import toast from 'react-hot-toast'
import client from '@/api/client'

function getErrorMessage(error, fallback) {
  const data = error?.response?.data
  if (!data) return fallback || 'Erro desconhecido'
  if (typeof data.detail === 'string') return data.detail
  const firstValue = Object.values(data)[0]
  return Array.isArray(firstValue) ? firstValue[0] : (firstValue || fallback)
}

export default function MoodleSettingsPage() {
  const [loading, setLoading] = useState(false)
  const [status, setStatus] = useState(null)
  const [lastResponse, setLastResponse] = useState(null)

  // Request editor state
  const [method, setMethod] = useState('get')
  const [path, setPath] = useState('/integracoes/moodle/categorias/')
  const [paramsText, setParamsText] = useState(JSON.stringify({ perpage: 1 }, null, 2))
  const [dataText, setDataText] = useState('{}')
  const [wstoken, setWstoken] = useState('')
  const [restFormat, setRestFormat] = useState('json')
  const [baseUrl, setBaseUrl] = useState('')
  const [restPath, setRestPath] = useState('/webservice/rest/server.php')
  const [timeout, setTimeoutValue] = useState('')
  const [verifySsl, setVerifySsl] = useState(true)

  async function testConnection() {
    setLoading(true)
    setStatus(null)
    setLastResponse(null)

    let params = undefined
    let data = undefined
    try {
      params = paramsText ? JSON.parse(paramsText) : undefined
    } catch (err) {
      toast.error('Parâmetros inválidos (JSON).')
      setLoading(false)
      return
    }

    try {
      data = dataText ? JSON.parse(dataText) : undefined
    } catch (err) {
      toast.error('Body inválido (JSON).')
      setLoading(false)
      return
    }

    // inject token and format into params if provided
    if (!params) params = {}
    if (wstoken) params.wstoken = wstoken
    if (restFormat) params.moodlewsrestformat = restFormat

    const start = Date.now()
    try {
      let res
      const opts = {}
      if (params) opts.params = params
      if (method.toLowerCase() === 'get') {
        res = await client.get(path, opts)
      } else if (method.toLowerCase() === 'post') {
        res = await client.post(path, data || {}, opts)
      } else if (method.toLowerCase() === 'put') {
        res = await client.put(path, data || {}, opts)
      } else if (method.toLowerCase() === 'delete') {
        res = await client.delete(path, opts)
      } else {
        throw new Error('Método não suportado')
      }

      const elapsed = Date.now() - start
      setStatus('ok')
      setLastResponse({ status: res.status, elapsed, data: res.data })
      toast.success('Requisição bem sucedida')
    } catch (err) {
      const elapsed = Date.now() - start
      setStatus('error')
      setLastResponse({ message: getErrorMessage(err, 'Falha na requisição'), elapsed, response: err.response?.data })
      toast.error('Falha na requisição')
    } finally {
      setLoading(false)
    }
  }

  async function testSiteInfo() {
    setLoading(true)
    setStatus(null)
    setLastResponse(null)

    const payload = {}
    if (wstoken) payload.wstoken = wstoken
    if (restFormat) payload.moodlewsrestformat = restFormat

    const start = Date.now()
    try {
      const res = await client.post('/api/v1/integracoes/moodle/test-connection/', payload)
      const elapsed = Date.now() - start
      setStatus('ok')
      setLastResponse({ status: res.status, elapsed, data: res.data })
      toast.success('Conexão com o Moodle OK')
    } catch (err) {
      const elapsed = Date.now() - start
      setStatus('error')
      setLastResponse({ message: getErrorMessage(err, 'Falha na conexão'), elapsed, response: err.response?.data })
      toast.error('Falha na conexão com o Moodle')
    } finally {
      setLoading(false)
    }
  }

  async function loadConfig() {
    try {
      const res = await client.get('/api/v1/integracoes/moodle/config/')
      const data = res.data || {}
      setBaseUrl(data.base_url || '')
      setWstoken(data.wstoken || '')
      setRestFormat(data.moodlewsrestformat || 'json')
      setRestPath(data.rest_path || '/webservice/rest/server.php')
      setTimeoutValue(data.timeout ?? '')
      setVerifySsl(data.verify_ssl ?? true)
    } catch (err) {
      // ignore - show empty defaults
    }
  }

  async function saveConfig() {
    setLoading(true)
    try {
      const payload = {
        base_url: baseUrl,
        wstoken: wstoken,
        moodlewsrestformat: restFormat,
        rest_path: restPath,
        timeout: timeout ? Number(timeout) : null,
        verify_ssl: verifySsl,
      }
      await client.post('/api/v1/integracoes/moodle/config/', payload)
      toast.success('Configurações salvas')
    } catch (err) {
      toast.error(getErrorMessage(err, 'Falha ao salvar configurações'))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadConfig()
  }, [])

  return (
    <div className="page page--wide moodle-settings-page">
      <nav className="profile-breadcrumb">
        <a href="/dashboard">Início</a>
        <span className="profile-breadcrumb__sep">›</span>
        <span>Ensino</span>
        <span className="profile-breadcrumb__sep">›</span>
        <span>Configurações Moodle</span>
      </nav>

      <div className="page-header">
        <div>
          <h1 className="page-title">Configurações do Moodle</h1>
          <p className="page-subtitle">Testes manuais e ajustes rápidos da integração com o Moodle.</p>
        </div>
      </div>

      <div className="page-content" style={{maxWidth: 980}}>
        <section className="search-card">
          <div style={{display: 'grid', gridTemplateColumns: '1fr auto', gap: 12, alignItems: 'start'}}>
            <div>
              <label style={{display: 'block', fontWeight: 700, marginBottom: 6}}>Método</label>
              <select value={method} onChange={(e) => setMethod(e.target.value)} style={{padding: 8, borderRadius: 8}}>
                <option value="get">GET</option>
                <option value="post">POST</option>
                <option value="put">PUT</option>
                <option value="delete">DELETE</option>
              </select>

              <label style={{display: 'block', fontWeight: 700, marginTop: 12, marginBottom: 6}}>Path (relative to API)</label>
              <input value={path} onChange={(e) => setPath(e.target.value)} style={{width: '100%', padding: 8, borderRadius: 8, border: '1px solid var(--color-gray-300)'}} />

              <div style={{marginTop: 12}}>
                <label style={{display: 'block', fontWeight: 700, marginBottom: 6}}>wstoken</label>
                <input value={wstoken} onChange={(e) => setWstoken(e.target.value)} placeholder="token do Moodle" style={{width: '100%', padding: 8, borderRadius: 8, border: '1px solid var(--color-gray-300)'}} />
              </div>

              <div style={{marginTop: 12}}>
                <label style={{display: 'block', fontWeight: 700, marginBottom: 6}}>moodlewsrestformat</label>
                <input value={restFormat} onChange={(e) => setRestFormat(e.target.value)} style={{width: '100%', padding: 8, borderRadius: 8, border: '1px solid var(--color-gray-300)'}} />
              </div>
            </div>

            <div style={{display: 'flex', gap: 8}}>
              <button type="button" className="button" onClick={testConnection} disabled={loading}>
                {loading ? 'Executando...' : 'Executar requisição'}
              </button>
              <button type="button" className="button button--secondary" onClick={testSiteInfo} disabled={loading}>
                Testar conexão Moodle
              </button>
              <button type="button" className="button" onClick={() => { setParamsText('{}'); setDataText('{}'); }}>
                Resetar
              </button>
            </div>
          </div>

          <div style={{display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginTop: 12}}>
            <div>
              <label style={{display: 'block', fontWeight: 700, marginBottom: 6}}>Params (JSON)</label>
              <textarea value={paramsText} onChange={(e) => setParamsText(e.target.value)} rows={6} style={{width: '100%', padding: 8, borderRadius: 8, border: '1px solid var(--color-gray-300)', fontFamily: 'monospace'}} />
            </div>

            <div>
              <label style={{display: 'block', fontWeight: 700, marginBottom: 6}}>Body (JSON)</label>
              <textarea value={dataText} onChange={(e) => setDataText(e.target.value)} rows={6} style={{width: '100%', padding: 8, borderRadius: 8, border: '1px solid var(--color-gray-300)', fontFamily: 'monospace'}} />
            </div>
          </div>

          {status ? (
            <div style={{marginTop: 16, display: 'grid', gridTemplateColumns: '280px 1fr', gap: 12}}>
              <div style={{padding: 12, border: '1px solid var(--color-gray-200)', borderRadius: 8}}>
                <div style={{fontWeight: 700, marginBottom: 8}}>Status</div>
                <div style={{marginBottom: 6}}>{status === 'ok' ? 'OK' : 'Erro'}</div>
                <div style={{fontWeight: 700, marginTop: 8}}>Tempo de resposta</div>
                <div>{lastResponse?.elapsed ? `${lastResponse.elapsed} ms` : '—'}</div>
                <div style={{fontWeight: 700, marginTop: 8}}>HTTP</div>
                <div>{lastResponse?.status ?? (lastResponse?.response ? 'erro' : '—')}</div>
              </div>

              <div style={{padding: 12, border: '1px solid var(--color-gray-200)', borderRadius: 8}}>
                <div style={{fontWeight: 700, marginBottom: 8}}>Resposta completa</div>
                <pre className="dev-diagnostics__pre" style={{marginTop: 8}}>
                  {lastResponse ? JSON.stringify(lastResponse, null, 2) : '—'}
                </pre>
              </div>
            </div>
          ) : null}
        </section>
      </div>
    </div>
  )
}
