import { useEffect, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { AlertTriangle, ArrowLeft, FileText, Lock, Plus, RotateCcw, Save } from 'lucide-react'
import { Link, useNavigate, useParams, useSearchParams } from 'react-router-dom'
import toast from 'react-hot-toast'

import { diarioApi } from '@/api/endpoints'

import './diarios.css'

const TABS = [
  { key: 'geral', label: 'Geral' },
  { key: 'registro-notas', label: 'Registro de Notas' },
  { key: 'materiais', label: 'Materiais de Aula' },
  { key: 'ocorrencias', label: 'Ocorrências' },
  { key: 'suspensoes', label: 'Suspensões' },
  { key: 'estatisticas', label: 'Estatísticas' },
]

function formatDate(value) {
  if (!value) return '-'
  const date = new Date(`${value}T00:00:00`)
  if (Number.isNaN(date.getTime())) return value
  return new Intl.DateTimeFormat('pt-BR').format(date)
}

function formatDecimal(value) {
  if (value === null || value === undefined || value === '') return '-'
  const number = Number(value)
  if (Number.isNaN(number)) return value
  return number.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

function getErrorMessage(error, fallback) {
  const data = error?.response?.data

  if (!data) return fallback
  if (typeof data.detail === 'string') return data.detail

  const firstValue = Object.values(data)[0]
  return Array.isArray(firstValue) ? firstValue[0] : (firstValue || fallback)
}

function SummaryCard({ label, value }) {
  return (
    <article className="diarios-summary-card diarios-summary-card--static">
      <span className="diarios-summary-card__label">{label}</span>
      <strong className="diarios-summary-card__value">{value || '0'}</strong>
    </article>
  )
}

function InfoField({ label, value, wide = false }) {
  return (
    <div className={`diario-info-field ${wide ? 'diario-info-field--wide' : ''}`}>
      <span className="diario-info-field__label">{label}</span>
      <strong className="diario-info-field__value">{value || '-'}</strong>
    </div>
  )
}

function EmptyState({ title, description }) {
  return (
    <div className="diario-empty-state">
      <AlertTriangle size={18} />
      <div>
        <strong>{title}</strong>
        <p>{description}</p>
      </div>
    </div>
  )
}

function MaterialCard({ item }) {
  return (
    <article className="diario-record-card">
      <div className="diario-record-card__header">
        <strong>{item.titulo}</strong>
        <span>{formatDate(item.data_referencia)}</span>
      </div>
      <p>{item.descricao || 'Sem descrição.'}</p>
      <div className="diario-record-card__footer">
        <span>Publicado por {item.criado_por_nome || 'Sistema'}</span>
        {item.url_material ? <a href={item.url_material} target="_blank" rel="noreferrer">Abrir material</a> : null}
      </div>
    </article>
  )
}

function OccurrenceCard({ item }) {
  return (
    <article className="diario-record-card">
      <div className="diario-record-card__header">
        <strong>{item.titulo}</strong>
        <span>{formatDate(item.data_ocorrencia)}</span>
      </div>
      <p>{item.descricao}</p>
      <div className="diario-record-card__footer">
        <span>{item.tipo_display}</span>
        <span>Registrado por {item.registrado_por_nome || 'Sistema'}</span>
      </div>
    </article>
  )
}

export default function DiarioDetailPage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { diarioId } = useParams()
  const [searchParams, setSearchParams] = useSearchParams()
  const activeTab = TABS.some((tab) => tab.key === searchParams.get('aba')) ? searchParams.get('aba') : 'geral'

  const [generalForm, setGeneralForm] = useState({ periodo: '', componente_curricular: '', observacoes: '' })
  const [materialForm, setMaterialForm] = useState({ titulo: '', descricao: '', data_referencia: '', url_material: '' })
  const [occurrenceForm, setOccurrenceForm] = useState({ titulo: '', descricao: '', data_ocorrencia: '', tipo: 'OCORRENCIA' })
  const [documentPreview, setDocumentPreview] = useState('')

  const { data, isLoading, isError } = useQuery({
    queryKey: ['diario', diarioId],
    queryFn: () => diarioApi.get(diarioId).then((response) => response.data),
    enabled: Boolean(diarioId),
    staleTime: 30_000,
  })

  useEffect(() => {
    if (!data) return
    setGeneralForm({
      periodo: data.periodo || '',
      componente_curricular: data.componente_curricular || '',
      observacoes: data.observacoes || '',
    })
  }, [data])

  const refreshDiary = async () => {
    await Promise.all([
      queryClient.invalidateQueries({ queryKey: ['diarios'] }),
      queryClient.invalidateQueries({ queryKey: ['diario', diarioId] }),
    ])
  }

  const saveMutation = useMutation({
    mutationFn: (payload) => diarioApi.patch(diarioId, payload),
    onSuccess: async () => {
      await refreshDiary()
      toast.success('Diário atualizado com sucesso.')
    },
    onError: (error) => toast.error(getErrorMessage(error, 'Não foi possível atualizar o diário.')),
  })

  const statusMutation = useMutation({
    mutationFn: (action) => (action === 'fechar' ? diarioApi.fechar(diarioId) : diarioApi.reabrir(diarioId)),
    onSuccess: async (_response, action) => {
      await refreshDiary()
      toast.success(action === 'fechar' ? 'Diário fechado com sucesso.' : 'Diário reaberto com sucesso.')
    },
    onError: (error) => toast.error(getErrorMessage(error, 'Não foi possível alterar o status do diário.')),
  })

  const documentMutation = useMutation({
    mutationFn: () => diarioApi.documento(diarioId),
    onSuccess: (response) => setDocumentPreview(response.data?.documento || ''),
    onError: (error) => toast.error(getErrorMessage(error, 'Não foi possível gerar o documento do diário.')),
  })

  const materialMutation = useMutation({
    mutationFn: (payload) => diarioApi.criarMaterial(diarioId, payload),
    onSuccess: async () => {
      await refreshDiary()
      setMaterialForm({ titulo: '', descricao: '', data_referencia: '', url_material: '' })
      toast.success('Material registrado com sucesso.')
    },
    onError: (error) => toast.error(getErrorMessage(error, 'Não foi possível registrar o material.')),
  })

  const occurrenceMutation = useMutation({
    mutationFn: (payload) => diarioApi.criarOcorrencia(diarioId, payload),
    onSuccess: async (_response, payload) => {
      await refreshDiary()
      setOccurrenceForm({ titulo: '', descricao: '', data_ocorrencia: '', tipo: payload.tipo || 'OCORRENCIA' })
      toast.success(payload.tipo === 'SUSPENSAO' ? 'Suspensão registrada com sucesso.' : 'Ocorrência registrada com sucesso.')
    },
    onError: (error) => toast.error(getErrorMessage(error, 'Não foi possível registrar a ocorrência.')),
  })

  if (isLoading) {
    return (
      <div className="page page--wide">
        <div className="page-loader" role="status" aria-live="polite">
          <div className="spinner" />
          <span>Carregando diário...</span>
        </div>
      </div>
    )
  }

  if (isError || !data) {
    return (
      <div className="page page--wide">
        <div className="page-error">
          <h1 className="page-error__title">Não foi possível carregar o diário</h1>
          <p className="page-error__description">Verifique se o registro existe e tente novamente.</p>
        </div>
      </div>
    )
  }

  const stats = data.estatisticas || {}

  return (
    <div className="page page--wide diario-detail-page">
      <nav className="profile-breadcrumb">
        <Link to="/dashboard">Início</Link>
        <span className="profile-breadcrumb__sep">&gt;</span>
        <Link to="/diarios">Diários</Link>
        <span className="profile-breadcrumb__sep">&gt;</span>
        <span>{data.turma_nome} • {data.periodo}</span>
      </nav>

      <section className="diario-hero-card">
        <div className="diario-hero-card__main">
          <div>
            <div className="diario-hero-card__meta">{data.unidade_nome} • {data.curso_nome}</div>
            <h1 className="page-title">{data.turma_nome} • {data.periodo}</h1>
            <p className="page-subtitle">{data.componente_curricular || 'Componente curricular ainda não definido.'}</p>
          </div>
          <div className="page-header__actions">
            <button type="button" className="btn btn--outline" onClick={() => navigate('/diarios')}>
              <ArrowLeft size={16} /> Voltar
            </button>
            <button type="button" className="btn btn--secondary" onClick={() => documentMutation.mutate()} disabled={documentMutation.isPending}>
              <FileText size={16} /> {documentMutation.isPending ? 'Gerando...' : 'Visualizar documento'}
            </button>
            {data.status === 'FECHADO' ? (
              <button type="button" className="btn btn--outline" onClick={() => statusMutation.mutate('reabrir')}>
                <RotateCcw size={16} /> Reabrir
              </button>
            ) : (
              <button type="button" className="btn btn--dark" onClick={() => statusMutation.mutate('fechar')}>
                <Lock size={16} /> Fechar diário
              </button>
            )}
          </div>
        </div>

        <div className="diarios-summary-grid diario-hero-card__summary">
          <SummaryCard label="Alunos ativos" value={stats.total_alunos} />
          <SummaryCard label="Notas pendentes" value={data.notas_pendentes} />
          <SummaryCard label="Frequências pendentes" value={data.frequencias_pendentes} />
          <SummaryCard label="Status" value={data.status_display} />
        </div>
      </section>

      {documentPreview ? (
        <section className="diario-panel diario-document-preview">
          <div className="diario-panel__header">
            <h2>Pré-visualização do documento</h2>
            <button type="button" className="btn btn--outline btn--sm" onClick={() => setDocumentPreview('')}>Fechar prévia</button>
          </div>
          <pre>{documentPreview}</pre>
        </section>
      ) : null}

      <div className="profile-tabs diarios-tabs" role="tablist" aria-label="Abas do diário">
        {TABS.map((tab) => (
          <button
            key={tab.key}
            type="button"
            className={`profile-tabs__item ${activeTab === tab.key ? 'profile-tabs__item--active' : ''}`}
            onClick={() => setSearchParams({ aba: tab.key })}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {activeTab === 'geral' ? (
        <div className="diario-detail-stack">
          <section className="diario-panel">
            <div className="diario-panel__header"><h2>Dados gerais</h2></div>
            <div className="diario-info-grid">
              <InfoField label="Turma" value={data.turma_nome} />
              <InfoField label="Curso" value={data.curso_nome} />
              <InfoField label="Unidade" value={data.unidade_nome} />
              <InfoField label="Professor" value={data.professor_nome} />
              <InfoField label="Abertura" value={formatDate(data.data_abertura)} />
              <InfoField label="Fechamento" value={formatDate(data.data_fechamento)} />
              <InfoField label="Aberto por" value={data.aberto_por_nome} />
              <InfoField label="Fechado por" value={data.fechado_por_nome} />
              <InfoField label="Status" value={data.status_display} />
              <InfoField label="Ano letivo" value={String(data.ano_letivo)} />
            </div>
          </section>

          <section className="diario-panel">
            <div className="diario-panel__header"><h2>Ajustes do diário</h2></div>
            <form className="diario-form-grid" onSubmit={(event) => { event.preventDefault(); saveMutation.mutate(generalForm) }}>
              <div className="form-field">
                <label htmlFor="diario-detail-periodo">Período</label>
                <input id="diario-detail-periodo" className="form-control" value={generalForm.periodo} onChange={(event) => setGeneralForm((current) => ({ ...current, periodo: event.target.value }))} />
              </div>
              <div className="form-field form-field--full">
                <label htmlFor="diario-detail-componente">Componente curricular</label>
                <input id="diario-detail-componente" className="form-control" value={generalForm.componente_curricular} onChange={(event) => setGeneralForm((current) => ({ ...current, componente_curricular: event.target.value }))} />
              </div>
              <div className="form-field form-field--full">
                <label htmlFor="diario-detail-observacoes">Observações</label>
                <textarea id="diario-detail-observacoes" className="form-control diarios-textarea" value={generalForm.observacoes} onChange={(event) => setGeneralForm((current) => ({ ...current, observacoes: event.target.value }))} />
              </div>
              <div className="diario-form-actions">
                <button type="submit" className="btn btn--primary" disabled={saveMutation.isPending}>
                  <Save size={16} /> {saveMutation.isPending ? 'Salvando...' : 'Salvar ajustes'}
                </button>
              </div>
            </form>
          </section>
        </div>
      ) : null}

      {activeTab === 'registro-notas' ? (
        <section className="diario-panel">
          <div className="diario-panel__header"><h2>Registro consolidado por aluno</h2></div>
          {data.estudantes?.length ? (
            <div className="diario-table-wrap">
              <table className="diario-table">
                <thead>
                  <tr>
                    <th>Matrícula</th>
                    <th>Aluno</th>
                    <th>Notas lançadas</th>
                    <th>Média</th>
                    <th>Frequência</th>
                    <th>Situação</th>
                  </tr>
                </thead>
                <tbody>
                  {data.estudantes.map((student) => (
                    <tr key={student.id}>
                      <td>{student.numero_matricula}</td>
                      <td>{student.aluno_nome}</td>
                      <td>
                        <div className="diario-note-list">
                          {student.notas.length ? student.notas.map((nota) => (
                            <span key={nota.id} className="diario-note-pill">{nota.descricao}: {formatDecimal(nota.valor)}</span>
                          )) : <span className="badge badge--warning">Sem notas</span>}
                        </div>
                      </td>
                      <td>{formatDecimal(student.media_final)}</td>
                      <td>{student.percentual_frequencia !== null ? `${formatDecimal(student.percentual_frequencia)}%` : '-'}</td>
                      <td>{student.situacao}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : <EmptyState title="Sem alunos ativos" description="A turma ainda não possui matrículas ativas vinculadas ao diário." />}
        </section>
      ) : null}

      {activeTab === 'materiais' ? (
        <div className="diario-detail-stack">
          <section className="diario-panel">
            <div className="diario-panel__header"><h2>Novo material de aula</h2></div>
            <form className="diario-form-grid" onSubmit={(event) => {
              event.preventDefault()
              materialMutation.mutate(materialForm)
            }}>
              <div className="form-field form-field--full">
                <label htmlFor="material-titulo">Título</label>
                <input id="material-titulo" className="form-control" value={materialForm.titulo} onChange={(event) => setMaterialForm((current) => ({ ...current, titulo: event.target.value }))} />
              </div>
              <div className="form-field form-field--full">
                <label htmlFor="material-descricao">Descrição</label>
                <textarea id="material-descricao" className="form-control diarios-textarea" value={materialForm.descricao} onChange={(event) => setMaterialForm((current) => ({ ...current, descricao: event.target.value }))} />
              </div>
              <div className="form-field">
                <label htmlFor="material-data">Data de referência</label>
                <input id="material-data" type="date" className="form-control" value={materialForm.data_referencia} onChange={(event) => setMaterialForm((current) => ({ ...current, data_referencia: event.target.value }))} />
              </div>
              <div className="form-field">
                <label htmlFor="material-url">URL do material</label>
                <input id="material-url" className="form-control" value={materialForm.url_material} onChange={(event) => setMaterialForm((current) => ({ ...current, url_material: event.target.value }))} placeholder="https://..." />
              </div>
              <div className="diario-form-actions">
                <button type="submit" className="btn btn--primary" disabled={materialMutation.isPending}>
                  <Plus size={16} /> {materialMutation.isPending ? 'Salvando...' : 'Adicionar material'}
                </button>
              </div>
            </form>
          </section>

          <section className="diario-panel">
            <div className="diario-panel__header"><h2>Materiais publicados</h2></div>
            <div className="diario-record-stack">
              {data.materiais_aula?.length ? data.materiais_aula.map((item) => <MaterialCard key={item.id} item={item} />) : <EmptyState title="Nenhum material publicado" description="Publique roteiros, links, apostilas e referências para a turma." />}
            </div>
          </section>
        </div>
      ) : null}

      {activeTab === 'ocorrencias' ? (
        <div className="diario-detail-stack">
          <section className="diario-panel">
            <div className="diario-panel__header"><h2>Nova ocorrência</h2></div>
            <form className="diario-form-grid" onSubmit={(event) => {
              event.preventDefault()
              occurrenceMutation.mutate({ ...occurrenceForm, tipo: 'OCORRENCIA' })
            }}>
              <div className="form-field form-field--full">
                <label htmlFor="ocorrencia-titulo">Título</label>
                <input id="ocorrencia-titulo" className="form-control" value={occurrenceForm.titulo} onChange={(event) => setOccurrenceForm((current) => ({ ...current, titulo: event.target.value }))} />
              </div>
              <div className="form-field form-field--full">
                <label htmlFor="ocorrencia-descricao">Descrição</label>
                <textarea id="ocorrencia-descricao" className="form-control diarios-textarea" value={occurrenceForm.descricao} onChange={(event) => setOccurrenceForm((current) => ({ ...current, descricao: event.target.value }))} />
              </div>
              <div className="form-field">
                <label htmlFor="ocorrencia-data">Data</label>
                <input id="ocorrencia-data" type="date" className="form-control" value={occurrenceForm.data_ocorrencia} onChange={(event) => setOccurrenceForm((current) => ({ ...current, data_ocorrencia: event.target.value }))} />
              </div>
              <div className="diario-form-actions">
                <button type="submit" className="btn btn--primary" disabled={occurrenceMutation.isPending}>
                  <Plus size={16} /> {occurrenceMutation.isPending ? 'Registrando...' : 'Registrar ocorrência'}
                </button>
              </div>
            </form>
          </section>

          <section className="diario-panel">
            <div className="diario-panel__header"><h2>Ocorrências registradas</h2></div>
            <div className="diario-record-stack">
              {data.ocorrencias?.length ? data.ocorrencias.map((item) => <OccurrenceCard key={item.id} item={item} />) : <EmptyState title="Nenhuma ocorrência registrada" description="Use esta aba para registrar fatos pedagógicos, disciplinares e administrativos da turma." />}
            </div>
          </section>
        </div>
      ) : null}

      {activeTab === 'suspensoes' ? (
        <div className="diario-detail-stack">
          <section className="diario-panel">
            <div className="diario-panel__header"><h2>Nova suspensão</h2></div>
            <form className="diario-form-grid" onSubmit={(event) => {
              event.preventDefault()
              occurrenceMutation.mutate({ ...occurrenceForm, tipo: 'SUSPENSAO' })
            }}>
              <div className="form-field form-field--full">
                <label htmlFor="suspensao-titulo">Título</label>
                <input id="suspensao-titulo" className="form-control" value={occurrenceForm.titulo} onChange={(event) => setOccurrenceForm((current) => ({ ...current, titulo: event.target.value }))} />
              </div>
              <div className="form-field form-field--full">
                <label htmlFor="suspensao-descricao">Descrição</label>
                <textarea id="suspensao-descricao" className="form-control diarios-textarea" value={occurrenceForm.descricao} onChange={(event) => setOccurrenceForm((current) => ({ ...current, descricao: event.target.value }))} />
              </div>
              <div className="form-field">
                <label htmlFor="suspensao-data">Data</label>
                <input id="suspensao-data" type="date" className="form-control" value={occurrenceForm.data_ocorrencia} onChange={(event) => setOccurrenceForm((current) => ({ ...current, data_ocorrencia: event.target.value }))} />
              </div>
              <div className="diario-form-actions">
                <button type="submit" className="btn btn--danger" disabled={occurrenceMutation.isPending}>
                  <Plus size={16} /> {occurrenceMutation.isPending ? 'Registrando...' : 'Registrar suspensão'}
                </button>
              </div>
            </form>
          </section>

          <section className="diario-panel">
            <div className="diario-panel__header"><h2>Suspensões registradas</h2></div>
            <div className="diario-record-stack">
              {data.suspensoes?.length ? data.suspensoes.map((item) => <OccurrenceCard key={item.id} item={item} />) : <EmptyState title="Nenhuma suspensão registrada" description="Registre aqui as suspensões e afastamentos disciplinares ligados à turma." />}
            </div>
          </section>
        </div>
      ) : null}

      {activeTab === 'estatisticas' ? (
        <div className="diario-detail-stack">
          <section className="diario-panel">
            <div className="diario-panel__header"><h2>Resumo acadêmico</h2></div>
            <div className="diarios-summary-grid diario-stats-grid">
              <SummaryCard label="Alunos com notas" value={stats.alunos_com_notas} />
              <SummaryCard label="Alunos sem notas" value={stats.alunos_sem_notas} />
              <SummaryCard label="Alunos com frequência" value={stats.alunos_com_frequencia} />
              <SummaryCard label="Alunos sem frequência" value={stats.alunos_sem_frequencia} />
              <SummaryCard label="Média geral" value={formatDecimal(stats.media_geral)} />
              <SummaryCard label="Frequência média" value={stats.frequencia_media !== null && stats.frequencia_media !== undefined ? `${formatDecimal(stats.frequencia_media)}%` : '-'} />
              <SummaryCard label="Materiais publicados" value={stats.materiais_publicados} />
              <SummaryCard label="Ocorrências" value={stats.ocorrencias_registradas} />
            </div>
          </section>

          <section className="diario-panel">
            <div className="diario-panel__header"><h2>Indicadores de fechamento</h2></div>
            <div className="diario-progress-stack">
              <div className="diario-progress-row">
                <span>Notas lançadas</span>
                <div className="diario-progress-bar"><div style={{ width: `${stats.total_alunos ? ((stats.alunos_com_notas || 0) / stats.total_alunos) * 100 : 0}%` }} /></div>
                <strong>{stats.alunos_com_notas || 0}/{stats.total_alunos || 0}</strong>
              </div>
              <div className="diario-progress-row">
                <span>Frequência lançada</span>
                <div className="diario-progress-bar"><div style={{ width: `${stats.total_alunos ? ((stats.alunos_com_frequencia || 0) / stats.total_alunos) * 100 : 0}%` }} /></div>
                <strong>{stats.alunos_com_frequencia || 0}/{stats.total_alunos || 0}</strong>
              </div>
              <div className="diario-progress-row">
                <span>Aprovações consolidadas</span>
                <div className="diario-progress-bar"><div style={{ width: `${stats.total_alunos ? ((stats.aprovados || 0) / stats.total_alunos) * 100 : 0}%` }} /></div>
                <strong>{stats.aprovados || 0}/{stats.total_alunos || 0}</strong>
              </div>
            </div>
          </section>
        </div>
      ) : null}
    </div>
  )
}