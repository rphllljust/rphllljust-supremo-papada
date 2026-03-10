import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { cursosApi } from '@/api/endpoints'
import DataTable from '@/components/ui/DataTable'
import { Plus } from 'lucide-react'

const COLUMNS = [
  { key: 'nome',        label: 'Curso' },
  { key: 'sigla',       label: 'Sigla' },
  { key: 'unidade_nome',label: 'Unidade' },
  { key: 'eixo_tecnologico', label: 'Eixo Tecnológico' },
  { key: 'carga_horaria', label: 'Carga Horária (h)' },
]

export default function CursosPage() {
  const [search, setSearch] = useState('')
  const [page, setPage] = useState(1)

  const { data, isLoading } = useQuery({
    queryKey: ['cursos', { search, page }],
    queryFn: () => cursosApi.list({ search, page }).then((r) => r.data),
    staleTime: 30_000,
  })

  return (
    <div className="page">
      <div className="page-header">
        <h1 className="page-title">Cursos</h1>
        <button className="btn btn--primary"><Plus size={16} /> Novo Curso</button>
      </div>
      <DataTable
        columns={COLUMNS}
        data={data}
        isLoading={isLoading}
        onSearch={(v) => { setSearch(v); setPage(1) }}
        searchPlaceholder="Buscar curso..."
        emptyMessage="Nenhum curso encontrado."
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
