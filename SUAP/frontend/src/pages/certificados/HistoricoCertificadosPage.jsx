import { useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'

import { certificadosApi } from '@/api/endpoints'
import DataTable from '@/components/ui/DataTable'

const ACAO_OPTIONS = [
  { value: '', label: 'Todas as acoes' },
  { value: 'EMISSAO', label: 'Emissao' },
  { value: 'EMISSAO_LOTE', label: 'Emissao em lote' },
  { value: 'PREVIEW', label: 'Preview' },
  { value: 'GERACAO_PDF', label: 'Geracao de PDF' },
  { value: 'REIMPRESSAO', label: 'Reimpressao' },
  { value: 'VALIDACAO_PUBLICA', label: 'Validacao publica' },
  { value: 'ALTERACAO_MODELO', label: 'Alteracao de modelo' },
  { value: 'ALTERACAO_STATUS', label: 'Alteracao de status' },
]

const COLUMNS = [
  { key: 'criado_em', label: 'Data/Hora' },
  { key: 'acao_display', label: 'Acao' },
  { key: 'numero_certificado', label: 'Certificado' },
  { key: 'modelo_nome', label: 'Modelo' },
  { key: 'usuario_nome', label: 'Usuario' },
  {
    key: 'descricao',
    label: 'Descricao',
    render: (row) => row.descricao || '-',
  },
]

export default function HistoricoCertificadosPage() {
  const [search, setSearch] = useState('')
  const [page, setPage] = useState(1)
  const [filters, setFilters] = useState({ acao: '' })

  const { data, isLoading, isError } = useQuery({
    queryKey: ['certificados-historico', { search, page, filters }],
    queryFn: () => certificadosApi.historico({ search, page, ...filters }).then((response) => response.data),
    staleTime: 15_000,
  })

  const rows = useMemo(() => {
    const results = data?.results || []
    return results.map((item) => ({
      ...item,
      criado_em: item.criado_em ? new Date(item.criado_em).toLocaleString('pt-BR') : '-',
    }))
  }, [data])

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <h1 className="page-title">Historico de Certificados</h1>
          <p className="page-subtitle">Trilha de auditoria completa do modulo de certificados.</p>
        </div>
      </div>

      <section className="form-panel" style={{ marginTop: 20 }}>
        <div className="form-panel__body">
          <div className="form-panel__grid">
            <div className="form-field">
              <label>Acao</label>
              <select
                className="select"
                value={filters.acao}
                onChange={(event) => {
                  setFilters((current) => ({ ...current, acao: event.target.value }))
                  setPage(1)
                }}
              >
                {ACAO_OPTIONS.map((acao) => (
                  <option key={acao.value || 'todas'} value={acao.value}>
                    {acao.label}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </div>
      </section>

      {isError ? <div className="alert alert--error">Nao foi possivel carregar o historico de certificados.</div> : null}

      <DataTable
        columns={COLUMNS}
        data={{ ...data, results: rows }}
        isLoading={isLoading}
        onSearch={(value) => {
          setSearch(value)
          setPage(1)
        }}
        searchPlaceholder="Buscar por descricao, certificado, modelo ou usuario..."
        emptyMessage="Nenhum evento registrado no historico."
      />

      {data ? (
        <div className="pagination">
          <button className="btn btn--secondary" disabled={!data.previous} onClick={() => setPage((current) => current - 1)}>
            Anterior
          </button>
          <span className="pagination__info">Pagina {page} - {data.count || 0} registros</span>
          <button className="btn btn--secondary" disabled={!data.next} onClick={() => setPage((current) => current + 1)}>
            Proxima
          </button>
        </div>
      ) : null}
    </div>
  )
}
