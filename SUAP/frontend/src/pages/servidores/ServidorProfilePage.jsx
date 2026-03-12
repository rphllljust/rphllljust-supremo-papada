import { useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { ChevronDown, CircleHelp, EllipsisVertical, Pencil, Upload, UserRound } from 'lucide-react'
import { Link, useNavigate, useParams } from 'react-router-dom'

import { authApi, servidoresApi } from '@/api/endpoints'
import { useAuth } from '@/context/AuthContext'

const TAB_ITEMS = [
  'Geral',
  'Ocorrencias/Afastamentos',
  'Setores',
  'Historico funcional',
  'Ferias',
]

const SUMMARY_DEFAULTS = {
  nomeUsual: '-',
  emailInstitucional: '-',
  emailSiape: '-',
  emailSecundario: '-',
  emailNotificacoes: '-',
  emailGoogleSala: '-',
  telefonesInstitucionais: '-',
  telefonesPessoais: '-',
  emPgd: 'Nao',
  cpf: '-',
  nomeRegistro: '-',
  nascimento: '-',
  estadoCivil: '-',
  naturalidade: '-',
  sexo: '-',
  grupoSanguineo: '-',
  dependentesIr: '-',
  racaEtnia: '-',
  nomePai: '-',
  nomeMae: '-',
  pisPasep: '-',
  titulacao: '-',
  escolaridade: '-',
  endereco: '-',
  identidade: '-',
  orgaoExpedidor: '-',
  ufRg: '-',
  dataExpedicao: '-',
  tituloEleitor: '-',
  zonaEleitoral: '-',
  secaoEleitoral: '-',
  ufTitulo: '-',
  matriculaServidor: '-',
  setorAtual: '-',
  regimeTrabalho: '-',
  jornadaTrabalho: '-',
  cargoAtual: '-',
  posicaoAtual: '-',
  classeFuncional: '-',
  nivelFuncional: '-',
  banco: '-',
  agencia: '-',
  contaCorrente: '-',
}

function formatDate(value) {
  if (!value) {
    return '-'
  }

  const date = new Date(`${value}T00:00:00`)
  if (Number.isNaN(date.getTime())) {
    return value
  }

  return new Intl.DateTimeFormat('pt-BR').format(date)
}

function formatBoolean(value) {
  return value ? 'Sim' : 'Nao'
}

function formatPeriod(start, end) {
  const formattedStart = formatDate(start)
  const formattedEnd = formatDate(end)
  if (formattedStart === '-' && formattedEnd === '-') {
    return '-'
  }
  if (formattedEnd === '-') {
    return `A partir de ${formattedStart}`
  }
  return `${formattedStart} a ${formattedEnd}`
}

function calculateDays(start, end) {
  if (!start || !end) {
    return '-'
  }

  const startDate = new Date(`${start}T00:00:00`)
  const endDate = new Date(`${end}T00:00:00`)
  if (Number.isNaN(startDate.getTime()) || Number.isNaN(endDate.getTime())) {
    return '-'
  }

  const diff = endDate.getTime() - startDate.getTime()
  return String(Math.max(0, Math.round(diff / 86_400_000) + 1))
}

function InfoItem({ label, value, hint }) {
  return (
    <div className="profile-summary__item">
      <div className="profile-summary__label-row">
        <span className="profile-summary__label">{label}</span>
        {hint ? <CircleHelp size={14} className="profile-summary__hint" /> : null}
      </div>
      <strong className="profile-summary__value">{value || '-'}</strong>
    </div>
  )
}

function DataField({ label, value, children }) {
  return (
    <div className="profile-field">
      <span className="profile-field__label">{label}</span>
      <strong className="profile-field__value">{value || '-'}</strong>
      {children}
    </div>
  )
}

function TabTableSection({ title, columns, rows, emptyMessage, noticeMessage }) {
  return (
    <div className="profile-tab-panel">
      <h2 className="profile-tab-panel__title">{title}</h2>
      <div className="profile-tab-panel__table-wrap">
        <table className="profile-tab-panel__table">
          <thead>
            <tr>
              {columns.map((column) => (
                <th key={column.key}>{column.label}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows?.length ? (
              rows.map((row) => (
                <tr key={row.id}>
                  {columns.map((column) => (
                    <td key={column.key}>{column.render ? column.render(row) : row[column.key] || '-'}</td>
                  ))}
                </tr>
              ))
            ) : (
              <tr>
                <td className="profile-tab-panel__empty-cell" colSpan={columns.length}>{emptyMessage}</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
      {noticeMessage ? <div className="profile-tab-panel__notice">{noticeMessage}</div> : null}
    </div>
  )
}

export default function ServidorProfilePage() {
  return <ServidorProfileView />
}

export function ServidorProfileView({ servidorId = null }) {
  const { user } = useAuth()
  const navigate = useNavigate()
  const { matricula } = useParams()
  const [activeTab, setActiveTab] = useState('Geral')
  const [personalPanelOpen, setPersonalPanelOpen] = useState(true)
  const [functionalPanelOpen, setFunctionalPanelOpen] = useState(true)
  const [bankPanelOpen, setBankPanelOpen] = useState(true)

  const { data: meData } = useQuery({
    queryKey: ['auth-me', 'profile-page'],
    queryFn: () => authApi.me().then((response) => response.data),
    staleTime: 60_000,
  })

  const currentUserId = meData?.id || user?.id
  const targetServidorId = servidorId || null
  const currentUserMatricula = matricula || meData?.matricula_servidor || user?.matricula_servidor

  const { data: profileData, isError } = useQuery({
    queryKey: ['servidor-profile', targetServidorId || currentUserMatricula || currentUserId],
    queryFn: () => {
      if (targetServidorId) {
        return servidoresApi.profile(targetServidorId).then((response) => response.data)
      }
      if (currentUserMatricula) {
        return servidoresApi.profileByMatricula(currentUserMatricula).then((response) => response.data)
      }
      return servidoresApi.profile(currentUserId).then((response) => response.data)
    },
    enabled: Boolean(targetServidorId || currentUserMatricula || currentUserId),
    staleTime: 60_000,
  })

  const resolvedServidorId = profileData?.usuario || targetServidorId || currentUserId || null
  const isDirectoryView = Boolean(targetServidorId)

  const profile = useMemo(() => ({
    ...SUMMARY_DEFAULTS,
    nomeUsual: profileData?.nome_usual || profileData?.nome_registro || user?.nome_completo || SUMMARY_DEFAULTS.nomeUsual,
    nomeRegistro: profileData?.nome_registro || user?.nome_completo || SUMMARY_DEFAULTS.nomeRegistro,
    emailInstitucional: profileData?.email_institucional || SUMMARY_DEFAULTS.emailInstitucional,
    emailSiape: profileData?.email_siape || SUMMARY_DEFAULTS.emailSiape,
    emailSecundario: profileData?.email_secundario_recuperacao || SUMMARY_DEFAULTS.emailSecundario,
    emailNotificacoes: profileData?.email_notificacoes || SUMMARY_DEFAULTS.emailNotificacoes,
    emailGoogleSala: profileData?.email_google_sala || SUMMARY_DEFAULTS.emailGoogleSala,
    telefonesInstitucionais: profileData?.telefones_institucionais || SUMMARY_DEFAULTS.telefonesInstitucionais,
    telefonesPessoais: profileData?.telefones_pessoais || SUMMARY_DEFAULTS.telefonesPessoais,
    emPgd: formatBoolean(Boolean(profileData?.em_pgd)),
    cpf: profileData?.cpf || user?.cpf || SUMMARY_DEFAULTS.cpf,
    username: profileData?.username || user?.username || '-',
    setorNome: profileData?.setor_atual_nome || '-',
    setorAtual: profileData?.setor_atual_nome || SUMMARY_DEFAULTS.setorAtual,
    perfil: profileData?.perfil_display || user?.tipo_display || 'Servidor',
    matriculaServidor: profileData?.matricula_servidor || currentUserMatricula || '-',
    nascimento: formatDate(profileData?.nascimento),
    estadoCivil: profileData?.estado_civil || SUMMARY_DEFAULTS.estadoCivil,
    naturalidade: profileData?.naturalidade || SUMMARY_DEFAULTS.naturalidade,
    sexo: profileData?.sexo || SUMMARY_DEFAULTS.sexo,
    grupoSanguineo: profileData?.grupo_sanguineo_rh || SUMMARY_DEFAULTS.grupoSanguineo,
    dependentesIr: profileData?.dependentes_ir ?? SUMMARY_DEFAULTS.dependentesIr,
    racaEtnia: profileData?.raca_etnia || SUMMARY_DEFAULTS.racaEtnia,
    nomePai: profileData?.nome_pai || SUMMARY_DEFAULTS.nomePai,
    nomeMae: profileData?.nome_mae || SUMMARY_DEFAULTS.nomeMae,
    pisPasep: profileData?.pis_pasep || SUMMARY_DEFAULTS.pisPasep,
    titulacao: profileData?.titulacao || SUMMARY_DEFAULTS.titulacao,
    escolaridade: profileData?.escolaridade || SUMMARY_DEFAULTS.escolaridade,
    endereco: profileData?.endereco?.descricao || SUMMARY_DEFAULTS.endereco,
    identidade: profileData?.identidade || SUMMARY_DEFAULTS.identidade,
    orgaoExpedidor: profileData?.orgao_expedidor || SUMMARY_DEFAULTS.orgaoExpedidor,
    ufRg: profileData?.uf_rg || SUMMARY_DEFAULTS.ufRg,
    dataExpedicao: formatDate(profileData?.data_expedicao),
    tituloEleitor: profileData?.titulo_eleitor_numero || SUMMARY_DEFAULTS.tituloEleitor,
    zonaEleitoral: profileData?.titulo_eleitor_zona || SUMMARY_DEFAULTS.zonaEleitoral,
    secaoEleitoral: profileData?.titulo_eleitor_secao || SUMMARY_DEFAULTS.secaoEleitoral,
    ufTitulo: profileData?.titulo_eleitor_uf || SUMMARY_DEFAULTS.ufTitulo,
    naoTemImpressaoDigital: Boolean(profileData?.nao_tem_impressao_digital),
    ativo: Boolean(profileData?.ativo ?? true),
    regimeTrabalho: profileData?.posicao?.regime_trabalho || SUMMARY_DEFAULTS.regimeTrabalho,
    jornadaTrabalho: profileData?.posicao?.jornada_trabalho || SUMMARY_DEFAULTS.jornadaTrabalho,
    cargoAtual: profileData?.posicao?.cargo_atual || SUMMARY_DEFAULTS.cargoAtual,
    posicaoAtual: profileData?.posicao?.posicao_atual || SUMMARY_DEFAULTS.posicaoAtual,
    classeFuncional: profileData?.posicao?.classe_funcional || SUMMARY_DEFAULTS.classeFuncional,
    nivelFuncional: profileData?.posicao?.nivel_funcional || SUMMARY_DEFAULTS.nivelFuncional,
    banco: profileData?.dados_bancarios?.banco || SUMMARY_DEFAULTS.banco,
    agencia: profileData?.dados_bancarios?.agencia || SUMMARY_DEFAULTS.agencia,
    contaCorrente: profileData?.dados_bancarios?.conta_corrente || SUMMARY_DEFAULTS.contaCorrente,
    ocorrenciasAfastamentos: profileData?.ocorrencias_afastamentos || [],
    setores: profileData?.setores || [],
    historicoFuncional: profileData?.historico_funcional || [],
    ferias: profileData?.ferias || [],
    posicao: profileData?.posicao || {},
  }), [profileData, user, currentUserMatricula])

  const isGeneralTab = activeTab === 'Geral'
  const registryTitle = `${profile.nomeUsual} (${profile.matriculaServidor})`
  const registrySubtitle = [profile.perfil, profile.setorAtual !== '-' ? profile.setorAtual : null].filter(Boolean).join(' • ')
  const ocorrenciasRows = profile.ocorrenciasAfastamentos.map((item) => ({
    ...item,
    inicio: formatDate(item.data_inicio),
    termino: formatDate(item.data_fim),
    totalDias: calculateDays(item.data_inicio, item.data_fim),
    tipoOcorrencia: item.tipo_display || item.titulo || '-',
  }))
  const setoresRows = profile.setores.map((item) => ({
    ...item,
    inicio: formatDate(item.data_inicio),
    fim: formatDate(item.data_fim),
  }))
  const historicoRows = profile.historicoFuncional.map((item) => ({
    ...item,
    dataEvento: formatDate(item.data_evento),
  }))
  const feriasRows = profile.ferias.map((item) => ({
    ...item,
    inicio: formatDate(item.periodo_inicio),
    fim: formatDate(item.periodo_fim),
  }))

  const handleEdit = () => {
    if (!resolvedServidorId) {
      return
    }

    navigate(`/rh/servidores/${resolvedServidorId}/editar`)
  }

  const handleBack = () => {
    navigate(isDirectoryView ? '/rh/servidores' : '/comum/minha_conta/')
  }

  return (
    <div className="page page--wide">
      <nav className="profile-breadcrumb">
        <Link to="/dashboard">Inicio</Link>
        <span className="profile-breadcrumb__sep">&gt;</span>
        {isDirectoryView ? (
          <>
            <Link to="/rh/servidores">Servidores</Link>
            <span className="profile-breadcrumb__sep">&gt;</span>
          </>
        ) : null}
        <span>{registryTitle}</span>
      </nav>

      <div className="profile-status-row">
        <span className={`badge ${profile.ativo ? 'badge--success' : 'badge--warning'}`}>{profile.ativo ? 'Ativo' : 'Inativo'}</span>
        {profile.naoTemImpressaoDigital ? <span className="badge badge--danger">Nao tem impressao digital</span> : null}
      </div>

      <div className="page-header profile-header">
        <div>
          <h1 className="page-title">{registryTitle}</h1>
          <p className="page-subtitle">{registrySubtitle}</p>
        </div>
        <div className="page-header__actions profile-header__actions">
          <button type="button" className="btn btn--primary" onClick={handleEdit} disabled={!resolvedServidorId}><Pencil size={16} /> Editar</button>
          <button type="button" className="btn btn--secondary"><Upload size={16} /> Importar Meus Dados</button>
          <button type="button" className="btn btn--outline" onClick={handleBack}><EllipsisVertical size={16} /> {isDirectoryView ? 'Voltar para listagem' : 'Outras opcoes'}</button>
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
            <InfoItem label="Nome usual" value={profile.nomeUsual} />
            <InfoItem label="E-mail institucional" value={profile.emailInstitucional} />
            <InfoItem label="E-mail SIAPE" value={profile.emailSiape} />
            <InfoItem label="E-mail secundario para Recuperacao de Senha" value={profile.emailSecundario} />
            <InfoItem label="E-mail para notificacoes" value={profile.emailNotificacoes} />
          </div>

          <div className="profile-summary-grid profile-summary-grid--secondary">
            <InfoItem label="E-mail Google Sala de Aula" value={profile.emailGoogleSala} hint />
            <InfoItem label="Telefones institucionais" value={profile.telefonesInstitucionais} />
            <InfoItem label="Telefones pessoais" value={profile.telefonesPessoais} />
            <InfoItem label="Em PGD (dados do suap)" value={profile.emPgd} />
          </div>
        </div>
      </section>

      <div className="profile-tabs">
        {TAB_ITEMS.map((tab) => (
          <button
            key={tab}
            type="button"
            className={`profile-tabs__item ${activeTab === tab ? 'profile-tabs__item--active' : ''}`}
            onClick={() => setActiveTab(tab)}
          >
            {tab}
          </button>
        ))}
      </div>

      <section className="dashboard-card profile-content-card">
        {isError ? <div className="profile-alert profile-alert--error">Nao foi possivel carregar todas as informacoes deste servidor.</div> : null}
        {isGeneralTab ? (
          <>
            <div className="profile-alert">
              Se as informacoes apresentadas estiverem incorretas ou desatualizadas corrija-as no SIGEPE. Se alguma dessas informacoes nao puder ser atualizada diretamente no SIGEPE, procure o setor de recursos humanos do seu campus.
            </div>

            <section className="profile-panel">
              <button type="button" className="profile-panel__header" onClick={() => setPersonalPanelOpen((current) => !current)}>
                <span>Dados pessoais</span>
                <ChevronDown size={18} className={personalPanelOpen ? 'profile-panel__chevron profile-panel__chevron--open' : 'profile-panel__chevron'} />
              </button>

              {personalPanelOpen ? (
                <div className="profile-panel__body">
                  <div className="profile-panel__cpf">CPF: <strong>{profile.cpf}</strong></div>

                  <div className="profile-fields-grid profile-fields-grid--six">
                    <DataField label="Nome do Registro" value={profile.nomeRegistro} />
                    <DataField label="Nascimento" value={profile.nascimento} />
                    <DataField label="Estado Civil" value={profile.estadoCivil} />
                    <DataField label="Naturalidade" value={profile.naturalidade} />
                    <DataField label="Sexo" value={profile.sexo} />
                    <DataField label="G. Sanguineo/RH" value={profile.grupoSanguineo} />
                  </div>

                  <div className="profile-fields-grid profile-fields-grid--six">
                    <DataField label="Dependentes IR" value={profile.dependentesIr} />
                    <DataField label="Raca/Etnia" value={profile.racaEtnia} />
                    <DataField label="Nome do Pai" value={profile.nomePai} />
                    <DataField label="Nome da Mae" value={profile.nomeMae} />
                    <DataField label="PIS/PASEP" value={profile.pisPasep} />
                    <DataField label="Titulacao" value={profile.titulacao} />
                  </div>

                  <div className="profile-fields-grid profile-fields-grid--two-thirds">
                    <DataField label="Escolaridade" value={profile.escolaridade} />
                    <DataField label="Endereco" value={profile.endereco} />
                  </div>

                  <div className="profile-subsection">
                    <h3 className="profile-subsection__title">Registro Geral</h3>
                    <div className="profile-fields-grid profile-fields-grid--four">
                      <DataField label="Identidade" value={profile.identidade} />
                      <DataField label="Orgao Expedidor" value={profile.orgaoExpedidor} />
                      <DataField label="UF" value={profile.ufRg} />
                      <DataField label="Data Expedicao" value={profile.dataExpedicao} />
                    </div>
                  </div>

                  <div className="profile-subsection">
                    <h3 className="profile-subsection__title">Titulo de Eleitor</h3>
                    <div className="profile-fields-grid profile-fields-grid--four">
                      <DataField label="Numero" value={profile.tituloEleitor} />
                      <DataField label="Zona" value={profile.zonaEleitoral} />
                      <DataField label="Secao" value={profile.secaoEleitoral} />
                      <DataField label="UF" value={profile.ufTitulo} />
                    </div>
                  </div>
                </div>
              ) : null}
            </section>

            <section className="profile-panel">
              <button type="button" className="profile-panel__header" onClick={() => setFunctionalPanelOpen((current) => !current)}>
                <span>Dados funcionais</span>
                <ChevronDown size={18} className={functionalPanelOpen ? 'profile-panel__chevron profile-panel__chevron--open' : 'profile-panel__chevron'} />
              </button>

              {functionalPanelOpen ? (
                <div className="profile-panel__body">
                  <div className="profile-fields-grid profile-fields-grid--four">
                    <DataField label="Matricula" value={profile.matriculaServidor} />
                    <DataField label="Setor SUAP" value={profile.setorAtual} />
                    <DataField label="Regime" value={profile.regimeTrabalho} />
                    <DataField label="Jornada de trabalho" value={profile.jornadaTrabalho} />
                  </div>

                  <div className="profile-fields-grid profile-fields-grid--four">
                    <DataField label="Posicao atual" value={profile.posicaoAtual} />
                    <DataField label="Cargo" value={profile.cargoAtual} />
                    <DataField label="Classe do cargo" value={profile.classeFuncional} />
                    <DataField label="Nivel do cargo" value={profile.nivelFuncional} />
                  </div>
                </div>
              ) : null}
            </section>

            <section className="profile-panel">
              <button type="button" className="profile-panel__header" onClick={() => setBankPanelOpen((current) => !current)}>
                <span>Dados bancarios</span>
                <ChevronDown size={18} className={bankPanelOpen ? 'profile-panel__chevron profile-panel__chevron--open' : 'profile-panel__chevron'} />
              </button>

              {bankPanelOpen ? (
                <div className="profile-panel__body">
                  <div className="profile-fields-grid profile-fields-grid--three">
                    <DataField label="Banco" value={profile.banco} />
                    <DataField label="Agencia" value={profile.agencia} />
                    <DataField label="Conta corrente" value={profile.contaCorrente} />
                  </div>
                </div>
              ) : null}
            </section>
          </>
        ) : activeTab === 'Ocorrencias/Afastamentos' ? (
          <TabTableSection
            title="Ocorrencias"
            columns={[
              { key: 'tipoOcorrencia', label: 'Tipo Ocorrencia' },
              { key: 'descricao', label: 'Descricao' },
              { key: 'inicio', label: 'Inicio' },
              { key: 'termino', label: 'Termino' },
              { key: 'totalDias', label: 'Total Dias' },
            ]}
            rows={ocorrenciasRows}
            emptyMessage="Nenhuma ocorrencia ou afastamento cadastrado para este servidor."
          />
        ) : activeTab === 'Setores' ? (
          <TabTableSection
            title="Historico nos Setores SUAP"
            columns={[
              { key: 'setor_nome', label: 'Setor' },
              { key: 'inicio', label: 'Inicio' },
              { key: 'fim', label: 'Fim' },
            ]}
            rows={setoresRows}
            emptyMessage="Nao ha historico em setores SUAP."
            noticeMessage={setoresRows.length <= 1 ? 'Nao ha historico em setores SUAP.' : ''}
          />
        ) : activeTab === 'Historico funcional' ? (
          <TabTableSection
            title="Historico funcional"
            columns={[
              { key: 'titulo', label: 'Evento' },
              { key: 'tipo_evento', label: 'Tipo' },
              { key: 'dataEvento', label: 'Data' },
              { key: 'descricao', label: 'Descricao' },
            ]}
            rows={historicoRows}
            emptyMessage="Nenhum evento do historico funcional foi cadastrado para este servidor."
          />
        ) : activeTab === 'Ferias' ? (
          <TabTableSection
            title="Ferias"
            columns={[
              { key: 'exercicio', label: 'Exercicio' },
              { key: 'inicio', label: 'Inicio' },
              { key: 'fim', label: 'Fim' },
              { key: 'situacao_display', label: 'Situacao' },
              { key: 'observacao', label: 'Observacao' },
            ]}
            rows={feriasRows}
            emptyMessage="Nenhum periodo de ferias foi encontrado para este servidor."
          />
        ) : (
          <div className="profile-empty-tab">
            <h2 className="profile-empty-tab__title">{activeTab}</h2>
            <p>Esta aba ainda nao foi detalhada no frontend, mas a estrutura da tela de perfil ja esta preparada para receber esse conteudo.</p>
          </div>
        )}
      </section>
    </div>
  )
}