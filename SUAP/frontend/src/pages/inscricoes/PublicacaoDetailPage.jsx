import { useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Eye, Pencil, Plus, Trash2, Users } from 'lucide-react'
import toast from 'react-hot-toast'
import { Link, useNavigate, useParams, useSearchParams } from 'react-router-dom'

import { inscricoesApi, publicacoesApi } from '@/api/endpoints'
import DataTable from '@/components/ui/DataTable'

import { formatDate, formatDateTime, getErrorMessage, PUBLICACAO_STATUS_BADGE } from './publicacaoShared'
import ProcessosSeletivosTabs from './ProcessosSeletivosTabs'

const TABS = [
  { key: 'dados-gerais', label: 'Dados Gerais' },
  { key: 'candidatos', label: 'Candidatos' },
  { key: 'listas', label: 'Listas' },
  { key: 'configuracao-migracao', label: 'Configuracao de Migracao de Vagas' },
  { key: 'ofertas', label: 'Ofertas de Vagas' },
  { key: 'quantitativo', label: 'Quantitativo de Inscritos' },
  { key: 'periodos', label: 'Periodos de Liberacao' },
]

const CANDIDATOS_COLUMNS = [
  { key: 'numero_inscricao', label: 'Número' },
  { key: 'nome_candidato', label: 'Candidato' },
  { key: 'cpf', label: 'CPF' },
  { key: 'email', label: 'E-mail' },
  {
    key: 'status',
    label: 'Status',
    render: (row) => row.status_display || row.status,
  },
  {
    key: 'data_inscricao',
    label: 'Data',
    render: (row) => formatDateTime(row.data_inscricao),
  },
]

function SummaryMetric({ label, value }) {
  return (
    <article className="dashboard-card processos-seletivos-metric-card">
      <span className="processos-seletivos-metric-card__label">{label}</span>
      <strong className="processos-seletivos-metric-card__value">{value}</strong>
    </article>
  )
}

function PlaceholderPanel({ title, description }) {
  return (
    <section className="dashboard-card processos-seletivos-placeholder">
      <strong>{title}</strong>
      <p>{description}</p>
    </section>
  )
}

export default function PublicacaoDetailPage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { publicacaoId } = useParams()
  const [searchParams, setSearchParams] = useSearchParams()
  const [candidatoSearch, setCandidatoSearch] = useState('')
  const activeTab = TABS.some((tab) => tab.key === searchParams.get('aba')) ? searchParams.get('aba') : 'dados-gerais'

  const { data, isLoading, isError } = useQuery({
    queryKey: ['publicacao', publicacaoId],
    queryFn: () => publicacoesApi.get(publicacaoId).then((response) => response.data),
    enabled: Boolean(publicacaoId),
    staleTime: 30_000,
  })

  const { data: inscricoesData, isLoading: isLoadingInscricoes } = useQuery({
    queryKey: ['inscricoes', 'publicacao', publicacaoId, candidatoSearch],
    queryFn: () => inscricoesApi.list({ publicacao: publicacaoId, search: candidatoSearch || undefined, page_size: 100 }).then((response) => response.data),
    enabled: Boolean(publicacaoId),
    staleTime: 30_000,
  })

  const deleteMutation = useMutation({
    mutationFn: (id) => publicacoesApi.remove(id),
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ['publicacoes'] }),
        queryClient.invalidateQueries({ queryKey: ['publicacao', publicacaoId] }),
      ])
      toast.success('Edital removido com sucesso.')
      navigate('/inscricoes/editais')
    },
    onError: (error) => toast.error(getErrorMessage(error, 'Nao foi possivel remover o edital.')),
  })

  const inscricoes = inscricoesData?.results || []

  const stats = useMemo(() => {
    const total = inscricoes.length
    const pendentes = inscricoes.filter((item) => item.status === 'PENDENTE').length
    const validadas = inscricoes.filter((item) => item.status === 'VALIDADA').length
    const indeferidas = inscricoes.filter((item) => item.status === 'INDEFERIDA').length
    const vagas = Number(data?.vagas || 0)

    return {
      total,
      pendentes,
      validadas,
      indeferidas,
      vagas,
      saldo: vagas - validadas,
    }
  }, [data?.vagas, inscricoes])

  const handleDelete = () => {
    if (!data) return
    if (!window.confirm(`Excluir o edital ${data.titulo}?`)) return
    deleteMutation.mutate(data.id)
  }

  if (isLoading) {
    return (
      <div className="page page--wide">
        <div className="page-loader" role="status" aria-live="polite">
          <div className="spinner" />
          <span>Carregando edital...</span>
        </div>
      </div>
    )
  }

  if (isError || !data) {
    return (
      <div className="page page--wide">
        <div className="page-error">
          <h1 className="page-error__title">Nao foi possivel carregar o edital</h1>
          <p className="page-error__description">Verifique se o registro existe e tente novamente.</p>
        </div>
      </div>
    )
  }

  return (
    <div className="page page--wide processos-seletivos-page">
      <nav className="profile-breadcrumb">
        <Link to="/dashboard">Início</Link>
        <span className="profile-breadcrumb__sep">&gt;</span>
        <Link to="/inscricoes/editais">Processos seletivos</Link>
        <span className="profile-breadcrumb__sep">&gt;</span>
        <span>{data.titulo}</span>
      </nav>

      <div className="page-header processos-seletivos-page__header">
        <div>
          <h1 className="page-title">{data.titulo}</h1>
          <p className="page-subtitle">{data.curso_nome || 'Curso nao informado'}</p>
        </div>
        <div className="page-header__actions">
          <button type="button" className="btn btn--outline" onClick={() => navigate('/inscricoes/editais')}>
            <Eye size={16} /> Voltar
          </button>
          <button type="button" className="btn btn--secondary" onClick={() => navigate(`/inscricoes/nova?publicacao=${data.id}`)}>
            <Plus size={16} /> Nova inscrição
          </button>
          <button type="button" className="btn btn--primary" onClick={() => navigate(`/inscricoes/editais/${data.id}/editar`)}>
            <Pencil size={16} /> Editar edital
          </button>
        </div>
      </div>

      <ProcessosSeletivosTabs activeTab="editais" />

      <div className="profile-status-row processos-seletivos-status-row">
        <span className={`badge ${PUBLICACAO_STATUS_BADGE[data.status] || 'badge--secondary'}`}>{data.status_display || data.status}</span>
        <span className="badge badge--info">{data.inscricoes_count ?? 0} inscritos</span>
      </div>

      <section className="stats-grid processos-seletivos-stats-grid">
        <SummaryMetric label="Vagas" value={stats.vagas} />
        <SummaryMetric label="Inscrições" value={stats.total} />
        <SummaryMetric label="Validadas" value={stats.validadas} />
        <SummaryMetric label="Saldo" value={stats.saldo} />
      </section>

      <div className="profile-tabs processos-seletivos-detail-tabs">
        {TABS.map((tab) => (
          <button key={tab.key} type="button" className={`profile-tabs__item ${activeTab === tab.key ? 'profile-tabs__item--active' : ''}`} onClick={() => setSearchParams({ aba: tab.key })}>
            {tab.label}
          </button>
        ))}
      </div>

      <section className="dashboard-card profile-content-card processos-seletivos-content-card">
        {activeTab === 'dados-gerais' ? (
          <div className="processos-seletivos-details-grid">
            <div className="processos-seletivos-detail-item">
              <span className="processos-seletivos-detail-item__label">Título</span>
              <strong className="processos-seletivos-detail-item__value">{data.titulo}</strong>
            </div>
            <div className="processos-seletivos-detail-item">
              <span className="processos-seletivos-detail-item__label">Curso</span>
              <strong className="processos-seletivos-detail-item__value">{data.curso_nome || '-'}</strong>
            </div>
            <div className="processos-seletivos-detail-item">
              <span className="processos-seletivos-detail-item__label">Vagas</span>
              <strong className="processos-seletivos-detail-item__value">{data.vagas ?? 0}</strong>
            </div>
            <div className="processos-seletivos-detail-item">
              <span className="processos-seletivos-detail-item__label">Publicado por</span>
              <strong className="processos-seletivos-detail-item__value">{data.publicado_por_nome || '-'}</strong>
            </div>
            <div className="processos-seletivos-detail-item">
              <span className="processos-seletivos-detail-item__label">Início das inscrições</span>
              <strong className="processos-seletivos-detail-item__value">{formatDate(data.data_inicio)}</strong>
            </div>
            <div className="processos-seletivos-detail-item">
              <span className="processos-seletivos-detail-item__label">Fim das inscrições</span>
              <strong className="processos-seletivos-detail-item__value">{formatDate(data.data_fim)}</strong>
            </div>
            <div className="processos-seletivos-detail-item processos-seletivos-detail-item--full">
              <span className="processos-seletivos-detail-item__label">Descrição</span>
              <strong className="processos-seletivos-detail-item__value">{data.descricao || 'Nenhuma descrição registrada.'}</strong>
            </div>
          </div>
        ) : null}

        {activeTab === 'candidatos' ? (
          <div className="processos-seletivos-tab-stack">
            <div className="dashboard-strip__card processos-seletivos-inline-filter">
              <label className="form-field processos-seletivos-inline-filter__field">
                <span className="form-field__label">Buscar candidato</span>
                <input className="form-control" value={candidatoSearch} onChange={(event) => setCandidatoSearch(event.target.value)} placeholder="Nome, CPF ou número" />
              </label>
            </div>
            <DataTable
              columns={CANDIDATOS_COLUMNS}
              data={{ results: inscricoes }}
              isLoading={isLoadingInscricoes}
              onSearch={() => {}}
              searchPlaceholder="Buscar dentro da tabela..."
              actions={null}
              emptyMessage="Nenhum candidato vinculado a este edital."
            />
          </div>
        ) : null}

        {activeTab === 'listas' ? (
          <div className="processos-seletivos-tab-stack">
            <PlaceholderPanel title="Listas de seleção" description="As listas finais deste edital serão exibidas aqui conforme a homologação das inscrições e classificações." />
            <div className="stats-grid processos-seletivos-stats-grid processos-seletivos-stats-grid--compact">
              <SummaryMetric label="Pendentes" value={stats.pendentes} />
              <SummaryMetric label="Validadas" value={stats.validadas} />
              <SummaryMetric label="Indeferidas" value={stats.indeferidas} />
              <SummaryMetric label="Total" value={stats.total} />
            </div>
          </div>
        ) : null}

        {activeTab === 'configuracao-migracao' ? (
          <PlaceholderPanel title="Migração de vagas" description="Ainda não há configuração específica de migração de vagas cadastrada para este edital." />
        ) : null}

        {activeTab === 'ofertas' ? (
          <div className="stats-grid processos-seletivos-stats-grid processos-seletivos-stats-grid--compact">
            <SummaryMetric label="Vagas ofertadas" value={stats.vagas} />
            <SummaryMetric label="Inscrições recebidas" value={stats.total} />
            <SummaryMetric label="Validadas" value={stats.validadas} />
            <SummaryMetric label="Saldo" value={stats.saldo} />
          </div>
        ) : null}

        {activeTab === 'quantitativo' ? (
          <div className="processos-seletivos-quantitativo-list">
            <div className="processos-seletivos-detail-item">
              <span className="processos-seletivos-detail-item__label">Pendente de validação</span>
              <strong className="processos-seletivos-detail-item__value">{stats.pendentes}</strong>
            </div>
            <div className="processos-seletivos-detail-item">
              <span className="processos-seletivos-detail-item__label">Validada</span>
              <strong className="processos-seletivos-detail-item__value">{stats.validadas}</strong>
            </div>
            <div className="processos-seletivos-detail-item">
              <span className="processos-seletivos-detail-item__label">Indeferida</span>
              <strong className="processos-seletivos-detail-item__value">{stats.indeferidas}</strong>
            </div>
            <div className="processos-seletivos-detail-item">
              <span className="processos-seletivos-detail-item__label">Total</span>
              <strong className="processos-seletivos-detail-item__value">{stats.total}</strong>
            </div>
          </div>
        ) : null}

        {activeTab === 'periodos' ? (
          <div className="processos-seletivos-quantitativo-list">
            <div className="processos-seletivos-detail-item">
              <span className="processos-seletivos-detail-item__label">Abertura das inscrições</span>
              <strong className="processos-seletivos-detail-item__value">{formatDate(data.data_inicio)}</strong>
            </div>
            <div className="processos-seletivos-detail-item">
              <span className="processos-seletivos-detail-item__label">Encerramento das inscrições</span>
              <strong className="processos-seletivos-detail-item__value">{formatDate(data.data_fim)}</strong>
            </div>
          </div>
        ) : null}
      </section>

      <div className="processos-seletivos-footer-actions">
        <button type="button" className="btn btn--secondary" onClick={() => navigate(`/inscricoes/nova?publicacao=${data.id}`)}>
          <Users size={16} /> Adicionar candidato
        </button>
        <button type="button" className="btn btn--danger" onClick={handleDelete}>
          <Trash2 size={16} /> Remover edital
        </button>
      </div>
    </div>
  )
}