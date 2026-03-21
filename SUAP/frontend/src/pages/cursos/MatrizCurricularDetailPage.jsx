import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import { BookCopy, Boxes, Pencil, RefreshCcw } from 'lucide-react'
import { Link, useNavigate, useParams } from 'react-router-dom'

import { matrizesCurricularesApi } from '@/api/endpoints'

function SummaryCard({ label, value }) {
  return (
    <article className="matrix-summary-card">
      <span className="matrix-summary-card__label">{label}</span>
      <strong className="matrix-summary-card__value">{value || '—'}</strong>
    </article>
  )
}

export default function MatrizCurricularDetailPage() {
  const { matrizId } = useParams()
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  const { data, isLoading, isError } = useQuery({
    queryKey: ['matriz-curricular', matrizId],
    queryFn: () => matrizesCurricularesApi.get(matrizId).then((response) => response.data),
    enabled: Boolean(matrizId),
    staleTime: 30_000,
  })

  const syncMutation = useMutation({
    mutationFn: () => matrizesCurricularesApi.syncTemplate(matrizId),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['matriz-curricular', matrizId] })
      await queryClient.invalidateQueries({ queryKey: ['matrizes-curriculares'] })
      toast.success('Curso modelo da matriz sincronizado com o Moodle.')
    },
    onError: (error) => {
      toast.error(error?.response?.data?.detail || 'Não foi possível sincronizar o curso modelo da matriz.')
    },
  })

  const offerMutation = useMutation({
    mutationFn: () => matrizesCurricularesApi.gerarOferta(matrizId),
    onSuccess: async (response) => {
      toast.success('Oferta real criada a partir da matriz curricular.')
      const courseId = response?.data?.curso?.id
      await queryClient.invalidateQueries({ queryKey: ['matriz-curricular', matrizId] })
      if (courseId) {
        navigate(`/ensino/cursotecnico/${courseId}/editar`)
      }
    },
    onError: (error) => {
      toast.error(error?.response?.data?.detail || 'Não foi possível gerar a oferta real a partir da matriz.')
    },
  })

  if (isLoading) {
    return (
      <div className="page page--wide">
        <div className="page-loader" role="status" aria-live="polite">
          <div className="spinner" />
          <span>Carregando matriz curricular...</span>
        </div>
      </div>
    )
  }

  if (isError || !data) {
    return (
      <div className="page page--wide">
        <div className="page-error">
          <h1 className="page-error__title">Não foi possível carregar a matriz curricular</h1>
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
        <Link to="/ensino/matrizes-curriculares/">Matrizes Curriculares</Link>
        <span className="profile-breadcrumb__sep">&gt;</span>
        <span>{data.nome}</span>
      </nav>

      <div className="page-header">
        <div>
          <h1 className="page-title">{data.nome}</h1>
          <p className="page-subtitle">Curso base: {data.curso_base_nome} • Ano {data.ano_referencia} • Versão {data.versao}</p>
        </div>
        <div className="page-header__actions">
          <button type="button" className="btn btn--outline" onClick={() => syncMutation.mutate()} disabled={syncMutation.isPending}>
            <RefreshCcw size={16} /> {syncMutation.isPending ? 'Sincronizando...' : 'Atualizar modelo Moodle'}
          </button>
          <button type="button" className="btn btn--secondary" onClick={() => offerMutation.mutate()} disabled={offerMutation.isPending}>
            <BookCopy size={16} /> {offerMutation.isPending ? 'Gerando oferta...' : 'Criar oferta a partir da matriz'}
          </button>
          <button type="button" className="btn btn--primary" onClick={() => navigate(`/ensino/matrizes-curriculares/${data.id}/editar`)}>
            <Pencil size={16} /> Editar matriz
          </button>
        </div>
      </div>

      <section className="dashboard-card matrix-page__hero">
        <div className="matrix-summary-grid">
          <SummaryCard label="Status" value={data.status} />
          <SummaryCard label="Ativa" value={data.ativa ? 'Sim' : 'Não'} />
          <SummaryCard label="Módulos" value={data.total_modulos} />
          <SummaryCard label="Componentes" value={data.total_componentes} />
          <SummaryCard label="Curso modelo Moodle" value={data.moodle_template_shortname || 'Não sincronizado'} />
          <SummaryCard label="Última sincronização" value={data.last_sync_at || 'Nunca sincronizada'} />
        </div>
      </section>

      <section className="dashboard-card matrix-page__section">
        <h2 className="dashboard-card__title">Dados gerais</h2>
        <div className="matrix-grid matrix-grid--two">
          <div className="matrix-field"><span>Curso base</span><strong>{data.curso_base_nome}</strong></div>
          <div className="matrix-field"><span>Sigla do curso base</span><strong>{data.curso_base_sigla || '—'}</strong></div>
          <div className="matrix-field"><span>Status</span><strong>{data.status}</strong></div>
          <div className="matrix-field"><span>Versão</span><strong>{data.versao}</strong></div>
          <div className="matrix-field matrix-field--full"><span>Descrição</span><strong>{data.descricao || 'Sem descrição cadastrada.'}</strong></div>
          <div className="matrix-field matrix-field--full"><span>Última mensagem de sincronização</span><strong>{data.last_sync_message || 'Sem mensagens registradas.'}</strong></div>
        </div>
      </section>

      <section className="dashboard-card matrix-page__section">
        <div className="matrix-section-header">
          <h2 className="dashboard-card__title">Organização por módulo</h2>
          <div className="matrix-section-header__tag"><Boxes size={14} /> Módulos e componentes</div>
        </div>
        <div className="matrix-modules">
          {(data.componentes_por_modulo || []).length ? (data.componentes_por_modulo || []).map((modulo) => (
            <article key={`${modulo.modulo_numero || 'sem'}-${modulo.modulo_nome}`} className="matrix-module-card">
              <header className="matrix-module-card__header">
                <div>
                  <h3>{modulo.modulo_nome}</h3>
                  <p>{modulo.modulo_numero ? `Módulo ${modulo.modulo_numero}` : 'Sem módulo estruturado'}</p>
                </div>
                <strong>{modulo.componentes?.length || 0} componentes</strong>
              </header>
              <div className="matrix-module-card__body">
                {(modulo.componentes || []).map((componente) => (
                  <div key={componente.id} className="matrix-component-row">
                    <div>
                      <strong>{componente.descricao || componente.nome}</strong>
                      <span>{componente.sigla || 'Sem sigla'} • {componente.carga_horaria || 0}h</span>
                    </div>
                    <div className="matrix-component-row__meta">
                      <span>Ordem {componente.ordem_no_modulo || '—'}</span>
                      <Link to={`/componentes/${componente.id}`}>Abrir componente</Link>
                    </div>
                  </div>
                ))}
              </div>
            </article>
          )) : <div className="matrix-empty">Nenhum componente foi vinculado a esta matriz curricular.</div>}
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
          )) : <div className="matrix-empty">Ainda não há eventos registrados para esta matriz.</div>}
        </div>
      </section>
    </div>
  )
}