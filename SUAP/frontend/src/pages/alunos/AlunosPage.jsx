import { useEffect, useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useForm } from 'react-hook-form'
import toast from 'react-hot-toast'
import { Eye, Pencil, Plus, Trash2 } from 'lucide-react'
import { Link, useLocation, useNavigate, useSearchParams } from 'react-router-dom'

import { alunosApi } from '@/api/endpoints'
import DataTable from '@/components/ui/DataTable'
import EntityDetailsPanel from '@/components/ui/EntityDetailsPanel'
import EntityFormPanel from '@/components/ui/EntityFormPanel'

const SITUACAO_OPTIONS = [
  { value: 'ATIVO', label: 'Ativo' },
  { value: 'INATIVO', label: 'Inativo' },
]

const COLUMNS = [
  { key: 'nome_completo', label: 'Aluno' },
  { key: 'username', label: 'Usuario' },
  { key: 'cpf', label: 'CPF' },
  { key: 'email', label: 'E-mail' },
  { key: 'situacao', label: 'Situacao' },
  {
    key: 'is_active',
    label: 'Ativo',
    render: (row) => (row.is_active ? 'Sim' : 'Nao'),
  },
]

const DEFAULT_VALUES = {
  nome_completo: '',
  cpf: '',
  email: '',
  situacao: 'ATIVO',
  is_active: true,
}

function getErrorMessage(error, fallback) {
  const data = error?.response?.data
  if (!data) {
    return fallback
  }

  if (typeof data.detail === 'string') {
    return data.detail
  }

  const firstValue = Object.values(data)[0]
  if (Array.isArray(firstValue)) {
    return firstValue[0]
  }

  return firstValue || fallback
}

export default function AlunosPage() {
  const location = useLocation()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [searchParams, setSearchParams] = useSearchParams()
  const [search, setSearch] = useState('')
  const [page, setPage] = useState(1)
  const [situacaoFiltro, setSituacaoFiltro] = useState('')
  const [selectedAlunoId, setSelectedAlunoId] = useState(searchParams.get('alunoId'))
  const [editingAlunoId, setEditingAlunoId] = useState(null)
  const isCreatePage = location.pathname.endsWith('/alunos/novo')

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm({ defaultValues: DEFAULT_VALUES })

  const listParams = useMemo(() => ({
    search,
    page,
    situacao: situacaoFiltro || undefined,
  }), [page, search, situacaoFiltro])

  const { data, isLoading, isError } = useQuery({
    queryKey: ['alunos', listParams],
    queryFn: () => alunosApi.list(listParams).then((response) => response.data),
    staleTime: 30_000,
  })

  const { data: selectedAluno, isLoading: isLoadingDetails, isError: isErrorDetails } = useQuery({
    queryKey: ['aluno', selectedAlunoId],
    queryFn: () => alunosApi.get(selectedAlunoId).then((response) => response.data),
    enabled: Boolean(selectedAlunoId),
    staleTime: 30_000,
  })

  const { data: editingAluno, isLoading: isLoadingEditing } = useQuery({
    queryKey: ['aluno-edit', editingAlunoId],
    queryFn: () => alunosApi.get(editingAlunoId).then((response) => response.data),
    enabled: Boolean(editingAlunoId),
    staleTime: 0,
  })

  useEffect(() => {
    setSelectedAlunoId(searchParams.get('alunoId'))
  }, [searchParams])

  useEffect(() => {
    if (!editingAluno) {
      return
    }

    reset({
      nome_completo: editingAluno.nome_completo || '',
      cpf: editingAluno.cpf || '',
      email: editingAluno.email || '',
      situacao: editingAluno.situacao || 'ATIVO',
      is_active: Boolean(editingAluno.is_active),
    })
  }, [editingAluno, reset])

  const saveMutation = useMutation({
    mutationFn: ({ id, payload }) => (id ? alunosApi.update(id, payload) : alunosApi.create(payload)),
    onSuccess: (_response, variables) => {
      queryClient.invalidateQueries({ queryKey: ['alunos'] })
      if (variables.id) {
        queryClient.invalidateQueries({ queryKey: ['aluno', variables.id] })
        toast.success('Aluno atualizado com sucesso.')
      } else {
        toast.success('Aluno criado com sucesso.')
      }
      setEditingAlunoId(null)
      reset(DEFAULT_VALUES)
      if (!variables.id) {
        navigate('/alunos')
      }
    },
    onError: (error) => {
      toast.error(getErrorMessage(error, 'Nao foi possivel salvar o aluno.'))
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (id) => alunosApi.remove(id),
    onSuccess: (_response, id) => {
      queryClient.invalidateQueries({ queryKey: ['alunos'] })
      queryClient.invalidateQueries({ queryKey: ['aluno', id] })
      if (selectedAlunoId === String(id) || selectedAlunoId === id) {
        setSelectedAlunoId(null)
        setSearchParams({})
      }
      if (editingAlunoId === id) {
        setEditingAlunoId(null)
        reset(DEFAULT_VALUES)
      }
      toast.success('Aluno excluido com sucesso.')
    },
    onError: (error) => {
      toast.error(getErrorMessage(error, 'Nao foi possivel excluir o aluno.'))
    },
  })

  const detailsFields = selectedAluno
    ? [
        { label: 'ID', value: selectedAluno.id },
        { label: 'Aluno', value: selectedAluno.nome_completo },
        { label: 'Usuario', value: selectedAluno.username },
        { label: 'CPF', value: selectedAluno.cpf },
        { label: 'E-mail', value: selectedAluno.email || '-' },
        { label: 'Perfil', value: selectedAluno.tipo_display },
        { label: 'Situacao academica', value: selectedAluno.situacao },
        { label: 'Data de ingresso', value: selectedAluno.data_ingresso || '-' },
        { label: 'Ativo', value: selectedAluno.is_active },
      ]
    : []

  const openEditForm = (id) => {
    setSelectedAlunoId(null)
    setEditingAlunoId(id)
  }

  const closeForm = () => {
    setEditingAlunoId(null)
    reset(DEFAULT_VALUES)
  }

  const onSubmit = handleSubmit(async (formData) => {
    await saveMutation.mutateAsync({
      id: editingAlunoId,
      payload: {
        nome_completo: formData.nome_completo.trim(),
        cpf: formData.cpf.trim(),
        email: formData.email.trim(),
        situacao: formData.situacao,
        is_active: Boolean(formData.is_active),
      },
    })
  })

  const handleDelete = (row) => {
    if (!window.confirm(`Deseja realmente excluir o aluno ${row.nome_completo}?`)) {
      return
    }

    deleteMutation.mutate(row.id)
  }

  if (isCreatePage) {
    return (
      <div className="page page--wide">
        <nav className="profile-breadcrumb">
          <Link to="/dashboard">Início</Link>
          <span className="profile-breadcrumb__sep">&gt;</span>
          <Link to="/alunos">Alunos</Link>
          <span className="profile-breadcrumb__sep">&gt;</span>
          <span>Novo Aluno</span>
        </nav>

        <div className="page-header">
          <div>
            <h1 className="page-title">Novo aluno</h1>
            <p className="page-subtitle">A criação agora acontece em uma página separada da listagem.</p>
          </div>
          <div className="page-header__actions">
            <button type="button" className="btn btn--outline" onClick={() => navigate('/alunos')}>
              Voltar para alunos
            </button>
          </div>
        </div>

        <EntityFormPanel
          title="Novo aluno"
          subtitle="Cadastre um novo aluno no modulo de Alunos e Professores."
          onSubmit={onSubmit}
          onCancel={() => navigate('/alunos')}
          submitLabel="Criar aluno"
          isSubmitting={isSubmitting || saveMutation.isPending}
        >
          <div className="form-field"><label htmlFor="aluno-nome">Nome completo</label><input id="aluno-nome" type="text" {...register('nome_completo', { required: 'Informe o nome completo' })} />{errors.nome_completo ? <span className="field-error">{errors.nome_completo.message}</span> : null}</div>
          <div className="form-field"><label htmlFor="aluno-cpf">CPF</label><input id="aluno-cpf" type="text" {...register('cpf', { required: 'Informe o CPF' })} />{errors.cpf ? <span className="field-error">{errors.cpf.message}</span> : null}</div>
          <div className="form-field"><label htmlFor="aluno-email">E-mail</label><input id="aluno-email" type="email" {...register('email')} /></div>
          <div className="form-field"><label htmlFor="aluno-situacao">Situacao academica</label><select id="aluno-situacao" className="select" {...register('situacao', { required: 'Selecione a situacao' })}>{SITUACAO_OPTIONS.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}</select>{errors.situacao ? <span className="field-error">{errors.situacao.message}</span> : null}</div>
          <div className="form-field form-field--checkbox"><label className="checkbox-field"><input type="checkbox" {...register('is_active')} /><span>Aluno ativo</span></label></div>
        </EntityFormPanel>
      </div>
    )
  }

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <h1 className="page-title">Alunos</h1>
          <p className="page-subtitle">Cadastro e manutenção de alunos</p>
        </div>
        <div className="page-header__actions">
          <select className="select" value={situacaoFiltro} onChange={(event) => { setSituacaoFiltro(event.target.value); setPage(1) }}>
            <option value="">Todas as situacoes</option>
            {SITUACAO_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>{option.label}</option>
            ))}
          </select>
          <button type="button" className="btn btn--primary" onClick={() => navigate('/alunos/novo')}>
            <Plus size={16} /> Novo Aluno
          </button>
        </div>
      </div>

      {isError ? (
        <div className="alert alert--error">
          Nao foi possivel carregar os alunos com as permissoes atuais.
        </div>
      ) : null}

      <DataTable
        columns={COLUMNS}
        data={data}
        isLoading={isLoading}
        onSearch={(value) => {
          setSearch(value)
          setPage(1)
        }}
        searchPlaceholder="Buscar por nome, CPF, usuario ou e-mail..."
        emptyMessage="Nenhum aluno encontrado."
        rowActions={(row) => (
          <div className="table-actions">
            <button type="button" className="btn btn--outline btn--sm" onClick={() => setSearchParams({ alunoId: String(row.id) })}>
              <Eye size={14} /> Visualizar
            </button>
            <button type="button" className="btn btn--secondary btn--sm" onClick={() => openEditForm(row.id)}>
              <Pencil size={14} /> Editar
            </button>
            <button type="button" className="btn btn--danger btn--sm" onClick={() => handleDelete(row)}>
              <Trash2 size={14} /> Excluir
            </button>
          </div>
        )}
      />

      {selectedAlunoId ? (
        <EntityDetailsPanel
          title="Detalhes do aluno"
          subtitle={selectedAluno?.nome_completo || 'Consultando aluno selecionado'}
          fields={detailsFields}
          isLoading={isLoadingDetails}
          errorMessage={isErrorDetails ? 'Nao foi possivel carregar os detalhes deste aluno.' : ''}
          onClose={() => setSearchParams({})}
        />
      ) : null}

      {editingAlunoId ? (
        <EntityFormPanel
          title="Editar aluno"
          subtitle="Atualize os dados do aluno selecionado."
          onSubmit={onSubmit}
          onCancel={closeForm}
          submitLabel="Salvar alteracoes"
          isSubmitting={isSubmitting || saveMutation.isPending || isLoadingEditing}
        >
          <div className="form-field">
            <label htmlFor="aluno-edit-nome">Nome completo</label>
            <input id="aluno-edit-nome" type="text" {...register('nome_completo', { required: 'Informe o nome completo' })} />
            {errors.nome_completo ? <span className="field-error">{errors.nome_completo.message}</span> : null}
          </div>
          <div className="form-field">
            <label htmlFor="aluno-edit-cpf">CPF</label>
            <input id="aluno-edit-cpf" type="text" {...register('cpf', { required: 'Informe o CPF' })} />
            {errors.cpf ? <span className="field-error">{errors.cpf.message}</span> : null}
          </div>
          <div className="form-field">
            <label htmlFor="aluno-edit-email">E-mail</label>
            <input id="aluno-edit-email" type="email" {...register('email')} />
          </div>
          <div className="form-field">
            <label htmlFor="aluno-edit-situacao">Situacao academica</label>
            <select id="aluno-edit-situacao" className="select" {...register('situacao', { required: 'Selecione a situacao' })}>
              {SITUACAO_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>{option.label}</option>
              ))}
            </select>
            {errors.situacao ? <span className="field-error">{errors.situacao.message}</span> : null}
          </div>
          <div className="form-field form-field--checkbox">
            <label className="checkbox-field">
              <input type="checkbox" {...register('is_active')} />
              <span>Aluno ativo</span>
            </label>
          </div>
        </EntityFormPanel>
      ) : null}

      {data ? (
        <div className="pagination">
          <button className="btn btn--secondary" disabled={!data.previous} onClick={() => setPage((current) => current - 1)}>Anterior</button>
          <span className="pagination__info">Pagina {page} — {data.count} registros</span>
          <button className="btn btn--secondary" disabled={!data.next} onClick={() => setPage((current) => current + 1)}>Proxima</button>
        </div>
      ) : null}
    </div>
  )
}
