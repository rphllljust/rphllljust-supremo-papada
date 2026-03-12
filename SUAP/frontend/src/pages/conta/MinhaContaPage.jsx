import { useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Eye, FileText, KeyRound, LogOut, Mail, Shield, UserRound } from 'lucide-react'
import { Link, useNavigate } from 'react-router-dom'

import { servidoresApi } from '@/api/endpoints'
import { useAuth } from '@/context/AuthContext'

function formatDateTime(value) {
  if (!value) {
    return 'Sem data informada'
  }

  const date = new Date(value)
  if (Number.isNaN(date.getTime())) {
    return value
  }

  return new Intl.DateTimeFormat('pt-BR', {
    dateStyle: 'short',
    timeStyle: 'medium',
  }).format(date)
}

function SummaryField({ label, value }) {
  return (
    <div className="account-summary-field">
      <span className="account-summary-field__label">{label}</span>
      <strong className="account-summary-field__value">{value || '-'}</strong>
    </div>
  )
}

function ShortcutCard({ to, icon: Icon, title, description }) {
  return (
    <Link to={to} className="account-shortcut-card">
      <span className="account-shortcut-card__icon">
        <Icon size={36} />
      </span>
      <strong className="account-shortcut-card__title">{title}</strong>
      <p className="account-shortcut-card__description">{description}</p>
    </Link>
  )
}

export default function MinhaContaPage() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  const { data: profileData } = useQuery({
    queryKey: ['servidor-my-profile'],
    queryFn: () => servidoresApi.myProfile().then((response) => response.data),
    staleTime: 60_000,
  })

  const registryLink = useMemo(() => {
    if (!user?.id) {
      return '/rh/servidores'
    }

    return `/rh/servidores/${user.id}`
  }, [user?.id])

  const summary = useMemo(() => ({
    nome: profileData?.nome_usual || profileData?.nome_registro || user?.nome_completo || user?.username || '-',
    perfil: profileData?.perfil_display || user?.tipo_display || 'Servidor',
    matricula: profileData?.matricula_servidor || user?.matricula_servidor || '-',
    usuario: profileData?.username || user?.username || '-',
    id: profileData?.usuario || user?.id || '-',
    emailInstitucional: profileData?.email_institucional || user?.email || '-',
    emailNotificacoes: profileData?.email_notificacoes || profileData?.email_secundario_recuperacao || '-',
    setor: profileData?.setor_atual_nome || '-',
    ultimoLogin: formatDateTime(profileData?.ultimo_login),
    dataRegistro: formatDateTime(profileData?.data_registro),
  }), [profileData, user])

  const historyItems = useMemo(() => {
    if (profileData?.historico_funcional?.length) {
      return profileData.historico_funcional.slice(0, 5).map((item) => ({
        id: item.id,
        title: item.titulo || summary.perfil,
        description: item.descricao || 'Registro funcional sincronizado com o perfil do servidor.',
        date: item.data_evento,
      }))
    }

    return [
      {
        id: 'perfil-atual',
        title: summary.perfil,
        description: `Conta vinculada ao cadastro de ${summary.nome}.`,
        date: profileData?.data_registro || null,
      },
    ]
  }, [profileData?.data_registro, profileData?.historico_funcional, summary.nome, summary.perfil])

  const handleLogout = () => {
    logout().finally(() => navigate('/login'))
  }

  return (
    <div className="page page--wide account-page">
      <nav className="profile-breadcrumb">
        <Link to="/dashboard">Inicio</Link>
        <span className="profile-breadcrumb__sep">&gt;</span>
        <span>Minha conta: {summary.nome}</span>
      </nav>

      <div className="account-page__header">
        <div>
          <h1 className="page-title">Minha conta: {summary.nome}</h1>
          <p className="page-subtitle">Resumo da conta autenticada e do vinculo funcional atual.</p>
        </div>

        <button type="button" className="btn btn--danger" onClick={handleLogout}>
          <LogOut size={16} /> Sair do sistema
        </button>
      </div>

      <div className="account-page__layout">
        <section className="dashboard-card account-card">
          <div className="account-card__toolbar">
            <Link to="/comum/alterar-senha" className="btn btn--secondary btn--sm">
              <KeyRound size={16} /> Alterar senha
            </Link>
            <Link
              to="/indisponivel/alterar-emails"
              state={{
                title: 'Alterar e-mails',
                description: 'A edicao dos e-mails da conta ainda nao possui uma tela dedicada neste frontend.',
              }}
              className="btn btn--secondary btn--sm"
            >
              <Mail size={16} /> Alterar emails
            </Link>
            <Link to={registryLink} className="btn btn--outline btn--sm">
              <Eye size={16} /> Vinculo
            </Link>
          </div>

          <div className="account-card__body">
            <div className="account-card__avatar">
              <div className="account-card__avatar-placeholder">
                <UserRound size={76} />
              </div>
            </div>

            <div className="account-card__content">
              <p className="account-card__title">
                Meu vinculo: <strong>{summary.perfil}</strong>
              </p>

              <div className="account-summary-grid">
                <SummaryField label="Nome" value={summary.nome} />
                <SummaryField label="Usuario" value={summary.usuario} />
                <SummaryField label="ID de usuario" value={summary.id} />
                <SummaryField label="Matricula" value={summary.matricula} />
                <SummaryField label="Setor atual" value={summary.setor} />
                <SummaryField label="Ultimo login" value={summary.ultimoLogin} />
                <SummaryField label="Data de registro" value={summary.dataRegistro} />
                <SummaryField label="E-mail institucional" value={summary.emailInstitucional} />
                <SummaryField label="E-mail para notificacoes" value={summary.emailNotificacoes} />
              </div>
            </div>
          </div>
        </section>

        <aside className="dashboard-card account-history">
          <div>
            <h2 className="account-history__title">Historico em grupos</h2>
          </div>

          <div className="account-timeline">
            {historyItems.map((item) => (
              <article key={item.id} className="account-timeline__item">
                <span className="account-timeline__date">{formatDateTime(item.date)}</span>
                <div className="account-timeline__card">
                  <strong>{item.title}</strong>
                  <p>{item.description}</p>
                </div>
              </article>
            ))}
          </div>

          <Link to={registryLink} className="btn btn--outline btn--sm account-history__link">
            <Eye size={16} /> Ver cadastro completo
          </Link>
        </aside>
      </div>

      <section className="account-shortcuts">
        <ShortcutCard
          to={registryLink}
          icon={Shield}
          title="Meu cadastro"
          description="Abra a listagem de servidores e consulte os dados funcionais vinculados a sua conta."
        />
        <ShortcutCard
          to="/comum/notificacoes"
          icon={UserRound}
          title="Acoes"
          description="Centralize alteracao de senha, notificacoes e outras configuracoes ligadas ao seu acesso."
        />
        <ShortcutCard
          to="/documentos"
          icon={FileText}
          title="Meus documentos"
          description="Acesse rapidamente os documentos emitidos e os modulos associados ao seu perfil atual."
        />
      </section>
    </div>
  )
}