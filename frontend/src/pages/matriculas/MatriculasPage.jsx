/**
 * Página de Matrículas — lista com busca e filtros.
 * Demonstra: useQuery com params, DataTable, useMutation.
 */
import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { matriculasApi } from '@/api/endpoints'
import DataTable from '@/components/ui/DataTable'
import { Plus, Eye } from 'lucide-react'
import toast from 'react-hot-toast'

const STATUS_BADGE = {
  ATIVA:     'badge--success',
  TRANCADA:  'badge--warning',
  CANCELADA: 'badge--danger',
  CONCLUIDA: 'badge--info',
}

const COLUMNS = [
  { key: 'numero_matricula', label: 'Nº Matrícula' },
  { key: 'aluno_nome',       label: 'Aluno' },
  { key: 'curso_nome',       label: 'Curso' },
  { key: 'turma_nome',       label: 'Turma' },
  {
    key: 'status',
    label: 'Status',
    render: (row) => (
      <span className={`badge ${STATUS_BADGE[row.status] || ''}`}>
        {row.status_display || row.status}
      </span>
    ),
  },
  { key: 'data_matricula', label: 'Data' },
  {
    key: 'actions',
    label: '',
    render: (row) => (
      <button className="btn btn--icon" title="Ver detalhes">
        <Eye size={16} />
      </button>
    ),
  },
]

export default function MatriculasPage() {
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [page, setPage] = useState(1)

  const { data, isLoading } = useQuery({
    queryKey: ['matriculas', { search, status: statusFilter, page }],
    queryFn: () =>
      matriculasApi.list({ search, status: statusFilter || undefined, page }).then((r) => r.data),
    staleTime: 30_000,
  })

  return (
    <div className="page">
      <div className="page-header">
        <h1 className="page-title">Matrículas</h1>
        <div className="page-header__actions">
          <select
            className="select"
            value={statusFilter}
            onChange={(e) => { setStatusFilter(e.target.value); setPage(1) }}
          >
            <option value="">Todos os status</option>
            <option value="ATIVA">Ativa</option>
            <option value="TRANCADA">Trancada</option>
            <option value="CANCELADA">Cancelada</option>
            <option value="CONCLUIDA">Concluída</option>
          </select>
          <button className="btn btn--primary">
            <Plus size={16} /> Nova Matrícula
          </button>
        </div>
      </div>

      <DataTable
        columns={COLUMNS}
        data={data}
        isLoading={isLoading}
        onSearch={(v) => { setSearch(v); setPage(1) }}
        searchPlaceholder="Buscar por nome, CPF ou número..."
        emptyMessage="Nenhuma matrícula encontrada."
      />

      {/* Paginação */}
      {data && (
        <div className="pagination">
          <button
            className="btn btn--secondary"
            disabled={!data.previous}
            onClick={() => setPage((p) => p - 1)}
          >
            Anterior
          </button>
          <span className="pagination__info">
            Página {page} — {data.count} registros
          </span>
          <button
            className="btn btn--secondary"
            disabled={!data.next}
            onClick={() => setPage((p) => p + 1)}
          >
            Próxima
          </button>
        </div>
      )}
    </div>
  )
}
