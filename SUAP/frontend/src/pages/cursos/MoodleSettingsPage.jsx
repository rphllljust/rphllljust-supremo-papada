import { useEffect, useMemo, useState } from 'react'
import toast from 'react-hot-toast'
import client from '@/api/client'

const REQUEST_PRESETS = {
  categoriasEspelho: {
    label: 'Espelho local de categorias',
    method: 'get',
    path: '/integracoes/moodle/espelho/categorias/',
    params: {},
    data: {},
  },
  cursosEspelho: {
    label: 'Espelho local de cursos',
    method: 'get',
    path: '/integracoes/moodle/espelho/cursos/',
    params: { tipo_curso: 'formacao_inicial' },
    data: {},
  },
  categoriasSync: {
    label: 'Sincronizar categorias Moodle',
    method: 'post',
    path: '/integracoes/moodle/sincronizar/categorias/',
    params: {},
    data: {},
  },
  cursosIniciaisSync: {
    label: 'Sincronizar cursos iniciais',
    method: 'post',
    path: '/integracoes/moodle/sincronizar/cursos/',
    params: {},
    data: { tipo_curso: 'formacao_inicial', root_category_ids: [399], integrar_catalogo_interno: true },
  },
  cursosTecnicosSync: {
    label: 'Sincronizar cursos técnicos',
    method: 'post',
    path: '/integracoes/moodle/sincronizar/cursos/',
    params: {},
    data: { tipo_curso: 'tecnico', root_category_ids: [387], integrar_catalogo_interno: true },
  },
  cursosItinerantesSync: {
    label: 'Sincronizar cursos itinerantes',
    method: 'post',
    path: '/integracoes/moodle/sincronizar/cursos/',
    params: {},
    data: { tipo_curso: 'itinerante', root_category_ids: [415], integrar_catalogo_interno: true },
  },
  buscarCursoPorId: {
    label: 'Inspecionar curso no espelho por ID Moodle',
    method: 'get',
    path: '/integracoes/moodle/cursos/',
    params: { action: 'core_course_get_courses_by_field', field: 'id', value: 1 },
    data: {},
  },
}

const QUICK_ACTIONS = [
  {
    key: 'test-connection',
    label: 'Testar conexão',
    description: 'Executa core_webservice_get_site_info usando a configuração persistida.',
    run: ({ executeShortcut }) => executeShortcut('testConnection'),
  },
  {
    key: 'sync-categorias',
    label: 'Sincronizar categorias',
    description: 'Atualiza o espelho local de categorias do Moodle.',
    run: ({ executeShortcut }) => executeShortcut('categoriasSync'),
  },
  {
    key: 'sync-iniciais',
    label: 'Sincronizar cursos iniciais',
    description: 'Importa cursos da raiz 399 e subcategorias para o SUAP.',
    run: ({ executeShortcut }) => executeShortcut('cursosIniciaisSync'),
  },
  {
    key: 'sync-tecnicos',
    label: 'Sincronizar cursos técnicos',
    description: 'Importa cursos da raiz 387 e subcategorias para o SUAP.',
    run: ({ executeShortcut }) => executeShortcut('cursosTecnicosSync'),
  },
  {
    key: 'sync-itinerantes',
    label: 'Sincronizar cursos itinerantes',
    description: 'Importa cursos da raiz 415 e subcategorias para o SUAP.',
    run: ({ executeShortcut }) => executeShortcut('cursosItinerantesSync'),
  },
  {
    key: 'reset-local',
    label: 'Resetar espelho local',
    description: 'Apaga o espelho local e o reconstrói a partir do Moodle.',
    run: ({ runRequest }) => runRequest({ method: 'post', path: '/integracoes/moodle/reset-local-and-sync/', params: {}, data: {} }, 'Espelho local reinicializado com sucesso.'),
  },
]

function getErrorMessage(error, fallback) {
  const data = error?.response?.data
  if (!data) return fallback || 'Erro desconhecido'
  if (typeof data.detail === 'string') return data.detail
  const firstValue = Object.values(data)[0]
  return Array.isArray(firstValue) ? firstValue[0] : (firstValue || fallback)
}

function parseJson(text, fallback, label) {
  if (!text || !text.trim()) {
    return fallback
  }

  try {
    return JSON.parse(text)
  } catch (_error) {
    throw new Error(`${label} inválido(a) em JSON.`)
  }
}

function getCount(payload) {
  if (!payload) return 0
  if (typeof payload.count === 'number') return payload.count
  if (Array.isArray(payload.results)) return payload.results.length
  if (Array.isArray(payload)) return payload.length
  return 0
}

export default function MoodleSettingsPage() {
  const [loading, setLoading] = useState(false)
  const [status, setStatus] = useState(null)
  const [lastResponse, setLastResponse] = useState(null)
  const [stats, setStats] = useState(null)
  const [presetKey, setPresetKey] = useState('categoriasEspelho')

  const [method, setMethod] = useState('get')
  const [path, setPath] = useState('/integracoes/moodle/espelho/categorias/')
  const [paramsText, setParamsText] = useState(JSON.stringify({}, null, 2))
  const [dataText, setDataText] = useState('{}')
  const [wstoken, setWstoken] = useState('')
  const [restFormat, setRestFormat] = useState('json')
  const [baseUrl, setBaseUrl] = useState('')
  const [restPath, setRestPath] = useState('/webservice/rest/server.php')
  const [timeout, setTimeoutValue] = useState('')
  const [verifySsl, setVerifySsl] = useState(true)

  const activePreset = useMemo(() => REQUEST_PRESETS[presetKey] || REQUEST_PRESETS.categoriasEspelho, [presetKey])

  async function runRequest(request, successMessage) {
    setLoading(true)
    setStatus(null)
    setLastResponse(null)

    try {
      const params = request.params || {}
      const data = request.data || {}

      let res
      const opts = {}
      if (params) opts.params = params
      const start = Date.now()

      if (request.method === 'get') {
        res = await client.get(request.path, opts)
      } else if (request.method === 'post') {
        res = await client.post(request.path, data || {}, opts)
      } else if (request.method === 'put') {
        res = await client.put(request.path, data || {}, opts)
      } else if (request.method === 'delete') {
        res = await client.delete(request.path, opts)
      } else {
        throw new Error('Método não suportado')
      }

      const elapsed = Date.now() - start
      setStatus('ok')
      setLastResponse({ status: res.status, elapsed, request, data: res.data })
      toast.success(successMessage || 'Requisição concluída com sucesso.')
      await loadDashboardData({ silent: true })
      return res
    } catch (err) {
      setStatus('error')
      setLastResponse({ message: getErrorMessage(err, 'Falha na requisição'), request, response: err.response?.data })
      toast.error(getErrorMessage(err, 'Falha na requisição'))
      throw err
    } finally {
      setLoading(false)
    }
  }

  async function testConnection() {
    let params
    let data

    try {
      params = parseJson(paramsText, {}, 'Parâmetros')
      data = parseJson(dataText, {}, 'Body')
    } catch (error) {
      toast.error(error.message)
      return
    }

    if (wstoken) params.wstoken = wstoken
    if (restFormat) params.moodlewsrestformat = restFormat

    await runRequest({ method, path, params, data }, 'Requisição executada com sucesso.')
  }

  async function testSiteInfo() {
    const payload = {}
    if (wstoken) payload.wstoken = wstoken
    if (restFormat) payload.moodlewsrestformat = restFormat
    await runRequest(
      {
        method: 'post',
        path: '/integracoes/moodle/test-connection/',
        params: {},
        data: payload,
      },
      'Conexão com o Moodle OK.',
    )
  }

  async function loadConfig() {
    try {
      const res = await client.get('/integracoes/moodle/config/')
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

  async function loadDashboardData({ silent = false } = {}) {
    if (!silent) {
      setLoading(true)
    }

    try {
      await loadConfig()
      const [categoriasRes, cursosRes, iniciaisRes, tecnicosRes, itinerantesRes] = await Promise.all([
        client.get('/integracoes/moodle/espelho/categorias/'),
        client.get('/integracoes/moodle/espelho/cursos/'),
        client.get('/cursos/', { params: { tipo_curso: 'formacao_inicial', page: 1 } }),
        client.get('/cursos/', { params: { tipo_curso: 'tecnico', page: 1 } }),
        client.get('/cursos/', { params: { tipo_curso: 'itinerante', page: 1 } }),
      ])

      setStats({
        categoriasEspelho: getCount(categoriasRes.data),
        cursosEspelho: getCount(cursosRes.data),
        cursosIniciais: getCount(iniciaisRes.data),
        cursosTecnicos: getCount(tecnicosRes.data),
        cursosItinerantes: getCount(itinerantesRes.data),
      })
    } catch (error) {
      if (!silent) {
        toast.error(getErrorMessage(error, 'Não foi possível atualizar o painel da integração Moodle.'))
      }
    } finally {
      if (!silent) {
        setLoading(false)
      }
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
      await client.post('/integracoes/moodle/config/', payload)
      toast.success('Configurações salvas')
      await loadDashboardData({ silent: true })
    } catch (err) {
      toast.error(getErrorMessage(err, 'Falha ao salvar configurações'))
    } finally {
      setLoading(false)
    }
  }

  async function executeShortcut(shortcutKey) {
    if (shortcutKey === 'testConnection') {
      await testSiteInfo()
      return
    }

    const preset = REQUEST_PRESETS[shortcutKey]
    if (!preset) {
      toast.error('Atalho não configurado.')
      return
    }

    await runRequest(
      {
        method: preset.method,
        path: preset.path,
        params: preset.params,
        data: preset.data,
      },
      `${preset.label} executado com sucesso.`,
    )
  }

  function applyPreset(nextPresetKey) {
    const preset = REQUEST_PRESETS[nextPresetKey]
    if (!preset) {
      return
    }

    setPresetKey(nextPresetKey)
    setMethod(preset.method)
    setPath(preset.path)
    setParamsText(JSON.stringify(preset.params, null, 2))
    setDataText(JSON.stringify(preset.data, null, 2))
  }

  useEffect(() => {
    loadDashboardData()
  }, [])

  return (
    <div className="page page--wide moodle-settings-page">
      <nav className="profile-breadcrumb">
        <a href="/dashboard">Início</a>
        <span className="profile-breadcrumb__sep">›</span>
        <span>Tecnologia da Informação</span>
        <span className="profile-breadcrumb__sep">›</span>
        <span>Moodle</span>
        <span className="profile-breadcrumb__sep">›</span>
        <span>Central Moodle</span>
      </nav>

      <div className="page-header">
        <div>
          <h1 className="page-title">Central Moodle</h1>
          <p className="page-subtitle">Configuração persistida, diagnósticos, sincronizações e inspeção operacional da integração com o Moodle.</p>
        </div>
        <div className="page-header__actions">
          <button type="button" className="btn btn--secondary" onClick={() => loadDashboardData()} disabled={loading}>
            Atualizar painel
          </button>
          <button type="button" className="btn btn--primary" onClick={saveConfig} disabled={loading}>
            Salvar configuração
          </button>
        </div>
      </div>

      <div className="moodle-settings-grid">
        <section className="dashboard-card moodle-settings-card moodle-settings-card--stats">
          <div className="moodle-settings-card__header">
            <h2 className="dashboard-card__title">Visão rápida</h2>
            <p className="page-subtitle">Estado atual do espelho local e do catálogo SUAP sincronizado.</p>
          </div>

          <div className="moodle-settings-stats">
            <div className="moodle-settings-stat"><strong>{stats?.categoriasEspelho ?? 0}</strong><span>Categorias no espelho</span></div>
            <div className="moodle-settings-stat"><strong>{stats?.cursosEspelho ?? 0}</strong><span>Cursos no espelho</span></div>
            <div className="moodle-settings-stat"><strong>{stats?.cursosIniciais ?? 0}</strong><span>Cursos iniciais no SUAP</span></div>
            <div className="moodle-settings-stat"><strong>{stats?.cursosTecnicos ?? 0}</strong><span>Cursos técnicos no SUAP</span></div>
            <div className="moodle-settings-stat"><strong>{stats?.cursosItinerantes ?? 0}</strong><span>Cursos itinerantes no SUAP</span></div>
          </div>
        </section>

        <section className="dashboard-card moodle-settings-card">
          <div className="moodle-settings-card__header">
            <h2 className="dashboard-card__title">Configuração persistida</h2>
            <p className="page-subtitle">Valores usados pelo backend para autenticar e chamar o Moodle.</p>
          </div>

          <div className="moodle-settings-form-grid">
            <label className="moodle-settings-field">
              <span>Base URL</span>
              <input value={baseUrl} onChange={(event) => setBaseUrl(event.target.value)} placeholder="https://moodle.exemplo.edu.br" />
            </label>
            <label className="moodle-settings-field">
              <span>REST path</span>
              <input value={restPath} onChange={(event) => setRestPath(event.target.value)} placeholder="/webservice/rest/server.php" />
            </label>
            <label className="moodle-settings-field moodle-settings-field--full">
              <span>Token</span>
              <input value={wstoken} onChange={(event) => setWstoken(event.target.value)} placeholder="Token do Moodle" />
            </label>
            <label className="moodle-settings-field">
              <span>Formato</span>
              <input value={restFormat} onChange={(event) => setRestFormat(event.target.value)} />
            </label>
            <label className="moodle-settings-field">
              <span>Timeout (s)</span>
              <input value={timeout} onChange={(event) => setTimeoutValue(event.target.value)} inputMode="numeric" />
            </label>
            <label className="moodle-settings-toggle">
              <input type="checkbox" checked={verifySsl} onChange={(event) => setVerifySsl(event.target.checked)} />
              <span>Validar certificado SSL</span>
            </label>
          </div>

          <div className="page-header__actions">
            <button type="button" className="btn btn--secondary" onClick={testSiteInfo} disabled={loading}>Testar conexão</button>
            <button type="button" className="btn btn--primary" onClick={saveConfig} disabled={loading}>Salvar</button>
          </div>
        </section>

        <section className="dashboard-card moodle-settings-card">
          <div className="moodle-settings-card__header">
            <h2 className="dashboard-card__title">Atalhos operacionais</h2>
            <p className="page-subtitle">Ações administrativas frequentes para manutenção da integração.</p>
          </div>

          <div className="moodle-settings-actions-grid">
            {QUICK_ACTIONS.map((action) => (
              <button
                key={action.key}
                type="button"
                className="moodle-settings-action"
                onClick={() => action.run({ executeShortcut, runRequest })}
                disabled={loading}
              >
                <strong>{action.label}</strong>
                <span>{action.description}</span>
              </button>
            ))}
          </div>
        </section>

        <section className="dashboard-card moodle-settings-card moodle-settings-card--wide">
          <div className="moodle-settings-card__header">
            <h2 className="dashboard-card__title">Execução manual</h2>
            <p className="page-subtitle">Monte chamadas para a API interna do SUAP, valide respostas e inspecione erros com presets reutilizáveis.</p>
          </div>

          <div className="moodle-settings-form-grid moodle-settings-form-grid--compact">
            <label className="moodle-settings-field">
              <span>Preset</span>
              <select value={presetKey} onChange={(event) => applyPreset(event.target.value)}>
                {Object.entries(REQUEST_PRESETS).map(([key, preset]) => (
                  <option key={key} value={key}>{preset.label}</option>
                ))}
              </select>
            </label>
            <label className="moodle-settings-field">
              <span>Método</span>
              <select value={method} onChange={(event) => setMethod(event.target.value)}>
                <option value="get">GET</option>
                <option value="post">POST</option>
                <option value="put">PUT</option>
                <option value="delete">DELETE</option>
              </select>
            </label>

            <label className="moodle-settings-field moodle-settings-field--full">
              <span>Path relativo da API</span>
              <input value={path} onChange={(event) => setPath(event.target.value)} />
            </label>

            <label className="moodle-settings-field">
              <span>Params (JSON)</span>
              <textarea value={paramsText} onChange={(event) => setParamsText(event.target.value)} rows={8} />
            </label>

            <label className="moodle-settings-field">
              <span>Body (JSON)</span>
              <textarea value={dataText} onChange={(event) => setDataText(event.target.value)} rows={8} />
            </label>
          </div>

          <div className="page-header__actions">
            <button type="button" className="btn btn--outline" onClick={() => applyPreset(presetKey)} disabled={loading}>Recarregar preset</button>
            <button type="button" className="btn btn--secondary" onClick={testConnection} disabled={loading}>Executar requisição</button>
          </div>
        </section>

        <section className="dashboard-card moodle-settings-card moodle-settings-card--wide">
          <div className="moodle-settings-card__header">
            <h2 className="dashboard-card__title">Resposta e diagnósticos</h2>
            <p className="page-subtitle">Última execução realizada nesta central, com payload completo e erro detalhado quando houver.</p>
          </div>

          <div className="moodle-settings-response-grid">
            <div className={`moodle-settings-response-status moodle-settings-response-status--${status || 'idle'}`}>
              <strong>Status</strong>
              <span>{status === 'ok' ? 'Sucesso' : status === 'error' ? 'Erro' : 'Aguardando execução'}</span>
              <strong>Preset ativo</strong>
              <span>{activePreset.label}</span>
              <strong>HTTP</strong>
              <span>{lastResponse?.status ?? '—'}</span>
              <strong>Tempo</strong>
              <span>{lastResponse?.elapsed ? `${lastResponse.elapsed} ms` : '—'}</span>
            </div>

            <div className="moodle-settings-response-payload">
              <pre className="dev-diagnostics__pre">{lastResponse ? JSON.stringify(lastResponse, null, 2) : 'Nenhuma execução realizada ainda.'}</pre>
            </div>
          </div>
        </section>
      </div>
    </div>
  )
}
