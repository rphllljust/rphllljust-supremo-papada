import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { usuariosApi } from '@/api/endpoints'
import DataTable from '@/components/ui/DataTable'

const COLUMNS = [
  { key: 'nome_completo', label: 'Nome' },
  { key: 'cpf',           label: 'CPF' },
  { key: 'email',         label: 'E-mail' },
  { key: 'is_active',     label: 'Ativo', render: (row) => row.is_active ? 'Sim' : 'Não' },
]

export default function AlunosPage() {
  const [search, setSearch] = useState('')
  const [page, setPage] = useState(1)

  const { data, isLoading } = useQuery({
    queryKey: ['alunos', { search, page }],
    queryFn: () => usuariosApi.list({ search, tipo: 'ALUNO', page }).then((r) => r.data),
    staleTime: 30_000,
  })

  return (
    <div className="page">
      <div className="page-header">
        <h1 className="page-title">Alunos</h1>
      </div>
      <DataTable
        columns={COLUMNS}
        data={data}
        isLoading={isLoading}
        onSearch={(v) => { setSearch(v); setPage(1) }}
        searchPlaceholder="Buscar aluno..."
        emptyMessage="Nenhum aluno encontrado."
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
