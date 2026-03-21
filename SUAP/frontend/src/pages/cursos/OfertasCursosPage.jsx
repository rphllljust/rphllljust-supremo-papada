import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import { Eye, Pencil, Plus, RefreshCcw, Trash2 } from 'lucide-react'
import { Link, useNavigate } from 'react-router-dom'

import { ofertasApi } from '@/api/endpoints'
import DataTable from '@/components/ui/DataTable'

const COLUMNS = [
  { key: 'nome', label: 'Oferta' },
  { key: 'curso_base_nome', label: 'Curso base' },
  { key: 'matriz_curricular_nome', label: 'Matriz' },
  { key: 'polo_nome', label: 'Polo' },
  { key: 'codigo_turma', label: 'Turma' },
  { key: 'turno', label: 'Turno' },
  { key: 'status', label: 'Status' },
  {
    key: 'last_sync_status',
    label: 'Sync Moodle',
    render: (row) => row.last_sync_status || 'pendente',
  },
]

export default function OfertasCursosPage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [search, setSearch] = useState('')
  const [page, setPage] = useState(1)

  const { data, isLoading, isError } = useQuery({
    queryKey: ['ofertas-cursos', { search, page }],
    queryFn: () => ofertasApi.list({ search, page }).then((response) => response.data),
    staleTime: 30_000,
  })

  const removeMutation = useMutation({
    mutationFn: (id) => ofertasApi.remove(id),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['ofertas-cursos'] })
      toast.success('Oferta removida com sucesso.')
    },
    onError: (error) => {
      toast.error(error?.response?.data?.detail || 'Não foi possível remover a oferta.')
    },
  })

  const handleRemove = (row) => {
    if (!window.confirm(`Deseja realmente remover a oferta ${row.nome}?`)) {
      return
    }
    removeMutation.mutate(row.id)
  }

  return (
    <div className="page page--wide matrix-page">
      <nav className="profile-breadcrumb">
        <Link to="/dashboard">Início</Link>
        <span className="profile-breadcrumb__sep">&gt;</span>
        <span>Ensino</span>
        <span className="profile-breadcrumb__sep">&gt;</span>
        <span>Cursos, Matrizes e Componentes</span>
        <span className="profile-breadcrumb__sep">&gt;</span>
        <span>Ofertas de Curso</span>
      </nav>

      <div className="page-header">
        <div>
          <h1 className="page-title">Ofertas de Curso</h1>
          <p className="page-subtitle">Execução operacional das matrizes curriculares técnicas, com vínculo explícito de polo, calendário e sincronização Moodle.</p>
        </div>
        <div className="page-header__actions">
          <button type="button" className="btn btn--outline" onClick={() => queryClient.invalidateQueries({ queryKey: ['ofertas-cursos'] })}>
            <RefreshCcw size={16} /> Atualizar
          </button>
          <button type="button" className="btn btn--primary" onClick={() => navigate('/ensino/ofertas/nova')}>
            <Plus size={16} /> Nova Oferta
          </button>
        </div>
      </div>

      {isError ? <div className="alert alert--error">Não foi possível carregar as ofertas de curso.</div> : null}

      <section className="dashboard-card matrix-page__card">
        <DataTable
          columns={COLUMNS}
          data={data}
          isLoading={isLoading}
          onSearch={(value) => {
            setSearch(value)
            setPage(1)
          }}
          searchPlaceholder="Buscar oferta, curso, matriz, polo ou turma..."
          emptyMessage="Nenhuma oferta de curso encontrada."
          rowActions={(row) => (
            <div className="table-actions">
              <button type="button" className="btn btn--outline btn--sm" onClick={() => navigate(`/ensino/ofertas/${row.id}`)}>
                <Eye size={14} /> Detalhes
              </button>
              <button type="button" className="btn btn--secondary btn--sm" onClick={() => navigate(`/ensino/ofertas/${row.id}/editar`)}>
                <Pencil size={14} /> Editar
              </button>
              <button type="button" className="btn btn--danger btn--sm" onClick={() => handleRemove(row)} disabled={removeMutation.isPending || Boolean(row.moodle_course_id)}>
                <Trash2 size={14} /> Excluir
              </button>
            </div>
          )}
        />

        {data ? (
          <div className="pagination">
            <button type="button" className="btn btn--secondary" disabled={!data.previous} onClick={() => setPage((current) => current - 1)}>Anterior</button>
            <span className="pagination__info">Página {page} • {data.count} registros</span>
            <button type="button" className="btn btn--secondary" disabled={!data.next} onClick={() => setPage((current) => current + 1)}>Próxima</button>
          </div>
        ) : null}
      </section>
    </div>
  )
}
