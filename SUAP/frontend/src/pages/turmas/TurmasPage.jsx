import { useEffect, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import DataTable from '@/components/ui/DataTable'
import EntityDetailsPanel from '@/components/ui/EntityDetailsPanel'
import EntityFormPanel from '@/components/ui/EntityFormPanel'
import SearchableRemoteSelect from '@/components/ui/SearchableRemoteSelect'
import { Eye, Pencil, Plus, Trash2 } from 'lucide-react'
import toast from 'react-hot-toast'

import { cursosApi, turmasApi, usuariosApi } from '@/api/endpoints'

const STATUS_BADGE = {
  PLANEJADA: 'badge--info',
  ATIVA:     'badge--success',
  ENCERRADA: 'badge--secondary',
  CANCELADA: 'badge--danger',
}

const STATUS_OPTIONS = [
  { value: 'PLANEJADA', label: 'Planejada' },
  { value: 'ATIVA', label: 'Ativa' },
  { value: 'ENCERRADA', label: 'Encerrada' },
  { value: 'CANCELADA', label: 'Cancelada' },
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

const COLUMNS = [
  { key: 'nome',           label: 'Turma' },
  { key: 'curso_nome',     label: 'Curso' },
  { key: 'ano_letivo',     label: 'Ano Letivo' },
  { key: 'professor_nome', label: 'Professor' },
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

export default function TurmasPage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [page, setPage] = useState(1)
  const [selectedTurmaId, setSelectedTurmaId] = useState(null)
  const [editingTurmaId, setEditingTurmaId] = useState(null)
  const [cursoSearch, setCursoSearch] = useState('')
  const [professorSearch, setProfessorSearch] = useState('')
  const [formData, setFormData] = useState(DEFAULT_FORM)

  const { data, isLoading, isError } = useQuery({
    queryKey: ['turmas', { search, status: statusFilter, page }],
    queryFn: () => turmasApi.list({ search, status: statusFilter || undefined, page }).then((r) => r.data),
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
        { label: 'Ano Letivo', value: selectedTurma.ano_letivo },
        { label: 'Professor', value: selectedTurma.professor_nome },
        { label: 'Status', value: selectedTurma.status_display || selectedTurma.status },
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

  return (
    <div className="page">
      <div className="page-header">
        <h1 className="page-title">Turmas</h1>
        <div className="page-header__actions">
          <select
            className="select"
            value={statusFilter}
            onChange={(event) => { setStatusFilter(event.target.value); setPage(1) }}
          >
            <option value="">Todos os status</option>
            {STATUS_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>{option.label}</option>
            ))}
          </select>
          <button
            className="btn btn--primary"
            onClick={() => navigate('/turmas/nova')}
          >
            <Plus size={16} /> Nova Turma
          </button>
        </div>
      </div>

      {isError ? (
        <div className="alert alert--error">
          Nao foi possivel carregar as turmas com as permissoes atuais.
        </div>
      ) : null}

      <DataTable
        columns={COLUMNS}
        data={data}
        isLoading={isLoading}
        onSearch={(v) => { setSearch(v); setPage(1) }}
        searchPlaceholder="Buscar turma..."
        emptyMessage="Nenhuma turma encontrada."
        rowActions={(row) => (
          <div className="table-actions">
            <button type="button" className="btn btn--outline btn--sm" onClick={() => setSelectedTurmaId(row.id)}>
              <Eye size={14} /> Detalhes
            </button>
            <button
              type="button"
              className="btn btn--secondary btn--sm"
              onClick={() => openEditForm(row.id)}
            >
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
        )}
      />

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
