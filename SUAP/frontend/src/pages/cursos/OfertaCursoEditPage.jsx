import { useEffect, useMemo } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useForm } from 'react-hook-form'
import toast from 'react-hot-toast'
import { ArrowLeft, Save } from 'lucide-react'
import { Link, useNavigate, useParams, useSearchParams } from 'react-router-dom'

import { cursosApi, matrizesCurricularesApi, ofertasApi, unidadesApi } from '@/api/endpoints'
import { loadAllPaginatedResults } from '@/utils/loadAllPaginatedResults'

const DEFAULT_VALUES = {
  curso_base_id: '',
  matriz_curricular_id: '',
  polo_id: '',
  calendario_letivo_id: '',
  nome: '',
  codigo_turma: '',
  ano_oferta: new Date().getFullYear(),
  periodo_letivo: '1',
  turno: 'NOITE',
  vagas_totais: 0,
  vagas_ocupadas: 0,
  status: 'PLANEJADA',
  observacao: '',
}

function getErrorMessage(error, fallback) {
  const detail = error?.response?.data
  if (!detail) {
    return fallback
  }
  if (typeof detail.detail === 'string') {
    return detail.detail
  }
  const firstValue = Object.values(detail)[0]
  if (Array.isArray(firstValue)) {
    return firstValue[0]
  }
  return firstValue || fallback
}

export default function OfertaCursoEditPage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { ofertaId } = useParams()
  const [searchParams] = useSearchParams()
  const isCreateMode = !ofertaId

  const {
    register,
    handleSubmit,
    reset,
    watch,
    setValue,
    formState: { errors },
  } = useForm({ defaultValues: DEFAULT_VALUES })

  const selectedCourseId = watch('curso_base_id')

  const { data: ofertaData, isLoading, isError } = useQuery({
    queryKey: ['oferta-curso', 'edit', ofertaId],
    queryFn: () => ofertasApi.get(ofertaId).then((response) => response.data),
    enabled: !isCreateMode,
    staleTime: 0,
  })

  const { data: technicalCourses = [], isLoading: isLoadingCourses } = useQuery({
    queryKey: ['ofertas-form', 'technical-courses'],
    queryFn: () => loadAllPaginatedResults((params) => cursosApi.list({ ...params, tipo_curso: 'tecnico' })),
    staleTime: 60_000,
  })

  const { data: polos = [], isLoading: isLoadingPolos } = useQuery({
    queryKey: ['ofertas-form', 'polos'],
    queryFn: () => loadAllPaginatedResults((params) => unidadesApi.list(params)),
    staleTime: 60_000,
  })

  const { data: matrizes = [], isLoading: isLoadingMatrizes } = useQuery({
    queryKey: ['ofertas-form', 'matrizes', selectedCourseId],
    queryFn: () => loadAllPaginatedResults((params) => matrizesCurricularesApi.list({ ...params, curso_base: selectedCourseId || undefined })),
    enabled: Boolean(selectedCourseId),
    staleTime: 60_000,
  })

  const { data: calendarios = [], isLoading: isLoadingCalendarios } = useQuery({
    queryKey: ['ofertas-form', 'calendarios', selectedCourseId],
    queryFn: () => cursosApi.calendarios(selectedCourseId).then((response) => response.data.results || response.data || []),
    enabled: Boolean(selectedCourseId),
    staleTime: 60_000,
  })

  const defaultQueryCourse = searchParams.get('curso_base') || ''
  const defaultQueryMatrix = searchParams.get('matriz_curricular') || ''

  useEffect(() => {
    if (!isCreateMode || !defaultQueryCourse) {
      return
    }
    setValue('curso_base_id', defaultQueryCourse, { shouldDirty: false })
    if (defaultQueryMatrix) {
      setValue('matriz_curricular_id', defaultQueryMatrix, { shouldDirty: false })
    }
  }, [defaultQueryCourse, defaultQueryMatrix, isCreateMode, setValue])

  useEffect(() => {
    if (!ofertaData) {
      return
    }

    reset({
      curso_base_id: ofertaData.curso_base_id ? String(ofertaData.curso_base_id) : '',
      matriz_curricular_id: ofertaData.matriz_curricular_id ? String(ofertaData.matriz_curricular_id) : '',
      polo_id: ofertaData.polo_id ? String(ofertaData.polo_id) : '',
      calendario_letivo_id: ofertaData.calendario_letivo_id ? String(ofertaData.calendario_letivo_id) : '',
      nome: ofertaData.nome || '',
      codigo_turma: ofertaData.codigo_turma || '',
      ano_oferta: ofertaData.ano_oferta || new Date().getFullYear(),
      periodo_letivo: ofertaData.periodo_letivo || '1',
      turno: ofertaData.turno || 'NOITE',
      vagas_totais: ofertaData.vagas_totais ?? 0,
      vagas_ocupadas: ofertaData.vagas_ocupadas ?? 0,
      status: ofertaData.status || 'PLANEJADA',
      observacao: ofertaData.observacao || '',
    })
  }, [ofertaData, reset])

  useEffect(() => {
    if (!isCreateMode || !matrizes.length) {
      return
    }
    if (defaultQueryMatrix) {
      return
    }
    const vigente = matrizes.find((matriz) => matriz.status === 'VIGENTE')
    if (vigente) {
      setValue('matriz_curricular_id', String(vigente.id), { shouldDirty: false })
    }
  }, [defaultQueryMatrix, isCreateMode, matrizes, setValue])

  useEffect(() => {
    if (!isCreateMode || !calendarios.length) {
      return
    }
    setValue('calendario_letivo_id', String(calendarios[0].id), { shouldDirty: false })
  }, [calendarios, isCreateMode, setValue])

  const saveMutation = useMutation({
    mutationFn: ({ id, payload }) => (id ? ofertasApi.patch(id, payload) : ofertasApi.create(payload)),
    onSuccess: async (response) => {
      const savedId = response?.data?.id || ofertaId
      await queryClient.invalidateQueries({ queryKey: ['ofertas-cursos'] })
      if (savedId) {
        await queryClient.invalidateQueries({ queryKey: ['oferta-curso', savedId] })
      }
      toast.success(isCreateMode ? 'Oferta criada com sucesso.' : 'Oferta atualizada com sucesso.')
      navigate(savedId ? `/ensino/ofertas/${savedId}` : '/ensino/ofertas/')
    },
    onError: (error) => {
      toast.error(getErrorMessage(error, 'Não foi possível salvar a oferta.'))
    },
  })

  const courseOptions = useMemo(() => technicalCourses.sort((left, right) => left.nome.localeCompare(right.nome)), [technicalCourses])
  const poloOptions = useMemo(() => polos.sort((left, right) => left.nome.localeCompare(right.nome)), [polos])

  if ((!isCreateMode && isLoading) || isLoadingCourses || isLoadingPolos || isLoadingMatrizes || isLoadingCalendarios) {
    return (
      <div className="page page--wide">
        <div className="page-loader" role="status" aria-live="polite">
          <div className="spinner" />
          <span>Carregando formulário da oferta...</span>
        </div>
      </div>
    )
  }

  if (!isCreateMode && (isError || !ofertaData)) {
    return (
      <div className="page page--wide">
        <div className="page-error">
          <h1 className="page-error__title">Não foi possível carregar a oferta</h1>
          <p className="page-error__description">Verifique se o registro existe e tente novamente.</p>
        </div>
      </div>
    )
  }

  const onSubmit = handleSubmit(async (formData) => {
    await saveMutation.mutateAsync({
      id: ofertaId,
      payload: {
        curso_base_id: Number(formData.curso_base_id),
        matriz_curricular_id: formData.matriz_curricular_id ? Number(formData.matriz_curricular_id) : null,
        polo_id: Number(formData.polo_id),
        calendario_letivo_id: Number(formData.calendario_letivo_id),
        nome: formData.nome.trim(),
        codigo_turma: formData.codigo_turma.trim(),
        ano_oferta: Number(formData.ano_oferta),
        periodo_letivo: formData.periodo_letivo.trim(),
        turno: formData.turno,
        vagas_totais: Number(formData.vagas_totais),
        vagas_ocupadas: Number(formData.vagas_ocupadas),
        status: formData.status,
        observacao: formData.observacao.trim(),
      },
    })
  })

  return (
    <div className="page page--wide matrix-page">
      <nav className="profile-breadcrumb">
        <Link to="/dashboard">Início</Link>
        <span className="profile-breadcrumb__sep">&gt;</span>
        <Link to="/ensino/ofertas/">Ofertas de Curso</Link>
        <span className="profile-breadcrumb__sep">&gt;</span>
        <span>{isCreateMode ? 'Nova oferta' : 'Editar oferta'}</span>
      </nav>

      <div className="page-header">
        <div>
          <h1 className="page-title">{isCreateMode ? 'Nova oferta de curso' : `Editar ${ofertaData.nome}`}</h1>
          <p className="page-subtitle">Cadastre a execução operacional da matriz curricular com curso base, calendário, polo e turno.</p>
        </div>
        <div className="page-header__actions">
          <button type="button" className="btn btn--outline" onClick={() => navigate(isCreateMode ? '/ensino/ofertas/' : `/ensino/ofertas/${ofertaId}`)}>
            <ArrowLeft size={16} /> Voltar
          </button>
        </div>
      </div>

      <form className="dashboard-card matrix-form" onSubmit={onSubmit}>
        <fieldset disabled={saveMutation.isPending}>
          <div className="matrix-form__grid">
            <label className="matrix-form__field">
              <span>Curso base técnico</span>
              <select {...register('curso_base_id', { required: 'Selecione o curso base.' })}>
                <option value="">Selecione</option>
                {courseOptions.map((curso) => <option key={curso.id} value={curso.id}>{curso.nome}</option>)}
              </select>
              {errors.curso_base_id ? <span className="form-field__error">{errors.curso_base_id.message}</span> : null}
            </label>

            <label className="matrix-form__field">
              <span>Matriz curricular</span>
              <select {...register('matriz_curricular_id')}>
                <option value="">Usar matriz vigente do curso</option>
                {matrizes.map((matriz) => <option key={matriz.id} value={matriz.id}>{matriz.nome} • {matriz.versao} • {matriz.status}</option>)}
              </select>
            </label>

            <label className="matrix-form__field">
              <span>Polo</span>
              <select {...register('polo_id', { required: 'Selecione o polo.' })}>
                <option value="">Selecione</option>
                {poloOptions.map((polo) => <option key={polo.id} value={polo.id}>{polo.nome}</option>)}
              </select>
              {errors.polo_id ? <span className="form-field__error">{errors.polo_id.message}</span> : null}
            </label>

            <label className="matrix-form__field">
              <span>Calendário letivo</span>
              <select {...register('calendario_letivo_id', { required: 'Selecione o calendário letivo.' })}>
                <option value="">Selecione</option>
                {calendarios.map((calendario) => <option key={calendario.id} value={calendario.id}>{calendario.ano_letivo} • {calendario.status}</option>)}
              </select>
              {errors.calendario_letivo_id ? <span className="form-field__error">{errors.calendario_letivo_id.message}</span> : null}
            </label>

            <label className="matrix-form__field matrix-form__field--full">
              <span>Nome da oferta</span>
              <input {...register('nome', { required: 'Informe o nome da oferta.' })} />
              {errors.nome ? <span className="form-field__error">{errors.nome.message}</span> : null}
            </label>

            <label className="matrix-form__field">
              <span>Turma</span>
              <input {...register('codigo_turma')} placeholder="Ex.: A" />
            </label>

            <label className="matrix-form__field">
              <span>Ano da oferta</span>
              <input type="number" min="2000" max="2100" {...register('ano_oferta', { required: 'Informe o ano da oferta.', valueAsNumber: true })} />
              {errors.ano_oferta ? <span className="form-field__error">{errors.ano_oferta.message}</span> : null}
            </label>

            <label className="matrix-form__field">
              <span>Período letivo</span>
              <input {...register('periodo_letivo', { required: 'Informe o período letivo.' })} />
            </label>

            <label className="matrix-form__field">
              <span>Turno</span>
              <select {...register('turno')}>
                <option value="MANHA">Manhã</option>
                <option value="TARDE">Tarde</option>
                <option value="NOITE">Noite</option>
                <option value="INTEGRAL">Integral</option>
              </select>
            </label>

            <label className="matrix-form__field">
              <span>Vagas totais</span>
              <input type="number" min="0" {...register('vagas_totais', { valueAsNumber: true })} />
            </label>

            <label className="matrix-form__field">
              <span>Vagas ocupadas</span>
              <input type="number" min="0" {...register('vagas_ocupadas', { valueAsNumber: true })} />
            </label>

            <label className="matrix-form__field">
              <span>Status</span>
              <select {...register('status')}>
                <option value="PLANEJADA">Planejada</option>
                <option value="ATIVA">Ativa</option>
                <option value="ENCERRADA">Encerrada</option>
                <option value="CANCELADA">Cancelada</option>
              </select>
            </label>

            <label className="matrix-form__field matrix-form__field--full">
              <span>Observações</span>
              <textarea rows="4" {...register('observacao')} />
            </label>
          </div>

          <div className="matrix-form__actions">
            <button type="submit" className="btn btn--primary" disabled={saveMutation.isPending}>
              <Save size={16} /> {saveMutation.isPending ? 'Salvando...' : 'Salvar oferta'}
            </button>
          </div>
        </fieldset>
      </form>
    </div>
  )
}