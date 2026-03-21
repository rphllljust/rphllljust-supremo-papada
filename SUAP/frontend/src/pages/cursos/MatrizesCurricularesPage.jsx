import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import { Copy, Eye, Pencil, Plus, RefreshCcw, Trash2 } from 'lucide-react'
import { Link, useNavigate } from 'react-router-dom'

import { matrizesCurricularesApi } from '@/api/endpoints'
import DataTable from '@/components/ui/DataTable'

const COLUMNS = [
  { key: 'nome', label: 'Matriz curricular' },
  { key: 'curso_base_nome', label: 'Curso base' },
  { key: 'ano_referencia', label: 'Ano' },
  { key: 'versao', label: 'Versão' },
  {
    key: 'status',
    label: 'Status',
    render: (row) => <span className={`matrix-badge matrix-badge--${String(row.status || '').toLowerCase()}`}>{row.status}</span>,
  },
  {
    key: 'ativa',
    label: 'Ativa',
    render: (row) => (row.ativa ? 'Sim' : 'Não'),
  },
  { key: 'total_componentes', label: 'Componentes' },
]

export default function MatrizesCurricularesPage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [search, setSearch] = useState('')
  const [page, setPage] = useState(1)

  const { data, isLoading, isError } = useQuery({
    queryKey: ['matrizes-curriculares', { search, page }],
    queryFn: () => matrizesCurricularesApi.list({ search, page }).then((response) => response.data),
    staleTime: 30_000,
  })

  const removeMutation = useMutation({
    mutationFn: (id) => matrizesCurricularesApi.remove(id),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['matrizes-curriculares'] })
      toast.success('Matriz curricular removida com sucesso.')
    },
    onError: (error) => {
      toast.error(error?.response?.data?.detail || 'Não foi possível remover a matriz curricular.')
    },
  })

  const cloneMutation = useMutation({
    mutationFn: (id) => matrizesCurricularesApi.clonar(id),
    onSuccess: async (response) => {
      const cloneId = response?.data?.matriz?.id
      await queryClient.invalidateQueries({ queryKey: ['matrizes-curriculares'] })
      toast.success('Matriz curricular clonada com sucesso.')
      if (cloneId) {
        navigate(`/ensino/matrizes-curriculares/${cloneId}/editar`)
      }
    },
    onError: (error) => {
      toast.error(error?.response?.data?.detail || 'Não foi possível clonar a matriz curricular.')
    },
  })

  const handleRemove = (row) => {
    if (!window.confirm(`Deseja realmente remover a matriz ${row.nome}?`)) {
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
        <span>Matrizes Curriculares</span>
      </nav>

      <div className="page-header">
        <div>
          <h1 className="page-title">Matrizes Curriculares</h1>
          <p className="page-subtitle">Gestão explícita das matrizes dos cursos técnicos, preservando a compatibilidade com o catálogo atual.</p>
        </div>
        <div className="page-header__actions">
          <button type="button" className="btn btn--outline" onClick={() => queryClient.invalidateQueries({ queryKey: ['matrizes-curriculares'] })}>
            <RefreshCcw size={16} /> Atualizar
          </button>
          <button type="button" className="btn btn--primary" onClick={() => navigate('/ensino/matrizes-curriculares/nova')}>
            <Plus size={16} /> Nova Matriz
          </button>
        </div>
      </div>

      {isError ? <div className="alert alert--error">Não foi possível carregar as matrizes curriculares.</div> : null}

      <section className="dashboard-card matrix-page__card">
        <div className="matrix-page__card-header">
          <div>
            <h2 className="dashboard-card__title">Catálogo de matrizes técnicas</h2>
            <p className="page-subtitle">Cada matriz agrupa componentes por módulo e pode sincronizar um curso modelo no Moodle.</p>
          </div>
        </div>

        <DataTable
          columns={COLUMNS}
          data={data}
          isLoading={isLoading}
          onSearch={(value) => {
            setSearch(value)
            setPage(1)
          }}
          searchPlaceholder="Buscar matriz, curso base ou versão..."
          emptyMessage="Nenhuma matriz curricular encontrada."
          rowActions={(row) => (
            <div className="table-actions">
              <button type="button" className="btn btn--outline btn--sm" onClick={() => navigate(`/ensino/matrizes-curriculares/${row.id}`)}>
                <Eye size={14} /> Detalhes
              </button>
              <button type="button" className="btn btn--secondary btn--sm" onClick={() => navigate(`/ensino/matrizes-curriculares/${row.id}/editar`)} disabled={!row.permite_edicao}>
                <Pencil size={14} /> Editar
              </button>
              <button type="button" className="btn btn--outline btn--sm" onClick={() => cloneMutation.mutate(row.id)} disabled={cloneMutation.isPending}>
                <Copy size={14} /> Clonar
              </button>
              <button type="button" className="btn btn--danger btn--sm" onClick={() => handleRemove(row)} disabled={removeMutation.isPending || row.status === 'VIGENTE'}>
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