import { useQuery } from '@tanstack/react-query'
import { Briefcase, CalendarDays, ClipboardList, Eye, FileText, Landmark, TimerReset, UserRound } from 'lucide-react'
import { Link, useParams } from 'react-router-dom'

import { estagiosApi } from '@/api/endpoints'

function formatDate(value) {
  if (!value) {
    return '-'
  }

  const date = new Date(`${value}T00:00:00`)
  if (Number.isNaN(date.getTime())) {
    return value
  }

  return new Intl.DateTimeFormat('pt-BR').format(date)
}

function formatMoney(value) {
  if (value === null || value === undefined || value === '') {
    return '-'
  }

  return new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency: 'BRL',
  }).format(Number(value))
}

function DetailField({ label, value }) {
  return (
    <div className="estagio-detail-field">
      <span className="estagio-detail-field__label">{label}</span>
      <strong className="estagio-detail-field__value">{value || '-'}</strong>
    </div>
  )
}

function FlagBadge({ active, label }) {
  return <span className={`badge ${active ? 'badge--success' : 'badge--secondary'}`}>{label}</span>
}

export default function EstagioDetailPage() {
  const { estagioId } = useParams()

  const { data, isLoading, isError } = useQuery({
    queryKey: ['estagio', estagioId],
    queryFn: () => estagiosApi.get(estagioId).then((response) => response.data),
    enabled: Boolean(estagioId),
    staleTime: 30_000,
  })

  if (isLoading) {
    return (
      <div className="page page--wide">
        <div className="page-loader" role="status" aria-live="polite">
          <div className="spinner" />
          <span>Carregando estágio...</span>
        </div>
      </div>
    )
  }

  if (isError || !data) {
    return (
      <div className="page page--wide">
        <div className="page-error">
          <h1 className="page-error__title">Não foi possível carregar o estágio</h1>
          <p className="page-error__description">Verifique se o registro existe e tente novamente.</p>
        </div>
      </div>
    )
  }

  return (
    <div className="page page--wide estagio-detail-page">
      <nav className="profile-breadcrumb">
        <Link to="/dashboard">Inicio</Link>
        <span className="profile-breadcrumb__sep">&gt;</span>
        <Link to="/estagio">Estágios</Link>
        <span className="profile-breadcrumb__sep">&gt;</span>
        <span>{data.aluno_nome}</span>
      </nav>

      <div className="page-header estagio-detail-page__header">
        <div>
          <h1 className="page-title">Estágio de {data.aluno_nome}</h1>
          <p className="page-subtitle">{data.curso_nome} • {data.campus_nome} • {data.modalidade_display}</p>
        </div>
        <div className="page-header__actions">
          <Link to="/estagio" className="btn btn--outline btn--sm">
            <Eye size={16} /> Voltar para listagem
          </Link>
        </div>
      </div>

      <div className="profile-status-row">
        <span className="badge badge--info">{data.status_display}</span>
        <FlagBadge active={data.possui_aditivo} label={data.possui_aditivo ? 'Com aditivo' : 'Sem aditivo'} />
        <FlagBadge active={data.apto_para_encerramento} label={data.apto_para_encerramento ? 'Apto para encerramento' : 'Em acompanhamento'} />
      </div>

      <section className="dashboard-card estagio-detail-hero">
        <div className="estagio-detail-hero__icon">
          <Briefcase size={42} />
        </div>
        <div className="estagio-detail-hero__content">
          <h2>{data.concedente_nome}</h2>
          <p>Professor orientador: {data.professor_orientador}</p>
          <div className="estagio-detail-hero__meta">
            <span><UserRound size={14} /> {data.aluno_identificador}</span>
            <span><CalendarDays size={14} /> Início em {formatDate(data.data_inicio)}</span>
            <span><TimerReset size={14} /> Previsto até {formatDate(data.data_prevista_encerramento)}</span>
          </div>
        </div>
      </section>

      <div className="estagio-detail-grid">
        <section className="dashboard-card estagio-detail-section">
          <div className="estagio-detail-section__title">
            <ClipboardList size={18} /> Dados do estágio
          </div>
          <div className="estagio-detail-fields">
            <DetailField label="Estagiário" value={data.aluno_nome} />
            <DetailField label="Matrícula" value={data.aluno_identificador} />
            <DetailField label="Situação do estagiário" value={data.situacao_estagiario} />
            <DetailField label="Situação da matrícula" value={data.situacao_matricula_periodo} />
            <DetailField label="Turma" value={data.turma_nome} />
            <DetailField label="Tipo de matrícula" value={data.matricula_tipo} />
            <DetailField label="Turno" value={data.turno} />
            <DetailField label="Campus" value={data.campus_nome} />
            <DetailField label="Curso" value={data.curso_nome} />
            <DetailField label="Modalidade" value={data.modalidade_display} />
            <DetailField label="Supervisor na empresa" value={data.supervisor_empresa} />
            <DetailField label="Seguro" value={data.seguro_numero} />
            <DetailField label="Carga horária total" value={data.carga_horaria_total ? `${data.carga_horaria_total} h` : '-'} />
            <DetailField label="Carga horária semanal" value={data.carga_horaria_semanal ? `${data.carga_horaria_semanal} h` : '-'} />
            <DetailField label="Bolsa mensal" value={formatMoney(data.bolsa_mensal)} />
            <DetailField label="Data do encerramento" value={formatDate(data.data_encerramento)} />
          </div>
          <div className="estagio-detail-note">
            <strong>Observação:</strong> {data.observacao || 'Nenhuma observação registrada para este estágio.'}
          </div>
        </section>

        <section className="dashboard-card estagio-detail-section">
          <div className="estagio-detail-section__title">
            <Landmark size={18} /> Convênio e termos
          </div>
          <div className="estagio-detail-fields">
            <DetailField label="Convênio" value={data.convenio_numero || '-'} />
            <DetailField label="Situação do convênio" value={data.situacao_convenio} />
            <DetailField label="Responsável IDEP" value={data.convenio_responsavel} />
            <DetailField label="Aguardando assinatura" value={data.aguardando_assinatura_coordenador ? 'Sim' : 'Não'} />
          </div>

          <div className="estagio-detail-list">
            {data.termos?.length ? data.termos.map((termo) => (
              <article key={termo.id} className="estagio-detail-list__card">
                <strong>{termo.numero_termo}</strong>
                <p>{termo.status_display} • Assinatura: {formatDate(termo.data_assinatura)}</p>
                <p>Aluno: {termo.assinado_aluno ? 'Sim' : 'Não'} • Empresa: {termo.assinado_empresa ? 'Sim' : 'Não'} • IDEP: {termo.assinado_idep ? 'Sim' : 'Não'}</p>
                <p>{termo.observacao || 'Sem observação adicional.'}</p>
              </article>
            )) : <p className="estagio-detail-empty">Nenhum termo de compromisso registrado.</p>}
          </div>
        </section>
      </div>

      <section className="dashboard-card estagio-detail-section">
        <div className="estagio-detail-section__title">
          <FileText size={18} /> Acompanhamentos
        </div>
        <div className="estagio-detail-list">
          {data.acompanhamentos?.length ? data.acompanhamentos.map((item) => (
            <article key={item.id} className="estagio-detail-list__card">
              <strong>{item.tipo_display}</strong>
              <p>{formatDate(item.data)} • Registrado por {item.registrado_por_nome}</p>
              <p>{item.descricao}</p>
            </article>
          )) : <p className="estagio-detail-empty">Nenhum acompanhamento registrado para este estágio.</p>}
        </div>
      </section>
    </div>
  )
}