import { useEffect } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useForm } from 'react-hook-form'
import toast from 'react-hot-toast'
import { ArrowLeft, Link2, Save } from 'lucide-react'
import { Link, useNavigate, useParams } from 'react-router-dom'

import { componentesApi } from '@/api/endpoints'
import './suap-componentes.css'

const DEFAULT_VALUES = {
  curso: '',
  carga_horaria: '',
  hora_aula: '',
  qtd_creditos: '',
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
    carga_horaria: component?.carga_horaria ?? '',
    hora_aula: component?.hora_aula ?? '',
    qtd_creditos: component?.qtd_creditos ?? '',
  }
}

function VinculacaoRow({ label, required = false, error, hint, children }) {
  return (
    <div className="area-curso-edit-row componente-edit-theme-row">
      <div className="area-curso-edit-row__label componente-edit-theme-row__label">
        <span className={required ? 'componente-edit-theme-row__label-text componente-edit-theme-row__label-text--required' : 'componente-edit-theme-row__label-text'}>
          {label}
        </span>
      </div>
      <div className="area-curso-edit-row__field componente-edit-theme-row__field">
        {children}
        {hint ? <div className="componente-edit-theme-row__hint">{hint}</div> : null}
        {error ? <span className="form-field__error">{error}</span> : null}
      </div>
    </div>
  )
}

function renderSelectOptions(options) {
  return (options || []).map((item) => (
    <option key={item.value} value={item.value}>{item.label}</option>
  ))
}

export default function ComponenteVinculacaoPage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { componenteId } = useParams()

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm({ defaultValues: DEFAULT_VALUES })

  const { data, isLoading, isError } = useQuery({
    queryKey: ['componentes', 'detail', componenteId],
    queryFn: () => componentesApi.get(componenteId).then((response) => response.data),
    enabled: Boolean(componenteId),
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
    mutationFn: ({ id, payload }) => componentesApi.patch(id, payload),
    onSuccess: async (_response, variables) => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ['componentes'] }),
        queryClient.invalidateQueries({ queryKey: ['componentes', 'detail', variables.id] }),
      ])

      toast.success('Vinculação à matriz curricular atualizada com sucesso.')
      navigate(`/componentes/${variables.id}`)
    },
    onError: (error) => {
      toast.error(getErrorMessage(error, 'Não foi possível salvar a vinculação à matriz curricular.'))
    },
  })

  if (isLoading) {
    return (
      <div className="page page--wide">
        <div className="page-loader" role="status" aria-live="polite">
          <div className="spinner" />
          <span>Carregando dados de vinculação...</span>
        </div>
      </div>
    )
  }

  if (isError || !data) {
    return (
      <div className="page page--wide">
        <div className="page-error">
          <h1 className="page-error__title">Não foi possível carregar a vinculação do componente</h1>
          <p className="page-error__description">Verifique se o registro existe e tente novamente.</p>
        </div>
      </div>
    )
  }

  const onSubmit = handleSubmit(async (formData) => {
    const payload = {
      curso: Number(formData.curso),
      carga_horaria: Number(formData.carga_horaria) || 0,
      hora_aula: Number(formData.hora_aula) || 0,
      qtd_creditos: Number(formData.qtd_creditos) || 0,
    }

    await saveMutation.mutateAsync({ id: data.id, payload })
  })

  return (
    <div className="page page--wide componente-edit-page">
      <nav className="profile-breadcrumb">
        <Link to="/dashboard">Início</Link>
        <span className="profile-breadcrumb__sep">&gt;</span>
        <Link to="/ensino/componentes/">Componentes</Link>
        <span className="profile-breadcrumb__sep">&gt;</span>
        <Link to={`/componentes/${data.id}`}>{data.sigla || data.descricao}</Link>
        <span className="profile-breadcrumb__sep">&gt;</span>
        <span>Vinculação à matriz curricular</span>
      </nav>

      <div className="page-header componente-edit-theme-header">
        <div>
          <h1 className="page-title">Vinculação à matriz curricular</h1>
          <p className="page-subtitle">Defina matriz, carga horária e créditos do componente {data.descricao}.</p>
        </div>
        <div className="page-header__actions">
          <button type="button" className="btn btn--outline" onClick={() => navigate(`/componentes/${data.id}`)}>
            <ArrowLeft size={16} /> Voltar para detalhes
          </button>
        </div>
      </div>

      <div className="dashboard-card componente-vinculacao-card">
        <div className="componente-vinculacao-card__intro">
          <div>
            <h2 className="dashboard-card__title">Parâmetros de vinculação</h2>
            <p className="componente-vinculacao-card__subtitle">Esta etapa concentra os dados que variam conforme a matriz curricular do curso técnico.</p>
          </div>
          <div className="componente-vinculacao-chip">
            <Link2 size={14} /> Fluxo de vinculação
          </div>
        </div>

        <form className="area-curso-edit-form componente-edit-theme-form" onSubmit={onSubmit}>
          <section className="componente-edit-theme-section">
            <div className="componente-edit-theme-section__title">Vinculação</div>
            <div className="area-curso-edit-form__rows">
              <VinculacaoRow label="Matriz curricular" required error={errors.curso?.message}>
                <select {...register('curso', { required: 'Selecione a matriz curricular.' })}>
                  <option value="">Selecione uma matriz curricular</option>
                  {renderSelectOptions(opcoes?.matrizes_curriculares)}
                </select>
              </VinculacaoRow>

              <VinculacaoRow label="Hora/relógio" required error={errors.carga_horaria?.message} hint="Carga horária efetiva do componente dentro da matriz selecionada.">
                <input type="number" min="0" {...register('carga_horaria', { required: 'Informe a hora/relógio.', valueAsNumber: true })} />
              </VinculacaoRow>

              <VinculacaoRow label="Hora/aula" required error={errors.hora_aula?.message} hint="Quantidade de horas-aula considerada na organização pedagógica da matriz.">
                <input type="number" min="0" {...register('hora_aula', { required: 'Informe a hora/aula.', valueAsNumber: true })} />
              </VinculacaoRow>

              <VinculacaoRow label="Quantidade de créditos" required error={errors.qtd_creditos?.message} hint="Créditos atribuídos ao componente dentro da estrutura curricular.">
                <input type="number" min="0" {...register('qtd_creditos', { required: 'Informe a quantidade de créditos.', valueAsNumber: true })} />
              </VinculacaoRow>
            </div>
          </section>

          <div className="componente-edit-form__actions">
            <button type="submit" className="btn btn--primary" disabled={saveMutation.isPending}>
              <Save size={16} /> Salvar vinculação
            </button>
            <button type="button" className="btn btn--outline" onClick={() => navigate(`/componentes/${data.id}`)}>
              Cancelar
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}