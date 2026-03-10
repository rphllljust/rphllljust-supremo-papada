import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { publicacoesApi } from '@/api/endpoints'
import DataTable from '@/components/ui/DataTable'
import { Plus } from 'lucide-react'

const STATUS_BADGE = {
  RASCUNHO:  'badge--secondary',
  PUBLICADO: 'badge--success',
  ENCERRADO: 'badge--danger',
}

const COLUMNS = [
  { key: 'titulo',       label: 'Edital' },
  { key: 'curso_nome',   label: 'Curso' },
  { key: 'vagas',        label: 'Vagas' },
  { key: 'data_inicio',  label: 'Início' },
  { key: 'data_fim',     label: 'Fim' },
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

export default function InscricoesPage() {
  const [search, setSearch] = useState('')
  const [page, setPage] = useState(1)

  const { data, isLoading } = useQuery({
    queryKey: ['publicacoes', { search, page }],
    queryFn: () => publicacoesApi.list({ search, page }).then((r) => r.data),
    staleTime: 30_000,
  })

  return (
    <div className="page">
      <div className="page-header">
        <h1 className="page-title">Inscrições / Editais</h1>
        <button className="btn btn--primary"><Plus size={16} /> Novo Edital</button>
      </div>
      <DataTable
        columns={COLUMNS}
        data={data}
        isLoading={isLoading}
        onSearch={(v) => { setSearch(v); setPage(1) }}
        searchPlaceholder="Buscar edital..."
        emptyMessage="Nenhum edital encontrado."
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
