import { useEffect, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Eye, Lock, Pencil, Plus, RotateCcw, Trash2 } from 'lucide-react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import toast from 'react-hot-toast'

import { cursosApi, diarioApi, turmasApi, unidadesApi, usuariosApi } from '@/api/endpoints'
import DataTable from '@/components/ui/DataTable'
import EntityFormPanel from '@/components/ui/EntityFormPanel'
import SearchableRemoteSelect from '@/components/ui/SearchableRemoteSelect'

import './diarios.css'

const LIST_TABS = [
  { key: 'TODOS', label: 'Todos' },
  { key: 'EM_ANDAMENTO', label: 'Em andamento' },
  { key: 'SEM_PROFESSOR', label: 'Sem professor' },
  { key: 'SEM_ALUNOS', label: 'Sem alunos' },
  { key: 'NOTAS_PENDENTES', label: 'Notas pendentes' },
  { key: 'FREQUENCIAS_PENDENTES', label: 'Frequências pendentes' },
  { key: 'FECHADOS', label: 'Fechados' },
]

const STATUS_OPTIONS = [
  { value: '', label: 'Todos os status' },
  { value: 'ABERTO', label: 'Aberto' },
  { value: 'REVISAO', label: 'Em revisão' },
  { value: 'FECHADO', label: 'Fechado' },
]

const STATUS_BADGE = {
  ABERTO: 'badge--success',
  REVISAO: 'badge--warning',
  FECHADO: 'badge--secondary',
}

const SUMMARY_LABELS = {
  TODOS: 'Todos os diários',
  EM_ANDAMENTO: 'Em andamento',
  SEM_PROFESSOR: 'Sem professor',
  SEM_ALUNOS: 'Sem alunos',
  NOTAS_PENDENTES: 'Notas pendentes',
  FREQUENCIAS_PENDENTES: 'Frequências pendentes',
  FECHADOS: 'Fechados',
}

const DEFAULT_FORM = {
  turma: '',
  periodo: `${new Date().getFullYear()}/1`,
  componente_curricular: '',
  status: 'ABERTO',
  observacoes: '',
}

const COLUMNS = [
  { key: 'periodo', label: 'Período' },
  { key: 'componente_curricular', label: 'Componente' },
  { key: 'turma_nome', label: 'Turma' },
  { key: 'curso_nome', label: 'Curso' },
  { key: 'professor_nome', label: 'Professor' },
  {
    key: 'pendencias',
    label: 'Pendências',
    render: (row) => (
      <div className="diarios-pendency-cell">
        <span className="badge badge--outline">Notas: {row.notas_pendentes || 0}</span>
        <span className="badge badge--outline">Freq.: {row.frequencias_pendentes || 0}</span>
      </div>
    ),
  },
  {
    key: 'status',
    label: 'Status',
    render: (row) => (
      <span className={`badge ${STATUS_BADGE[row.status] || ''}`}>
        {row.status_display || row.status}
      </span>
    ),
  },
]

function getErrorMessage(error, fallback) {
  const data = error?.response?.data

  if (!data) return fallback
  if (typeof data.detail === 'string') return data.detail

  const firstValue = Object.values(data)[0]
  return Array.isArray(firstValue) ? firstValue[0] : (firstValue || fallback)
}

function SummaryCard({ label, value, active = false, onClick }) {
  return (
    <button type="button" className={`diarios-summary-card ${active ? 'diarios-summary-card--active' : ''}`} onClick={onClick}>
      <span className="diarios-summary-card__label">{label}</span>
      <strong className="diarios-summary-card__value">{value || 0}</strong>
    </button>
  )
}

export default function DiariosPage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [searchParams] = useSearchParams()

  const [search, setSearch] = useState('')
  const [page, setPage] = useState(1)
  const [activeTab, setActiveTab] = useState(searchParams.get('aba') || 'TODOS')
  const [statusFilter, setStatusFilter] = useState(searchParams.get('status') || '')
  const [anoLetivoFilter, setAnoLetivoFilter] = useState(searchParams.get('ano_letivo') || String(new Date().getFullYear()))
  const [periodoFilter, setPeriodoFilter] = useState(searchParams.get('periodo') || '')
  const [unidadeFilter, setUnidadeFilter] = useState(searchParams.get('unidade') || '')
  const [cursoFilter, setCursoFilter] = useState(searchParams.get('curso') || '')
  const [turmaFilter, setTurmaFilter] = useState(searchParams.get('turma') || '')
  const [professorFilter, setProfessorFilter] = useState(searchParams.get('professor') || '')
  const [editingDiarioId, setEditingDiarioId] = useState(null)
  const [formPanelOpen, setFormPanelOpen] = useState(false)
  const [unidadeSearch, setUnidadeSearch] = useState('')
  const [cursoSearch, setCursoSearch] = useState('')
  const [turmaSearch, setTurmaSearch] = useState('')
  const [professorSearch, setProfessorSearch] = useState('')
  const [formTurmaSearch, setFormTurmaSearch] = useState('')
  const [formData, setFormData] = useState(DEFAULT_FORM)

  const { data, isLoading, isError } = useQuery({
    queryKey: ['diarios', { search, page, activeTab, statusFilter, anoLetivoFilter, periodoFilter, unidadeFilter, cursoFilter, turmaFilter, professorFilter }],
    queryFn: () => diarioApi.list({
      search: search || undefined,
      page,
      aba: activeTab,
      status: statusFilter || undefined,
      ano_letivo: anoLetivoFilter || undefined,
      periodo: periodoFilter || undefined,
      unidade: unidadeFilter || undefined,
      curso: cursoFilter || undefined,
      turma: turmaFilter || undefined,
      professor: professorFilter || undefined,
    }).then((response) => response.data),
    staleTime: 30_000,
  })

  const { data: unidadesData } = useQuery({
    queryKey: ['unidades', 'diarios-filters', unidadeSearch],
    queryFn: () => unidadesApi.list({ page_size: 10, search: unidadeSearch || undefined }).then((response) => response.data),
    staleTime: 60_000,
  })

  const { data: cursosData } = useQuery({
    queryKey: ['cursos', 'diarios-filters', cursoSearch, unidadeFilter],
    queryFn: () => cursosApi.list({ page_size: 10, search: cursoSearch || undefined, unidade: unidadeFilter || undefined }).then((response) => response.data),
    staleTime: 60_000,
  })

  const { data: turmasData } = useQuery({
    queryKey: ['turmas', 'diarios-filters', turmaSearch, cursoFilter, professorFilter],
    queryFn: () => turmasApi.list({ page_size: 10, search: turmaSearch || undefined, curso: cursoFilter || undefined }).then((response) => response.data),
    staleTime: 60_000,
  })

  const { data: professoresData } = useQuery({
    queryKey: ['usuarios', 'diarios-professores', professorSearch],
    queryFn: () => usuariosApi.list({ tipo: 'PROFESSOR', page_size: 10, search: professorSearch || undefined }).then((response) => response.data),
    staleTime: 60_000,
  })

  const { data: formTurmasData } = useQuery({
    queryKey: ['turmas', 'diarios-form', formTurmaSearch],
    queryFn: () => turmasApi.list({ page_size: 10, search: formTurmaSearch || undefined }).then((response) => response.data),
    staleTime: 60_000,
  })

  const { data: editingDiario } = useQuery({
    queryKey: ['diario', editingDiarioId],
    queryFn: () => diarioApi.get(editingDiarioId).then((response) => response.data),
    enabled: Boolean(editingDiarioId),
    staleTime: 0,
  })

  useEffect(() => {
    setTurmaFilter('')
  }, [cursoFilter, professorFilter])

  useEffect(() => {
    if (!editingDiario) return

    setFormData({
      turma: editingDiario.turma ? String(editingDiario.turma) : '',
      periodo: editingDiario.periodo || `${new Date().getFullYear()}/1`,
      componente_curricular: editingDiario.componente_curricular || '',
      status: editingDiario.status || 'ABERTO',
      observacoes: editingDiario.observacoes || '',
    })
  }, [editingDiario])

  const saveMutation = useMutation({
    mutationFn: ({ id, payload }) => (id ? diarioApi.patch(id, payload) : diarioApi.create(payload)),
    onSuccess: async (_response, variables) => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ['diarios'] }),
        variables.id ? queryClient.invalidateQueries({ queryKey: ['diario', variables.id] }) : Promise.resolve(),
      ])
      toast.success(variables.id ? 'Diário atualizado com sucesso.' : 'Diário criado com sucesso.')
      setEditingDiarioId(null)
      setFormPanelOpen(false)
      setFormData(DEFAULT_FORM)
    },
    onError: (error) => toast.error(getErrorMessage(error, 'Não foi possível salvar o diário.')),
  })

  const statusMutation = useMutation({
    mutationFn: ({ id, action }) => (action === 'fechar' ? diarioApi.fechar(id) : diarioApi.reabrir(id)),
    onSuccess: async (_response, variables) => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ['diarios'] }),
        queryClient.invalidateQueries({ queryKey: ['diario', variables.id] }),
      ])
      toast.success(variables.action === 'fechar' ? 'Diário fechado com sucesso.' : 'Diário reaberto com sucesso.')
    },
    onError: (error) => toast.error(getErrorMessage(error, 'Não foi possível atualizar o status do diário.')),
  })

  const deleteMutation = useMutation({
    mutationFn: (id) => diarioApi.remove(id),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['diarios'] })
      toast.success('Diário excluído com sucesso.')
      setEditingDiarioId(null)
      setFormPanelOpen(false)
      setFormData(DEFAULT_FORM)
    },
    onError: (error) => toast.error(getErrorMessage(error, 'Não foi possível excluir o diário.')),
  })

  const closeForm = () => {
    setEditingDiarioId(null)
    setFormPanelOpen(false)
    setFormData(DEFAULT_FORM)
  }

  const handleSubmit = (event) => {
    event.preventDefault()

    if (!formData.turma || !formData.periodo.trim()) {
      toast.error('Informe turma e período letivo.')
      return
    }

    saveMutation.mutate({
      id: editingDiarioId,
      payload: {
        turma: Number(formData.turma),
        periodo: formData.periodo.trim(),
        componente_curricular: formData.componente_curricular.trim(),
        status: formData.status,
        observacoes: formData.observacoes.trim(),
      },
    })
  }

  const unidades = unidadesData?.results || []
  const cursos = cursosData?.results || []
  const turmas = turmasData?.results || []
  const professores = professoresData?.results || []
  const formTurmas = formTurmasData?.results || []
  const summary = data?.summary || {}

  const selectedTurmaOption = formData.turma && editingDiario ? {
    id: editingDiario.turma,
    nome: editingDiario.turma_nome,
    curso_nome: editingDiario.curso_nome,
  } : null

  return (
    <div className="page page--wide diarios-page">
      <nav className="profile-breadcrumb">
        <Link to="/dashboard">Início</Link>
        <span className="profile-breadcrumb__sep">&gt;</span>
        <span>Ensino</span>
        <span className="profile-breadcrumb__sep">&gt;</span>
        <span>Diários</span>
      </nav>

      <div className="page-header diarios-page__header">
        <div>
          <h1 className="page-title">Diários de Classe</h1>
          <p className="page-subtitle">Acompanhe lançamento de notas, frequência, materiais e ocorrências por turma.</p>
        </div>
        <div className="page-header__actions">
          <select className="select" value={statusFilter} onChange={(event) => { setStatusFilter(event.target.value); setPage(1) }}>
            {STATUS_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>{option.label}</option>
            ))}
          </select>
          <button type="button" className="btn btn--primary" onClick={() => { setEditingDiarioId(null); setFormPanelOpen(true); setFormData(DEFAULT_FORM) }}>
            <Plus size={16} /> Novo Diário
          </button>
        </div>
      </div>

      <div className="diarios-summary-grid">
        {LIST_TABS.map((tab) => (
          <SummaryCard
            key={tab.key}
            label={SUMMARY_LABELS[tab.key] || tab.label}
            value={summary[tab.key]}
            active={activeTab === tab.key}
            onClick={() => { setActiveTab(tab.key); setPage(1) }}
          />
        ))}
      </div>

      <div className="profile-tabs diarios-tabs" role="tablist" aria-label="Situação dos diários">
        {LIST_TABS.map((tab) => (
          <button
            key={tab.key}
            type="button"
            className={`profile-tabs__item ${activeTab === tab.key ? 'profile-tabs__item--active' : ''}`}
            onClick={() => { setActiveTab(tab.key); setPage(1) }}
          >
            {tab.label}
          </button>
        ))}
      </div>

      <div className="diarios-filter-grid">
        <div className="form-field">
          <label htmlFor="diarios-ano-letivo">Ano letivo</label>
          <input id="diarios-ano-letivo" className="form-control" value={anoLetivoFilter} onChange={(event) => { setAnoLetivoFilter(event.target.value); setPage(1) }} placeholder="2026" />
        </div>
        <div className="form-field">
          <label htmlFor="diarios-periodo">Período</label>
          <input id="diarios-periodo" className="form-control" value={periodoFilter} onChange={(event) => { setPeriodoFilter(event.target.value); setPage(1) }} placeholder="2026/1" />
        </div>
        <SearchableRemoteSelect
          id="diarios-unidade-filtro"
          label="Filtrar por unidade"
          searchLabel="Buscar unidade"
          searchPlaceholder="Digite a unidade"
          searchValue={unidadeSearch}
          onSearchChange={setUnidadeSearch}
          value={unidadeFilter}
          onChange={(nextValue) => { setUnidadeFilter(nextValue); setPage(1) }}
          options={unidades}
          emptyOptionLabel="Todas as unidades"
          getOptionLabel={(item) => item.nome}
        />
        <SearchableRemoteSelect
          id="diarios-curso-filtro"
          label="Filtrar por curso"
          searchLabel="Buscar curso"
          searchPlaceholder="Digite o nome do curso"
          searchValue={cursoSearch}
          onSearchChange={setCursoSearch}
          value={cursoFilter}
          onChange={(nextValue) => { setCursoFilter(nextValue); setPage(1) }}
          options={cursos}
          emptyOptionLabel="Todos os cursos"
          getOptionLabel={(item) => item.nome}
        />
        <SearchableRemoteSelect
          id="diarios-professor-filtro"
          label="Filtrar por professor"
          searchLabel="Buscar professor"
          searchPlaceholder="Digite o nome do professor"
          searchValue={professorSearch}
          onSearchChange={setProfessorSearch}
          value={professorFilter}
          onChange={(nextValue) => { setProfessorFilter(nextValue); setPage(1) }}
          options={professores}
          emptyOptionLabel="Todos os professores"
          getOptionLabel={(item) => item.nome_completo || item.username}
        />
        <SearchableRemoteSelect
          id="diarios-turma-filtro"
          label="Filtrar por turma"
          searchLabel="Buscar turma"
          searchPlaceholder="Digite a turma"
          searchValue={turmaSearch}
          onSearchChange={setTurmaSearch}
          value={turmaFilter}
          onChange={(nextValue) => { setTurmaFilter(nextValue); setPage(1) }}
          options={turmas}
          emptyOptionLabel="Todas as turmas"
          getOptionLabel={(item) => `${item.nome} - ${item.curso_nome || 'Sem curso'}`}
        />
      </div>

      {isError ? <div className="alert alert--error">Não foi possível carregar os diários com as permissões atuais.</div> : null}

      <DataTable
        columns={COLUMNS}
        data={data}
        isLoading={isLoading}
        onSearch={(value) => { setSearch(value); setPage(1) }}
        searchPlaceholder="Buscar diário, turma, curso, componente ou professor..."
        emptyMessage="Nenhum diário encontrado para os filtros atuais."
        rowActions={(row) => (
          <div className="table-actions">
            <button type="button" className="btn btn--outline btn--sm" onClick={() => navigate(`/diarios/${row.id}`)}>
              <Eye size={14} /> Detalhes
            </button>
            <button type="button" className="btn btn--secondary btn--sm" onClick={() => { setEditingDiarioId(row.id); setFormPanelOpen(true) }}>
              <Pencil size={14} /> Editar
            </button>
            {row.status === 'FECHADO' ? (
              <button type="button" className="btn btn--outline btn--sm" onClick={() => statusMutation.mutate({ id: row.id, action: 'reabrir' })}>
                <RotateCcw size={14} /> Reabrir
              </button>
            ) : (
              <button type="button" className="btn btn--dark btn--sm" onClick={() => statusMutation.mutate({ id: row.id, action: 'fechar' })}>
                <Lock size={14} /> Fechar
              </button>
            )}
            <button type="button" className="btn btn--danger btn--sm" onClick={() => window.confirm(`Excluir o diário ${row.periodo} da turma ${row.turma_nome}?`) && deleteMutation.mutate(row.id)}>
              <Trash2 size={14} /> Excluir
            </button>
          </div>
        )}
      />

      {formPanelOpen ? (
        <EntityFormPanel
          title={editingDiarioId ? 'Editar diário' : 'Novo diário'}
          subtitle="Associe o diário a uma turma e defina o período letivo para o acompanhamento pedagógico."
          onSubmit={handleSubmit}
          onCancel={closeForm}
          submitLabel={editingDiarioId ? 'Salvar alterações' : 'Criar diário'}
          isSubmitting={saveMutation.isPending}
        >
          <SearchableRemoteSelect
            id="diario-form-turma"
            label="Turma"
            searchLabel="Buscar turma"
            searchPlaceholder="Digite a turma ou o curso"
            searchValue={formTurmaSearch}
            onSearchChange={setFormTurmaSearch}
            value={formData.turma}
            onChange={(nextValue) => setFormData((current) => ({ ...current, turma: nextValue }))}
            options={formTurmas}
            selectedOption={selectedTurmaOption}
            getOptionLabel={(item) => `${item.nome} - ${item.curso_nome || 'Sem curso'}`}
          />

          <div className="form-field">
            <label htmlFor="diario-form-periodo">Período</label>
            <input id="diario-form-periodo" className="form-control" value={formData.periodo} onChange={(event) => setFormData((current) => ({ ...current, periodo: event.target.value }))} placeholder="2026/1" />
          </div>

          <div className="form-field">
            <label htmlFor="diario-form-status">Status</label>
            <select id="diario-form-status" className="select" value={formData.status} onChange={(event) => setFormData((current) => ({ ...current, status: event.target.value }))}>
              <option value="ABERTO">Aberto</option>
              <option value="REVISAO">Em revisão</option>
              <option value="FECHADO">Fechado</option>
            </select>
          </div>

          <div className="form-field form-field--full">
            <label htmlFor="diario-form-componente">Componente curricular</label>
            <input id="diario-form-componente" className="form-control" value={formData.componente_curricular} onChange={(event) => setFormData((current) => ({ ...current, componente_curricular: event.target.value }))} placeholder="Ex.: Língua Portuguesa" />
          </div>

          <div className="form-field form-field--full">
            <label htmlFor="diario-form-observacoes">Observações</label>
            <textarea id="diario-form-observacoes" className="form-control diarios-textarea" value={formData.observacoes} onChange={(event) => setFormData((current) => ({ ...current, observacoes: event.target.value }))} placeholder="Contexto pedagógico, ajustes e observações administrativas." />
          </div>
        </EntityFormPanel>
      ) : null}
    </div>
  )
}