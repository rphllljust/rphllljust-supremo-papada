import { useState } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'
import { CheckCircle2, ExternalLink, Search, ShieldAlert } from 'lucide-react'

import { historicosDigitaisApi } from '@/api/endpoints'
import DataTable from '@/components/ui/DataTable'

const COLUMNS = [
  { key: 'numero_unico', label: 'Numero unico' },
  { key: 'historico_protocolo', label: 'Historico' },
  { key: 'tipo_documento_display', label: 'Tipo MEC' },
  { key: 'status_display', label: 'Status' },
  { key: 'aluno_nome', label: 'Aluno' },
]

export default function HistoricosDigitaisPage() {
  const [search, setSearch] = useState('')
  const [page, setPage] = useState(1)
  const [chave, setChave] = useState('')

  const { data, isLoading, isError } = useQuery({
    queryKey: ['historicos-digitais', { search, page }],
    queryFn: () => historicosDigitaisApi.list({ search, page }).then((response) => response.data),
    staleTime: 30_000,
  })

  const validateMutation = useMutation({
    mutationFn: (value) => historicosDigitaisApi.validarPublico(value).then((response) => response.data),
  })

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <h1 className="page-title">Historicos Digitais MEC</h1>
          <p className="page-subtitle">Consulta de emissao XML/XSD, chave de autenticacao e versoes digitais.</p>
        </div>
      </div>

      <section className="entity-details-panel">
        <div className="entity-details-panel__header">
          <h2>Validacao publica por chave</h2>
          <p>Use a mesma consulta para QR Code e chave de autenticacao institucional.</p>
        </div>

        <div className="form-grid">
          <div className="form-field form-field--full">
            <label htmlFor="chave-validacao">Chave de autenticacao</label>
            <div style={{ display: 'flex', gap: '0.75rem' }}>
              <input
                id="chave-validacao"
                type="text"
                value={chave}
                placeholder="Informe a chave"
                onChange={(event) => setChave(event.target.value)}
              />
              <button
                type="button"
                className="btn btn--primary"
                onClick={() => validateMutation.mutate(chave.trim())}
                disabled={!chave.trim() || validateMutation.isPending}
              >
                <Search size={16} />
                Validar
              </button>
            </div>
          </div>
        </div>

        {validateMutation.data ? (
          <div className="entity-details-grid">
            <div className="entity-details-item">
              <span className="entity-details-item__label">Documento</span>
              <span className="entity-details-item__value">{validateMutation.data.numero_unico}</span>
            </div>
            <div className="entity-details-item">
              <span className="entity-details-item__label">Status</span>
              <span className="entity-details-item__value">
                {validateMutation.data.revogado ? <ShieldAlert size={16} /> : <CheckCircle2 size={16} />}
                {' '}
                {validateMutation.data.status}
              </span>
            </div>
            <div className="entity-details-item">
              <span className="entity-details-item__label">Aluno</span>
              <span className="entity-details-item__value">{validateMutation.data.aluno_nome || '-'}</span>
            </div>
            <div className="entity-details-item">
              <span className="entity-details-item__label">Hash</span>
              <span className="entity-details-item__value">{validateMutation.data.hash_documento || '-'}</span>
            </div>
          </div>
        ) : null}
      </section>

      {isError ? <div className="alert alert--error">Nao foi possivel carregar os historicos digitais.</div> : null}

      <DataTable
        columns={COLUMNS}
        data={data}
        isLoading={isLoading}
        onSearch={(value) => {
          setSearch(value)
          setPage(1)
        }}
        searchPlaceholder="Buscar por numero unico, chave, protocolo ou aluno..."
        emptyMessage="Nenhum historico digital encontrado."
        rowActions={(row) => (
          <div className="table-actions">
            {row.pdf_url ? (
              <a className="btn btn--outline btn--sm" href={row.pdf_url} target="_blank" rel="noreferrer">
                <ExternalLink size={14} /> PDF
              </a>
            ) : (
              <span className="text-muted">PDF indisponivel</span>
            )}
          </div>
        )}
      />

      {data ? (
        <div className="pagination">
          <button className="btn btn--secondary" disabled={!data.previous} onClick={() => setPage((current) => current - 1)}>Anterior</button>
          <span className="pagination__info">Pagina {page} — {data.count} registros</span>
          <button className="btn btn--secondary" disabled={!data.next} onClick={() => setPage((current) => current + 1)}>Proxima</button>
        </div>
      ) : null}
    </div>
  )
}
