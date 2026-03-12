import { useEffect, useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useForm } from 'react-hook-form'
import toast from 'react-hot-toast'
import { Eye, Pencil, Plus, Trash2 } from 'lucide-react'
import { Link, useLocation, useNavigate, useSearchParams } from 'react-router-dom'

import { servidoresApi, setoresApi } from '@/api/endpoints'
import DataTable from '@/components/ui/DataTable'
import EntityDetailsPanel from '@/components/ui/EntityDetailsPanel'
import EntityFormPanel from '@/components/ui/EntityFormPanel'
import SearchableRemoteSelect from '@/components/ui/SearchableRemoteSelect'

const PERFIL_OPTIONS = [
  { value: 'PROFESSOR', label: 'Professor' },
  { value: 'SECRETARIA', label: 'Secretaria' },
  { value: 'COORDENACAO', label: 'Coordenacao/Consulta' },
  { value: 'ADMIN', label: 'Administrador' },
]

const COLUMNS = [
  { key: 'nome_completo', label: 'Servidor' },
  { key: 'username', label: 'Usuario' },
  { key: 'cpf', label: 'CPF' },
  { key: 'email', label: 'E-mail' },
  { key: 'setor_nome', label: 'Setor' },
  { key: 'tipo_display', label: 'Perfil' },
  {
    key: 'is_active',
    label: 'Ativo',
    render: (row) => (row.is_active ? 'Sim' : 'Nao'),
  },
]

const DEFAULT_VALUES = {
  username: '',
  nome_completo: '',
  cpf: '',
  email: '',
  tipo: 'PROFESSOR',
  setor: '',
  is_active: true,
  password: '',
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

export default function ServidoresPage() {
  const location = useLocation()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [searchParams, setSearchParams] = useSearchParams()
  const [search, setSearch] = useState('')
  const [page, setPage] = useState(1)
  const [tipoFiltro, setTipoFiltro] = useState('')
  const [setorFiltro, setSetorFiltro] = useState('')
  const [selectedServidorId, setSelectedServidorId] = useState(searchParams.get('servidorId'))
  const [editingServidorId, setEditingServidorId] = useState(null)
  const [setorSearch, setSetorSearch] = useState('')
  const isCreatePage = location.pathname.endsWith('/rh/servidores/novo')

  const {
    register,
    handleSubmit,
    reset,
    setValue,
    watch,
    formState: { errors, isSubmitting },
  } = useForm({ defaultValues: DEFAULT_VALUES })

  const listParams = useMemo(() => ({
    search,
    page,
    tipo: tipoFiltro || undefined,
    setor: setorFiltro || undefined,
  }), [page, search, setorFiltro, tipoFiltro])

  const { data, isLoading, isError } = useQuery({
    queryKey: ['servidores', listParams],
    queryFn: () => servidoresApi.list(listParams).then((response) => response.data),
    staleTime: 30_000,
  })

  const { data: setoresData } = useQuery({
    queryKey: ['setores', 'options', setorSearch],
    queryFn: () => setoresApi.list({ page_size: 10, search: setorSearch || undefined }).then((response) => response.data),
    staleTime: 60_000,
  })

  const { data: selectedServidor, isLoading: isLoadingDetails, isError: isErrorDetails } = useQuery({
    queryKey: ['servidor', selectedServidorId],
    queryFn: () => servidoresApi.get(selectedServidorId).then((response) => response.data),
    enabled: Boolean(selectedServidorId),
    staleTime: 30_000,
  })

  const { data: editingServidor, isLoading: isLoadingEditing } = useQuery({
    queryKey: ['servidor-edit', editingServidorId],
    queryFn: () => servidoresApi.get(editingServidorId).then((response) => response.data),
    enabled: Boolean(editingServidorId),
    staleTime: 0,
  })

  const setorOptions = setoresData?.results || []
  const setorValue = watch('setor')
  const selectedSetorOption = setorValue && editingServidor ? {
    id: editingServidor.setor,
    nome: editingServidor.setor_nome,
  } : null

  useEffect(() => {
    setSelectedServidorId(searchParams.get('servidorId'))
  }, [searchParams])

  useEffect(() => {
    if (!editingServidor) {
      return
    }

    reset({
      username: editingServidor.username || '',
      nome_completo: editingServidor.nome_completo || '',
      cpf: editingServidor.cpf || '',
      email: editingServidor.email || '',
      tipo: editingServidor.tipo || 'PROFESSOR',
      setor: editingServidor.setor ? String(editingServidor.setor) : '',
      is_active: Boolean(editingServidor.is_active),
      password: '',
    })
  }, [editingServidor, reset])

  const saveMutation = useMutation({
    mutationFn: ({ id, payload }) => (id ? servidoresApi.update(id, payload) : servidoresApi.create(payload)),
    onSuccess: (_response, variables) => {
      queryClient.invalidateQueries({ queryKey: ['servidores'] })
      if (variables.id) {
        queryClient.invalidateQueries({ queryKey: ['servidor', variables.id] })
        toast.success('Servidor atualizado com sucesso.')
      } else {
        toast.success('Servidor criado com sucesso.')
      }
      setEditingServidorId(null)
      reset(DEFAULT_VALUES)
      if (!variables.id) {
        navigate('/rh/servidores')
      }
    },
    onError: (error) => {
      toast.error(getErrorMessage(error, 'Nao foi possivel salvar o servidor.'))
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (id) => servidoresApi.remove(id),
    onSuccess: (_response, id) => {
      queryClient.invalidateQueries({ queryKey: ['servidores'] })
      queryClient.invalidateQueries({ queryKey: ['servidor', id] })
      if (selectedServidorId === id) {
        setSelectedServidorId(null)
      }
      if (editingServidorId === id) {
        setEditingServidorId(null)
        reset(DEFAULT_VALUES)
      }
      toast.success('Servidor excluido com sucesso.')
    },
    onError: (error) => {
      toast.error(getErrorMessage(error, 'Nao foi possivel excluir o servidor.'))
    },
  })

  const detailsFields = selectedServidor
    ? [
        { label: 'ID', value: selectedServidor.id },
        { label: 'Servidor', value: selectedServidor.nome_completo },
        { label: 'Usuario', value: selectedServidor.username },
        { label: 'CPF', value: selectedServidor.cpf },
        { label: 'E-mail', value: selectedServidor.email || '-' },
        { label: 'Perfil', value: selectedServidor.tipo_display },
        { label: 'Setor', value: selectedServidor.setor_nome || '-' },
        { label: 'Ativo', value: selectedServidor.is_active },
      ]
    : []

  const openEditForm = (id) => {
    setSelectedServidorId(null)
    setEditingServidorId(id)
  }

  const closeForm = () => {
    setEditingServidorId(null)
    reset(DEFAULT_VALUES)
  }

  const onSubmit = handleSubmit(async (formData) => {
    const payload = {
      username: formData.username.trim(),
      nome_completo: formData.nome_completo.trim(),
      cpf: formData.cpf.trim(),
      email: formData.email.trim(),
      tipo: formData.tipo,
      setor: formData.setor ? Number(formData.setor) : null,
      is_active: Boolean(formData.is_active),
    }

    if (formData.password) {
      payload.password = formData.password
    }

    await saveMutation.mutateAsync({
      id: editingServidorId,
      payload,
    })
  })

  const handleDelete = (row) => {
    if (!window.confirm(`Deseja realmente excluir o servidor ${row.nome_completo}?`)) {
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
          <Link to="/rh/servidores">Servidores</Link>
          <span className="profile-breadcrumb__sep">&gt;</span>
          <span>Novo Servidor</span>
        </nav>

        <div className="page-header">
          <div>
            <h1 className="page-title">Novo servidor</h1>
            <p className="page-subtitle">A criação agora acontece em uma página separada da listagem.</p>
          </div>
          <div className="page-header__actions">
            <button type="button" className="btn btn--outline" onClick={() => navigate('/rh/servidores')}>
              Voltar para servidores
            </button>
          </div>
        </div>

        <EntityFormPanel
          title="Novo servidor"
          subtitle="Cadastre um novo servidor no modulo de Gestao de Pessoas."
          onSubmit={onSubmit}
          onCancel={() => navigate('/rh/servidores')}
          submitLabel="Criar servidor"
          isSubmitting={isSubmitting || saveMutation.isPending}
        >
          <div className="form-field"><label htmlFor="servidor-username">Usuario</label><input id="servidor-username" type="text" {...register('username', { required: 'Informe o usuario' })} />{errors.username ? <span className="field-error">{errors.username.message}</span> : null}</div>
          <div className="form-field"><label htmlFor="servidor-nome">Nome completo</label><input id="servidor-nome" type="text" {...register('nome_completo', { required: 'Informe o nome completo' })} />{errors.nome_completo ? <span className="field-error">{errors.nome_completo.message}</span> : null}</div>
          <div className="form-field"><label htmlFor="servidor-cpf">CPF</label><input id="servidor-cpf" type="text" {...register('cpf', { required: 'Informe o CPF' })} />{errors.cpf ? <span className="field-error">{errors.cpf.message}</span> : null}</div>
          <div className="form-field"><label htmlFor="servidor-email">E-mail</label><input id="servidor-email" type="email" {...register('email')} /></div>
          <div className="form-field"><label htmlFor="servidor-tipo">Perfil</label><select id="servidor-tipo" className="select" {...register('tipo', { required: 'Selecione o perfil' })}>{PERFIL_OPTIONS.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}</select>{errors.tipo ? <span className="field-error">{errors.tipo.message}</span> : null}</div>
          <SearchableRemoteSelect id="servidor-setor" label="Setor" searchLabel="Buscar setor" searchPlaceholder="Digite nome, sigla ou codigo" searchValue={setorSearch} onSearchChange={setSetorSearch} value={setorValue || ''} onChange={(nextValue) => setValue('setor', nextValue)} options={setorOptions} emptyOptionLabel="Sem setor" getOptionLabel={(setor) => setor.nome} />
          <div className="form-field"><label htmlFor="servidor-password">Senha</label><input id="servidor-password" type="password" {...register('password', { required: 'Informe a senha inicial' })} />{errors.password ? <span className="field-error">{errors.password.message}</span> : null}</div>
          <div className="form-field form-field--checkbox"><label className="checkbox-field"><input type="checkbox" {...register('is_active')} /><span>Servidor ativo</span></label></div>
        </EntityFormPanel>
      </div>
    )
  }

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <h1 className="page-title">Servidores</h1>
          <p className="page-subtitle">Gestao de Pessoas</p>
        </div>
        <div className="page-header__actions">
          <select className="select" value={tipoFiltro} onChange={(event) => { setTipoFiltro(event.target.value); setPage(1) }}>
            <option value="">Todos os perfis</option>
            {PERFIL_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>{option.label}</option>
            ))}
          </select>
          <select className="select" value={setorFiltro} onChange={(event) => { setSetorFiltro(event.target.value); setPage(1) }}>
            <option value="">Todos os setores</option>
            {setorOptions.map((setor) => (
              <option key={setor.id} value={setor.id}>{setor.nome}</option>
            ))}
          </select>
          <button type="button" className="btn btn--primary" onClick={() => navigate('/rh/servidores/novo')}>
            <Plus size={16} /> Novo Servidor
          </button>
        </div>
      </div>

      {isError ? (
        <div className="alert alert--error">
          Nao foi possivel carregar os servidores com as permissoes atuais.
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
        searchPlaceholder="Buscar por nome, CPF, usuario, e-mail ou setor..."
        emptyMessage="Nenhum servidor encontrado."
        rowActions={(row) => (
          <div className="table-actions">
            <button type="button" className="btn btn--outline btn--sm" onClick={() => setSearchParams({ servidorId: String(row.id) })}>
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

      {selectedServidorId ? (
        <EntityDetailsPanel
          title="Detalhes do servidor"
          subtitle={selectedServidor?.nome_completo || 'Consultando servidor selecionado'}
          fields={detailsFields}
          isLoading={isLoadingDetails}
          errorMessage={isErrorDetails ? 'Nao foi possivel carregar os detalhes deste servidor.' : ''}
          onClose={() => setSearchParams({})}
        />
      ) : null}

      {editingServidorId ? (
        <EntityFormPanel
          title="Editar servidor"
          subtitle="Atualize os dados do servidor selecionado."
          onSubmit={onSubmit}
          onCancel={closeForm}
          submitLabel="Salvar alteracoes"
          isSubmitting={isSubmitting || saveMutation.isPending || isLoadingEditing}
        >
          <div className="form-field">
            <label htmlFor="servidor-username">Usuario</label>
            <input id="servidor-username" type="text" {...register('username', { required: 'Informe o usuario' })} />
            {errors.username ? <span className="field-error">{errors.username.message}</span> : null}
          </div>

          <div className="form-field">
            <label htmlFor="servidor-nome">Nome completo</label>
            <input id="servidor-nome" type="text" {...register('nome_completo', { required: 'Informe o nome completo' })} />
            {errors.nome_completo ? <span className="field-error">{errors.nome_completo.message}</span> : null}
          </div>

          <div className="form-field">
            <label htmlFor="servidor-cpf">CPF</label>
            <input id="servidor-cpf" type="text" {...register('cpf', { required: 'Informe o CPF' })} />
            {errors.cpf ? <span className="field-error">{errors.cpf.message}</span> : null}
          </div>

          <div className="form-field">
            <label htmlFor="servidor-email">E-mail</label>
            <input id="servidor-email" type="email" {...register('email')} />
          </div>

          <div className="form-field">
            <label htmlFor="servidor-tipo">Perfil</label>
            <select id="servidor-tipo" className="select" {...register('tipo', { required: 'Selecione o perfil' })}>
              {PERFIL_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>{option.label}</option>
              ))}
            </select>
            {errors.tipo ? <span className="field-error">{errors.tipo.message}</span> : null}
          </div>

          <SearchableRemoteSelect
            id="servidor-setor"
            label="Setor"
            searchLabel="Buscar setor"
            searchPlaceholder="Digite nome, sigla ou codigo"
            searchValue={setorSearch}
            onSearchChange={setSetorSearch}
            value={setorValue || ''}
            onChange={(nextValue) => setValue('setor', nextValue)}
            options={setorOptions}
            selectedOption={selectedSetorOption}
            emptyOptionLabel="Sem setor"
            getOptionLabel={(setor) => setor.nome}
          />

          <div className="form-field">
            <label htmlFor="servidor-password">{editingServidorId ? 'Nova senha' : 'Senha'}</label>
            <input
              id="servidor-password"
              type="password"
              {...register('password', editingServidorId ? {} : { required: 'Informe a senha inicial' })}
            />
            {errors.password ? <span className="field-error">{errors.password.message}</span> : null}
          </div>

          <div className="form-field form-field--checkbox">
            <label className="checkbox-field">
              <input type="checkbox" {...register('is_active')} />
              <span>Servidor ativo</span>
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