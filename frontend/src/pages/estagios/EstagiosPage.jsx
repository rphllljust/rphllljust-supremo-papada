import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { estagiosApi } from '@/api/endpoints'
import DataTable from '@/components/ui/DataTable'

const STATUS_BADGE = {
  PREVISTO:     'badge--info',
  EM_ANDAMENTO: 'badge--success',
  CONCLUIDO:    'badge--secondary',
  CANCELADO:    'badge--danger',
  INTERROMPIDO: 'badge--warning',
}

const COLUMNS = [
  { key: 'aluno_nome',   label: 'Aluno' },
  { key: 'modalidade',   label: 'Modalidade' },
  {
    key: 'status',
    label: 'Status',
    render: (row) => (
      <span className={`badge ${STATUS_BADGE[row.status] || ''}`}>
        {row.status_display || row.status}
      </span>
    ),
  },
]

export default function EstagiosPage() {
  const [search, setSearch] = useState('')
  const [page, setPage] = useState(1)

  const { data, isLoading } = useQuery({
    queryKey: ['estagios', { search, page }],
    queryFn: () => estagiosApi.list({ search, page }).then((r) => r.data),
    staleTime: 30_000,
  })

  return (
    <div className="page">
      <div className="page-header">
        <h1 className="page-title">Estágios</h1>
      </div>
      <DataTable
        columns={COLUMNS}
        data={data}
        isLoading={isLoading}
        onSearch={(v) => { setSearch(v); setPage(1) }}
        searchPlaceholder="Buscar estágio..."
        emptyMessage="Nenhum estágio encontrado."
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
