import { useEffect } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useForm } from 'react-hook-form'
import toast from 'react-hot-toast'
import { ArrowLeft, Save } from 'lucide-react'
import { Link, useNavigate, useParams } from 'react-router-dom'

import { cursosApi, matrizesCurricularesApi } from '@/api/endpoints'
import { loadAllPaginatedResults } from '@/utils/loadAllPaginatedResults'

const DEFAULT_VALUES = {
  curso_base: '',
  nome: '',
  ano_referencia: new Date().getFullYear(),
  versao: '1.0',
  status: 'RASCUNHO',
  ativa: true,
  descricao: '',
}

export default function MatrizCurricularEditPage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { matrizId } = useParams()
  const isCreateMode = !matrizId

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm({ defaultValues: DEFAULT_VALUES })

  const { data, isLoading, isError } = useQuery({
    queryKey: ['matriz-curricular', 'edit', matrizId],
    queryFn: () => matrizesCurricularesApi.get(matrizId).then((response) => response.data),
    enabled: !isCreateMode,
    staleTime: 0,
  })

  const { data: technicalCourses = [], isLoading: isLoadingCourses } = useQuery({
    queryKey: ['curso', 'tecnicos-options'],
    queryFn: () => loadAllPaginatedResults((params) => cursosApi.list({ ...params, tipo_curso: 'tecnico' })),
    staleTime: 60_000,
  })

  useEffect(() => {
    if (!data) {
      return
    }

    reset({
      curso_base: data.curso_base ? String(data.curso_base) : '',
      nome: data.nome || '',
      ano_referencia: data.ano_referencia || new Date().getFullYear(),
      versao: data.versao || '1.0',
      status: data.status || 'RASCUNHO',
      ativa: data.ativa ?? true,
      descricao: data.descricao || '',
    })
  }, [data, reset])

  const saveMutation = useMutation({
    mutationFn: ({ id, payload }) => (id ? matrizesCurricularesApi.patch(id, payload) : matrizesCurricularesApi.create(payload)),
    onSuccess: async (response) => {
      const savedId = response?.data?.id || matrizId
      await queryClient.invalidateQueries({ queryKey: ['matrizes-curriculares'] })
      if (savedId) {
        await queryClient.invalidateQueries({ queryKey: ['matriz-curricular', savedId] })
      }
      toast.success(isCreateMode ? 'Matriz curricular criada com sucesso.' : 'Matriz curricular atualizada com sucesso.')
      navigate(savedId ? `/ensino/matrizes-curriculares/${savedId}` : '/ensino/matrizes-curriculares/')
    },
    onError: (error) => {
      const detail = error?.response?.data
      const firstMessage = detail?.detail || Object.values(detail || {})?.[0]?.[0] || 'Não foi possível salvar a matriz curricular.'
      toast.error(firstMessage)
    },
  })

  if ((!isCreateMode && isLoading) || isLoadingCourses) {
    return (
      <div className="page page--wide">
        <div className="page-loader" role="status" aria-live="polite">
          <div className="spinner" />
          <span>Carregando formulário da matriz...</span>
        </div>
      </div>
    )
  }

  if (!isCreateMode && (isError || !data)) {
    return (
      <div className="page page--wide">
        <div className="page-error">
          <h1 className="page-error__title">Não foi possível carregar a matriz curricular</h1>
          <p className="page-error__description">Verifique se o registro existe e tente novamente.</p>
        </div>
      </div>
    )
  }

  const onSubmit = handleSubmit(async (formData) => {
    await saveMutation.mutateAsync({
      id: matrizId,
      payload: {
        curso_base: Number(formData.curso_base),
        nome: formData.nome.trim(),
        ano_referencia: Number(formData.ano_referencia),
        versao: formData.versao.trim(),
        status: formData.status,
        ativa: Boolean(formData.ativa),
        descricao: formData.descricao.trim(),
      },
    })
  })

  return (
    <div className="page page--wide matrix-page">
      <nav className="profile-breadcrumb">
        <Link to="/dashboard">Início</Link>
        <span className="profile-breadcrumb__sep">&gt;</span>
        <Link to="/ensino/matrizes-curriculares/">Matrizes Curriculares</Link>
        <span className="profile-breadcrumb__sep">&gt;</span>
        <span>{isCreateMode ? 'Nova matriz' : 'Editar matriz'}</span>
      </nav>

      <div className="page-header">
        <div>
          <h1 className="page-title">{isCreateMode ? 'Nova matriz curricular' : `Editar ${data.nome}`}</h1>
          <p className="page-subtitle">Cadastre a matriz curricular explícita sem remover os vínculos legados do curso e dos componentes.</p>
        </div>
        <div className="page-header__actions">
          <button type="button" className="btn btn--outline" onClick={() => navigate(isCreateMode ? '/ensino/matrizes-curriculares/' : `/ensino/matrizes-curriculares/${matrizId}`)}>
            <ArrowLeft size={16} /> Voltar
          </button>
        </div>
      </div>

      <form className="dashboard-card matrix-form" onSubmit={onSubmit}>
        <div className="matrix-form__grid">
          <label className="matrix-form__field matrix-form__field--full">
            <span>Curso base técnico</span>
            <select {...register('curso_base', { required: 'Selecione o curso base da matriz.' })}>
              <option value="">Selecione</option>
              {technicalCourses.map((curso) => <option key={curso.id} value={curso.id}>{curso.nome}</option>)}
            </select>
            {errors.curso_base ? <span className="form-field__error">{errors.curso_base.message}</span> : null}
          </label>

          <label className="matrix-form__field matrix-form__field--full">
            <span>Nome</span>
            <input {...register('nome', { required: 'Informe o nome da matriz curricular.' })} />
            {errors.nome ? <span className="form-field__error">{errors.nome.message}</span> : null}
          </label>

          <label className="matrix-form__field">
            <span>Ano de referência</span>
            <input type="number" min="2000" max="2100" {...register('ano_referencia', { required: 'Informe o ano de referência.', valueAsNumber: true })} />
            {errors.ano_referencia ? <span className="form-field__error">{errors.ano_referencia.message}</span> : null}
          </label>

          <label className="matrix-form__field">
            <span>Versão</span>
            <input {...register('versao', { required: 'Informe a versão da matriz.' })} />
            {errors.versao ? <span className="form-field__error">{errors.versao.message}</span> : null}
          </label>

          <label className="matrix-form__field">
            <span>Status</span>
            <select {...register('status', { required: 'Selecione o status.' })}>
              <option value="RASCUNHO">Rascunho</option>
              <option value="VIGENTE">Vigente</option>
              <option value="ENCERRADA">Encerrada</option>
            </select>
          </label>

          <label className="matrix-form__field matrix-form__field--checkbox">
            <span>Ativa</span>
            <input type="checkbox" {...register('ativa')} />
          </label>

          <label className="matrix-form__field matrix-form__field--full">
            <span>Descrição</span>
            <textarea rows="5" {...register('descricao')} />
          </label>
        </div>

        <div className="matrix-form__actions">
          <button type="submit" className="btn btn--primary" disabled={saveMutation.isPending}>
            <Save size={16} /> {saveMutation.isPending ? 'Salvando...' : 'Salvar matriz'}
          </button>
        </div>
      </form>
    </div>
  )
}