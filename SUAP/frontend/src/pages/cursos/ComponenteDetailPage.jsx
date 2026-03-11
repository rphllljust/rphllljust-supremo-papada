import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { BookOpen, Clock3, Info, Pencil } from 'lucide-react'
import { Link, useNavigate, useParams } from 'react-router-dom'

import { componentesApi } from '@/api/endpoints'

const TABS = [
  { key: 'dados-gerais', label: 'Dados gerais' },
  { key: 'matrizes', label: 'Matrizes' },
  { key: 'equivalencias', label: 'Equivalências' },
]

function DetailField({ label, value }) {
  return (
    <div className="estagio-detail-field">
      <span className="estagio-detail-field__label">{label}</span>
      <strong className="estagio-detail-field__value">{value || '-'}</strong>
    </div>
  )
}

function SummaryCard({ label, value }) {
  return (
    <article className="componente-summary-card">
      <span className="componente-summary-card__label">{label}</span>
      <strong className="componente-summary-card__value">{value || '0'}</strong>
    </article>
  )
}

export default function ComponenteDetailPage() {
  const navigate = useNavigate()
  const { componenteId } = useParams()
  const [activeTab, setActiveTab] = useState('dados-gerais')

  const { data, isLoading, isError } = useQuery({
    queryKey: ['componentes', 'detail', componenteId],
    queryFn: () => componentesApi.get(componenteId).then((response) => response.data),
    enabled: Boolean(componenteId),
    staleTime: 30_000,
  })

  if (isLoading) {
    return (
      <div className="page page--wide">
        <div className="page-loader" role="status" aria-live="polite">
          <div className="spinner" />
          <span>Carregando componente...</span>
        </div>
      </div>
    )
  }

  if (isError || !data) {
    return (
      <div className="page page--wide">
        <div className="page-error">
          <h1 className="page-error__title">Não foi possível carregar o componente</h1>
          <p className="page-error__description">Verifique se o registro existe e tente novamente.</p>
        </div>
      </div>
    )
  }

  const title = [data.sigla, data.descricao].filter(Boolean).join(' - ') || `Componente ${data.id}`

  return (
    <div className="page page--wide componente-detail-page">
      <nav className="profile-breadcrumb">
        <Link to="/dashboard">Início</Link>
        <span className="profile-breadcrumb__sep">&gt;</span>
        <Link to="/ensino/componentes/">Componentes</Link>
        <span className="profile-breadcrumb__sep">&gt;</span>
        <span>{title}</span>
      </nav>

      <div className="page-header estagio-detail-page__header">
        <div>
          <h1 className="page-title">{title}</h1>
          <p className="page-subtitle">{data.matriz_curricular || 'Sem matriz curricular definida'} • {data.tipo_componente || 'Tipo não informado'}</p>
        </div>
        <div className="page-header__actions">
          <button type="button" className="btn btn--primary" onClick={() => navigate(`/componentes/${data.id}/editar`)}>
            <Pencil size={16} /> Editar componente
          </button>
        </div>
      </div>

      <div className="profile-status-row">
        <span className={`badge ${data.esta_ativo ? 'badge--success' : 'badge--secondary'}`}>{data.esta_ativo ? 'Ativo' : 'Inativo'}</span>
        <span className="badge badge--info">{data.nivel_ensino || 'Nível não informado'}</span>
        <span className="badge badge--secondary">{data.grupo_atuacao || 'Grupo não informado'}</span>
      </div>

      <section className="dashboard-card componente-hero-card">
        <div className="componente-hero-card__title">
          <BookOpen size={28} />
          <div>
            <strong>{data.descricao}</strong>
            <span>{data.descricao_diploma_historico || 'Sem descrição para diploma e histórico.'}</span>
          </div>
        </div>
        <div className="componente-summary-grid">
          <SummaryCard label="Hora/relógio" value={data.carga_horaria ? `${data.carga_horaria}h` : '-'} />
          <SummaryCard label="Hora/aula" value={data.hora_aula ? `${data.hora_aula}h` : '-'} />
          <SummaryCard label="Créditos" value={data.qtd_creditos || '-'} />
          <SummaryCard label="Abreviatura" value={data.abreviatura || '-'} />
        </div>
      </section>

      <div className="profile-tabs">
        {TABS.map((tab) => (
          <button
            key={tab.key}
            type="button"
            className={`profile-tabs__item ${activeTab === tab.key ? 'profile-tabs__item--active' : ''}`}
            onClick={() => setActiveTab(tab.key)}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {activeTab === 'dados-gerais' ? (
        <div className="estagio-detail-grid componente-detail-grid">
          <section className="dashboard-card estagio-detail-section">
            <div className="estagio-detail-section__title">
              <Info size={18} /> Dados gerais
            </div>
            <div className="estagio-detail-fields">
              <DetailField label="Descrição" value={data.descricao} />
              <DetailField label="Descrição no diploma e histórico" value={data.descricao_diploma_historico} />
              <DetailField label="Abreviatura" value={data.abreviatura} />
              <DetailField label="Sigla" value={data.sigla} />
              <DetailField label="Tipo do componente" value={data.tipo_componente} />
              <DetailField label="Diretoria" value={data.diretoria} />
              <DetailField label="Nível de ensino" value={data.nivel_ensino} />
              <DetailField label="Está ativo" value={data.esta_ativo ? 'Sim' : 'Não'} />
              <DetailField label="Hora/relógio" value={data.carga_horaria ? `${data.carga_horaria}h` : '-'} />
              <DetailField label="Hora/aula" value={data.hora_aula ? `${data.hora_aula}h` : '-'} />
              <DetailField label="Quantidade de créditos" value={data.qtd_creditos} />
              <DetailField label="Grupo de atuação" value={data.grupo_atuacao} />
              <DetailField label="Sigla do Q-Acadêmico" value={data.sigla_qacademico} />
              <DetailField label="Matriz curricular" value={data.matriz_curricular} />
            </div>
          </section>

          <section className="dashboard-card estagio-detail-section">
            <div className="estagio-detail-section__title">
              <Clock3 size={18} /> Observações
            </div>
            <div className="estagio-detail-note">
              {data.observacao || 'Nenhuma observação registrada para este componente.'}
            </div>
          </section>
        </div>
      ) : null}

      {activeTab === 'matrizes' ? (
        <section className="dashboard-card estagio-detail-section componente-detail-placeholder">
          <div className="estagio-detail-section__title">
            <BookOpen size={18} /> Matrizes vinculadas
          </div>
          <p>Este componente está atualmente vinculado à matriz curricular {data.matriz_curricular || 'não informada'}.</p>
          <p>O detalhamento completo das matrizes será expandido em uma próxima etapa.</p>
        </section>
      ) : null}

      {activeTab === 'equivalencias' ? (
        <section className="dashboard-card estagio-detail-section componente-detail-placeholder">
          <div className="estagio-detail-section__title">
            <BookOpen size={18} /> Equivalências
          </div>
          <p>Ainda não há equivalências cadastradas para este componente.</p>
        </section>
      ) : null}
    </div>
  )
}