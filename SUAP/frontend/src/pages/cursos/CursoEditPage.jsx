import { useEffect, useMemo, useRef } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useForm } from 'react-hook-form'
import toast from 'react-hot-toast'
import { ArrowLeft, Save, Trash2 } from 'lucide-react'
import { Link, useLocation, useNavigate, useParams } from 'react-router-dom'

import { areasCursoApi, cursosApi, eixosTecnologicosApi, unidadesApi } from '@/api/endpoints'
import { loadAllPaginatedResults } from '@/utils/loadAllPaginatedResults'

const DEFAULT_VALUES = {
  nome: '',
  sigla: '',
  unidade: '',
  area_curso: '',
  eixo_tecnologico: '',
  carga_horaria: '',
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

export default function CursoEditPage() {
  const location = useLocation()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const submitModeRef = useRef('view')
  const { cursoId } = useParams()
  const isCreateMode = !cursoId
  const isTechnicalCatalog = location.pathname.includes('/ensino/cursotecnico')
  const listPath = isTechnicalCatalog ? '/ensino/cursotecnico/' : '/ensino/cursoitinerante/'

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm({ defaultValues: DEFAULT_VALUES })

  const { data, isLoading, isError } = useQuery({
    queryKey: ['curso', 'detail-edit', cursoId],
    queryFn: () => cursosApi.get(cursoId).then((response) => response.data),
    enabled: !isCreateMode,
    staleTime: 0,
  })

  const { data: optionsData, isLoading: isLoadingOptions } = useQuery({
    queryKey: ['curso', 'edit-options', isTechnicalCatalog ? 'tecnico' : 'superior'],
    queryFn: async () => {
      const [unidades, areas, eixos] = await Promise.all([
        loadAllPaginatedResults((params) => unidadesApi.list(params)),
        loadAllPaginatedResults((params) => areasCursoApi.list(params)),
        loadAllPaginatedResults((params) => eixosTecnologicosApi.list(params)),
      ])

      return {
        unidades: unidades.sort((left, right) => left.nome.localeCompare(right.nome)),
        areas: areas.sort((left, right) => (left.descricao || '').localeCompare(right.descricao || '')),
        eixos: eixos.sort((left, right) => left.descricao.localeCompare(right.descricao)),
      }
    },
    staleTime: 60_000,
  })

  useEffect(() => {
    if (!data) {
      return
    }

    reset({
      nome: data.nome || '',
      sigla: data.sigla || '',
      unidade: data.unidade ? String(data.unidade) : '',
      area_curso: data.area_curso ? String(data.area_curso) : '',
      eixo_tecnologico: data.eixo_tecnologico || '',
      carga_horaria: typeof data.carga_horaria === 'number' ? String(data.carga_horaria) : '',
    })
  }, [data, reset])

  const saveMutation = useMutation({
    mutationFn: ({ id, payload }) => (id ? cursosApi.patch(id, payload) : cursosApi.create(payload)),
    onSuccess: async (response, variables) => {
      const savedId = response.data?.id || variables.id

      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ['cursos'] }),
        savedId ? queryClient.invalidateQueries({ queryKey: ['curso'] }) : Promise.resolve(),
      ])

      toast.success(isCreateMode ? 'Curso salvo com sucesso.' : 'Curso atualizado com sucesso.')

      if (submitModeRef.current === 'add') {
        reset(DEFAULT_VALUES)
        navigate(isTechnicalCatalog ? '/ensino/cursotecnico/novo' : '/ensino/cursoitinerante/novo')
        return
      }

      if (submitModeRef.current === 'stay' && savedId) {
        navigate(isTechnicalCatalog ? `/ensino/cursotecnico/${savedId}/editar` : `/ensino/cursoitinerante/${savedId}/editar`, { replace: true })
        return
      }

      navigate(listPath)
    },
    onError: (error) => {
      toast.error(getErrorMessage(error, isCreateMode ? 'Não foi possível criar o curso.' : 'Não foi possível salvar o curso.'))
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (id) => cursosApi.remove(id),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['cursos'] })
      toast.success('Curso removido com sucesso.')
      navigate(listPath)
    },
    onError: (error) => {
      toast.error(getErrorMessage(error, 'Não foi possível remover o curso.'))
    },
  })

  const title = useMemo(() => {
    if (isCreateMode) {
      return isTechnicalCatalog ? 'Novo curso técnico' : 'Novo curso itinerante'
    }
    return data?.nome || 'Editar curso'
  }, [data?.nome, isCreateMode, isTechnicalCatalog])

  if ((!isCreateMode && isLoading) || isLoadingOptions) {
    return (
      <div className="page page--wide">
        <div className="page-loader" role="status" aria-live="polite">
          <div className="spinner" />
          <span>Carregando curso...</span>
        </div>
      </div>
    )
  }

  if (!isCreateMode && (isError || !data)) {
    return (
      <div className="page page--wide">
        <div className="page-error">
          <h1 className="page-error__title">Não foi possível carregar o curso</h1>
          <p className="page-error__description">Verifique se o registro existe e tente novamente.</p>
        </div>
      </div>
    )
  }

  const unidades = optionsData?.unidades || []
  const areas = optionsData?.areas || []
  const eixos = optionsData?.eixos || []

  const onSubmit = handleSubmit(async (formData) => {
    const payload = {
      nome: formData.nome.trim(),
      sigla: formData.sigla.trim(),
      unidade: Number(formData.unidade),
      area_curso: formData.area_curso ? Number(formData.area_curso) : null,
      eixo_tecnologico: formData.eixo_tecnologico.trim(),
      carga_horaria: Number(formData.carga_horaria),
    }

    await saveMutation.mutateAsync({ id: data?.id, payload })
  })

  const handleDelete = () => {
    if (!window.confirm(`Deseja realmente remover o curso ${title}?`)) {
      return
    }

    deleteMutation.mutate(data.id)
  }

  return (
    <div className="page page--wide area-curso-edit-page">
      <nav className="profile-breadcrumb">
        <Link to="/dashboard">Início</Link>
        <span className="profile-breadcrumb__sep">&gt;</span>
        <Link to={listPath}>{isTechnicalCatalog ? 'Catálogo de cursos técnicos' : 'Cursos itinerantes'}</Link>
        <span className="profile-breadcrumb__sep">&gt;</span>
        <span>{isCreateMode ? title : `Editar ${title}`}</span>
      </nav>

      <div className="page-header area-cursos-page__header">
        <div>
          <h1 className="page-title">{isCreateMode ? title : `Editar ${title}`}</h1>
        </div>
        <div className="page-header__actions">
          <button type="button" className="btn btn--outline" onClick={() => navigate(listPath)}>
            <ArrowLeft size={16} /> Voltar para listagem
          </button>
        </div>
      </div>

      <form className="dashboard-card area-curso-edit-form" onSubmit={onSubmit}>
        <div className="area-curso-edit-form__rows">
          <div className="area-curso-edit-row">
            <label className="area-curso-edit-row__label">* Nome</label>
            <div className="area-curso-edit-row__field">
              <input {...register('nome', { required: 'Informe o nome do curso.' })} />
              {errors.nome ? <span className="form-field__error">{errors.nome.message}</span> : null}
            </div>
          </div>

          <div className="area-curso-edit-row">
            <label className="area-curso-edit-row__label">Sigla</label>
            <div className="area-curso-edit-row__field">
              <input {...register('sigla')} />
            </div>
          </div>

          <div className="area-curso-edit-row">
            <label className="area-curso-edit-row__label">* Unidade</label>
            <div className="area-curso-edit-row__field">
              <select {...register('unidade', { required: 'Selecione a unidade.' })}>
                <option value="">Selecione</option>
                {unidades.map((item) => (
                  <option key={item.id} value={item.id}>{item.nome}</option>
                ))}
              </select>
              {errors.unidade ? <span className="form-field__error">{errors.unidade.message}</span> : null}
            </div>
          </div>

          <div className="area-curso-edit-row">
            <label className="area-curso-edit-row__label">Área do curso</label>
            <div className="area-curso-edit-row__field">
              <select {...register('area_curso')}>
                <option value="">Sem área vinculada</option>
                {areas.map((item) => (
                  <option key={item.id} value={item.id}>{item.descricao}</option>
                ))}
              </select>
            </div>
          </div>

          <div className="area-curso-edit-row">
            <label className="area-curso-edit-row__label">{isTechnicalCatalog ? '* Eixo tecnológico' : 'Eixo tecnológico'}</label>
            <div className="area-curso-edit-row__field">
              <select
                {...register('eixo_tecnologico', {
                  validate: (value) => (isTechnicalCatalog && !value.trim() ? 'Selecione o eixo tecnológico.' : true),
                })}
              >
                <option value="">{isTechnicalCatalog ? 'Selecione' : 'Sem eixo tecnológico'}</option>
                {eixos.map((item) => (
                  <option key={item.id} value={item.descricao}>{item.descricao}</option>
                ))}
              </select>
              {errors.eixo_tecnologico ? <span className="form-field__error">{errors.eixo_tecnologico.message}</span> : null}
            </div>
          </div>

          <div className="area-curso-edit-row">
            <label className="area-curso-edit-row__label">* Carga horária (h)</label>
            <div className="area-curso-edit-row__field">
              <input type="number" min="1" step="1" {...register('carga_horaria', { required: 'Informe a carga horária.' })} />
              {errors.carga_horaria ? <span className="form-field__error">{errors.carga_horaria.message}</span> : null}
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