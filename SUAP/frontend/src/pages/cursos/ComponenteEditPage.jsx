import { useEffect, useRef } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useForm } from 'react-hook-form'
import toast from 'react-hot-toast'
import { ArrowLeft, CircleHelp, Save, Trash2 } from 'lucide-react'
import { Link, useNavigate, useParams } from 'react-router-dom'

import { componentesApi, cursosApi, matrizesCurricularesApi } from '@/api/endpoints'
import { loadAllPaginatedResults } from '@/utils/loadAllPaginatedResults'
import './suap-componentes.css'

const DEFAULT_VALUES = {
  descricao: '',
  descricao_historico: '',
  descricao_diploma: '',
  abreviatura: '',
  sigla: '',
  tipo_componente_id: '',
  diretoria: '',
  nivel_ensino_id: '',
  esta_ativo: true,
  grupo_atuacao: '',
  sigla_qacademico: '',
  observacao: '',
  curso: '',
  matriz_curricular_id: '',
  carga_horaria: 0,
  hora_aula: 0,
  qtd_creditos: 0,
  modulo_numero: '',
  modulo_nome: '',
  ordem_no_modulo: '',
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
    tipo_componente_id: component?.tipo_componente_id ? String(component.tipo_componente_id) : '',
    diretoria: component?.diretoria || '',
    nivel_ensino_id: component?.nivel_ensino_id ? String(component.nivel_ensino_id) : '',
    esta_ativo: component?.esta_ativo ?? true,
    grupo_atuacao: component?.grupo_atuacao || '',
    sigla_qacademico: component?.sigla_qacademico || '',
    observacao: component?.observacao || '',
    curso: component?.curso_id ? String(component.curso_id) : '',
    matriz_curricular_id: component?.matriz_curricular_id ? String(component.matriz_curricular_id) : '',
    carga_horaria: component?.carga_horaria ?? 0,
    hora_aula: component?.hora_aula ?? 0,
    qtd_creditos: component?.qtd_creditos ?? 0,
    modulo_numero: component?.modulo_numero ?? '',
    modulo_nome: component?.modulo_nome ?? '',
    ordem_no_modulo: component?.ordem_no_modulo ?? '',
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
    queryFn: async () => {
      const [summary, cursos, matrizes] = await Promise.all([
        componentesApi.list({}).then((response) => response.data?.summary?.filter_options || {}),
        loadAllPaginatedResults((params) => cursosApi.list({ ...params, tipo_curso: 'tecnico' })),
        loadAllPaginatedResults((params) => matrizesCurricularesApi.list(params)),
      ])
      return {
        ...summary,
        cursos,
        matrizes,
      }
    },
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
      tipo_componente_id: formData.tipo_componente_id ? Number(formData.tipo_componente_id) : null,
      diretoria: formData.diretoria.trim(),
      nivel_ensino_id: formData.nivel_ensino_id ? Number(formData.nivel_ensino_id) : null,
      esta_ativo: parseBooleanSelectValue(formData.esta_ativo),
      grupo_atuacao: formData.grupo_atuacao.trim(),
      sigla_qacademico: formData.sigla_qacademico.trim(),
      observacao: formData.observacao.trim(),
      curso: formData.curso ? Number(formData.curso) : undefined,
      matriz_curricular_id: formData.matriz_curricular_id ? Number(formData.matriz_curricular_id) : null,
      carga_horaria: Number(formData.carga_horaria) || 0,
      hora_aula: Number(formData.hora_aula) || 0,
      qtd_creditos: Number(formData.qtd_creditos) || 0,
      modulo_numero: formData.modulo_numero ? Number(formData.modulo_numero) : null,
      modulo_nome: formData.modulo_nome.trim(),
      ordem_no_modulo: formData.ordem_no_modulo ? Number(formData.ordem_no_modulo) : null,
    }

    if (!isCreateMode && data?.curso_id && !payload.curso) {
      payload.curso = data.curso_id
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
              <select {...register('tipo_componente_id')}>
                <option value="">Escolha uma opção</option>
                {renderSelectOptions(opcoes?.tipos_componente)}
              </select>
            </FormRow>


            <FormRow label="Nível de ensino">
              <select {...register('nivel_ensino_id')}>
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

            <FormRow label="Curso legado / oferta" error={errors.curso?.message} hint="Mantido por compatibilidade durante a transição para matrizes explícitas.">
              <select {...register('curso')}>
                <option value="">Selecione um curso técnico</option>
                {(opcoes?.cursos || []).map((curso) => (
                  <option key={curso.id} value={curso.id}>{curso.nome}</option>
                ))}
              </select>
            </FormRow>

            <FormRow label="Matriz curricular explícita" error={errors.matriz_curricular_id?.message} hint="Quando preenchida, passa a ser o vínculo principal do componente na nova modelagem.">
              <select {...register('matriz_curricular_id')}>
                <option value="">Selecione uma matriz curricular</option>
                {(opcoes?.matrizes || []).map((matriz) => (
                  <option key={matriz.id} value={matriz.id}>{matriz.nome}</option>
                ))}
              </select>
            </FormRow>

            <FormRow label="Carga horária" required error={errors.carga_horaria?.message}>
              <input type="number" min="0" {...register('carga_horaria', { valueAsNumber: true })} />
            </FormRow>

            <FormRow label="Hora/aula">
              <input type="number" min="0" {...register('hora_aula', { valueAsNumber: true })} />
            </FormRow>

            <FormRow label="Qtd. créditos">
              <input type="number" min="0" {...register('qtd_creditos', { valueAsNumber: true })} />
            </FormRow>

            <FormRow label="Módulo">
              <input type="number" min="1" {...register('modulo_numero', { valueAsNumber: true })} placeholder="Ex.: 1" />
            </FormRow>

            <FormRow label="Nome do módulo">
              <input {...register('modulo_nome')} placeholder="Ex.: Fundamentos da formação técnica" />
            </FormRow>

            <FormRow label="Ordem no módulo">
              <input type="number" min="1" {...register('ordem_no_modulo', { valueAsNumber: true })} />
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