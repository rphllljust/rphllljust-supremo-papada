import { useEffect, useRef } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useForm } from 'react-hook-form'
import toast from 'react-hot-toast'
import { ArrowLeft, Save, Trash2 } from 'lucide-react'
import { Link, useNavigate, useParams } from 'react-router-dom'

import { componentesApi } from '@/api/endpoints'

const DEFAULT_VALUES = {
  curso: '',
  descricao: '',
  descricao_diploma_historico: '',
  abreviatura: '',
  sigla: '',
  tipo_componente: '',
  diretoria: '',
  nivel_ensino: '',
  esta_ativo: true,
  carga_horaria: 0,
  hora_aula: 0,
  qtd_creditos: 0,
  grupo_atuacao: '',
  sigla_qacademico: '',
  observacao: '',
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

function buildFormValues(component) {
  return {
    curso: component?.curso_id ? String(component.curso_id) : '',
    descricao: component?.descricao || '',
    descricao_diploma_historico: component?.descricao_diploma_historico || '',
    abreviatura: component?.abreviatura || '',
    sigla: component?.sigla || '',
    tipo_componente: component?.tipo_componente || '',
    diretoria: component?.diretoria || '',
    nivel_ensino: component?.nivel_ensino || '',
    esta_ativo: component?.esta_ativo ?? true,
    carga_horaria: component?.carga_horaria ?? 0,
    hora_aula: component?.hora_aula ?? 0,
    qtd_creditos: component?.qtd_creditos ?? 0,
    grupo_atuacao: component?.grupo_atuacao || '',
    sigla_qacademico: component?.sigla_qacademico || '',
    observacao: component?.observacao || '',
  }
}

export default function ComponenteEditPage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { componenteId } = useParams()
  const submitModeRef = useRef('view')
  const isCreateMode = !componenteId

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm({ defaultValues: DEFAULT_VALUES })

  const { data, isLoading, isError } = useQuery({
    queryKey: ['componentes', 'detail', componenteId],
    queryFn: () => componentesApi.get(componenteId).then((response) => response.data),
    enabled: !isCreateMode,
    staleTime: 0,
  })

  const { data: opcoes } = useQuery({
    queryKey: ['componentes', 'form-options'],
    queryFn: () => componentesApi.list({}).then((response) => response.data?.summary?.filter_options || {}),
    staleTime: 60_000,
  })

  useEffect(() => {
    if (!data) {
      return
    }

    reset(buildFormValues(data))
  }, [data, reset])

  const saveMutation = useMutation({
    mutationFn: ({ id, payload }) => (id ? componentesApi.patch(id, payload) : componentesApi.create(payload)),
    onSuccess: async (response, variables) => {
      const savedId = response.data?.id || variables.id

      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ['componentes'] }),
        savedId ? queryClient.invalidateQueries({ queryKey: ['componentes', 'detail', savedId] }) : Promise.resolve(),
      ])

      toast.success(isCreateMode ? 'Componente criado com sucesso.' : 'Componente atualizado com sucesso.')

      if (submitModeRef.current === 'add') {
        reset(DEFAULT_VALUES)
        navigate('/ensino/componentes/novo')
        return
      }

      if (submitModeRef.current === 'stay') {
        if (isCreateMode && savedId) {
          navigate(`/componentes/${savedId}/editar`, { replace: true })
        }
        return
      }

      if (savedId) {
        navigate(`/componentes/${savedId}`)
      }
    },
    onError: (error) => {
      toast.error(getErrorMessage(error, isCreateMode ? 'Não foi possível criar o componente.' : 'Não foi possível salvar o componente.'))
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (id) => componentesApi.remove(id),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['componentes'] })
      toast.success('Componente removido com sucesso.')
      navigate('/ensino/componentes/')
    },
    onError: (error) => {
      toast.error(getErrorMessage(error, 'Não foi possível remover o componente.'))
    },
  })

  if (!isCreateMode && isLoading) {
    return (
      <div className="page page--wide">
        <div className="page-loader" role="status" aria-live="polite">
          <div className="spinner" />
          <span>Carregando componente...</span>
        </div>
      </div>
    )
  }

  if (!isCreateMode && (isError || !data)) {
    return (
      <div className="page page--wide">
        <div className="page-error">
          <h1 className="page-error__title">Não foi possível carregar o componente</h1>
          <p className="page-error__description">Verifique se o registro existe e tente novamente.</p>
        </div>
      </div>
    )
  }

  const onSubmit = handleSubmit(async (formData) => {
    const payload = {
      curso: Number(formData.curso),
      descricao: formData.descricao.trim(),
      descricao_diploma_historico: formData.descricao_diploma_historico.trim(),
      abreviatura: formData.abreviatura.trim(),
      sigla: formData.sigla.trim(),
      tipo_componente: formData.tipo_componente.trim(),
      diretoria: formData.diretoria.trim(),
      nivel_ensino: formData.nivel_ensino.trim(),
      esta_ativo: Boolean(formData.esta_ativo),
      carga_horaria: Number(formData.carga_horaria) || 0,
      hora_aula: Number(formData.hora_aula) || 0,
      qtd_creditos: Number(formData.qtd_creditos) || 0,
      grupo_atuacao: formData.grupo_atuacao.trim(),
      sigla_qacademico: formData.sigla_qacademico.trim(),
      observacao: formData.observacao.trim(),
    }

    await saveMutation.mutateAsync({
      id: data?.id,
      payload,
    })
  })

  const handleDelete = () => {
    if (!window.confirm(`Deseja realmente remover o componente ${data.descricao}?`)) {
      return
    }

    deleteMutation.mutate(data.id)
  }

  return (
    <div className="page page--wide componente-edit-page">
      <nav className="profile-breadcrumb">
        <Link to="/dashboard">Início</Link>
        <span className="profile-breadcrumb__sep">&gt;</span>
        <Link to="/ensino/componentes/">Componentes</Link>
        {isCreateMode ? (
          <>
            <span className="profile-breadcrumb__sep">&gt;</span>
            <span>Novo</span>
          </>
        ) : (
          <>
            <span className="profile-breadcrumb__sep">&gt;</span>
            <Link to={`/componentes/${data.id}`}>{data.sigla || data.descricao}</Link>
            <span className="profile-breadcrumb__sep">&gt;</span>
            <span>Editar</span>
          </>
        )}
      </nav>

      <div className="page-header componente-edit-page__header">
        <div>
          <h1 className="page-title">{isCreateMode ? 'Novo componente' : 'Editar componente'}</h1>
          <p className="page-subtitle">{isCreateMode ? 'Cadastre um novo componente curricular.' : `${data.sigla || 'Sem sigla'} • ${data.matriz_curricular || 'Sem matriz curricular'}`}</p>
        </div>
        <div className="page-header__actions">
          <button type="button" className="btn btn--outline" onClick={() => navigate(isCreateMode ? '/ensino/componentes/' : `/componentes/${data.id}`)}>
            <ArrowLeft size={16} /> {isCreateMode ? 'Voltar para listagem' : 'Voltar para detalhes'}
          </button>
        </div>
      </div>

      <form className="dashboard-card componente-edit-form" onSubmit={onSubmit}>
        <div className="componente-edit-form__body">
          <div className="componente-edit-form__grid componente-edit-form__grid--wide">
            <label className="form-field">
              <span className="form-field__label">Matriz curricular</span>
              <select {...register('curso', { required: 'Selecione a matriz curricular.' })}>
                <option value="">Selecione...</option>
                {(opcoes?.matrizes_curriculares || []).map((item) => (
                  <option key={item.value} value={item.value}>{item.label}</option>
                ))}
              </select>
              {errors.curso ? <span className="form-field__error">{errors.curso.message}</span> : null}
            </label>

            <label className="form-field form-field--full">
              <span className="form-field__label">Descrição</span>
              <input {...register('descricao', { required: 'Informe a descrição.' })} />
              {errors.descricao ? <span className="form-field__error">{errors.descricao.message}</span> : null}
            </label>

            <label className="form-field form-field--full">
              <span className="form-field__label">Descrição no diploma e histórico</span>
              <input {...register('descricao_diploma_historico')} />
            </label>

            <label className="form-field">
              <span className="form-field__label">Abreviatura</span>
              <input {...register('abreviatura')} />
            </label>

            <label className="form-field">
              <span className="form-field__label">Sigla</span>
              <input {...register('sigla')} />
            </label>

            <label className="form-field">
              <span className="form-field__label">Tipo do componente</span>
              <input {...register('tipo_componente')} />
            </label>

            <label className="form-field">
              <span className="form-field__label">Diretoria</span>
              <input {...register('diretoria')} />
            </label>

            <label className="form-field">
              <span className="form-field__label">Nível de ensino</span>
              <input {...register('nivel_ensino')} />
            </label>

            <label className="form-field form-field--checkbox">
              <input type="checkbox" {...register('esta_ativo')} />
              <span>Está ativo</span>
            </label>

            <label className="form-field">
              <span className="form-field__label">Hora/relógio</span>
              <input type="number" min="0" {...register('carga_horaria', { valueAsNumber: true })} />
            </label>

            <label className="form-field">
              <span className="form-field__label">Hora/aula</span>
              <input type="number" min="0" {...register('hora_aula', { valueAsNumber: true })} />
            </label>

            <label className="form-field">
              <span className="form-field__label">Créditos</span>
              <input type="number" min="0" {...register('qtd_creditos', { valueAsNumber: true })} />
            </label>

            <label className="form-field">
              <span className="form-field__label">Grupo de atuação</span>
              <input {...register('grupo_atuacao')} />
            </label>

            <label className="form-field">
              <span className="form-field__label">Sigla do Q-Acadêmico</span>
              <input {...register('sigla_qacademico')} />
            </label>

            <label className="form-field form-field--full">
              <span className="form-field__label">Observação</span>
              <textarea rows="5" {...register('observacao')} />
            </label>
          </div>
        </div>

        <div className="componente-edit-form__actions">
          <button
            type="submit"
            className="btn btn--primary"
            disabled={saveMutation.isPending}
            onClick={() => { submitModeRef.current = 'view' }}
          >
            <Save size={16} /> Salvar
          </button>
          <button
            type="submit"
            className="btn btn--secondary"
            disabled={saveMutation.isPending}
            onClick={() => { submitModeRef.current = 'add' }}
          >
            <Save size={16} /> Salvar e adicionar outro(a)
          </button>
          <button
            type="submit"
            className="btn btn--outline"
            disabled={saveMutation.isPending}
            onClick={() => { submitModeRef.current = 'stay' }}
          >
            <Save size={16} /> Salvar e continuar editando
          </button>
          {!isCreateMode ? (
            <button
              type="button"
              className="btn btn--danger"
              disabled={deleteMutation.isPending}
              onClick={handleDelete}
            >
              <Trash2 size={16} /> Remover
            </button>
          ) : null}
        </div>
      </form>
    </div>
  )
}