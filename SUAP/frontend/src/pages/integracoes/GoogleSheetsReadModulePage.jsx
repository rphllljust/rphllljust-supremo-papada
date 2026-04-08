import { useEffect, useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  CheckCircle2,
  Copy,
  Database,
  ExternalLink,
  FileSpreadsheet,
  Filter,
  Link2,
  RefreshCcw,
  Search,
  ShieldCheck,
  Table2,
} from 'lucide-react'
import toast from 'react-hot-toast'

import { dashboardApi } from '@/api/endpoints'

const SOURCE_URL_STORAGE_KEY = 'suap.google_sheets.source_url'

function parseSourceUrls(text) {
  return Array.from(new Set(
    String(text || '')
      .split(/\r?\n/g)
      .map((item) => item.trim())
      .filter(Boolean),
  ))
}

function copyToClipboard(value, label) {
  if (!value) return
  navigator.clipboard.writeText(value)
    .then(() => toast.success(`${label} copiado.`))
    .catch(() => toast.error(`Nao foi possivel copiar ${label.toLowerCase()}.`))
}

function getErrorMessage(error, fallback) {
  const detail = error?.response?.data?.detail
  if (typeof detail === 'string' && detail.trim()) return detail
  return fallback
}

export default function GoogleSheetsReadModulePage() {
  const [activeSection, setActiveSection] = useState('all')
  const [searchTerm, setSearchTerm] = useState('')
  const [sourceInputUrlsText, setSourceInputUrlsText] = useState(() => localStorage.getItem(SOURCE_URL_STORAGE_KEY) || '')
  const [sourceAppliedUrlsText, setSourceAppliedUrlsText] = useState(() => localStorage.getItem(SOURCE_URL_STORAGE_KEY) || '')
  const [serviceAccountJsonInput, setServiceAccountJsonInput] = useState('')
  const [savingServiceAccount, setSavingServiceAccount] = useState(false)
  const sourceAppliedUrls = useMemo(() => parseSourceUrls(sourceAppliedUrlsText), [sourceAppliedUrlsText])

  const { data, isLoading, isError, error, isFetching, refetch } = useQuery({
    queryKey: ['dashboard-sheets-module', sourceAppliedUrlsText],
    queryFn: () => dashboardApi.sheetsModule({
      limit: 40,
      ...(sourceAppliedUrlsText ? { source_urls_text: sourceAppliedUrlsText } : {}),
    }).then((response) => response.data),
    staleTime: 30_000,
    refetchInterval: 60_000,
  })

  const summaryCards = useMemo(() => {
    const summary = data?.summary || {}
    return [
      { key: 'recent_enrollments', label: 'Matriculas (7 dias)', value: summary.recent_enrollments ?? 0 },
      { key: 'document_pending', label: 'Pendencias documentais', value: summary.document_pending ?? 0 },
      { key: 'classes_without_students', label: 'Turmas sem alunos', value: summary.classes_without_students ?? 0 },
      { key: 'upcoming_deadlines', label: 'Prazos proximos', value: summary.upcoming_deadlines ?? 0 },
    ]
  }, [data])

  const previewColumns = data?.preview_columns || []
  const previewRows = data?.preview_rows || []
  const csvUrl = data?.export_url_with_token || data?.export_url || ''
  const sourceBadgeLabel = data?.source_is_external ? 'Google Sheets externo' : 'Leitura interna'
  const sourceCsvUrl = data?.source_csv_url || ''
  const sourceInputUrls = data?.source_input_urls || (data?.source_input_url ? [data.source_input_url] : [])
  const sourceCsvUrls = data?.source_csv_urls || (sourceCsvUrl ? [sourceCsvUrl] : [])
  const sourceErrors = data?.source_errors || []
  const serviceAccountEmail = data?.service_account_email || ''
  const serviceAccountError = data?.service_account_error || ''

  const generatedAtLabel = useMemo(() => {
    if (!data?.generated_at) return '-'
    const generatedAtDate = new Date(data.generated_at)
    if (Number.isNaN(generatedAtDate.getTime())) return '-'
    return new Intl.DateTimeFormat('pt-BR', {
      dateStyle: 'short',
      timeStyle: 'medium',
    }).format(generatedAtDate)
  }, [data?.generated_at])

  const sectionCounters = useMemo(() => {
    const counters = {}
    previewRows.forEach((row) => {
      const section = row?.secao || 'sem_secao'
      counters[section] = (counters[section] || 0) + 1
    })
    return counters
  }, [previewRows])

  const sectionOptions = useMemo(() => {
    const sections = Object.keys(sectionCounters)
    return sections.sort((a, b) => {
      if (a === 'summary') return -1
      if (b === 'summary') return 1
      return a.localeCompare(b)
    })
  }, [sectionCounters])

  useEffect(() => {
    if (activeSection !== 'all' && !sectionOptions.includes(activeSection)) {
      setActiveSection('all')
    }
  }, [activeSection, sectionOptions])

  const filteredRows = useMemo(() => {
    const term = searchTerm.trim().toLowerCase()

    return previewRows.filter((row) => {
      if (activeSection !== 'all' && row?.secao !== activeSection) {
        return false
      }

      if (!term) {
        return true
      }

      return previewColumns.some((column) => String(row?.[column] || '').toLowerCase().includes(term))
    })
  }, [activeSection, previewColumns, previewRows, searchTerm])

  const applySourceUrls = () => {
    const normalized = parseSourceUrls(sourceInputUrlsText).join('\n')
    setSourceAppliedUrlsText(normalized)
    if (normalized) {
      localStorage.setItem(SOURCE_URL_STORAGE_KEY, normalized)
    } else {
      localStorage.removeItem(SOURCE_URL_STORAGE_KEY)
    }
  }

  const clearSourceUrls = () => {
    setSourceInputUrlsText('')
    setSourceAppliedUrlsText('')
    localStorage.removeItem(SOURCE_URL_STORAGE_KEY)
  }

  const saveServiceAccount = async () => {
    const payload = serviceAccountJsonInput.trim()
    if (!payload) {
      toast.error('Cole o JSON da conta de servico.')
      return
    }

    setSavingServiceAccount(true)
    try {
      const response = await dashboardApi.saveSheetsServiceAccount({ service_account_json: payload })
      toast.success(response?.data?.message || 'Credencial salva com sucesso.')
      setServiceAccountJsonInput('')
      await refetch()
    } catch (requestError) {
      toast.error(getErrorMessage(requestError, 'Nao foi possivel salvar a credencial Google Sheets.'))
    } finally {
      setSavingServiceAccount(false)
    }
  }

  const removeServiceAccount = async () => {
    setSavingServiceAccount(true)
    try {
      const response = await dashboardApi.saveSheetsServiceAccount({ clear_service_account: true })
      toast.success(response?.data?.message || 'Credencial removida.')
      await refetch()
    } catch (requestError) {
      toast.error(getErrorMessage(requestError, 'Nao foi possivel remover a credencial Google Sheets.'))
    } finally {
      setSavingServiceAccount(false)
    }
  }

  return (
    <div className="page page--wide sheets-read-module">
      <div className="page-header">
        <div>
          <h1 className="page-title">Leitura Google Sheets</h1>
          <p className="page-subtitle">
            Cole a URL da planilha Google Sheets para ler os dados dentro do SUAP, com tabela organizada por secao.
          </p>
        </div>
        <div className="sheets-read-module__actions">
          <button type="button" className="btn btn--secondary" onClick={() => refetch()} disabled={isFetching}>
            <RefreshCcw size={16} />
            {isFetching ? 'Atualizando...' : 'Atualizar leitura'}
          </button>
        </div>
      </div>

      <section className="dashboard-card sheets-read-module__quick-status">
        <article className="sheets-read-module__quick-status-item">
          <span>Integracao</span>
          <strong>{data?.integrated ? 'Ativa' : 'Pendente'}</strong>
        </article>
        <article className="sheets-read-module__quick-status-item">
          <span>Origem ativa</span>
          <strong>{sourceBadgeLabel}</strong>
        </article>
        <article className="sheets-read-module__quick-status-item">
          <span>Planilhas carregadas</span>
          <strong>{data?.source_total_loaded ?? (data?.source_is_external ? sourceInputUrls.length : 0)}</strong>
        </article>
        <article className="sheets-read-module__quick-status-item">
          <span>URL publica</span>
          <strong>{data?.public_base_url || '-'}</strong>
        </article>
        <article className="sheets-read-module__quick-status-item">
          <span>Ultima geracao</span>
          <strong>{generatedAtLabel}</strong>
        </article>
      </section>

      {isError ? (
        <div className="alert alert--error">
          {getErrorMessage(error, 'Nao foi possivel carregar o modulo de leitura do Google Sheets.')}
        </div>
      ) : null}

      <section className="dashboard-card sheets-read-module__source-card">
        <div className="sheets-read-module__status-head">
          <h2 className="dashboard-card__title">
            <Link2 size={18} />
            <span>Fonte da leitura</span>
          </h2>
          <span className={`badge ${data?.source_is_external ? 'badge--success' : 'badge--info'}`}>
            {sourceBadgeLabel}
          </span>
        </div>

        <p className="sheets-read-module__source-description">
          Cole uma URL por linha para carregar varias planilhas no SUAP.
        </p>

        {serviceAccountEmail ? (
          <p className="sheets-read-module__source-description">
            Conta de servico: <strong>{serviceAccountEmail}</strong>
          </p>
        ) : null}

        {serviceAccountError ? (
          <div className="alert alert--warning">
            {serviceAccountError}
          </div>
        ) : null}

        <div className="sheets-read-module__service-account-block">
          <label>Credencial Service Account (JSON)</label>
          <textarea
            className="form-control"
            value={serviceAccountJsonInput}
            onChange={(event) => setServiceAccountJsonInput(event.target.value)}
            placeholder='{"type":"service_account","client_email":"...","private_key":"..."}'
            rows={4}
          />
          <div className="sheets-read-module__panel-actions">
            <button
              type="button"
              className="btn btn--secondary"
              onClick={saveServiceAccount}
              disabled={savingServiceAccount}
            >
              Salvar credencial
            </button>
            <button
              type="button"
              className="btn btn--outline"
              onClick={removeServiceAccount}
              disabled={savingServiceAccount || !serviceAccountEmail}
            >
              Remover credencial
            </button>
          </div>
        </div>

        <div className="sheets-read-module__source-row">
          <textarea
            className="form-control"
            value={sourceInputUrlsText}
            onChange={(event) => setSourceInputUrlsText(event.target.value)}
            placeholder={'https://docs.google.com/spreadsheets/d/.../edit#gid=0\nhttps://docs.google.com/spreadsheets/d/.../edit#gid=0'}
            rows={4}
          />
          <button
            type="button"
            className="btn btn--primary"
            onClick={applySourceUrls}
            disabled={isFetching}
          >
            Aplicar planilhas
          </button>
          <button
            type="button"
            className="btn btn--outline"
            onClick={clearSourceUrls}
            disabled={!sourceInputUrlsText && !sourceAppliedUrlsText}
          >
            Limpar
          </button>
        </div>

        <div className="sheets-read-module__source-details">
          <article className="sheets-read-module__source-meta">
            <span>Fontes enviadas</span>
            <strong>{sourceInputUrls.length ? `${sourceInputUrls.length} planilha(s)` : '-'}</strong>
          </article>
          <article className="sheets-read-module__source-meta">
            <span>CSVs resolvidos</span>
            <strong>{sourceCsvUrls.length ? `${sourceCsvUrls.length} CSV(s)` : '-'}</strong>
          </article>
        </div>

        {sourceInputUrls.length ? (
          <div className="sheets-read-module__source-list">
            {sourceInputUrls.map((item) => (
              <div key={item} className="sheets-read-module__source-list-item">{item}</div>
            ))}
          </div>
        ) : null}

        {sourceErrors.length ? (
          <div className="alert alert--warning">
            {sourceErrors.length} planilha(s) com erro de leitura.
            {sourceErrors.map((item, index) => (
              <div key={`${item.source_url}-${index}`}>
                {item.source_url}: {item.detail}
              </div>
            ))}
          </div>
        ) : null}

        {sourceCsvUrls.length ? (
          <div className="sheets-read-module__panel-actions">
            <button
              type="button"
              className="btn btn--outline"
              onClick={() => copyToClipboard(sourceCsvUrls.join('\n'), 'URLs CSV de origem')}
            >
              <Copy size={14} />
              Copiar CSVs de origem
            </button>
            {sourceCsvUrls[0] ? (
              <a className="btn btn--outline" href={sourceCsvUrls[0]} target="_blank" rel="noreferrer">
                <ExternalLink size={14} />
                Abrir primeira origem
              </a>
            ) : null}
          </div>
        ) : null}
      </section>

      <section className="dashboard-card sheets-read-module__status-card">
        <div className="sheets-read-module__status-head">
          <h2 className="dashboard-card__title">
            <ShieldCheck size={18} />
            <span>Status da Integracao</span>
          </h2>
          <span className={`badge ${data?.integrated ? 'badge--success' : 'badge--warning'}`}>
            {data?.integrated ? 'Ativa' : 'Pendente'}
          </span>
        </div>

        <div className="sheets-read-module__meta-grid">
          {summaryCards.map((card) => (
            <article key={card.key} className="sheets-read-module__meta-item">
              <span>{card.label}</span>
              <strong>{isLoading ? '...' : card.value}</strong>
            </article>
          ))}
        </div>

        <div className="sheets-read-module__field-block">
          <label>URL CSV publica</label>
          <div className="sheets-read-module__field-row">
            <input
              className="form-control"
              readOnly
              value={data?.export_url_with_token || data?.export_url || ''}
              placeholder="Sem URL disponivel"
            />
            <button
              type="button"
              className="btn btn--outline"
              onClick={() => copyToClipboard(data?.export_url_with_token || data?.export_url || '', 'URL')}
              disabled={!data?.export_url && !data?.export_url_with_token}
            >
              <Copy size={14} />
              Copiar
            </button>
            {data?.export_url_with_token ? (
              <a className="btn btn--outline" href={data.export_url_with_token} target="_blank" rel="noreferrer">
                <ExternalLink size={14} />
                Abrir
              </a>
            ) : null}
          </div>
        </div>

        <div className="sheets-read-module__field-block">
          <label>Formula Google Sheets</label>
          <div className="sheets-read-module__field-row">
            <input
              className="form-control"
              readOnly
              value={data?.sheets_formula || ''}
              placeholder="Formula disponivel para perfil ADMIN com token configurado"
            />
            <button
              type="button"
              className="btn btn--outline"
              onClick={() => copyToClipboard(data?.sheets_formula || '', 'Formula')}
              disabled={!data?.sheets_formula}
            >
              <Copy size={14} />
              Copiar
            </button>
          </div>
        </div>
      </section>

      <section className="dashboard-card sheets-read-module__connection-card">
        <div className="sheets-read-module__status-head">
          <h2 className="dashboard-card__title">
            <Link2 size={18} />
            <span>Conexao com o Google Sheets</span>
          </h2>
          <span className="badge badge--info">
            Token protegido
          </span>
        </div>

        <div className="sheets-read-module__connection-grid">
          <article className="sheets-read-module__connection-panel">
            <header>
              <h3>1. URL CSV publica</h3>
              <p>Use para importar dados no Sheets ou integrar com outro sistema.</p>
            </header>
            <textarea
              className="form-control sheets-read-module__multiline-input"
              readOnly
              value={csvUrl}
              placeholder="Sem URL disponivel"
              rows={3}
            />
            <div className="sheets-read-module__panel-actions">
              <button
                type="button"
                className="btn btn--outline"
                onClick={() => copyToClipboard(csvUrl, 'URL')}
                disabled={!csvUrl}
              >
                <Copy size={14} />
                Copiar URL
              </button>
              {csvUrl ? (
                <a className="btn btn--outline" href={csvUrl} target="_blank" rel="noreferrer">
                  <ExternalLink size={14} />
                  Abrir CSV
                </a>
              ) : null}
            </div>
          </article>

          <article className="sheets-read-module__connection-panel">
            <header>
              <h3>2. Formula pronta</h3>
              <p>Cole direto em uma celula para preencher a planilha automaticamente.</p>
            </header>
            <textarea
              className="form-control sheets-read-module__multiline-input"
              readOnly
              value={data?.sheets_formula || ''}
              placeholder="Formula disponivel para perfil ADMIN com token configurado"
              rows={3}
            />
            <div className="sheets-read-module__panel-actions">
              <button
                type="button"
                className="btn btn--outline"
                onClick={() => copyToClipboard(data?.sheets_formula || '', 'Formula')}
                disabled={!data?.sheets_formula}
              >
                <Copy size={14} />
                Copiar formula
              </button>
            </div>
          </article>
        </div>

        <div className="sheets-read-module__steps">
          <div className="sheets-read-module__step">
            <CheckCircle2 size={16} />
            <span>Passo 1: copie a URL CSV ou a formula.</span>
          </div>
          <div className="sheets-read-module__step">
            <CheckCircle2 size={16} />
            <span>Passo 2: cole no Google Sheets com `IMPORTDATA`.</span>
          </div>
          <div className="sheets-read-module__step">
            <CheckCircle2 size={16} />
            <span>Passo 3: clique em atualizar leitura para conferir.</span>
          </div>
        </div>
      </section>

      <section className="dashboard-card">
        <div className="sheets-read-module__status-head">
          <h2 className="dashboard-card__title">
            <FileSpreadsheet size={18} />
            <span>Pre-visualizacao dos dados lidos</span>
          </h2>
          <span className="badge badge--info">
            {filteredRows.length} de {previewRows.length} linha(s)
          </span>
        </div>

        <div className="sheets-read-module__section-overview">
          <div className="sheets-read-module__section-overview-title">
            <Database size={16} />
            <span>Linhas por secao</span>
          </div>
          <div className="sheets-read-module__section-overview-grid">
            <button
              type="button"
              className={`sheets-read-module__section-chip ${activeSection === 'all' ? 'sheets-read-module__section-chip--active' : ''}`}
              onClick={() => setActiveSection('all')}
            >
              <span>Todas</span>
              <strong>{previewRows.length}</strong>
            </button>
            {sectionOptions.map((section) => (
              <button
                type="button"
                key={section}
                className={`sheets-read-module__section-chip ${activeSection === section ? 'sheets-read-module__section-chip--active' : ''}`}
                onClick={() => setActiveSection(section)}
              >
                <span>{section}</span>
                <strong>{sectionCounters[section]}</strong>
              </button>
            ))}
          </div>
        </div>

        <div className="sheets-read-module__filter-row">
          <div className="sheets-read-module__filter-label">
            <Filter size={14} />
            <span>Filtro rapido</span>
          </div>
          <label className="sheets-read-module__search-box">
            <Search size={14} />
            <input
              type="text"
              value={searchTerm}
              onChange={(event) => setSearchTerm(event.target.value)}
              placeholder="Pesquisar em qualquer coluna..."
            />
          </label>
        </div>

        {previewRows.length ? (
          <div className="table-wrapper sheets-read-module__table-wrap">
            <table className="sheets-read-module__table">
              <thead>
                <tr>
                  <th>#</th>
                  {previewColumns.map((column) => (
                    <th key={column}>{column}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {filteredRows.map((row, rowIndex) => (
                  <tr key={`row-${rowIndex}`}>
                    <td>{rowIndex + 1}</td>
                    {previewColumns.map((column) => (
                      <td key={`${rowIndex}-${column}`}>{row[column] || '-'}</td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="dashboard-empty">
            Nenhum dado retornado para leitura no momento.
          </p>
        )}

        {previewRows.length && !filteredRows.length ? (
          <p className="dashboard-empty">
            Nenhuma linha encontrada com o filtro atual.
          </p>
        ) : null}
      </section>

      <section className="dashboard-card sheets-read-module__dataset-card">
        <div className="sheets-read-module__status-head">
          <h2 className="dashboard-card__title">
            <Table2 size={18} />
            <span>Resumo da leitura</span>
          </h2>
        </div>
        <div className="sheets-read-module__dataset-grid">
          <article>
            <span>Colunas disponiveis</span>
            <strong>{previewColumns.length}</strong>
          </article>
          <article>
            <span>Secoes encontradas</span>
            <strong>{sectionOptions.length}</strong>
          </article>
          <article>
            <span>Linhas carregadas</span>
            <strong>{previewRows.length}</strong>
          </article>
          <article>
            <span>Leitura filtrada</span>
            <strong>{filteredRows.length}</strong>
          </article>
        </div>
      </section>
    </div>
  )
}
