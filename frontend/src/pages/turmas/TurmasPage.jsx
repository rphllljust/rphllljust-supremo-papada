import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { turmasApi } from '@/api/endpoints'
import DataTable from '@/components/ui/DataTable'
import { Plus } from 'lucide-react'

const STATUS_BADGE = {
  PLANEJADA: 'badge--info',
  ATIVA:     'badge--success',
  ENCERRADA: 'badge--secondary',
  CANCELADA: 'badge--danger',
}

const COLUMNS = [
  { key: 'nome',           label: 'Turma' },
  { key: 'curso_nome',     label: 'Curso' },
  { key: 'ano_letivo',     label: 'Ano Letivo' },
  { key: 'professor_nome', label: 'Professor' },
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

export default function TurmasPage() {
  const [search, setSearch] = useState('')
  const [page, setPage] = useState(1)

  const { data, isLoading } = useQuery({
    queryKey: ['turmas', { search, page }],
    queryFn: () => turmasApi.list({ search, page }).then((r) => r.data),
    staleTime: 30_000,
  })

  return (
    <div className="page">
      <div className="page-header">
        <h1 className="page-title">Turmas</h1>
        <button className="btn btn--primary">
          <Plus size={16} /> Nova Turma
        </button>
      </div>

      <DataTable
        columns={COLUMNS}
        data={data}
        isLoading={isLoading}
        onSearch={(v) => { setSearch(v); setPage(1) }}
        searchPlaceholder="Buscar turma..."
        emptyMessage="Nenhuma turma encontrada."
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
