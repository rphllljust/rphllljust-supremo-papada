import { useEffect, useMemo, useRef } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useForm } from 'react-hook-form'
import toast from 'react-hot-toast'
import { ArrowLeft, Save, Trash2 } from 'lucide-react'
import { Link, useLocation, useNavigate, useParams } from 'react-router-dom'

import { cursosApi, eixosTecnologicosApi, unidadesApi, moodleIntegrationApi } from '@/api/endpoints'
import { loadAllPaginatedResults } from '@/utils/loadAllPaginatedResults'

const DEFAULT_VALUES = {
  nome: '',
  sigla: '',
  unidade: '',
  eixo_tecnologico: '',
  carga_horaria: '',
  moodle_category: '',
}

const EIXOS_OFICIAIS = [
  'Ambiente e Saúde',
  'Controle e Processos Industriais',
  'Desenvolvimento Educacional e Social',
  'Gestão e Negócios',
  'Informação e Comunicação',
  'Infraestrutura',
  'Militar',
  'Produção Alimentícia',
  'Produção Cultural e Design',
  'Produção Industrial',
  'Recursos Naturais',
  'Segurança',
  'Turismo, Hospitalidade e Lazer',
]

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
  const isInitialCatalog = location.pathname.includes('/ensino/cursoinicial')
  const catalogCourseType = isTechnicalCatalog ? 'tecnico' : (isInitialCatalog ? 'formacao_inicial' : 'itinerante')
  const catalogMeta = isTechnicalCatalog
    ? {
        listPath: '/ensino/cursotecnico/',
        createPath: '/ensino/cursotecnico/novo',
        editPathBuilder: (savedId) => `/ensino/cursotecnico/${savedId}/editar`,
        titleCreate: 'Novo curso técnico',
        titleList: 'Catálogo de cursos técnicos',
        optionsScope: 'tecnico',
      }
    : isInitialCatalog
      ? {
          listPath: '/ensino/cursoinicial/',
          createPath: '/ensino/cursoinicial/novo',
          editPathBuilder: (savedId) => `/ensino/cursoinicial/${savedId}/editar`,
          titleCreate: 'Novo curso inicial',
          titleList: 'Cursos iniciais',
          optionsScope: 'inicial',
        }
      : {
          listPath: '/ensino/cursoitinerante/',
          createPath: '/ensino/cursoitinerante/novo',
          editPathBuilder: (savedId) => `/ensino/cursoitinerante/${savedId}/editar`,
          titleCreate: 'Novo curso itinerante',
          titleList: 'Cursos itinerantes',
          optionsScope: 'itinerante',
        }
  // Se veio de um fluxo externo (ex: moodle-categorias-cursos), retorna para lá
  const fromPath = location.state?.from
  const listPath = fromPath || catalogMeta.listPath
  const openedFromMoodlePanel = Boolean(
    fromPath
      && (
        String(fromPath).includes('/ensino/moodle-categorias-cursos')
        || String(fromPath).includes('/ti/moodle/catalogo')
      )
  )

  const {
    register,
    handleSubmit,
    reset,
    setValue,
    getValues,
    formState: { errors },
  } = useForm({ defaultValues: DEFAULT_VALUES })

  const { data, isLoading, isError } = useQuery({
    queryKey: ['curso', 'detail-edit', cursoId],
    queryFn: () => cursosApi.get(cursoId).then((response) => response.data),
    enabled: !isCreateMode,
    staleTime: 0,
  })

  const { data: optionsData, isLoading: isLoadingOptions } = useQuery({
    queryKey: ['curso', 'edit-options', catalogMeta.optionsScope],
    queryFn: async () => {
      const [unidades, eixos] = await Promise.all([
        loadAllPaginatedResults((params) => unidadesApi.list(params)),
        loadAllPaginatedResults((params) => eixosTecnologicosApi.list(params)),
      ])

      return {
        unidades: unidades.sort((left, right) => left.nome.localeCompare(right.nome)),
        eixos: eixos.sort((left, right) => left.descricao.localeCompare(right.descricao)),
      }
    },
    staleTime: 60_000,
  })

  // Sempre registrar o hook de categorias do Moodle aqui para manter a ordem de hooks
  const { data: moodleCatsResp } = useQuery({ queryKey: ['moodle-categorias'], queryFn: () => moodleIntegrationApi.getCategorias(), enabled: isInitialCatalog || openedFromMoodlePanel, staleTime: 5 * 60 * 1000 })

  const { data: moodleCourseMirrorResp } = useQuery({
    queryKey: ['moodle-cursos', 'edit-detail', data?.moodle_course_id],
    queryFn: () => moodleIntegrationApi.getCursosByField('id', data.moodle_course_id).then((response) => response.data),
    enabled: !isCreateMode && isInitialCatalog && Boolean(data?.moodle_course_id),
    staleTime: 5 * 60 * 1000,
  })

  const moodleCategories = Array.isArray(moodleCatsResp?.data)
    ? moodleCatsResp.data
    : Array.isArray(moodleCatsResp?.data?.results)
      ? moodleCatsResp.data.results
      : Array.isArray(moodleCatsResp)
        ? moodleCatsResp
        : Array.isArray(moodleCatsResp?.results)
          ? moodleCatsResp.results
          : []
  const mirroredCourse = Array.isArray(moodleCourseMirrorResp?.data)
    ? moodleCourseMirrorResp.data[0]
    : Array.isArray(moodleCourseMirrorResp?.results)
      ? moodleCourseMirrorResp.results[0]
      : Array.isArray(moodleCourseMirrorResp)
        ? moodleCourseMirrorResp[0]
        : moodleCourseMirrorResp?.data?.[0] || moodleCourseMirrorResp?.results?.[0] || null
  const currentMoodleCategoryId = Number(location.state?.categoryId || mirroredCourse?.categoryid || 0)
  const selectedMoodleCategory = useMemo(() => {
    const selectedId = currentMoodleCategoryId
    if (!selectedId || moodleCategories.length === 0) {
      return null
    }

    return moodleCategories.find((category) => Number(category?.id) === selectedId) || null
  }, [currentMoodleCategoryId, moodleCategories])

  useEffect(() => {
    if (!data) {
      return
    }

    reset({
      nome: data.nome || '',
      sigla: data.sigla || '',
      unidade: data.unidade ? String(data.unidade) : '',
      eixo_tecnologico: data.eixo_tecnologico || '',
      carga_horaria: typeof data.carga_horaria === 'number' ? String(data.carga_horaria) : '',
      moodle_category: '',
    })
  }, [data, reset])

  useEffect(() => {
    if (!currentMoodleCategoryId) {
      return
    }

    if (String(getValues('moodle_category') || '').trim()) {
      return
    }

    setValue('moodle_category', String(currentMoodleCategoryId), {
      shouldDirty: false,
      shouldTouch: false,
      shouldValidate: false,
    })
  }, [currentMoodleCategoryId, getValues, setValue])

  const saveMutation = useMutation({
    mutationFn: ({ id, payload }) => (id ? cursosApi.patch(id, payload) : cursosApi.create(payload)),
    onSuccess: async (response, variables) => {
      const savedId = response.data?.id || variables.id

      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ['cursos'] }),
        savedId ? queryClient.invalidateQueries({ queryKey: ['curso'] }) : Promise.resolve(),
      ])

      toast.success(
        isCreateMode
          ? 'Curso salvo com sucesso.'
          : isInitialCatalog
            ? 'Curso sincronizado com o Moodle e salvo com sucesso.'
            : 'Curso atualizado com sucesso.'
      )

      if (submitModeRef.current === 'add') {
        reset(DEFAULT_VALUES)
        navigate(catalogMeta.createPath)
        return
      }

      if (submitModeRef.current === 'stay' && savedId) {
        navigate(catalogMeta.editPathBuilder(savedId), { replace: true })
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
      return catalogMeta.titleCreate
    }
    return data?.nome || 'Editar curso'
  }, [catalogMeta.titleCreate, data?.nome, isCreateMode])

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
  const eixosApi = optionsData?.eixos || []
  const eixosMap = new Map()
  EIXOS_OFICIAIS.forEach((descricao) => eixosMap.set(descricao, { id: descricao, descricao }))
  eixosApi.forEach((item) => {
    if (!eixosMap.has(item.descricao)) {
      eixosMap.set(item.descricao, { id: item.id, descricao: item.descricao })
    }
  })
  const eixos = Array.from(eixosMap.values())
  const showMoodleCategoryField = isInitialCatalog || (!isCreateMode && openedFromMoodlePanel)

  const onSubmit = handleSubmit(async (formData) => {
    const payload = {
      tipo_curso: catalogCourseType,
      nome: formData.nome.trim(),
      sigla: formData.sigla.trim(),
      unidade: Number(formData.unidade),
      eixo_tecnologico: formData.eixo_tecnologico.trim(),
      carga_horaria: Number(formData.carga_horaria),
    }

    // When creating a course initial, create it in Moodle first so the category binding is real.
    const initialCategoryId = Number(formData.moodle_category || currentMoodleCategoryId || 0)

    if (isInitialCatalog && !initialCategoryId) {
      toast.error('Selecione uma categoria do Moodle antes de criar ou atualizar o curso.')
      return
    }

    if (isCreateMode && showMoodleCategoryField) {
      const basePayload = {
        unidade_codigo: 'sede',
        persistir_espelho_local: true,
        integrar_catalogo_interno: true,
        params: {
          courses: [
            {
              fullname: formData.nome.trim(),
              shortname: formData.sigla.trim() || formData.nome.trim().slice(0, 16),
              categoryid: initialCategoryId,
              idnumber: formData.sigla.trim(),
              summary: formData.nome.trim(),
            },
          ],
        },
      }

      try {
        await moodleIntegrationApi.createCursos(basePayload)
        toast.success('Curso criado no Moodle e importado para o SUAP.')

        queryClient.invalidateQueries({ queryKey: ['moodle-cursos'] })
        queryClient.invalidateQueries({ queryKey: ['moodle-categorias'] })
        queryClient.invalidateQueries({ queryKey: ['cursos'] })
        navigate(location.state?.from || '/ti/moodle/catalogo/')
        return
      } catch (err) {
        const message = err?.response?.data?.detail || err?.message || 'Erro ao criar/atualizar curso no Moodle.'
        toast.error(String(message))
        return
      }
    }

    if (isInitialCatalog && !isCreateMode) {
      const moodleCourseId = Number(data?.moodle_course_id || 0)
      const basePayload = {
        unidade_codigo: 'sede',
        persistir_espelho_local: true,
        integrar_catalogo_interno: true,
        params: {
          courses: [
            {
              fullname: formData.nome.trim(),
              shortname: formData.sigla.trim() || formData.nome.trim().slice(0, 16),
              categoryid: initialCategoryId || undefined,
              idnumber: formData.sigla.trim(),
              summary: formData.nome.trim(),
            },
          ],
        },
      }

      if (moodleCourseId) {
        basePayload.params.courses[0].id = moodleCourseId
        await moodleIntegrationApi.updateCursos(basePayload)
      } else {
        await moodleIntegrationApi.createCursos(basePayload)
      }
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
        <Link to={catalogMeta.listPath}>{catalogMeta.titleList}</Link>
        <span className="profile-breadcrumb__sep">&gt;</span>
        <span>{isCreateMode ? title : `Editar ${title}`}</span>
      </nav>

      <div className="page-header area-cursos-page__header">
        <div>
          <h1 className="page-title">{isCreateMode ? title : `Editar ${title}`}</h1>
        </div>
        <div className="page-header__actions">
          <button type="button" className="btn btn--outline" onClick={() => navigate(listPath)}>
            <ArrowLeft size={16} /> Voltar
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
            <label className="area-curso-edit-row__label">* Sigla</label>
            <div className="area-curso-edit-row__field">
              <input {...register('sigla', { required: 'Informe a sigla do curso.' })} />
              {errors.sigla ? <span className="form-field__error">{errors.sigla.message}</span> : null}
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
            <label className="area-curso-edit-row__label">* Eixo tecnológico</label>
            <div className="area-curso-edit-row__field">
              <select
                {...register('eixo_tecnologico', {
                  required: 'Selecione o eixo tecnológico.',
                })}
              >
                <option value="">Selecione</option>
                {eixos.map((item) => (
                  <option key={item.id} value={item.descricao}>
                    {item.descricao}
                  </option>
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

          {showMoodleCategoryField ? (
            <div className="area-curso-edit-row">
              <label className="area-curso-edit-row__label">* Vínculo Categoria Moodle</label>
              <div className="area-curso-edit-row__field">
                <select
                  {...register('moodle_category', {
                    required: 'Selecione uma categoria do Moodle.',
                    validate: (value) => (Number(value || 0) > 0 ? true : 'Selecione uma categoria do Moodle.'),
                  })}
                >
                  <option value="">— Selecionar categoria —</option>
                  {moodleCategories.map((mc) => (
                    <option key={mc.id} value={mc.id}>{mc.name || mc.nome || `ID ${mc.id}`}</option>
                  ))}
                </select>
                {selectedMoodleCategory ? (
                  <div style={{ marginTop: 6, fontSize: 12, color: '#666' }}>
                    Categoria selecionada: <strong>{selectedMoodleCategory.name || selectedMoodleCategory.nome || `ID ${selectedMoodleCategory.id}`}</strong>
                  </div>
                ) : null}
                {errors.moodle_category ? <span className="form-field__error">{errors.moodle_category.message}</span> : null}
              </div>
            </div>
          ) : null}
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
