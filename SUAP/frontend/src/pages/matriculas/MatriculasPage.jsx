import { useEffect, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Eye, Pencil, Plus, Trash2 } from 'lucide-react'
import toast from 'react-hot-toast'
import { Link, useLocation, useNavigate } from 'react-router-dom'

import { cursosApi, matriculasApi, turmasApi, usuariosApi } from '@/api/endpoints'
import DataTable from '@/components/ui/DataTable'
import EntityDetailsPanel from '@/components/ui/EntityDetailsPanel'
import EntityFormPanel from '@/components/ui/EntityFormPanel'
import SearchableRemoteSelect from '@/components/ui/SearchableRemoteSelect'

const STATUS_BADGE = {
  ATIVA: 'badge--success',
  TRANCADA: 'badge--warning',
  CANCELADA: 'badge--danger',
  CONCLUIDA: 'badge--info',
}

const STATUS_OPTIONS = [
  { value: 'ATIVA', label: 'Ativa' },
  { value: 'TRANCADA', label: 'Trancada' },
  { value: 'CANCELADA', label: 'Cancelada' },
  { value: 'CONCLUIDA', label: 'Concluida' },
]

const TIPO_OPTIONS = [
  { value: 'NOVA', label: 'Nova Matricula' },
  { value: 'REMATRICULA', label: 'Rematricula' },
]

const TURNO_OPTIONS = [
  { value: '', label: 'Nao informado' },
  { value: 'MANHA', label: 'Manha' },
  { value: 'TARDE', label: 'Tarde' },
  { value: 'NOITE', label: 'Noite' },
  { value: 'INTEGRAL', label: 'Integral' },
]

const DEFAULT_FORM = {
  aluno: '',
  curso: '',
  turma: '',
  status: 'ATIVA',
  tipo_matricula: 'NOVA',
  turno: '',
}

function formatDate(value) {
  if (!value) {
    return '-'
  }

  return new Date(`${value}T00:00:00`).toLocaleDateString('pt-BR')
}

function getErrorMessage(error, fallback) {
  const data = error?.response?.data
  if (!data) return fallback
  if (typeof data.detail === 'string') return data.detail
  const firstValue = Object.values(data)[0]
  return Array.isArray(firstValue) ? firstValue[0] : (firstValue || fallback)
}

const COLUMNS = [
  { key: 'numero_matricula', label: 'Nº Matrícula' },
  { key: 'aluno_nome', label: 'Aluno' },
  { key: 'curso_nome', label: 'Curso' },
  { key: 'turma_nome', label: 'Turma' },
  {
    key: 'status',
    label: 'Status',
    render: (row) => (
      <span className={`badge ${STATUS_BADGE[row.status] || ''}`}>
        {row.status_display || row.status}
      </span>
    ),
  },
  { key: 'tipo_matricula_display', label: 'Tipo' },
  { key: 'data_matricula', label: 'Data', render: (row) => formatDate(row.data_matricula) },
]

export default function MatriculasPage() {
  const location = useLocation()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [page, setPage] = useState(1)
  const [selectedMatriculaId, setSelectedMatriculaId] = useState(null)
  const [editingMatriculaId, setEditingMatriculaId] = useState(null)
  const [formData, setFormData] = useState(DEFAULT_FORM)
  const [alunoSearch, setAlunoSearch] = useState('')
  const [cursoSearch, setCursoSearch] = useState('')
  const [turmaSearch, setTurmaSearch] = useState('')
  const isCreatePage = location.pathname.endsWith('/matriculas/nova')

  const { data, isLoading, isError } = useQuery({
    queryKey: ['matriculas', { search, status: statusFilter, page }],
    queryFn: () =>
      matriculasApi.list({ search, status: statusFilter || undefined, page }).then((r) => r.data),
    staleTime: 30_000,
  })

  const { data: alunosData } = useQuery({
    queryKey: ['usuarios', 'matriculas-alunos', alunoSearch],
    queryFn: () => usuariosApi.list({ tipo: 'ALUNO', page_size: 10, search: alunoSearch || undefined }).then((response) => response.data),
    staleTime: 60_000,
  })

  const { data: cursosData } = useQuery({
    queryKey: ['cursos', 'matriculas-options', cursoSearch],
    queryFn: () => cursosApi.list({ page_size: 10, search: cursoSearch || undefined }).then((response) => response.data),
    staleTime: 60_000,
  })

  const { data: turmasData } = useQuery({
    queryKey: ['turmas', 'matriculas-options', turmaSearch, formData.curso],
    queryFn: () => turmasApi.list({ page_size: 10, search: turmaSearch || undefined, curso: formData.curso || undefined }).then((response) => response.data),
    staleTime: 60_000,
  })

  const { data: selectedMatricula, isLoading: isLoadingDetails, isError: isErrorDetails } = useQuery({
    queryKey: ['matricula', selectedMatriculaId],
    queryFn: () => matriculasApi.get(selectedMatriculaId).then((response) => response.data),
    enabled: Boolean(selectedMatriculaId),
    staleTime: 30_000,
  })

  const { data: editingMatricula } = useQuery({
    queryKey: ['matricula-edit', editingMatriculaId],
    queryFn: () => matriculasApi.get(editingMatriculaId).then((response) => response.data),
    enabled: Boolean(editingMatriculaId),
    staleTime: 0,
  })

  useEffect(() => {
    if (!editingMatricula) return
    setFormData({
      aluno: editingMatricula.aluno ? String(editingMatricula.aluno) : '',
      curso: editingMatricula.curso ? String(editingMatricula.curso) : '',
      turma: editingMatricula.turma ? String(editingMatricula.turma) : '',
      status: editingMatricula.status || 'ATIVA',
      tipo_matricula: editingMatricula.tipo_matricula || 'NOVA',
      turno: editingMatricula.turno || '',
    })
  }, [editingMatricula])

  const saveMutation = useMutation({
    mutationFn: ({ id, payload }) => (id ? matriculasApi.update(id, payload) : matriculasApi.create(payload)),
        onSuccess: (_response, variables) => {
      queryClient.invalidateQueries({ queryKey: ['matriculas'] })
      if (variables.id) {
        queryClient.invalidateQueries({ queryKey: ['matricula', variables.id] })
      }
      toast.success(variables.id ? 'Matricula atualizada com sucesso.' : 'Matricula criada com sucesso.')
      setEditingMatriculaId(null)
      setFormData(DEFAULT_FORM)
      if (!variables.id) {
        navigate('/matriculas')
      }
    },
    onError: (error) => {
      const msg = getErrorMessage(error, 'Nao foi possivel salvar a matricula.')
      // T107: exibe mensagem de conflito de versao
      if (msg.includes('version') || msg.includes('concorr') || msg.includes('conflito')) {
        toast.error('Conflito de versao: outro usuario alterou esta matricula. Recarregue e tente novamente.')
      } else {
        toast.error(msg)
      }
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (id) => matriculasApi.remove(id),
    onSuccess: (_response, id) => {
      queryClient.invalidateQueries({ queryKey: ['matriculas'] })
      queryClient.invalidateQueries({ queryKey: ['matricula', id] })
      setSelectedMatriculaId((current) => (current === id ? null : current))
      setEditingMatriculaId((current) => (current === id ? null : current))
      setFormData(DEFAULT_FORM)
      toast.success('Matricula excluida com sucesso.')
    },
    onError: (error) => toast.error(getErrorMessage(error, 'Nao foi possivel excluir a matricula.')),
  })

  const alunos = alunosData?.results || []
  const cursos = cursosData?.results || []
  const turmas = turmasData?.results || []

  const selectedAlunoOption = formData.aluno && editingMatricula ? {
    id: editingMatricula.aluno,
    nome_completo: editingMatricula.aluno_nome,
    username: editingMatricula.aluno_username,
  } : null
  const selectedCursoOption = formData.curso && editingMatricula ? {
    id: editingMatricula.curso,
    nome: editingMatricula.curso_nome,
  } : null
  const selectedTurmaOption = formData.turma && editingMatricula ? {
    id: editingMatricula.turma,
    nome: editingMatricula.turma_nome,
  } : null

  const detailsFields = selectedMatricula ? [
    { label: 'ID', value: selectedMatricula.id },
    { label: 'Numero', value: selectedMatricula.numero_matricula },
    { label: 'Aluno', value: selectedMatricula.aluno_nome },
    { label: 'Usuario', value: selectedMatricula.aluno_username },
    { label: 'Curso', value: selectedMatricula.curso_nome },
    { label: 'Turma', value: selectedMatricula.turma_nome },
    { label: 'Status', value: selectedMatricula.status_display },
    { label: 'Tipo', value: selectedMatricula.tipo_matricula_display || '-' },
    { label: 'Turno', value: selectedMatricula.turno_display || '-' },
    { label: 'Data da matricula', value: formatDate(selectedMatricula.data_matricula) },
  ] : []

  const openEditForm = (id) => {
    setSelectedMatriculaId(null)
    setEditingMatriculaId(id)
  }

  const closeForm = () => {
    setEditingMatriculaId(null)
    setFormData(DEFAULT_FORM)
  }

  if (isCreatePage) {
    return (
      <div className="page page--wide">
        <nav className="profile-breadcrumb">
          <Link to="/dashboard">Início</Link>
          <span className="profile-breadcrumb__sep">&gt;</span>
          <Link to="/matriculas">Matrículas</Link>
          <span className="profile-breadcrumb__sep">&gt;</span>
          <span>Nova Matrícula</span>
        </nav>

        <div className="page-header">
          <div>
            <h1 className="page-title">Nova matrícula</h1>
            <p className="page-subtitle">A criação agora acontece em uma página separada da listagem.</p>
          </div>
          <div className="page-header__actions">
            <button type="button" className="btn btn--outline" onClick={() => navigate('/matriculas')}>
              Voltar para matrículas
            </button>
          </div>
        </div>

        <EntityFormPanel
          title="Nova matricula"
          subtitle="Informe aluno, curso, turma e situacao da matricula."
          onSubmit={(event) => {
            event.preventDefault()
            saveMutation.mutate({
              payload: {
                aluno: Number(formData.aluno),
                curso: Number(formData.curso),
                turma: Number(formData.turma),
                status: formData.status,
                tipo_matricula: formData.tipo_matricula,
                turno: formData.turno || '',
              },
            })
          }}
          onCancel={() => navigate('/matriculas')}
          submitLabel="Criar matricula"
          isSubmitting={saveMutation.isPending}
        >
          <SearchableRemoteSelect id="matricula-aluno" label="Aluno" searchLabel="Buscar aluno" searchPlaceholder="Digite nome, CPF ou usuario" searchValue={alunoSearch} onSearchChange={setAlunoSearch} value={formData.aluno} onChange={(nextValue) => setFormData((current) => ({ ...current, aluno: nextValue }))} options={alunos} getOptionLabel={(item) => `${item.nome_completo} - ${item.username}`} />
          <SearchableRemoteSelect id="matricula-curso" label="Curso" searchLabel="Buscar curso" searchPlaceholder="Digite nome, sigla ou unidade" searchValue={cursoSearch} onSearchChange={setCursoSearch} value={formData.curso} onChange={(nextValue) => setFormData((current) => ({ ...current, curso: nextValue, turma: '' }))} options={cursos} getOptionLabel={(item) => `${item.nome}${item.sigla ? ` - ${item.sigla}` : ''}`} />
          <SearchableRemoteSelect id="matricula-turma" label="Turma" searchLabel="Buscar turma" searchPlaceholder="Digite nome da turma" searchValue={turmaSearch} onSearchChange={setTurmaSearch} value={formData.turma} onChange={(nextValue) => setFormData((current) => ({ ...current, turma: nextValue }))} options={turmas} getOptionLabel={(item) => `${item.nome} - ${item.curso_nome}`} />
          <div className="form-field"><label>Status</label><select className="select" value={formData.status} onChange={(event) => setFormData((current) => ({ ...current, status: event.target.value }))}>{STATUS_OPTIONS.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}</select></div>
          <div className="form-field"><label>Tipo da matricula</label><select className="select" value={formData.tipo_matricula} onChange={(event) => setFormData((current) => ({ ...current, tipo_matricula: event.target.value }))}>{TIPO_OPTIONS.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}</select></div>
                    <div className="form-field"><label>Turno {formData.status === 'ATIVA' ? <span className="field-required">*</span> : ''}</label><select className="select" value={formData.turno} onChange={(event) => setFormData((current) => ({ ...current, turno: event.target.value }))}>{TURNO_OPTIONS.map((option) => <option key={option.value || 'blank'} value={option.value}>{option.label}</option>)}</select>{formData.status === 'ATIVA' && !formData.turno ? <span className="field-error">Turno obrigatorio para matricula ativa.</span> : null}</div>
        </EntityFormPanel>
      </div>
    )
  }

  return (
    <div className="page">
      <div className="page-header">
        <h1 className="page-title">Matriculas</h1>
        <div className="page-header__actions">
          <select
            className="select"
            value={statusFilter}
            onChange={(e) => { setStatusFilter(e.target.value); setPage(1) }}
          >
            <option value="">Todos os status</option>
            {STATUS_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>{option.label}</option>
            ))}
          </select>
          <button type="button" className="btn btn--primary" onClick={() => navigate('/matriculas/nova')}>
            <Plus size={16} /> Nova Matrícula
          </button>
        </div>
      </div>

      {isError ? <div className="alert alert--error">Nao foi possivel carregar as matriculas.</div> : null}

      <DataTable
        columns={COLUMNS}
        data={data}
        isLoading={isLoading}
        onSearch={(v) => { setSearch(v); setPage(1) }}
        searchPlaceholder="Buscar por nome, CPF ou número..."
        emptyMessage="Nenhuma matrícula encontrada."
        rowActions={(row) => (
          <div className="table-actions">
            <button type="button" className="btn btn--outline btn--sm" onClick={() => setSelectedMatriculaId(row.id)}>
              <Eye size={14} /> Detalhes
            </button>
            <button type="button" className="btn btn--secondary btn--sm" onClick={() => openEditForm(row.id)}>
              <Pencil size={14} /> Editar
            </button>
            <button type="button" className="btn btn--danger btn--sm" onClick={() => window.confirm(`Excluir a matricula ${row.numero_matricula}?`) && deleteMutation.mutate(row.id)}>
              <Trash2 size={14} /> Excluir
            </button>
          </div>
        )}
      />

      {selectedMatriculaId ? (
        <EntityDetailsPanel
          title="Detalhes da matricula"
          subtitle={selectedMatricula?.numero_matricula || 'Consultando matricula selecionada'}
          fields={detailsFields}
          isLoading={isLoadingDetails}
          errorMessage={isErrorDetails ? 'Nao foi possivel carregar os detalhes desta matricula.' : ''}
          onClose={() => setSelectedMatriculaId(null)}
        />
      ) : null}

      {editingMatriculaId ? (
        <EntityFormPanel
          title="Editar matricula"
          subtitle="Informe aluno, curso, turma e situacao da matricula."
          onSubmit={(event) => {
            event.preventDefault()
                        saveMutation.mutate({
              id: editingMatriculaId,
              payload: {
                aluno: Number(formData.aluno),
                curso: Number(formData.curso),
                turma: Number(formData.turma),
                status: formData.status,
                tipo_matricula: formData.tipo_matricula,
                turno: formData.turno || '',
                // T107: enviar versao atual para controle de concorrencia
                ...(editingMatricula?.version !== undefined ? { version: editingMatricula.version } : {}),
              },
            })
          }}
          onCancel={closeForm}
          submitLabel="Salvar alteracoes"
          isSubmitting={saveMutation.isPending}
        >
          <SearchableRemoteSelect
            id="matricula-aluno"
            label="Aluno"
            searchLabel="Buscar aluno"
            searchPlaceholder="Digite nome, CPF ou usuario"
            searchValue={alunoSearch}
            onSearchChange={setAlunoSearch}
            value={formData.aluno}
            onChange={(nextValue) => setFormData((current) => ({ ...current, aluno: nextValue }))}
            options={alunos}
            selectedOption={selectedAlunoOption}
            getOptionLabel={(item) => `${item.nome_completo} - ${item.username}`}
          />
          <SearchableRemoteSelect
            id="matricula-curso"
            label="Curso"
            searchLabel="Buscar curso"
            searchPlaceholder="Digite nome, sigla ou unidade"
            searchValue={cursoSearch}
            onSearchChange={setCursoSearch}
            value={formData.curso}
            onChange={(nextValue) => setFormData((current) => ({ ...current, curso: nextValue, turma: '' }))}
            options={cursos}
            selectedOption={selectedCursoOption}
            getOptionLabel={(item) => `${item.nome}${item.sigla ? ` - ${item.sigla}` : ''}`}
          />
          <SearchableRemoteSelect
            id="matricula-turma"
            label="Turma"
            searchLabel="Buscar turma"
            searchPlaceholder="Digite nome da turma"
            searchValue={turmaSearch}
            onSearchChange={setTurmaSearch}
            value={formData.turma}
            onChange={(nextValue) => setFormData((current) => ({ ...current, turma: nextValue }))}
            options={turmas}
            selectedOption={selectedTurmaOption}
            getOptionLabel={(item) => `${item.nome} - ${item.curso_nome}`}
          />
          <div className="form-field">
            <label>Status</label>
            <select className="select" value={formData.status} onChange={(event) => setFormData((current) => ({ ...current, status: event.target.value }))}>
              {STATUS_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>{option.label}</option>
              ))}
            </select>
          </div>
          <div className="form-field">
            <label>Tipo da matricula</label>
            <select className="select" value={formData.tipo_matricula} onChange={(event) => setFormData((current) => ({ ...current, tipo_matricula: event.target.value }))}>
              {TIPO_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>{option.label}</option>
              ))}
            </select>
          </div>
                    <div className="form-field">
                        <label>Turno {formData.status === 'ATIVA' ? <span className="field-required">*</span> : ''}</label>
            <select className="select" value={formData.turno} onChange={(event) => setFormData((current) => ({ ...current, turno: event.target.value }))}>
              {TURNO_OPTIONS.map((option) => (
                <option key={option.value || 'blank'} value={option.value}>{option.label}</option>
              ))}
            </select>
            {formData.status === 'ATIVA' && !formData.turno ? <span className="field-error">Turno obrigatorio para matricula ativa.</span> : null}
          </div>
        </EntityFormPanel>
      ) : null}

      {data && (
        <div className="pagination">
          <button
            className="btn btn--secondary"
            disabled={!data.previous}
            onClick={() => setPage((p) => p - 1)}
          >
            Anterior
          </button>
          <span className="pagination__info">Pagina {page} — {data.count} registros</span>
          <button
            className="btn btn--secondary"
            disabled={!data.next}
            onClick={() => setPage((p) => p + 1)}
          >
            Próxima
          </button>
        </div>
      )}
    </div>
  )
}
