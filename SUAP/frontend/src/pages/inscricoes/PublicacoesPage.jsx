import { useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Eye, Pencil, Plus, Trash2 } from 'lucide-react'
import toast from 'react-hot-toast'
import { Link, useNavigate } from 'react-router-dom'

import { publicacoesApi } from '@/api/endpoints'
import DataTable from '@/components/ui/DataTable'

import { formatDate, getErrorMessage, PUBLICACAO_STATUS_OPTIONS } from './publicacaoShared'
import ProcessosSeletivosTabs from './ProcessosSeletivosTabs'

const COLUMNS = [
  { key: 'titulo', label: 'Edital' },
  { key: 'curso_nome', label: 'Curso' },
  { key: 'vagas', label: 'Vagas' },
  {
    key: 'periodo',
    label: 'Período',
    render: (row) => `${formatDate(row.data_inicio)} a ${formatDate(row.data_fim)}`,
  },
  {
    key: 'status',
    label: 'Status',
    render: (row) => <span className={`badge ${row.status === 'PUBLICADO' ? 'badge--success' : row.status === 'ENCERRADO' ? 'badge--danger' : 'badge--secondary'}`}>{row.status_display || row.status}</span>,
  },
  { key: 'inscricoes_count', label: 'Inscritos' },
]

function StatCard({ label, value, tone = 'default' }) {
  return (
    <article className={`stat-card processos-seletivos-stat-card processos-seletivos-stat-card--${tone}`}>
      <div className="stat-card__content">
        <strong className="stat-card__value">{value}</strong>
        <span className="stat-card__label">{label}</span>
      </div>
    </article>
  )
}

export default function PublicacoesPage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [search, setSearch] = useState('')
  const [status, setStatus] = useState('')
  const [page, setPage] = useState(1)

  const { data, isLoading, isError } = useQuery({
    queryKey: ['publicacoes', { search, status, page }],
    queryFn: () => publicacoesApi.list({ search: search || undefined, status: status || undefined, page }).then((response) => response.data),
    staleTime: 30_000,
  })

  const deleteMutation = useMutation({
    mutationFn: (id) => publicacoesApi.remove(id),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['publicacoes'] })
      toast.success('Edital removido com sucesso.')
    },
    onError: (error) => toast.error(getErrorMessage(error, 'Nao foi possivel remover o edital.')),
  })

  const rows = data?.results || []
  const totalInscritos = rows.reduce((accumulator, row) => accumulator + Number(row.inscricoes_count || 0), 0)
  const totalPublicados = rows.filter((row) => row.status === 'PUBLICADO').length
  const totalEncerrados = rows.filter((row) => row.status === 'ENCERRADO').length
  const countLabel = useMemo(() => {
    if (isLoading) return 'Consultando editais...'
    if (isError) return 'Nao foi possivel carregar os editais.'
    return `Mostrando ${rows.length} de ${data?.count || 0} editais.`
  }, [data?.count, isError, isLoading, rows.length])

  return (
    <div className="page page--wide processos-seletivos-page">
      <nav className="profile-breadcrumb">
        <Link to="/dashboard">Início</Link>
        <span className="profile-breadcrumb__sep">&gt;</span>
        <span>Processos seletivos</span>
        <span className="profile-breadcrumb__sep">&gt;</span>
        <span>Editais</span>
      </nav>

      <div className="page-header processos-seletivos-page__header">
        <div>
          <h1 className="page-title">Processos seletivos</h1>
          <p className="page-subtitle">Acompanhe editais publicados e o fluxo de inscrições no mesmo módulo.</p>
        </div>
        <div className="page-header__actions">
          <button type="button" className="btn btn--outline" onClick={() => window.print()}>
            Imprimir
          </button>
          <button type="button" className="btn btn--primary" onClick={() => navigate('/inscricoes/editais/novo')}>
            <Plus size={16} /> Novo edital
          </button>
        </div>
      </div>

      <ProcessosSeletivosTabs activeTab="editais" />

      <section className="stats-grid processos-seletivos-stats-grid">
        <StatCard label="Editais listados" value={data?.count || 0} tone="primary" />
        <StatCard label="Inscrições vinculadas" value={totalInscritos} tone="info" />
        <StatCard label="Publicados" value={totalPublicados} tone="success" />
        <StatCard label="Encerrados" value={totalEncerrados} tone="danger" />
      </section>

      <section className="dashboard-card processos-seletivos-filters-card">
        <div className="processos-seletivos-filters-card__header">
          <h2 className="dashboard-card__title">Filtros de editais</h2>
          <span className="page-subtitle">{countLabel}</span>
        </div>
        <div className="processos-seletivos-filters-grid">
          <label className="form-field processos-seletivos-filters-grid__search">
            <span className="form-field__label">Busca</span>
            <input
              className="form-control"
              value={search}
              onChange={(event) => {
                setSearch(event.target.value)
                setPage(1)
              }}
              placeholder="Título, curso ou descrição"
            />
          </label>

          <label className="form-field">
            <span className="form-field__label">Status</span>
            <select
              className="select"
              value={status}
              onChange={(event) => {
                setStatus(event.target.value)
                setPage(1)
              }}
            >
              <option value="">Todos</option>
              {PUBLICACAO_STATUS_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>{option.label}</option>
              ))}
            </select>
          </label>

          <div className="processos-seletivos-filters-grid__actions">
            <button type="button" className="btn btn--secondary" onClick={() => navigate('/inscricoes?aba=inscricoes')}>
              Ir para inscrições
            </button>
          </div>
        </div>
      </section>

      {isError ? <div className="alert alert--error">Nao foi possivel carregar os editais.</div> : null}

      <DataTable
        columns={COLUMNS}
        data={{ results: rows }}
        isLoading={isLoading}
        onSearch={(value) => {
          setSearch(value)
          setPage(1)
        }}
        searchPlaceholder="Buscar edital por título, curso ou descrição..."
        emptyMessage="Nenhum edital encontrado."
        actions={(
          <span className="processos-seletivos-table-summary">{countLabel}</span>
        )}
        rowActions={(row) => (
          <div className="table-actions">
            <button type="button" className="btn btn--outline btn--sm" onClick={() => navigate(`/inscricoes/editais/${row.id}`)}>
              <Eye size={14} /> Ver
            </button>
            <button type="button" className="btn btn--secondary btn--sm" onClick={() => navigate(`/inscricoes/editais/${row.id}/editar`)}>
              <Pencil size={14} /> Editar
            </button>
            <button type="button" className="btn btn--danger btn--sm" onClick={() => window.confirm(`Excluir o edital ${row.titulo}?`) && deleteMutation.mutate(row.id)}>
              <Trash2 size={14} /> Excluir
            </button>
          </div>
        )}
        rowActionsLabel="Ações"
      />

      {data ? (
        <div className="pagination processos-seletivos-pagination">
          <button type="button" className="btn btn--secondary" disabled={!data.previous} onClick={() => setPage((current) => current - 1)}>
            Anterior
          </button>
          <span className="pagination__info">Página {page} — {data.count || 0} registros</span>
          <button type="button" className="btn btn--secondary" disabled={!data.next} onClick={() => setPage((current) => current + 1)}>
            Próxima
          </button>
        </div>
      ) : null}
    </div>
  )
}