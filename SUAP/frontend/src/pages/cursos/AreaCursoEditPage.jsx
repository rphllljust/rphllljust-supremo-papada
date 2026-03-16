import { useEffect, useRef } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useForm } from 'react-hook-form'
import toast from 'react-hot-toast'
import { ArrowLeft, Save, Trash2 } from 'lucide-react'
import { Link, useNavigate, useParams } from 'react-router-dom'

import { areasCursoApi } from '@/api/endpoints'

const DEFAULT_VALUES = {
  codigo_cine: '',
  codigo_area_detalhada: '',
  codigo_area_especifica: '',
  codigo_area_geral: '',
  cine: '',
  area_detalhada: '',
  area_especifica: '',
  area_geral: '',
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

export default function AreaCursoEditPage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const submitModeRef = useRef('view')
  const { areaCursoId } = useParams()
  const isCreateMode = !areaCursoId

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm({ defaultValues: DEFAULT_VALUES })

  const { data, isLoading, isError } = useQuery({
    queryKey: ['areas-curso', 'detail', areaCursoId],
    queryFn: () => areasCursoApi.get(areaCursoId).then((response) => response.data),
    enabled: !isCreateMode,
    staleTime: 0,
  })

  useEffect(() => {
    if (!data) {
      return
    }

    reset({
      codigo_cine: data.codigo_cine || '',
      codigo_area_detalhada: data.codigo_area_detalhada || '',
      codigo_area_especifica: data.codigo_area_especifica || '',
      codigo_area_geral: data.codigo_area_geral || '',
      cine: data.cine || '',
      area_detalhada: data.area_detalhada || '',
      area_especifica: data.area_especifica || '',
      area_geral: data.area_geral || '',
    })
  }, [data, reset])

  const saveMutation = useMutation({
    mutationFn: ({ id, payload }) => (id ? areasCursoApi.patch(id, payload) : areasCursoApi.create(payload)),
    onSuccess: async (response, variables) => {
      const savedId = response.data?.id || variables.id

      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ['areas-curso'] }),
        savedId ? queryClient.invalidateQueries({ queryKey: ['areas-curso', 'detail', savedId] }) : Promise.resolve(),
      ])

      toast.success(isCreateMode ? 'Área de curso criada com sucesso.' : 'Área de curso atualizada com sucesso.')

      if (submitModeRef.current === 'add') {
        reset(DEFAULT_VALUES)
        navigate('/ensino/cursoinicial/nova')
        return
      }

      if (submitModeRef.current === 'stay') {
        if (isCreateMode && savedId) {
          navigate(`/ensino/cursoinicial/${savedId}/editar`, { replace: true })
        }
        return
      }

      if (savedId) {
        navigate(`/ensino/cursoinicial/${savedId}`)
      }
    },
    onError: (error) => {
      toast.error(getErrorMessage(error, isCreateMode ? 'Não foi possível criar a área de curso.' : 'Não foi possível salvar a área de curso.'))
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (id) => areasCursoApi.remove(id),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['areas-curso'] })
      toast.success('Área de curso removida com sucesso.')
      navigate('/ensino/cursoinicial/')
    },
    onError: (error) => {
      toast.error(getErrorMessage(error, 'Não foi possível remover a área de curso.'))
    },
  })

  if (!isCreateMode && isLoading) {
    return (
      <div className="page page--wide">
        <div className="page-loader" role="status" aria-live="polite">
          <div className="spinner" />
          <span>Carregando área de curso...</span>
        </div>
      </div>
    )
  }

  if (!isCreateMode && (isError || !data)) {
    return (
      <div className="page page--wide">
        <div className="page-error">
          <h1 className="page-error__title">Não foi possível carregar a área de curso</h1>
          <p className="page-error__description">Verifique se o registro existe e tente novamente.</p>
        </div>
      </div>
    )
  }

  const titulo = isCreateMode ? 'Nova área de curso' : [data.codigo_cine, data.cine || data.descricao].filter(Boolean).join(' - ')

  const onSubmit = handleSubmit(async (formData) => {
    const payload = {
      codigo_cine: formData.codigo_cine.trim(),
      codigo_area_detalhada: formData.codigo_area_detalhada.trim(),
      codigo_area_especifica: formData.codigo_area_especifica.trim(),
      codigo_area_geral: formData.codigo_area_geral.trim(),
      cine: formData.cine.trim(),
      area_detalhada: formData.area_detalhada.trim(),
      area_especifica: formData.area_especifica.trim(),
      area_geral: formData.area_geral.trim(),
    }

    await saveMutation.mutateAsync({ id: data?.id, payload })
  })

  const handleDelete = () => {
    if (!window.confirm(`Deseja realmente remover a área de curso ${titulo}?`)) {
      return
    }

    deleteMutation.mutate(data.id)
  }

  return (
    <div className="page page--wide area-curso-edit-page">
      <nav className="profile-breadcrumb">
        <Link to="/dashboard">Início</Link>
        <span className="profile-breadcrumb__sep">&gt;</span>
        <Link to="/ensino/cursoinicial/">Cursos iniciais</Link>
        {isCreateMode ? (
          <>
            <span className="profile-breadcrumb__sep">&gt;</span>
            <span>{titulo}</span>
          </>
        ) : (
          <>
            <span className="profile-breadcrumb__sep">&gt;</span>
            <Link to={`/ensino/cursoinicial/${data.id}`}>{titulo}</Link>
            <span className="profile-breadcrumb__sep">&gt;</span>
            <span>Editar {titulo}</span>
          </>
        )}
      </nav>

      <div className="page-header area-cursos-page__header">
        <div>
          <h1 className="page-title">{isCreateMode ? titulo : `Editar ${titulo}`}</h1>
        </div>
        <div className="page-header__actions">
          <button type="button" className="btn btn--outline" onClick={() => navigate(isCreateMode ? '/ensino/cursoinicial/' : `/ensino/cursoinicial/${data.id}`)}>
            <ArrowLeft size={16} /> {isCreateMode ? 'Voltar para listagem' : 'Voltar para detalhes'}
          </button>
        </div>
      </div>

      <form className="dashboard-card area-curso-edit-form" onSubmit={onSubmit}>
        <div className="area-curso-edit-form__rows">
          <div className="area-curso-edit-row">
            <label className="area-curso-edit-row__label">* Código CINE</label>
            <div className="area-curso-edit-row__field">
              <input {...register('codigo_cine', { required: 'Informe o código CINE.' })} />
              {errors.codigo_cine ? <span className="form-field__error">{errors.codigo_cine.message}</span> : null}
            </div>
          </div>
          <div className="area-curso-edit-row">
            <label className="area-curso-edit-row__label">* Código da área detalhada</label>
            <div className="area-curso-edit-row__field">
              <input {...register('codigo_area_detalhada', { required: 'Informe o código da área detalhada.' })} />
              {errors.codigo_area_detalhada ? <span className="form-field__error">{errors.codigo_area_detalhada.message}</span> : null}
            </div>
          </div>
          <div className="area-curso-edit-row">
            <label className="area-curso-edit-row__label">* Código da área específica</label>
            <div className="area-curso-edit-row__field">
              <input {...register('codigo_area_especifica', { required: 'Informe o código da área específica.' })} />
              {errors.codigo_area_especifica ? <span className="form-field__error">{errors.codigo_area_especifica.message}</span> : null}
            </div>
          </div>
          <div className="area-curso-edit-row">
            <label className="area-curso-edit-row__label">* Código da área geral</label>
            <div className="area-curso-edit-row__field">
              <input {...register('codigo_area_geral', { required: 'Informe o código da área geral.' })} />
              {errors.codigo_area_geral ? <span className="form-field__error">{errors.codigo_area_geral.message}</span> : null}
            </div>
          </div>
          <div className="area-curso-edit-row">
            <label className="area-curso-edit-row__label">* CINE</label>
            <div className="area-curso-edit-row__field">
              <input {...register('cine', { required: 'Informe a CINE.' })} />
              {errors.cine ? <span className="form-field__error">{errors.cine.message}</span> : null}
            </div>
          </div>
          <div className="area-curso-edit-row">
            <label className="area-curso-edit-row__label">* Área detalhada</label>
            <div className="area-curso-edit-row__field">
              <input {...register('area_detalhada', { required: 'Informe a área detalhada.' })} />
              {errors.area_detalhada ? <span className="form-field__error">{errors.area_detalhada.message}</span> : null}
            </div>
          </div>
          <div className="area-curso-edit-row">
            <label className="area-curso-edit-row__label">* Área específica</label>
            <div className="area-curso-edit-row__field">
              <input {...register('area_especifica', { required: 'Informe a área específica.' })} />
              {errors.area_especifica ? <span className="form-field__error">{errors.area_especifica.message}</span> : null}
            </div>
          </div>
          <div className="area-curso-edit-row">
            <label className="area-curso-edit-row__label">* Área geral</label>
            <div className="area-curso-edit-row__field">
              <input {...register('area_geral', { required: 'Informe a área geral.' })} />
              {errors.area_geral ? <span className="form-field__error">{errors.area_geral.message}</span> : null}
            </div>
          </div>
        </div>

        <div className="componente-edit-form__actions">
          <button type="submit" className="btn btn--primary" disabled={saveMutation.isPending} onClick={() => { submitModeRef.current = 'view' }}>
            <Save size={16} /> Salvar
          </button>
          <button type="submit" className="btn btn--secondary" disabled={saveMutation.isPending} onClick={() => { submitModeRef.current = 'add' }}>
            <Save size={16} /> Salvar e adicionar outro(a)
          </button>
          <button type="submit" className="btn btn--outline" disabled={saveMutation.isPending} onClick={() => { submitModeRef.current = 'stay' }}>
            <Save size={16} /> Salvar e continuar editando
          </button>
          {!isCreateMode ? (
            <button type="button" className="btn btn--danger" disabled={deleteMutation.isPending} onClick={handleDelete}>
              <Trash2 size={16} /> Remover
            </button>
          ) : null}
        </div>
      </form>
    </div>
  )
}