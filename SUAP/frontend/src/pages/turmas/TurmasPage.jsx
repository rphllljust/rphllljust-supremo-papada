import { useEffect, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Link, useNavigate } from 'react-router-dom'
import EntityDetailsPanel from '@/components/ui/EntityDetailsPanel'
import EntityFormPanel from '@/components/ui/EntityFormPanel'
import SearchableRemoteSelect from '@/components/ui/SearchableRemoteSelect'
import { BookOpen, Eye, Pencil, Plus, Trash2 } from 'lucide-react'
import toast from 'react-hot-toast'

import { cursosApi, turmasApi, usuariosApi } from '@/api/endpoints'

import './turmas.css'

const STATUS_BADGE = {
  PLANEJADA: 'badge--info',
  ATIVA:     'badge--success',
  ENCERRADA: 'badge--secondary',
  CANCELADA: 'badge--danger',
}

const STATUS_OPTIONS = [
  { value: '', label: 'Todos os status' },
  { value: 'PLANEJADA', label: 'Planejada' },
  { value: 'ATIVA', label: 'Ativa' },
  { value: 'ENCERRADA', label: 'Encerrada' },
  { value: 'CANCELADA', label: 'Cancelada' },
]

const LIST_TABS = [
  { key: 'TODOS', label: 'Todos' },
  { key: 'ATIVAS', label: 'Ativas' },
  { key: 'PLANEJADAS', label: 'Planejadas' },
  { key: 'ENCERRADAS', label: 'Encerradas' },
  { key: 'CANCELADAS', label: 'Canceladas' },
  { key: 'SEM_DIARIOS', label: 'Sem diários' },
]

const DEFAULT_FORM = {
  curso: '',
  nome: '',
  ano_letivo: String(new Date().getFullYear()),
  status: 'PLANEJADA',
  professor_responsavel: '',
}

function getErrorMessage(error, fallback) {
  const data = error?.response?.data

  if (!data) return fallback
  if (typeof data.detail === 'string') return data.detail

  const firstValue = Object.values(data)[0]
  return Array.isArray(firstValue) ? firstValue[0] : (firstValue || fallback)
}

export default function TurmasPage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [search, setSearch] = useState('')
  const [activeTab, setActiveTab] = useState('TODOS')
  const [statusFilter, setStatusFilter] = useState('')
  const [anoLetivoFilter, setAnoLetivoFilter] = useState(String(new Date().getFullYear()))
  const [cursoFilter, setCursoFilter] = useState('')
  const [professorFilter, setProfessorFilter] = useState('')
  const [page, setPage] = useState(1)
  const [selectedTurmaId, setSelectedTurmaId] = useState(null)
  const [editingTurmaId, setEditingTurmaId] = useState(null)
  const [cursoSearch, setCursoSearch] = useState('')
  const [professorSearch, setProfessorSearch] = useState('')
  const [formData, setFormData] = useState(DEFAULT_FORM)

  const { data, isLoading, isError } = useQuery({
    queryKey: ['turmas', { search, status: statusFilter, ano_letivo: anoLetivoFilter, curso: cursoFilter, professor: professorFilter, aba: activeTab, page }],
    queryFn: () => turmasApi.list({
      search: search || undefined,
      status: statusFilter || undefined,
      ano_letivo: anoLetivoFilter || undefined,
      curso: cursoFilter || undefined,
      professor: professorFilter || undefined,
      aba: activeTab,
      page,
    }).then((r) => r.data),
    staleTime: 30_000,
  })

  const { data: cursosData } = useQuery({
    queryKey: ['cursos', 'turmas-options', cursoSearch],
    queryFn: () => cursosApi.list({ page_size: 10, search: cursoSearch || undefined }).then((response) => response.data),
    staleTime: 60_000,
  })

  const { data: professoresData } = useQuery({
    queryKey: ['usuarios', 'turmas-professores', professorSearch],
    queryFn: () => usuariosApi.list({ tipo: 'PROFESSOR', page_size: 10, search: professorSearch || undefined }).then((response) => response.data),
    staleTime: 60_000,
  })

  const { data: selectedTurma, isLoading: isLoadingDetails, isError: isErrorDetails } = useQuery({
    queryKey: ['turma', selectedTurmaId],
    queryFn: () => turmasApi.get(selectedTurmaId).then((response) => response.data),
    enabled: Boolean(selectedTurmaId),
    staleTime: 30_000,
  })

  const { data: editingTurma } = useQuery({
    queryKey: ['turma-edit', editingTurmaId],
    queryFn: () => turmasApi.get(editingTurmaId).then((response) => response.data),
    enabled: Boolean(editingTurmaId),
    staleTime: 0,
  })

  useEffect(() => {
    if (!editingTurma) return

    setFormData({
      curso: editingTurma.curso ? String(editingTurma.curso) : '',
      nome: editingTurma.nome || '',
      ano_letivo: editingTurma.ano_letivo ? String(editingTurma.ano_letivo) : String(new Date().getFullYear()),
      status: editingTurma.status || 'PLANEJADA',
      professor_responsavel: editingTurma.professor_responsavel ? String(editingTurma.professor_responsavel) : '',
    })
  }, [editingTurma])

  const saveMutation = useMutation({
    mutationFn: ({ id, payload }) => (id ? turmasApi.patch(id, payload) : turmasApi.create(payload)),
    onSuccess: (_response, variables) => {
      queryClient.invalidateQueries({ queryKey: ['turmas'] })
      if (variables.id) {
        queryClient.invalidateQueries({ queryKey: ['turma', variables.id] })
        queryClient.invalidateQueries({ queryKey: ['turma-edit', variables.id] })
      }

      toast.success(variables.id ? 'Turma atualizada com sucesso.' : 'Turma criada com sucesso.')
      setEditingTurmaId(null)
      setFormData(DEFAULT_FORM)
    },
    onError: (error) => toast.error(getErrorMessage(error, 'Nao foi possivel salvar a turma.')),
  })

  const deleteMutation = useMutation({
    mutationFn: (id) => turmasApi.remove(id),
    onSuccess: (_response, id) => {
      queryClient.invalidateQueries({ queryKey: ['turmas'] })
      queryClient.invalidateQueries({ queryKey: ['turma', id] })
      queryClient.invalidateQueries({ queryKey: ['turma-edit', id] })
      setSelectedTurmaId((current) => (current === id ? null : current))
      setEditingTurmaId((current) => (current === id ? null : current))
      setFormData(DEFAULT_FORM)
      toast.success('Turma excluida com sucesso.')
    },
    onError: (error) => toast.error(getErrorMessage(error, 'Nao foi possivel excluir a turma.')),
  })

  const cursos = cursosData?.results || []
  const professores = professoresData?.results || []
  const rows = data?.results || []
  const summary = data?.summary || {}

  const selectedCursoOption = formData.curso && editingTurma ? {
    id: editingTurma.curso,
    nome: editingTurma.curso_nome,
  } : null

  const selectedProfessorOption = formData.professor_responsavel && editingTurma ? {
    id: editingTurma.professor_responsavel,
    nome_completo: editingTurma.professor_nome,
    username: '',
  } : null

  const turmaDetailsFields = selectedTurma
    ? [
        { label: 'ID', value: selectedTurma.id },
        { label: 'Turma', value: selectedTurma.nome },
        { label: 'Curso', value: selectedTurma.curso_nome },
        { label: 'Sigla do curso', value: selectedTurma.curso_sigla || '-' },
        { label: 'Ano Letivo', value: selectedTurma.ano_letivo },
        { label: 'Professor', value: selectedTurma.professor_nome },
        { label: 'Status', value: selectedTurma.status_display || selectedTurma.status },
        { label: 'Alunos ativos', value: selectedTurma.total_alunos ?? 0 },
        { label: 'Diários', value: selectedTurma.total_diarios ?? 0 },
      ]
    : []

  const openEditForm = (id) => {
    setSelectedTurmaId(null)
    setEditingTurmaId(id)
  }

  const closeForm = () => {
    setEditingTurmaId(null)
    setFormData(DEFAULT_FORM)
  }

  const handleSubmit = (event) => {
    event.preventDefault()

    if (!formData.curso || !formData.nome.trim() || !formData.ano_letivo) {
      toast.error('Informe curso, nome da turma e ano letivo.')
      return
    }

    saveMutation.mutate({
      id: editingTurmaId,
      payload: {
        curso: Number(formData.curso),
        nome: formData.nome.trim(),
        ano_letivo: Number(formData.ano_letivo),
        status: formData.status,
        professor_responsavel: formData.professor_responsavel ? Number(formData.professor_responsavel) : null,
      },
    })
  }

  const openCreatePage = () => navigate('/turmas/nova')

  const resetFilters = () => {
    setSearch('')
    setStatusFilter('')
    setAnoLetivoFilter(String(new Date().getFullYear()))
    setCursoFilter('')
    setProfessorFilter('')
    setPage(1)
    setActiveTab('TODOS')
  }

  return (
    <div className="page page--wide turmas-page">
      <nav className="profile-breadcrumb">
        <Link to="/dashboard">Início</Link>
        <span className="profile-breadcrumb__sep">&gt;</span>
        <span>Atividades Específicas</span>
        <span className="profile-breadcrumb__sep">&gt;</span>
        <span>Turmas</span>
      </nav>

      <div className="page-header turmas-page__header">
        <div>
          <h1 className="page-title">Turmas</h1>
          <p className="page-subtitle">Acompanhe a oferta, o vínculo com cursos e a evolução de diários e matrículas por turma.</p>
        </div>
        <div className="page-header__actions">
          <button className="btn btn--outline" onClick={resetFilters}>Limpar filtros</button>
          <button className="btn btn--primary" onClick={openCreatePage}>
            <Plus size={16} /> Nova Turma
          </button>
        </div>
      </div>

      <div className="turmas-summary-grid">
        {LIST_TABS.map((tab) => (
          <button
            key={tab.key}
            type="button"
            className={`turmas-summary-card ${activeTab === tab.key ? 'turmas-summary-card--active' : ''}`}
            onClick={() => {
              setActiveTab(tab.key)
              setPage(1)
            }}
          >
            <span className="turmas-summary-card__label">{tab.label}</span>
            <strong className="turmas-summary-card__value">{summary[tab.key] || 0}</strong>
          </button>
        ))}
      </div>

      <section className="turmas-filters-card">
        <div className="turmas-filters-card__header">
          <h2>Filtros</h2>
          <span>Refine a listagem por situação, ano, curso e professor.</span>
        </div>
        <div className="turmas-filter-grid">
          <div className="form-field">
            <label htmlFor="turmas-search">Texto</label>
            <input
              id="turmas-search"
              className="form-control"
              value={search}
              onChange={(event) => {
                setSearch(event.target.value)
                setPage(1)
              }}
              placeholder="Buscar turma, curso, sigla ou professor"
            />
          </div>

          <div className="form-field">
            <label htmlFor="turmas-ano-letivo">Ano letivo</label>
            <input
              id="turmas-ano-letivo"
              type="number"
              min="2000"
              max="2100"
              className="form-control"
              value={anoLetivoFilter}
              onChange={(event) => {
                setAnoLetivoFilter(event.target.value)
                setPage(1)
              }}
            />
          </div>

          <div className="form-field">
            <label htmlFor="turmas-status">Status</label>
            <select
              id="turmas-status"
              className="select"
              value={statusFilter}
              onChange={(event) => {
                setStatusFilter(event.target.value)
                setPage(1)
              }}
            >
              {STATUS_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>{option.label}</option>
              ))}
            </select>
          </div>

          <SearchableRemoteSelect
            id="turmas-filtro-curso"
            label="Curso"
            searchLabel="Buscar curso"
            searchPlaceholder="Digite o nome do curso"
            searchValue={cursoSearch}
            onSearchChange={setCursoSearch}
            value={cursoFilter}
            onChange={(nextValue) => {
              setCursoFilter(nextValue)
              setPage(1)
            }}
            options={cursos}
            emptyOptionLabel="Todos os cursos"
            getOptionLabel={(item) => `${item.nome}${item.sigla ? ` - ${item.sigla}` : ''}`}
          />

          <SearchableRemoteSelect
            id="turmas-filtro-professor"
            label="Professor"
            searchLabel="Buscar professor"
            searchPlaceholder="Digite o nome do professor"
            searchValue={professorSearch}
            onSearchChange={setProfessorSearch}
            value={professorFilter}
            onChange={(nextValue) => {
              setProfessorFilter(nextValue)
              setPage(1)
            }}
            options={professores}
            emptyOptionLabel="Todos os professores"
            getOptionLabel={(item) => item.username ? `${item.nome_completo} - ${item.username}` : item.nome_completo}
          />
        </div>
      </section>

      {isError ? (
        <div className="alert alert--error">
          Nao foi possivel carregar as turmas com as permissoes atuais.
        </div>
      ) : null}

      <section className="turmas-table-card">
        <div className="turmas-table-card__header">
          <span>Mostrando {data?.count || 0} turma{(data?.count || 0) === 1 ? '' : 's'}</span>
          <span>Aba ativa: {LIST_TABS.find((tab) => tab.key === activeTab)?.label || 'Todos'}</span>
        </div>

        {isLoading ? (
          <div className="table-skeleton">
            {Array.from({ length: 6 }).map((_, index) => <div key={index} className="skeleton-row" />)}
          </div>
        ) : (
          <div className="turmas-table-wrap">
            <table className="turmas-table">
              <thead>
                <tr>
                  <th>#</th>
                  <th>Turma</th>
                  <th>Curso</th>
                  <th>Sigla</th>
                  <th>Ano letivo</th>
                  <th>Professor</th>
                  <th>Diários</th>
                  <th>Alunos</th>
                  <th>Status</th>
                  <th className="turmas-table__actions">Ações</th>
                </tr>
              </thead>
              <tbody>
                {rows.length === 0 ? (
                  <tr>
                    <td colSpan={10} className="empty-state">Nenhuma turma encontrada.</td>
                  </tr>
                ) : rows.map((row) => (
                  <tr key={row.id}>
                    <td>{row.id}</td>
                    <td>
                      <div className="turmas-table__main-cell">
                        <strong>{row.nome}</strong>
                        <span>{row.status_display || row.status}</span>
                      </div>
                    </td>
                    <td>{row.curso_nome}</td>
                    <td>{row.curso_sigla || '-'}</td>
                    <td>{row.ano_letivo}</td>
                    <td>{row.professor_nome || '-'}</td>
                    <td><span className="badge badge--outline">{row.total_diarios ?? 0}</span></td>
                    <td><span className="badge badge--outline">{row.total_alunos ?? 0}</span></td>
                    <td>
                      <span className={`badge ${STATUS_BADGE[row.status] || ''}`}>
                        {row.status_display || row.status}
                      </span>
                    </td>
                    <td>
                      <div className="turmas-table__actions-group">
                        <button type="button" className="btn btn--outline btn--sm" onClick={() => setSelectedTurmaId(row.id)}>
                          <Eye size={14} /> Detalhes
                        </button>
                        <button type="button" className="btn btn--outline btn--sm" onClick={() => navigate(`/diarios?turma=${row.id}`)}>
                          <BookOpen size={14} /> Diários
                        </button>
                        <button type="button" className="btn btn--secondary btn--sm" onClick={() => openEditForm(row.id)}>
                          <Pencil size={14} /> Editar
                        </button>
                        <button
                          type="button"
                          className="btn btn--danger btn--sm"
                          onClick={() => window.confirm(`Excluir a turma ${row.nome}?`) && deleteMutation.mutate(row.id)}
                        >
                          <Trash2 size={14} /> Excluir
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      {selectedTurmaId ? (
        <EntityDetailsPanel
          title="Detalhes da turma"
          subtitle={selectedTurma?.nome || 'Consultando turma selecionada'}
          fields={turmaDetailsFields}
          isLoading={isLoadingDetails}
          errorMessage={isErrorDetails ? 'Nao foi possivel carregar os detalhes desta turma.' : ''}
          onClose={() => setSelectedTurmaId(null)}
        />
      ) : null}

      {editingTurmaId ? (
        <EntityFormPanel
          title="Editar turma"
          subtitle="Informe curso, identificação da turma, ano letivo e professor responsável."
          onSubmit={handleSubmit}
          onCancel={closeForm}
          submitLabel="Salvar alteracoes"
          isSubmitting={saveMutation.isPending}
        >
          <SearchableRemoteSelect
            id="turma-curso"
            label="Curso"
            searchLabel="Buscar curso"
            searchPlaceholder="Digite nome ou sigla do curso"
            searchValue={cursoSearch}
            onSearchChange={setCursoSearch}
            value={formData.curso}
            onChange={(nextValue) => setFormData((current) => ({ ...current, curso: nextValue }))}
            options={cursos}
            selectedOption={selectedCursoOption}
            getOptionLabel={(item) => `${item.nome}${item.sigla ? ` - ${item.sigla}` : ''}`}
          />

          <div className="form-field form-field--full">
            <label htmlFor="turma-nome">Turma</label>
            <input
              id="turma-nome"
              className="form-control"
              value={formData.nome}
              onChange={(event) => setFormData((current) => ({ ...current, nome: event.target.value }))}
              placeholder="Ex.: 1A, 2026.1, ADS-N1"
            />
          </div>

          <div className="form-field">
            <label htmlFor="turma-ano-letivo">Ano letivo</label>
            <input
              id="turma-ano-letivo"
              type="number"
              min="2000"
              max="2100"
              className="form-control"
              value={formData.ano_letivo}
              onChange={(event) => setFormData((current) => ({ ...current, ano_letivo: event.target.value }))}
            />
          </div>

          <div className="form-field">
            <label htmlFor="turma-status">Status</label>
            <select
              id="turma-status"
              className="select"
              value={formData.status}
              onChange={(event) => setFormData((current) => ({ ...current, status: event.target.value }))}
            >
              {STATUS_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>{option.label}</option>
              ))}
            </select>
          </div>

          <SearchableRemoteSelect
            id="turma-professor"
            label="Professor responsável"
            searchLabel="Buscar professor"
            searchPlaceholder="Digite nome, CPF ou usuario"
            searchValue={professorSearch}
            onSearchChange={setProfessorSearch}
            value={formData.professor_responsavel}
            onChange={(nextValue) => setFormData((current) => ({ ...current, professor_responsavel: nextValue }))}
            options={professores}
            selectedOption={selectedProfessorOption}
            getOptionLabel={(item) => item.username ? `${item.nome_completo} - ${item.username}` : item.nome_completo}
            emptyOptionLabel="Nao informado"
          />
        </EntityFormPanel>
      ) : null}

      {data && (
        <div className="pagination">
          <button className="btn btn--secondary" disabled={!data.previous} onClick={() => setPage((p) => p - 1)}>Anterior</button>
          <span className="pagination__info">Página {page} — {data.count} registros</span>
          <button className="btn btn--secondary" disabled={!data.next} onClick={() => setPage((p) => p + 1)}>Próxima</button>
        </div>
      )}
    </div>
  )
}
