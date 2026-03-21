import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import { Pencil, RefreshCcw } from 'lucide-react'
import { Link, useNavigate, useParams } from 'react-router-dom'

import { ofertasApi } from '@/api/endpoints'

function SummaryCard({ label, value }) {
  return (
    <article className="matrix-summary-card">
      <span className="matrix-summary-card__label">{label}</span>
      <strong className="matrix-summary-card__value">{value || '—'}</strong>
    </article>
  )
}

export default function OfertaCursoDetailPage() {
  const { ofertaId } = useParams()
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  const { data, isLoading, isError } = useQuery({
    queryKey: ['oferta-curso', ofertaId],
    queryFn: () => ofertasApi.get(ofertaId).then((response) => response.data),
    enabled: Boolean(ofertaId),
    staleTime: 30_000,
  })

  const syncMutation = useMutation({
    mutationFn: () => ofertasApi.syncMoodle(ofertaId),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['oferta-curso', ofertaId] })
      await queryClient.invalidateQueries({ queryKey: ['ofertas-cursos'] })
      toast.success('Oferta sincronizada com o Moodle.')
    },
    onError: (error) => {
      toast.error(error?.response?.data?.detail || 'Não foi possível sincronizar a oferta com o Moodle.')
    },
  })

  if (isLoading) {
    return (
      <div className="page page--wide">
        <div className="page-loader" role="status" aria-live="polite">
          <div className="spinner" />
          <span>Carregando oferta...</span>
        </div>
      </div>
    )
  }

  if (isError || !data) {
    return (
      <div className="page page--wide">
        <div className="page-error">
          <h1 className="page-error__title">Não foi possível carregar a oferta</h1>
          <p className="page-error__description">Verifique se o registro existe e tente novamente.</p>
        </div>
      </div>
    )
  }

  return (
    <div className="page page--wide matrix-page">
      <nav className="profile-breadcrumb">
        <Link to="/dashboard">Início</Link>
        <span className="profile-breadcrumb__sep">&gt;</span>
        <Link to="/ensino/ofertas/">Ofertas de Curso</Link>
        <span className="profile-breadcrumb__sep">&gt;</span>
        <span>{data.nome}</span>
      </nav>

      <div className="page-header">
        <div>
          <h1 className="page-title">{data.nome}</h1>
          <p className="page-subtitle">{data.curso_base_nome} • Matriz {data.matriz_curricular_nome} • Polo {data.polo_nome}</p>
        </div>
        <div className="page-header__actions">
          <button type="button" className="btn btn--outline" onClick={() => syncMutation.mutate()} disabled={syncMutation.isPending || !data.pode_sincronizar_moodle}>
            <RefreshCcw size={16} /> {syncMutation.isPending ? 'Sincronizando...' : 'Sincronizar Moodle'}
          </button>
          <button type="button" className="btn btn--primary" onClick={() => navigate(`/ensino/ofertas/${data.id}/editar`)}>
            <Pencil size={16} /> Editar oferta
          </button>
        </div>
      </div>

      <section className="dashboard-card matrix-page__hero">
        <div className="matrix-summary-grid">
          <SummaryCard label="Ano/Período" value={`${data.ano_oferta}.${data.periodo_letivo}`} />
          <SummaryCard label="Turma" value={data.codigo_turma || 'Sem código'} />
          <SummaryCard label="Turno" value={data.turno} />
          <SummaryCard label="Status" value={data.status} />
          <SummaryCard label="Vagas" value={`${data.vagas_ocupadas}/${data.vagas_totais}`} />
          <SummaryCard label="Sync Moodle" value={data.last_sync_status || 'pendente'} />
        </div>
      </section>

      <section className="dashboard-card matrix-page__section">
        <h2 className="dashboard-card__title">Dados gerais</h2>
        <div className="matrix-grid matrix-grid--two">
          <div className="matrix-field"><span>Curso base</span><strong>{data.curso_base_nome}</strong></div>
          <div className="matrix-field"><span>Matriz curricular</span><strong>{data.matriz_curricular_nome}</strong></div>
          <div className="matrix-field"><span>Polo</span><strong>{data.polo_nome}</strong></div>
          <div className="matrix-field"><span>Calendário letivo</span><strong>{data.calendario_letivo_nome}</strong></div>
          <div className="matrix-field"><span>Módulos previstos</span><strong>{data.modulos_previstos}</strong></div>
          <div className="matrix-field"><span>Curso Moodle</span><strong>{data.moodle_shortname || 'Ainda não sincronizado'}</strong></div>
          <div className="matrix-field matrix-field--full"><span>Observações</span><strong>{data.observacao || 'Sem observações cadastradas.'}</strong></div>
          <div className="matrix-field matrix-field--full"><span>Última mensagem de sincronização</span><strong>{data.last_sync_message || 'Sem mensagens registradas.'}</strong></div>
        </div>
      </section>

      <section className="dashboard-card matrix-page__section">
        <h2 className="dashboard-card__title">Logs recentes</h2>
        <div className="matrix-logs">
          {(data.logs_recentes || []).length ? data.logs_recentes.slice(0, 10).map((item) => (
            <div key={item.id} className={`matrix-log matrix-log--${item.status}`}>
              <strong>{item.evento}</strong>
              <span>{item.mensagem || 'Sem mensagem complementar.'}</span>
              <small>{item.created_at}</small>
            </div>
          )) : <div className="matrix-empty">Ainda não há eventos registrados para esta oferta.</div>}
        </div>
      </section>
    </div>
  )
}
