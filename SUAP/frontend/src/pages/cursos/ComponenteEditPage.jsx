import { useEffect, useRef } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useForm } from 'react-hook-form'
import toast from 'react-hot-toast'
import { ArrowLeft, CircleHelp, Save, Trash2 } from 'lucide-react'
import { Link, useNavigate, useParams } from 'react-router-dom'

import { componentesApi } from '@/api/endpoints'
import './suap-componentes.css'

const DEFAULT_VALUES = {
  descricao: '',
  descricao_historico: '',
  descricao_diploma: '',
  abreviatura: '',
  sigla: '',
  tipo_componente: '',
  diretoria: '',
  nivel_ensino: '',
  esta_ativo: true,
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
  const descricaoOficial = component?.descricao_diploma_historico || ''

  return {
    descricao: component?.descricao || '',
    descricao_historico: descricaoOficial,
    descricao_diploma: descricaoOficial,
    abreviatura: component?.abreviatura || '',
    sigla: component?.sigla || '',
    tipo_componente: component?.tipo_componente || '',
    diretoria: component?.diretoria || '',
    nivel_ensino: component?.nivel_ensino || '',
    esta_ativo: component?.esta_ativo ?? true,
    grupo_atuacao: component?.grupo_atuacao || '',
    sigla_qacademico: component?.sigla_qacademico || '',
    observacao: component?.observacao || '',
  }
}

function parseBooleanSelectValue(value) {
  if (typeof value === 'boolean') {
    return value
  }

  return value === 'true'
}

function SectionField({ label, error, full = false, children }) {
  return (
    <label className={`form-field ${full ? 'componente-form-field--full' : ''}`}>
      <span className="componente-form-field__label">{label}</span>
      {children}
      {error ? <span className="form-field__error">{error}</span> : null}
    </label>
  )
}

function FormRow({ label, required = false, error, hint, children }) {
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

function resolveOfficialDescriptions(formData) {
  const descricaoBase = formData.descricao.trim()
  const descricaoHistorico = formData.descricao_historico.trim() || descricaoBase
  const descricaoDiploma = formData.descricao_diploma.trim() || descricaoBase

  return {
    descricaoHistorico,
    descricaoDiploma,
    descricaoPersistida: descricaoDiploma || descricaoHistorico || descricaoBase,
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
    watch,
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

  const descricaoHistoricoValue = watch('descricao_historico')
  const descricaoDiplomaValue = watch('descricao_diploma')

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
    const { descricaoPersistida } = resolveOfficialDescriptions(formData)
    const payload = {
      descricao: formData.descricao.trim(),
      descricao_diploma_historico: descricaoPersistida,
      abreviatura: formData.abreviatura.trim(),
      sigla: formData.sigla.trim(),
      tipo_componente: formData.tipo_componente.trim(),
      diretoria: formData.diretoria.trim(),
      nivel_ensino: formData.nivel_ensino.trim(),
      esta_ativo: parseBooleanSelectValue(formData.esta_ativo),
      grupo_atuacao: formData.grupo_atuacao.trim(),
      sigla_qacademico: formData.sigla_qacademico.trim(),
      observacao: formData.observacao.trim(),
    }

    if (!isCreateMode && data?.curso_id) {
      payload.curso = data.curso_id
    }

    if (!isCreateMode && typeof data?.carga_horaria !== 'undefined') {
      payload.carga_horaria = data.carga_horaria
    }

    if (!isCreateMode && typeof data?.hora_aula !== 'undefined') {
      payload.hora_aula = data.hora_aula
    }

    if (!isCreateMode && typeof data?.qtd_creditos !== 'undefined') {
      payload.qtd_creditos = data.qtd_creditos
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
            <span>Adicionar Componente</span>
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

      <div className="page-header componente-edit-theme-header">
        <div>
          <h1 className="page-title">{isCreateMode ? 'Adicionar Componente' : 'Editar componente curricular'}</h1>
          <p className="page-subtitle">{isCreateMode ? 'Preencha os dados do componente curricular.' : `${data.sigla || 'Sem sigla'} • ${data.matriz_curricular || 'Sem matriz curricular definida'}`}</p>
        </div>
        <div className="page-header__actions">
          <Link
            to="/indisponivel/ajuda-componentes"
            state={{
              title: 'Ajuda de Componentes',
              description: 'A ajuda detalhada desta funcionalidade ainda será portada para o frontend React.',
            }}
            className="btn btn--outline"
          >
            <CircleHelp size={16} /> Ajuda
          </Link>
          <button type="button" className="btn btn--outline" onClick={() => navigate(isCreateMode ? '/ensino/componentes/' : `/componentes/${data.id}`)}>
            <ArrowLeft size={16} /> {isCreateMode ? 'Voltar para listagem' : 'Voltar para detalhes'}
          </button>
        </div>
      </div>

      <form className="dashboard-card area-curso-edit-form componente-edit-theme-form" onSubmit={onSubmit}>
        <section className="componente-edit-theme-section">
          <div className="componente-edit-theme-section__title">Dados gerais</div>
          <div className="area-curso-edit-form__rows">
            <FormRow label="Descrição" required error={errors.descricao?.message}>
              <input
                {...register('descricao', { required: 'Informe a descrição.' })}
                placeholder="Ex.: Instalações Elétricas Prediais"
              />
            </FormRow>

            <FormRow label="Abreviatura">
              <input {...register('abreviatura')} placeholder="Ex.: Inst. Elétricas" />
            </FormRow>

            <FormRow label="Sigla">
              <input {...register('sigla')} placeholder="Ex.: IEP" />
            </FormRow>

            <FormRow label="Tipo do Componente">
              <select {...register('tipo_componente')}>
                <option value="">Escolha uma opção</option>
                {renderSelectOptions(opcoes?.tipos_componente)}
              </select>
            </FormRow>


            <FormRow label="Nível de ensino">
              <select {...register('nivel_ensino')}>
                <option value="">Escolha uma opção</option>
                {renderSelectOptions(opcoes?.niveis_ensino)}
              </select>
            </FormRow>

            <FormRow label="Coordenação/Departamento responsável">
              <input {...register('diretoria')} placeholder="Ex.: Coordenação de Eletrotécnica" />
            </FormRow>

            <FormRow label="Eixo tecnológico / Área de conhecimento">
              <select {...register('grupo_atuacao')}>
                <option value="">Escolha uma opção</option>
                {renderSelectOptions(opcoes?.grupos_atuacao)}
              </select>
            </FormRow>

            <FormRow label="Está ativo">
              <div className="componente-edit-theme-row__checkbox">
                <input type="checkbox" {...register('esta_ativo')} />
              </div>
            </FormRow>
          </div>
        </section>

        <section className="componente-edit-theme-section componente-edit-theme-section--muted">
          <div className="componente-edit-theme-section__title">Documentação Oficial</div>
          <div className="area-curso-edit-form__rows">
            <FormRow
              label="Descrição no Histórico"
              hint={isCreateMode ? 'Se não for preenchida, será usada a descrição principal do componente.' : `Valor salvo atualmente: ${data?.descricao_diploma_historico || 'será usada a descrição principal.'}`}
            >
              <input
                {...register('descricao_historico')}
                placeholder="Se vazio, será usada a descrição principal"
              />
            </FormRow>

            <FormRow
              label="Descrição no Diploma"
              hint={descricaoHistoricoValue && descricaoDiplomaValue && descricaoHistoricoValue !== descricaoDiplomaValue ? 'Atualmente o backend ainda persiste uma única descrição oficial compartilhada entre histórico e diploma.' : 'Se não for preenchida, será usada a descrição principal do componente.'}
            >
              <input
                {...register('descricao_diploma')}
                placeholder="Se vazio, será usada a descrição principal"
              />
            </FormRow>
          </div>
        </section>

        <section className="componente-edit-theme-section componente-edit-theme-section--muted">
          <div className="componente-edit-theme-section__title">Integrações e Controle</div>
          <div className="area-curso-edit-form__rows">
            <FormRow label="Código no sistema legado / Q-Acadêmico">
              <input {...register('sigla_qacademico')} placeholder="Ex.: TEC-ELE-001" />
            </FormRow>

            <FormRow label="Observação" hint="Campo opcional para anotações administrativas ou acadêmicas do cadastro base.">
              <textarea rows="5" {...register('observacao')} placeholder="Ex.: Componente comum aos módulos iniciais do curso técnico." />
            </FormRow>
          </div>
        </section>

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