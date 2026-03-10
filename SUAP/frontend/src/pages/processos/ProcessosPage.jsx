import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { processosApi } from '@/api/endpoints'
import DataTable from '@/components/ui/DataTable'
import { Plus } from 'lucide-react'

const STATUS_BADGE = {
  ABERTO:        'badge--info',
  EM_TRAMITACAO: 'badge--warning',
  CONCLUIDO:     'badge--success',
  ARQUIVADO:     'badge--secondary',
}

const COLUMNS = [
  { key: 'numero',         label: 'Nº Processo' },
  { key: 'tipo_display',   label: 'Tipo' },
  { key: 'assunto',        label: 'Assunto' },
  { key: 'requerente_nome',label: 'Requerente' },
  {
    key: 'status',
    label: 'Status',
    render: (row) => (
      <span className={`badge ${STATUS_BADGE[row.status] || ''}`}>
        {row.status_display || row.status}
      </span>
    ),
  },
  { key: 'data_abertura', label: 'Abertura' },
]

export default function ProcessosPage() {
  const [search, setSearch] = useState('')
  const [page, setPage] = useState(1)

  const { data, isLoading } = useQuery({
    queryKey: ['processos', { search, page }],
    queryFn: () => processosApi.list({ search, page }).then((r) => r.data),
    staleTime: 30_000,
  })

  return (
    <div className="page">
      <div className="page-header">
        <h1 className="page-title">Processos</h1>
        <button className="btn btn--primary">
          <Plus size={16} /> Abrir Processo
        </button>
      </div>

      <DataTable
        columns={COLUMNS}
        data={data}
        isLoading={isLoading}
        onSearch={(v) => { setSearch(v); setPage(1) }}
        searchPlaceholder="Buscar por número ou assunto..."
        emptyMessage="Nenhum processo encontrado."
      />

      {data && (
        <div className="pagination">
          <button className="btn btn--secondary" disabled={!data.previous} onClick={() => setPage((p) => p - 1)}>Anterior</button>
          <span className="pagination__info">Página {page} — {data.count} registros</span>
          <button className="btn btn--secondary" disabled={!data.next} onClick={() => setPage((p) => p + 1)}>Próxima</button>
        </div>
      )}
    </div>
  )
}
