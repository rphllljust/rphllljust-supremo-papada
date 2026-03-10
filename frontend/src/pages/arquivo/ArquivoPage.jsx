import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { guardaApi } from '@/api/endpoints'
import DataTable from '@/components/ui/DataTable'

const COLUMNS = [
  { key: 'numero_registro',  label: 'Nº Registro' },
  { key: 'tipo_documento',   label: 'Tipo' },
  { key: 'descricao',        label: 'Descrição' },
  { key: 'localizacao',      label: 'Localização' },
  { key: 'status_display',   label: 'Status' },
  { key: 'data_arquivamento',label: 'Data' },
]

export default function ArquivoPage() {
  const [search, setSearch] = useState('')
  const [page, setPage] = useState(1)

  const { data, isLoading } = useQuery({
    queryKey: ['guarda', { search, page }],
    queryFn: () => guardaApi.list({ search, page }).then((r) => r.data),
    staleTime: 30_000,
  })

  return (
    <div className="page">
      <div className="page-header">
        <h1 className="page-title">Arquivo / Guarda Documental</h1>
      </div>
      <DataTable
        columns={COLUMNS}
        data={data}
        isLoading={isLoading}
        onSearch={(v) => { setSearch(v); setPage(1) }}
        searchPlaceholder="Buscar documento..."
        emptyMessage="Nenhum documento arquivado encontrado."
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
