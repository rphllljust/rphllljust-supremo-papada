import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { eventosApi } from '@/api/endpoints'
import DataTable from '@/components/ui/DataTable'
import { Plus } from 'lucide-react'

const COLUMNS = [
  { key: 'titulo',     label: 'Evento' },
  { key: 'turma_nome', label: 'Turma' },
  { key: 'inicio',     label: 'Início', render: (row) => row.inicio?.slice(0, 16).replace('T', ' ') },
  { key: 'fim',        label: 'Fim',    render: (row) => row.fim?.slice(0, 16).replace('T', ' ') },
]

export default function AgendaPage() {
  const [search, setSearch] = useState('')
  const [page, setPage] = useState(1)

  const { data, isLoading } = useQuery({
    queryKey: ['eventos', { search, page }],
    queryFn: () => eventosApi.list({ search, page }).then((r) => r.data),
    staleTime: 30_000,
  })

  return (
    <div className="page">
      <div className="page-header">
        <h1 className="page-title">Agenda</h1>
        <button className="btn btn--primary"><Plus size={16} /> Novo Evento</button>
      </div>
      <DataTable
        columns={COLUMNS}
        data={data}
        isLoading={isLoading}
        onSearch={(v) => { setSearch(v); setPage(1) }}
        searchPlaceholder="Buscar evento..."
        emptyMessage="Nenhum evento encontrado."
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
