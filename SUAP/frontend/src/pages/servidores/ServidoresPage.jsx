import { useEffect, useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useForm } from 'react-hook-form'
import toast from 'react-hot-toast'
import { Eye, Pencil, Plus, Trash2 } from 'lucide-react'
import { Link, useLocation, useNavigate, useSearchParams } from 'react-router-dom'

import { servidoresApi, setoresApi } from '@/api/endpoints'
import DataTable from '@/components/ui/DataTable'
import EntityFormPanel from '@/components/ui/EntityFormPanel'
import SearchableRemoteSelect from '@/components/ui/SearchableRemoteSelect'
import { normalizeCpf } from '@/utils/cpf'

const PERFIL_OPTIONS = [
  { value: 'PROFESSOR', label: 'Professor' },
  { value: 'SECRETARIA', label: 'Secretaria' },
  { value: 'COORDENACAO', label: 'Coordenador de Curso' },
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
  const [searchParams] = useSearchParams()
  const [search, setSearch] = useState('')
  const [page, setPage] = useState(1)
  const [tipoFiltro, setTipoFiltro] = useState('')
  const [setorFiltro, setSetorFiltro] = useState('')
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

  useEffect(() => {
    const servidorId = searchParams.get('servidorId')
    const mode = searchParams.get('mode')

    if (!servidorId || isCreatePage) {
      return
    }

    navigate(mode === 'edit' ? `/rh/servidores/${servidorId}/editar` : `/rh/servidores/${servidorId}`, { replace: true })
  }, [isCreatePage, navigate, searchParams])

  const setorOptions = setoresData?.results || []
  const setorValue = watch('setor')

  const saveMutation = useMutation({
    mutationFn: ({ payload }) => servidoresApi.create(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['servidores'] })
      toast.success('Servidor criado com sucesso.')
      reset(DEFAULT_VALUES)
      navigate('/rh/servidores')
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
      toast.success('Servidor excluido com sucesso.')
    },
    onError: (error) => {
      toast.error(getErrorMessage(error, 'Nao foi possivel excluir o servidor.'))
    },
  })

  const onSubmit = handleSubmit(async (formData) => {
    const payload = {
      username: formData.username.trim(),
      nome_completo: formData.nome_completo.trim(),
      cpf: normalizeCpf(formData.cpf),
      email: formData.email.trim(),
      tipo: formData.tipo,
      setor: formData.setor ? Number(formData.setor) : null,
      is_active: Boolean(formData.is_active),
    }

    if (formData.password) {
      payload.password = formData.password
    }

    await saveMutation.mutateAsync({ payload })
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
            <button type="button" className="btn btn--outline btn--sm" onClick={() => navigate(`/rh/servidores/${row.id}`)}>
              <Eye size={14} /> Visualizar
            </button>
            <button type="button" className="btn btn--secondary btn--sm" onClick={() => navigate(`/rh/servidores/${row.id}/editar`)}>
              <Pencil size={14} /> Editar
            </button>
            <button type="button" className="btn btn--danger btn--sm" onClick={() => handleDelete(row)}>
              <Trash2 size={14} /> Excluir
            </button>
          </div>
        )}
      />

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