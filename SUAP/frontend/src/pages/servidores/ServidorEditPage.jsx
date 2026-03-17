import { useEffect, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useForm } from 'react-hook-form'
import toast from 'react-hot-toast'
import { EllipsisVertical, Pencil, Upload, UserRound } from 'lucide-react'
import { Link, useNavigate, useParams } from 'react-router-dom'

import { servidoresApi, setoresApi } from '@/api/endpoints'
import SearchableRemoteSelect from '@/components/ui/SearchableRemoteSelect'
import { normalizeCpf } from '@/utils/cpf'

const PERFIL_OPTIONS = [
  { value: 'PROFESSOR', label: 'Professor' },
  { value: 'SECRETARIA', label: 'Secretaria' },
  { value: 'COORDENACAO', label: 'Coordenador de Curso' },
  { value: 'ADMIN', label: 'Administrador' },
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
  matricula_servidor: '',
  nome_usual: '',
  email_institucional: '',
  email_siape: '',
  email_secundario_recuperacao: '',
  email_notificacoes: '',
  email_google_sala: '',
  telefones_institucionais: '',
  telefones_pessoais: '',
  em_pgd: false,
  nao_tem_impressao_digital: false,
  estado_civil: '',
  naturalidade: '',
  sexo: '',
  grupo_sanguineo_rh: '',
  dependentes_ir: '',
  raca_etnia: '',
  nome_pai: '',
  nome_mae: '',
  pis_pasep: '',
  titulacao: '',
  escolaridade: '',
  identidade: '',
  orgao_expedidor: '',
  uf_rg: '',
  data_expedicao: '',
  titulo_eleitor_numero: '',
  titulo_eleitor_zona: '',
  titulo_eleitor_secao: '',
  titulo_eleitor_uf: '',
  posicao_atual: '',
  cargo_atual: '',
  regime_trabalho: '',
  jornada_trabalho: '',
  classe_funcional: '',
  nivel_funcional: '',
  banco: '',
  agencia: '',
  conta_corrente: '',
}

function SummaryItem({ label, value }) {
  return (
    <div className="profile-summary__item">
      <div className="profile-summary__label-row">
        <span className="profile-summary__label">{label}</span>
      </div>
      <strong className="profile-summary__value">{value || '-'}</strong>
    </div>
  )
}

function TextField({ id, label, type = 'text', register, errors, validation, step }) {
  return (
    <div className="form-field">
      <label htmlFor={id}>{label}</label>
      <input id={id} type={type} step={step} {...register(id, validation)} />
      {errors[id] ? <span className="field-error">{errors[id].message}</span> : null}
    </div>
  )
}

function SelectField({ id, label, register, errors, options, validation }) {
  return (
    <div className="form-field">
      <label htmlFor={id}>{label}</label>
      <select id={id} className="select" {...register(id, validation)}>
        {options.map((option) => (
          <option key={option.value} value={option.value}>{option.label}</option>
        ))}
      </select>
      {errors[id] ? <span className="field-error">{errors[id].message}</span> : null}
    </div>
  )
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

export default function ServidorEditPage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { servidorId } = useParams()
  const [setorSearch, setSetorSearch] = useState('')

  const {
    register,
    handleSubmit,
    reset,
    setValue,
    watch,
    formState: { errors, isSubmitting },
  } = useForm({ defaultValues: DEFAULT_VALUES })

  const { data: servidor, isLoading } = useQuery({
    queryKey: ['servidor-edit', servidorId],
    queryFn: () => servidoresApi.get(servidorId).then((response) => response.data),
    enabled: Boolean(servidorId),
    staleTime: 0,
  })

  const { data: setoresData } = useQuery({
    queryKey: ['setores', 'options', 'servidor-edit', setorSearch],
    queryFn: () => setoresApi.list({ page_size: 10, search: setorSearch || undefined }).then((response) => response.data),
    staleTime: 60_000,
  })

  useEffect(() => {
    if (!servidor) {
      return
    }

    reset({
      username: servidor.username || '',
      nome_completo: servidor.nome_completo || '',
      cpf: servidor.cpf || '',
      email: servidor.email || '',
      tipo: servidor.tipo || 'PROFESSOR',
      setor: servidor.setor ? String(servidor.setor) : '',
      is_active: Boolean(servidor.is_active),
      password: '',
      matricula_servidor: servidor.matricula_servidor || '',
      nome_usual: servidor.nome_usual || '',
      email_institucional: servidor.email_institucional || '',
      email_siape: servidor.email_siape || '',
      email_secundario_recuperacao: servidor.email_secundario_recuperacao || '',
      email_notificacoes: servidor.email_notificacoes || '',
      email_google_sala: servidor.email_google_sala || '',
      telefones_institucionais: servidor.telefones_institucionais || '',
      telefones_pessoais: servidor.telefones_pessoais || '',
      em_pgd: Boolean(servidor.em_pgd),
      nao_tem_impressao_digital: Boolean(servidor.nao_tem_impressao_digital),
      estado_civil: servidor.estado_civil || '',
      naturalidade: servidor.naturalidade || '',
      sexo: servidor.sexo || '',
      grupo_sanguineo_rh: servidor.grupo_sanguineo_rh || '',
      dependentes_ir: servidor.dependentes_ir ?? '',
      raca_etnia: servidor.raca_etnia || '',
      nome_pai: servidor.nome_pai || '',
      nome_mae: servidor.nome_mae || '',
      pis_pasep: servidor.pis_pasep || '',
      titulacao: servidor.titulacao || '',
      escolaridade: servidor.escolaridade || '',
      identidade: servidor.identidade || '',
      orgao_expedidor: servidor.orgao_expedidor || '',
      uf_rg: servidor.uf_rg || '',
      data_expedicao: servidor.data_expedicao || '',
      titulo_eleitor_numero: servidor.titulo_eleitor_numero || '',
      titulo_eleitor_zona: servidor.titulo_eleitor_zona || '',
      titulo_eleitor_secao: servidor.titulo_eleitor_secao || '',
      titulo_eleitor_uf: servidor.titulo_eleitor_uf || '',
      posicao_atual: servidor.posicao_atual || '',
      cargo_atual: servidor.cargo_atual || '',
      regime_trabalho: servidor.regime_trabalho || '',
      jornada_trabalho: servidor.jornada_trabalho || '',
      classe_funcional: servidor.classe_funcional || '',
      nivel_funcional: servidor.nivel_funcional || '',
      banco: servidor.banco || '',
      agencia: servidor.agencia || '',
      conta_corrente: servidor.conta_corrente || '',
    })
  }, [reset, servidor])

  const setorOptions = setoresData?.results || []
  const setorValue = watch('setor')
  const selectedSetorOption = setorValue && servidor ? {
    id: servidor.setor,
    nome: servidor.setor_nome,
  } : null

  const saveMutation = useMutation({
    mutationFn: ({ id, payload }) => servidoresApi.update(id, payload),
    onSuccess: (_response, variables) => {
      queryClient.invalidateQueries({ queryKey: ['servidores'] })
      queryClient.invalidateQueries({ queryKey: ['servidor', variables.id] })
      queryClient.invalidateQueries({ queryKey: ['servidor-profile', variables.id] })
      queryClient.invalidateQueries({ queryKey: ['servidor-edit', variables.id] })
      toast.success('Servidor atualizado com sucesso.')
      navigate(`/rh/servidores/${variables.id}`)
    },
    onError: (error) => {
      toast.error(getErrorMessage(error, 'Nao foi possivel salvar o servidor.'))
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
      matricula_servidor: formData.matricula_servidor.trim(),
      nome_usual: formData.nome_usual.trim(),
      email_institucional: formData.email_institucional.trim(),
      email_siape: formData.email_siape.trim(),
      email_secundario_recuperacao: formData.email_secundario_recuperacao.trim(),
      email_notificacoes: formData.email_notificacoes.trim(),
      email_google_sala: formData.email_google_sala.trim(),
      telefones_institucionais: formData.telefones_institucionais.trim(),
      telefones_pessoais: formData.telefones_pessoais.trim(),
      em_pgd: Boolean(formData.em_pgd),
      nao_tem_impressao_digital: Boolean(formData.nao_tem_impressao_digital),
      estado_civil: formData.estado_civil.trim(),
      naturalidade: formData.naturalidade.trim(),
      sexo: formData.sexo.trim(),
      grupo_sanguineo_rh: formData.grupo_sanguineo_rh.trim(),
      dependentes_ir: formData.dependentes_ir === '' ? null : Number(formData.dependentes_ir),
      raca_etnia: formData.raca_etnia.trim(),
      nome_pai: formData.nome_pai.trim(),
      nome_mae: formData.nome_mae.trim(),
      pis_pasep: formData.pis_pasep.trim(),
      titulacao: formData.titulacao.trim(),
      escolaridade: formData.escolaridade.trim(),
      identidade: formData.identidade.trim(),
      orgao_expedidor: formData.orgao_expedidor.trim(),
      uf_rg: formData.uf_rg.trim(),
      data_expedicao: formData.data_expedicao || null,
      titulo_eleitor_numero: formData.titulo_eleitor_numero.trim(),
      titulo_eleitor_zona: formData.titulo_eleitor_zona.trim(),
      titulo_eleitor_secao: formData.titulo_eleitor_secao.trim(),
      titulo_eleitor_uf: formData.titulo_eleitor_uf.trim(),
      posicao_atual: formData.posicao_atual.trim(),
      cargo_atual: formData.cargo_atual.trim(),
      regime_trabalho: formData.regime_trabalho.trim(),
      jornada_trabalho: formData.jornada_trabalho.trim(),
      classe_funcional: formData.classe_funcional.trim(),
      nivel_funcional: formData.nivel_funcional.trim(),
      banco: formData.banco.trim(),
      agencia: formData.agencia.trim(),
      conta_corrente: formData.conta_corrente.trim(),
    }

    if (formData.password) {
      payload.password = formData.password
    }

    await saveMutation.mutateAsync({
      id: servidorId,
      payload,
    })
  })

  const nomeResumo = watch('nome_usual') || watch('nome_completo') || servidor?.nome_completo || 'Servidor'
  const matriculaResumo = watch('matricula_servidor') || servidor?.matricula_servidor || '-'
  const perfilResumo = PERFIL_OPTIONS.find((option) => option.value === watch('tipo'))?.label || servidor?.tipo_display || 'Servidor'
  const setorResumo = selectedSetorOption?.nome || servidor?.setor_nome || '-'
  const isAtivo = Boolean(watch('is_active'))
  const naoTemBiometria = Boolean(watch('nao_tem_impressao_digital'))

  return (
    <div className="page page--wide">
      <form className="profile-edit-form" onSubmit={onSubmit}>
        <nav className="profile-breadcrumb">
          <Link to="/dashboard">Inicio</Link>
          <span className="profile-breadcrumb__sep">&gt;</span>
          <Link to="/rh/servidores">Servidores</Link>
          <span className="profile-breadcrumb__sep">&gt;</span>
          <Link to={`/rh/servidores/${servidorId}`}>{servidor?.nome_completo || 'Servidor'}</Link>
          <span className="profile-breadcrumb__sep">&gt;</span>
          <span>Editar</span>
        </nav>

        <div className="profile-status-row">
          <span className={`badge ${isAtivo ? 'badge--success' : 'badge--warning'}`}>{isAtivo ? 'Ativo' : 'Inativo'}</span>
          {naoTemBiometria ? <span className="badge badge--danger">Nao tem impressao digital</span> : null}
        </div>

        <div className="page-header profile-header">
          <div>
            <h1 className="page-title">Editar {nomeResumo} ({matriculaResumo})</h1>
            <p className="page-subtitle">Ajuste os dados cadastrais e funcionais na mesma linguagem visual da ficha do servidor.</p>
          </div>
          <div className="page-header__actions profile-header__actions">
            <button type="submit" className="btn btn--primary" disabled={isSubmitting || saveMutation.isPending || isLoading}><Pencil size={16} /> {isSubmitting || saveMutation.isPending ? 'Salvando...' : 'Salvar alteracoes'}</button>
            <button type="button" className="btn btn--secondary"><Upload size={16} /> Importar Meus Dados</button>
            <button type="button" className="btn btn--outline" onClick={() => navigate(`/rh/servidores/${servidorId}`)}><EllipsisVertical size={16} /> Voltar ao cadastro</button>
            <Link to="/comum/minha_conta/" className="btn btn--outline"><UserRound size={16} /> Minha conta</Link>
          </div>
        </div>

        <section className="dashboard-card profile-summary-card">
          <div className="profile-summary-card__avatar">
            <div className="profile-avatar-placeholder">
              <UserRound size={64} />
            </div>
          </div>

          <div className="profile-summary-card__content">
            <div className="profile-summary-grid">
              <SummaryItem label="Nome usual" value={watch('nome_usual') || nomeResumo} />
              <SummaryItem label="Perfil" value={perfilResumo} />
              <SummaryItem label="Setor" value={setorResumo} />
              <SummaryItem label="E-mail institucional" value={watch('email_institucional') || watch('email') || '-'} />
              <SummaryItem label="Matricula" value={matriculaResumo} />
            </div>

            <div className="profile-summary-grid profile-summary-grid--secondary">
              <SummaryItem label="E-mail notificacoes" value={watch('email_notificacoes') || '-'} />
              <SummaryItem label="Telefones institucionais" value={watch('telefones_institucionais') || '-'} />
              <SummaryItem label="Telefones pessoais" value={watch('telefones_pessoais') || '-'} />
              <SummaryItem label="Em PGD" value={watch('em_pgd') ? 'Sim' : 'Nao'} />
            </div>
          </div>
        </section>

        <section className="dashboard-card profile-content-card">
          <div className="profile-alert">
            Os campos exibidos na ficha do servidor agora podem ser persistidos pelo cadastro funcional. Preencha ou ajuste as secoes abaixo para manter a visualizacao coerente com a tela de detalhe.
          </div>

          <section className="profile-panel">
            <div className="profile-panel__header">
              <span>Dados principais</span>
            </div>
            <div className="profile-panel__body">
              <div className="profile-fields-grid profile-fields-grid--four">
                <TextField id="username" label="Usuario" register={register} errors={errors} validation={{ required: 'Informe o usuario' }} />
                <TextField id="nome_completo" label="Nome completo" register={register} errors={errors} validation={{ required: 'Informe o nome completo' }} />
                <TextField id="cpf" label="CPF" register={register} errors={errors} validation={{ required: 'Informe o CPF' }} />
                <TextField id="email" label="E-mail principal" type="email" register={register} errors={errors} />
              </div>
              <div className="profile-fields-grid profile-fields-grid--four">
                <TextField id="matricula_servidor" label="Matricula" register={register} errors={errors} />
                <TextField id="nome_usual" label="Nome usual" register={register} errors={errors} />
                <SelectField id="tipo" label="Perfil" register={register} errors={errors} options={PERFIL_OPTIONS} validation={{ required: 'Selecione o perfil' }} />
                <TextField id="password" label="Nova senha" type="password" register={register} errors={errors} />
              </div>
              <div className="profile-fields-grid profile-fields-grid--two-thirds">
                <SearchableRemoteSelect id="servidor-setor" label="Setor" searchLabel="Buscar setor" searchPlaceholder="Digite nome, sigla ou codigo" searchValue={setorSearch} onSearchChange={setSetorSearch} value={setorValue || ''} onChange={(nextValue) => setValue('setor', nextValue)} options={setorOptions} selectedOption={selectedSetorOption} emptyOptionLabel="Sem setor" getOptionLabel={(setor) => setor.nome} />
                <div className="profile-edit-checkboxes">
                  <div className="form-field form-field--checkbox"><label className="checkbox-field"><input type="checkbox" {...register('is_active')} /><span>Servidor ativo</span></label></div>
                  <div className="form-field form-field--checkbox"><label className="checkbox-field"><input type="checkbox" {...register('em_pgd')} /><span>Participa do PGD</span></label></div>
                  <div className="form-field form-field--checkbox"><label className="checkbox-field"><input type="checkbox" {...register('nao_tem_impressao_digital')} /><span>Nao tem impressao digital</span></label></div>
                </div>
              </div>
            </div>
          </section>

          <section className="profile-panel">
            <div className="profile-panel__header">
              <span>Contatos institucionais</span>
            </div>
            <div className="profile-panel__body">
              <div className="profile-fields-grid profile-fields-grid--four">
                <TextField id="email_institucional" label="E-mail institucional" type="email" register={register} errors={errors} />
                <TextField id="email_siape" label="E-mail SIAPE" type="email" register={register} errors={errors} />
                <TextField id="email_secundario_recuperacao" label="E-mail secundario" type="email" register={register} errors={errors} />
                <TextField id="email_notificacoes" label="E-mail notificacoes" type="email" register={register} errors={errors} />
              </div>
              <div className="profile-fields-grid profile-fields-grid--four">
                <TextField id="email_google_sala" label="E-mail Google Sala" type="email" register={register} errors={errors} />
                <TextField id="telefones_institucionais" label="Telefones institucionais" register={register} errors={errors} />
                <TextField id="telefones_pessoais" label="Telefones pessoais" register={register} errors={errors} />
              </div>
            </div>
          </section>

          <section className="profile-panel">
            <div className="profile-panel__header">
              <span>Dados pessoais e documentais</span>
            </div>
            <div className="profile-panel__body">
              <div className="profile-fields-grid profile-fields-grid--four">
                <TextField id="estado_civil" label="Estado civil" register={register} errors={errors} />
                <TextField id="naturalidade" label="Naturalidade" register={register} errors={errors} />
                <TextField id="sexo" label="Sexo" register={register} errors={errors} />
                <TextField id="grupo_sanguineo_rh" label="Grupo sanguineo/RH" register={register} errors={errors} />
              </div>
              <div className="profile-fields-grid profile-fields-grid--four">
                <TextField id="dependentes_ir" label="Dependentes IR" type="number" register={register} errors={errors} step="1" />
                <TextField id="raca_etnia" label="Raca/etnia" register={register} errors={errors} />
                <TextField id="pis_pasep" label="PIS/PASEP" register={register} errors={errors} />
                <TextField id="titulacao" label="Titulacao" register={register} errors={errors} />
              </div>
              <div className="profile-fields-grid profile-fields-grid--four">
                <TextField id="nome_pai" label="Nome do pai" register={register} errors={errors} />
                <TextField id="nome_mae" label="Nome da mae" register={register} errors={errors} />
                <TextField id="escolaridade" label="Escolaridade" register={register} errors={errors} />
                <TextField id="identidade" label="Identidade" register={register} errors={errors} />
              </div>
              <div className="profile-fields-grid profile-fields-grid--four">
                <TextField id="orgao_expedidor" label="Orgao expedidor" register={register} errors={errors} />
                <TextField id="uf_rg" label="UF RG" register={register} errors={errors} />
                <TextField id="data_expedicao" label="Data expedicao" type="date" register={register} errors={errors} />
              </div>
              <div className="profile-fields-grid profile-fields-grid--four">
                <TextField id="titulo_eleitor_numero" label="Titulo de eleitor" register={register} errors={errors} />
                <TextField id="titulo_eleitor_zona" label="Zona" register={register} errors={errors} />
                <TextField id="titulo_eleitor_secao" label="Secao" register={register} errors={errors} />
                <TextField id="titulo_eleitor_uf" label="UF titulo" register={register} errors={errors} />
              </div>
            </div>
          </section>

          <section className="profile-panel">
            <div className="profile-panel__header">
              <span>Dados funcionais</span>
            </div>
            <div className="profile-panel__body">
              <div className="profile-fields-grid profile-fields-grid--four">
                <TextField id="posicao_atual" label="Posicao atual" register={register} errors={errors} />
                <TextField id="cargo_atual" label="Cargo atual" register={register} errors={errors} />
                <TextField id="regime_trabalho" label="Regime" register={register} errors={errors} />
                <TextField id="jornada_trabalho" label="Jornada de trabalho" register={register} errors={errors} />
              </div>
              <div className="profile-fields-grid profile-fields-grid--four">
                <TextField id="classe_funcional" label="Classe funcional" register={register} errors={errors} />
                <TextField id="nivel_funcional" label="Nivel funcional" register={register} errors={errors} />
              </div>
            </div>
          </section>

          <section className="profile-panel">
            <div className="profile-panel__header">
              <span>Dados bancarios</span>
            </div>
            <div className="profile-panel__body">
              <div className="profile-fields-grid profile-fields-grid--three">
                <TextField id="banco" label="Banco" register={register} errors={errors} />
                <TextField id="agencia" label="Agencia" register={register} errors={errors} />
                <TextField id="conta_corrente" label="Conta corrente" register={register} errors={errors} />
              </div>
            </div>
          </section>

          <div className="profile-edit-actions">
            <button type="submit" className="btn btn--primary" disabled={isSubmitting || saveMutation.isPending || isLoading}>Salvar alteracoes</button>
            <button type="button" className="btn btn--secondary" onClick={() => navigate(`/rh/servidores/${servidorId}`)} disabled={isSubmitting || saveMutation.isPending}>Cancelar</button>
          </div>
        </section>
      </form>
    </div>
  )
}