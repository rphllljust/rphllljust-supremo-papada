import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { unidadesApi } from '@/api/endpoints'
import DataTable from '@/components/ui/DataTable'

const COLUMNS = [
  { key: 'codigo', label: 'Código' },
  { key: 'nome', label: 'Unidade' },
]

export default function UnidadesPage() {
  const [search, setSearch] = useState('')
  const [page, setPage] = useState(1)

  const { data, isLoading, isError } = useQuery({
    queryKey: ['unidades', { search, page }],
    queryFn: () => unidadesApi.list({ search, page }).then((response) => response.data),
    staleTime: 30_000,
  })

  return (
    <div className="page">
      <div className="page-header">
        <h1 className="page-title">Unidades</h1>
      </div>

      {isError && (
        <div className="alert alert--error">
          Não foi possível carregar as unidades disponíveis.
        </div>
      )}

      <DataTable
        columns={COLUMNS}
        data={data}
        isLoading={isLoading}
        onSearch={(value) => {
          setSearch(value)
          setPage(1)
        }}
        searchPlaceholder="Buscar unidade por nome ou código..."
        emptyMessage="Nenhuma unidade encontrada."
      />

      {data && (
        <div className="pagination">
          <button className="btn btn--secondary" disabled={!data.previous} onClick={() => setPage((current) => current - 1)}>
            Anterior
          </button>
          <span className="pagination__info">Página {page} — {data.count} registros</span>
          <button className="btn btn--secondary" disabled={!data.next} onClick={() => setPage((current) => current + 1)}>
            Próxima
          </button>
        </div>
      )}
    </div>
  )
}