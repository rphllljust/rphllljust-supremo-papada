import { useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Copy, ExternalLink, FileSpreadsheet, RefreshCcw, ShieldCheck } from 'lucide-react'
import toast from 'react-hot-toast'

import { dashboardApi } from '@/api/endpoints'

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
  const { data, isLoading, isError, error, isFetching, refetch } = useQuery({
    queryKey: ['dashboard-sheets-module'],
    queryFn: () => dashboardApi.sheetsModule({ limit: 40 }).then((response) => response.data),
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

  return (
    <div className="page page--wide sheets-read-module">
      <div className="page-header">
        <div>
          <h1 className="page-title">Leitura Google Sheets</h1>
          <p className="page-subtitle">
            Modulo implantado para leitura: exportacao CSV, formula do Sheets e pre-visualizacao em tempo real.
          </p>
        </div>
        <div className="sheets-read-module__actions">
          <button type="button" className="btn btn--secondary" onClick={() => refetch()} disabled={isFetching}>
            <RefreshCcw size={16} />
            {isFetching ? 'Atualizando...' : 'Atualizar leitura'}
          </button>
        </div>
      </div>

      {isError ? (
        <div className="alert alert--error">
          {getErrorMessage(error, 'Nao foi possivel carregar o modulo de leitura do Google Sheets.')}
        </div>
      ) : null}

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

      <section className="dashboard-card">
        <div className="sheets-read-module__status-head">
          <h2 className="dashboard-card__title">
            <FileSpreadsheet size={18} />
            <span>Pre-visualizacao dos dados lidos</span>
          </h2>
          <span className="badge badge--info">
            {previewRows.length} linha(s)
          </span>
        </div>

        {previewRows.length ? (
          <div className="table-wrapper sheets-read-module__table-wrap">
            <table className="sheets-read-module__table">
              <thead>
                <tr>
                  {previewColumns.map((column) => (
                    <th key={column}>{column}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {previewRows.map((row, rowIndex) => (
                  <tr key={`row-${rowIndex}`}>
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
      </section>
    </div>
  )
}
