import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Link2, Pencil } from 'lucide-react'
import { Link, useNavigate, useParams } from 'react-router-dom'

import { componentesApi } from '@/api/endpoints'
import './suap-componentes.css'

const TABS = [
  { key: 'cadastro-base', label: 'Cadastro base' },
  { key: 'vinculacao-matriz', label: 'Vinculação à matriz' },
  { key: 'equivalencias', label: 'Equivalências' },
]

function DetailField({ label, value, wide = false }) {
  return (
    <div className={`componente-detail-field ${wide ? 'componente-detail-field--wide' : ''}`}>
      <span className="componente-detail-field__label">{label}</span>
      <strong className="componente-detail-field__value">{value || '-'}</strong>
    </div>
  )
}

function SummaryCard({ label, value }) {
  return (
    <article className="componente-summary-card suap-card">
      <span className="componente-summary-card__label">{label}</span>
      <strong className="componente-summary-card__value">{value || '0'}</strong>
    </article>
  )
}

export default function ComponenteDetailPage() {
  const navigate = useNavigate()
  const { componenteId } = useParams()
  const [activeTab, setActiveTab] = useState('cadastro-base')

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
    <div className="page page--wide componente-detail-page suap-componentes-shell">
      <nav className="componentes-page__breadcrumb suap-breadcrumb">
        <Link to="/dashboard">Início</Link>
        <span className="suap-breadcrumb__sep">&rsaquo;</span>
        <span>Ensino</span>
        <span className="suap-breadcrumb__sep">&rsaquo;</span>
        <span>Cursos, Matrizes e Componentes</span>
        <span className="suap-breadcrumb__sep">&rsaquo;</span>
        <Link to="/ensino/componentes/">Componentes</Link>
        <span className="suap-breadcrumb__sep">&rsaquo;</span>
        <span>{title}</span>
      </nav>

      <section className="suap-card componente-detail-header">
        <div className="componente-detail-header__main">
          <div>
            <h1 className="componentes-page__title componentes-page__title--detail">{data.descricao || title}</h1>
            <p className="componente-detail-header__subtitle">Cadastro base do componente curricular, separado dos parâmetros de vinculação à matriz.</p>
          </div>
          <div className="componente-detail-header__actions">
            <button type="button" className="componentes-page__toolbar-btn componentes-page__toolbar-btn--blue" onClick={() => navigate(`/componentes/${data.id}/vinculacao`)}>
              <Link2 size={14} /> Vinculação à matriz
            </button>
            <button type="button" className="componentes-page__toolbar-btn componentes-page__toolbar-btn--green" onClick={() => navigate(`/componentes/${data.id}/editar`)}>
              <Pencil size={14} /> Editar cadastro base
            </button>
          </div>
        </div>

        <div className="componente-summary-grid componente-summary-grid--detail">
          <SummaryCard label="Sigla" value={data.sigla || '-'} />
          <SummaryCard label="Abreviatura" value={data.abreviatura || '-'} />
          <SummaryCard label="Nível de ensino" value={data.nivel_ensino_nome || data.nivel_ensino || '-'} />
          <SummaryCard label="Status" value={data.esta_ativo ? 'Ativo' : 'Inativo'} />
        </div>
      </section>

      <div className="componentes-tabs">
        {TABS.map((tab) => (
          <button
            key={tab.key}
            type="button"
            className={`componentes-tabs__item ${activeTab === tab.key ? 'componentes-tabs__item--active' : ''}`}
            onClick={() => setActiveTab(tab.key)}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {activeTab === 'cadastro-base' ? (
        <div className="componente-detail-stack">
          <section className="suap-card componente-detail-panel">
            <div className="componente-detail-panel__header">Dados gerais</div>
            <div className="componente-detail-grid">
              <DetailField label="Descrição" value={data.descricao} wide />
              <DetailField label="Abreviatura" value={data.abreviatura} />
              <DetailField label="Sigla" value={data.sigla} />
              <DetailField label="Tipo do componente" value={data.tipo_componente_nome || data.tipo_componente} />
              <DetailField label="Nível de ensino" value={data.nivel_ensino_nome || data.nivel_ensino} />
              <DetailField label="Coordenação/Departamento responsável" value={data.diretoria} />
              <DetailField label="Eixo tecnológico / Área de conhecimento" value={data.grupo_atuacao} />
              <DetailField label="Está ativo" value={data.esta_ativo ? 'Sim' : 'Não'} />
            </div>
          </section>

          <section className="suap-card componente-detail-panel">
            <div className="componente-detail-panel__header">Documentação oficial</div>
            <div className="componente-detail-grid">
              <DetailField label="Descrição no histórico" value={data.descricao_diploma_historico || data.descricao} wide />
              <DetailField label="Descrição no diploma" value={data.descricao_diploma_historico || data.descricao} wide />
            </div>
          </section>

          <section className="suap-card componente-detail-panel">
            <div className="componente-detail-panel__header">Integrações e controle</div>
            <div className="componente-detail-grid">
              <DetailField label="Código no sistema legado / Q-Acadêmico" value={data.sigla_qacademico} />
              <DetailField label="Observação" value={data.observacao} wide />
            </div>
          </section>
        </div>
      ) : null}

      {activeTab === 'vinculacao-matriz' ? (
        <div className="componente-detail-stack">
          <section className="suap-card componente-detail-panel">
            <div className="componente-detail-panel__header">Parâmetros atuais de vinculação</div>
            <div className="componente-detail-grid">
              <DetailField label="Matriz curricular" value={data.matriz_curricular} wide />
              <DetailField label="Curso legado / oferta" value={data.curso_nome} wide />
              <DetailField label="Hora/relógio" value={data.carga_horaria ? `${data.carga_horaria} h` : '-'} />
              <DetailField label="Hora/aula" value={data.hora_aula ? `${data.hora_aula} h` : '-'} />
              <DetailField label="Quantidade de créditos" value={data.qtd_creditos} />
              <DetailField label="Módulo" value={data.modulo_numero ? `Módulo ${data.modulo_numero}` : '-'} />
              <DetailField label="Nome do módulo" value={data.modulo_nome} />
              <DetailField label="Conteúdo abordado no módulo" value={data.conteudo_modulo} wide />
              <DetailField label="Ordem no módulo" value={data.ordem_no_modulo} />
            </div>
          </section>

          <section className="suap-card componente-detail-panel">
            <div className="componente-detail-panel__header">Fluxo de vinculação</div>
            <div className="componente-detail-note componente-detail-note--actionable">
              <p>Os dados de matriz curricular, carga horária e créditos ficam concentrados no fluxo de vinculação, separado do cadastro base do componente.</p>
              <button type="button" className="btn btn--secondary" onClick={() => navigate(`/componentes/${data.id}/vinculacao`)}>
                <Link2 size={16} /> Editar vinculação à matriz
              </button>
            </div>
          </section>
        </div>
      ) : null}

      {activeTab === 'equivalencias' ? (
        <section className="suap-card componente-detail-panel">
          <div className="componente-detail-panel__header">Equivalências</div>
          <div className="componente-detail-note">
            Ainda não há equivalências cadastradas para este componente.
          </div>
        </section>
      ) : null}
    </div>
  )
}
