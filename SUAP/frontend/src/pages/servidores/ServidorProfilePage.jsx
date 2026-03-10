import { useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { ChevronDown, CircleHelp, EllipsisVertical, Pencil, Upload, UserRound } from 'lucide-react'
import { Link, useParams } from 'react-router-dom'

import { authApi, servidoresApi } from '@/api/endpoints'
import { useAuth } from '@/context/AuthContext'

const TAB_ITEMS = [
  'Geral',
  'Ocorrencias/Afastamentos',
  'Setores',
  'Historico funcional',
  'Ferias',
  'Posicao',
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

function TabList({ title, items, renderItem, emptyMessage }) {
  return (
    <div className="profile-empty-tab">
      <h2 className="profile-empty-tab__title">{title}</h2>
      {items?.length ? (
        <div className="records-list">
          {items.map((item) => (
            <article key={item.id} className="dashboard-card profile-record-card">
              {renderItem(item)}
            </article>
          ))}
        </div>
      ) : (
        <p>{emptyMessage}</p>
      )}
    </div>
  )
}

export default function ServidorProfilePage() {
  const { user } = useAuth()
  const { matricula } = useParams()
  const [activeTab, setActiveTab] = useState('Geral')
  const [panelOpen, setPanelOpen] = useState(true)

  const { data: meData } = useQuery({
    queryKey: ['auth-me', 'profile-page'],
    queryFn: () => authApi.me().then((response) => response.data),
    staleTime: 60_000,
  })

  const currentUserId = meData?.id || user?.id
  const currentUserMatricula = matricula || meData?.matricula_servidor || user?.matricula_servidor

  const { data: profileData } = useQuery({
    queryKey: ['servidor-profile', currentUserMatricula || currentUserId],
    queryFn: () => {
      if (currentUserMatricula) {
        return servidoresApi.profileByMatricula(currentUserMatricula).then((response) => response.data)
      }
      return servidoresApi.profile(currentUserId).then((response) => response.data)
    },
    enabled: Boolean(currentUserMatricula || currentUserId),
    staleTime: 60_000,
  })

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
    ocorrenciasAfastamentos: profileData?.ocorrencias_afastamentos || [],
    setores: profileData?.setores || [],
    historicoFuncional: profileData?.historico_funcional || [],
    ferias: profileData?.ferias || [],
    posicao: profileData?.posicao || {},
  }), [profileData, user, currentUserMatricula])

  const isGeneralTab = activeTab === 'Geral'

  return (
    <div className="page page--wide">
      <nav className="profile-breadcrumb">
        <Link to="/dashboard">Inicio</Link>
        <span className="profile-breadcrumb__sep">&gt;</span>
        <span>{profile.nomeUsual} ({profile.matriculaServidor})</span>
      </nav>

      <div className="profile-status-row">
        <span className={`badge ${profile.ativo ? 'badge--success' : 'badge--warning'}`}>{profile.ativo ? 'Ativo' : 'Inativo'}</span>
        {profile.naoTemImpressaoDigital ? <span className="badge badge--danger">Nao tem impressao digital</span> : null}
      </div>

      <div className="page-header profile-header">
        <div>
          <h1 className="page-title">{profile.nomeUsual} ({profile.matriculaServidor})</h1>
          <p className="page-subtitle">{profile.perfil}</p>
        </div>
        <div className="page-header__actions profile-header__actions">
          <button type="button" className="btn btn--primary"><Pencil size={16} /> Editar</button>
          <button type="button" className="btn btn--secondary"><Upload size={16} /> Importar Meus Dados</button>
          <button type="button" className="btn btn--outline"><EllipsisVertical size={16} /> Outras opcoes</button>
          <button type="button" className="btn btn--outline"><UserRound size={16} /> Minha conta</button>
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
        {isGeneralTab ? (
          <>
            <div className="profile-alert">
              Se as informacoes apresentadas estiverem incorretas ou desatualizadas corrija-as no SIGEPE. Se alguma dessas informacoes nao puder ser atualizada diretamente no SIGEPE, procure o setor de recursos humanos do seu campus.
            </div>

            <section className="profile-panel">
              <button type="button" className="profile-panel__header" onClick={() => setPanelOpen((current) => !current)}>
                <span>Dados pessoais</span>
                <ChevronDown size={18} className={panelOpen ? 'profile-panel__chevron profile-panel__chevron--open' : 'profile-panel__chevron'} />
              </button>

              {panelOpen ? (
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
          </>
        ) : activeTab === 'Ocorrencias/Afastamentos' ? (
          <TabList
            title="Ocorrencias/Afastamentos"
            items={profile.ocorrenciasAfastamentos}
            emptyMessage="Nenhuma ocorrencia ou afastamento cadastrado para este servidor."
            renderItem={(item) => (
              <>
                <div className="page-header page-header--compact">
                  <div>
                    <h3 className="page-title">{item.titulo}</h3>
                    <p className="page-subtitle">{item.tipo_display} • {item.situacao_display}</p>
                  </div>
                </div>
                <div className="profile-fields-grid profile-fields-grid--three">
                  <DataField label="Periodo" value={formatPeriod(item.data_inicio, item.data_fim)} />
                  <DataField label="Situacao" value={item.situacao_display} />
                  <DataField label="Tipo" value={item.tipo_display} />
                </div>
                <DataField label="Descricao" value={item.descricao || '-'} />
              </>
            )}
          />
        ) : activeTab === 'Setores' ? (
          <TabList
            title="Setores"
            items={profile.setores}
            emptyMessage="Nenhum historico de lotacao foi encontrado para este servidor."
            renderItem={(item) => (
              <>
                <div className="page-header page-header--compact">
                  <div>
                    <h3 className="page-title">{item.setor_nome || '-'}</h3>
                    <p className="page-subtitle">{item.tipo_vinculo || 'Lotacao'}</p>
                  </div>
                </div>
                <div className="profile-fields-grid profile-fields-grid--four">
                  <DataField label="Codigo" value={item.setor_codigo || '-'} />
                  <DataField label="Sigla" value={item.setor_sigla || '-'} />
                  <DataField label="Principal" value={formatBoolean(Boolean(item.principal))} />
                  <DataField label="Periodo" value={formatPeriod(item.data_inicio, item.data_fim)} />
                </div>
                <DataField label="Observacao" value={item.observacao || '-'} />
              </>
            )}
          />
        ) : activeTab === 'Historico funcional' ? (
          <TabList
            title="Historico funcional"
            items={profile.historicoFuncional}
            emptyMessage="Nenhum evento do historico funcional foi cadastrado para este servidor."
            renderItem={(item) => (
              <>
                <div className="page-header page-header--compact">
                  <div>
                    <h3 className="page-title">{item.titulo}</h3>
                    <p className="page-subtitle">{item.tipo_evento || 'Evento funcional'}</p>
                  </div>
                </div>
                <div className="profile-fields-grid profile-fields-grid--two">
                  <DataField label="Data do evento" value={formatDate(item.data_evento)} />
                  <DataField label="Tipo" value={item.tipo_evento || '-'} />
                </div>
                <DataField label="Descricao" value={item.descricao || '-'} />
              </>
            )}
          />
        ) : activeTab === 'Ferias' ? (
          <TabList
            title="Ferias"
            items={profile.ferias}
            emptyMessage="Nenhum periodo de ferias foi encontrado para este servidor."
            renderItem={(item) => (
              <>
                <div className="page-header page-header--compact">
                  <div>
                    <h3 className="page-title">Exercicio {item.exercicio}</h3>
                    <p className="page-subtitle">{item.situacao_display}</p>
                  </div>
                </div>
                <div className="profile-fields-grid profile-fields-grid--three">
                  <DataField label="Periodo" value={formatPeriod(item.periodo_inicio, item.periodo_fim)} />
                  <DataField label="Situacao" value={item.situacao_display} />
                  <DataField label="Exercicio" value={item.exercicio} />
                </div>
                <DataField label="Observacao" value={item.observacao || '-'} />
              </>
            )}
          />
        ) : activeTab === 'Posicao' ? (
          <div className="profile-empty-tab">
            <h2 className="profile-empty-tab__title">Posicao</h2>
            <div className="profile-fields-grid profile-fields-grid--five">
              <DataField label="Posicao atual" value={profile.posicao?.posicao_atual || '-'} />
              <DataField label="Cargo" value={profile.posicao?.cargo_atual || '-'} />
              <DataField label="Jornada" value={profile.posicao?.jornada_trabalho || '-'} />
              <DataField label="Classe" value={profile.posicao?.classe_funcional || '-'} />
              <DataField label="Nivel" value={profile.posicao?.nivel_funcional || '-'} />
            </div>
            <div className="profile-fields-grid profile-fields-grid--two">
              <DataField label="Setor atual" value={profile.posicao?.setor_atual || '-'} />
              <DataField label="Perfil funcional" value={profile.perfil} />
            </div>
          </div>
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