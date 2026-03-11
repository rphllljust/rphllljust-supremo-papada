import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { Bell, CalendarClock, ClipboardList, FileClock, School2, Sparkles, TriangleAlert } from 'lucide-react'

import { dashboardApi } from '@/api/endpoints'
import StatCard from '@/components/ui/StatCard'
import { useAuth } from '@/context/AuthContext'

const STATS_CONFIG = [
  { key: 'recent_enrollments', label: 'Matrículas nos últimos 7 dias', icon: ClipboardList, color: '#1351B4' },
  { key: 'document_pending', label: 'Pendências documentais', icon: FileClock, color: '#B35C00' },
  { key: 'classes_without_students', label: 'Turmas sem alunos', icon: School2, color: '#7A1CAC' },
  { key: 'system_alerts', label: 'Avisos não lidos', icon: Bell, color: '#155BCB' },
  { key: 'upcoming_deadlines', label: 'Prazos nos próximos 7 dias', icon: CalendarClock, color: '#1A7F5A' },
]

export default function DashboardPage() {
  const { user } = useAuth()

  const { data, isLoading, isError } = useQuery({
    queryKey: ['dashboard-overview'],
    queryFn: () => dashboardApi.overview().then((response) => response.data),
    staleTime: 30_000,
    refetchInterval: 60_000,
  })

  const stats = data?.summary || {}

  return (
    <div className="dashboard-page">
      <div className="page-header">
        <h1 className="page-title">Dashboard</h1>
        <p className="page-subtitle">
          Bem-vindo(a), <strong>{user?.nome_completo || user?.username}</strong>
        </p>
      </div>

      {isError ? (
        <div className="alert alert--error">
          Não foi possível carregar os dados do painel. Verifique a autenticação e a API.
        </div>
      ) : null}

      <div className="stats-grid">
        {STATS_CONFIG.map(({ key, label, icon, color }) => (
          <StatCard
            key={key}
            label={label}
            value={stats[key]}
            icon={icon}
            color={color}
            loading={isLoading}
          />
        ))}
      </div>

      <div className="dashboard-grid">
        <SectionCard title="Matrículas recentes" icon={ClipboardList} emptyMessage="Nenhuma matrícula recente encontrada.">
          {(data?.recent_matriculas || []).map((item) => (
            <LinkedListItem
              key={item.id}
              to={item.href}
              title={item.aluno_nome}
              subtitle={`${item.numero_matricula} • ${item.curso_nome} • ${item.turma_nome}`}
              meta={formatDate(item.data_matricula)}
              badge={{ label: item.status_display, tone: getStatusTone(item.status) }}
            />
          ))}
        </SectionCard>

        <SectionCard title="Pendências de documentos" icon={TriangleAlert} emptyMessage="Nenhuma pendência documental aberta.">
          {(data?.document_pending || []).map((item) => (
            <LinkedListItem
              key={item.id}
              to={item.href}
              title={item.descricao}
              subtitle={`${item.aluno_nome} • ${item.numero_matricula}`}
              meta={item.prazo ? `Prazo: ${formatDate(item.prazo)}` : 'Sem prazo definido'}
              badge={{ label: item.status_display, tone: 'warning' }}
            />
          ))}
        </SectionCard>

        <SectionCard title="Turmas sem alunos" icon={School2} emptyMessage="Nenhuma turma ativa sem alunos no momento.">
          {(data?.turmas_sem_alunos || []).map((item) => (
            <LinkedListItem
              key={item.id}
              to={item.href}
              title={item.nome}
              subtitle={`${item.curso_nome} • ${item.ano_letivo}`}
              meta={item.status_display}
              badge={{ label: 'Sem alunos', tone: 'danger' }}
            />
          ))}
        </SectionCard>

        <SectionCard title="Avisos do sistema" icon={Bell} emptyMessage="Nenhum aviso disponível.">
          {(data?.system_alerts || []).map((item) => (
            <LinkedListItem
              key={item.id}
              to={item.href}
              title={item.titulo}
              subtitle={item.resumo || item.categoria_titulo}
              meta={formatDateTime(item.data_evento)}
              badge={{ label: item.is_unread ? 'Novo' : item.tipo_display, tone: item.is_unread ? 'success' : 'info' }}
            />
          ))}
        </SectionCard>

        <QuickLinksSection />

        <SectionCard title="Atividades recentes" icon={Sparkles} emptyMessage="Nenhuma atividade recente encontrada.">
          {(data?.recent_activities || []).map((item, index) => (
            <LinkedListItem
              key={`${item.kind}-${index}-${item.title}`}
              to={item.href}
              title={item.title}
              subtitle={item.description}
              meta={formatActivityDate(item.date)}
              badge={{ label: getActivityLabel(item.kind), tone: item.badge }}
            />
          ))}
        </SectionCard>

        <SectionCard title="Próximos prazos" icon={CalendarClock} emptyMessage="Nenhum prazo próximo encontrado.">
          {(data?.upcoming_deadlines || []).map((item) => (
            <LinkedListItem
              key={item.id}
              to={item.href}
              title={item.descricao}
              subtitle={`${item.aluno_nome} • ${item.numero_matricula}`}
              meta={`Vence em ${formatDate(item.prazo)}`}
              badge={{ label: getDeadlineLabel(item.prazo), tone: getDeadlineTone(item.prazo) }}
            />
          ))}
        </SectionCard>
      </div>
    </div>
  )
}

function QuickLinksSection() {
  const quickLinks = [
    { href: '/matriculas', label: 'Nova Matrícula' },
    { href: '/documentos', label: 'Pendências de Documentos' },
    { href: '/turmas', label: 'Gerenciar Turmas' },
    { href: '/comum/notificacoes', label: 'Avisos do Sistema' },
    { href: '/ensino/areacurso/', label: 'Áreas de Cursos' },
    { href: '/estagio', label: 'Próximos Prazos de Estágio' },
  ]

  return (
    <div className="dashboard-card dashboard-section-card">
      <h2 className="dashboard-card__title">Atalhos frequentes</h2>
      <div className="quick-links">
        {quickLinks.map(({ href, label }) => (
          <Link key={href} to={href} className="quick-link">
            {label}
          </Link>
        ))}
      </div>
    </div>
  )
}

function SectionCard({ title, icon: Icon, children, emptyMessage }) {
  const items = Array.isArray(children) ? children.filter(Boolean) : [children].filter(Boolean)

  return (
    <section className="dashboard-card dashboard-section-card">
      <div className="dashboard-section-card__header">
        <h2 className="dashboard-card__title">
          {Icon ? <Icon size={18} /> : null}
          <span>{title}</span>
        </h2>
      </div>
      {items.length ? <div className="dashboard-list">{items}</div> : <p className="dashboard-empty">{emptyMessage}</p>}
    </section>
  )
}

function LinkedListItem({ to, title, subtitle, meta, badge }) {
  return (
    <Link to={to} className="dashboard-list-item">
      <div className="dashboard-list-item__content">
        <strong className="dashboard-list-item__title">{title}</strong>
        <span className="dashboard-list-item__subtitle">{subtitle}</span>
      </div>
      <div className="dashboard-list-item__meta">
        {badge ? <span className={`badge badge--${badge.tone || 'secondary'}`}>{badge.label}</span> : null}
        {meta ? <span className="dashboard-list-item__date">{meta}</span> : null}
      </div>
    </Link>
  )
}

function formatDate(value) {
  if (!value) return '-'
  const date = new Date(`${value}T00:00:00`)
  if (Number.isNaN(date.getTime())) return value
  return new Intl.DateTimeFormat('pt-BR').format(date)
}

function formatDateTime(value) {
  if (!value) return '-'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return new Intl.DateTimeFormat('pt-BR', { dateStyle: 'short', timeStyle: 'short' }).format(date)
}

function formatActivityDate(value) {
  if (!value) return '-'
  const date = new Date(value)
  if (!Number.isNaN(date.getTime())) {
    return new Intl.DateTimeFormat('pt-BR', { dateStyle: 'short', timeStyle: 'short' }).format(date)
  }
  return formatDate(value)
}

function getStatusTone(status) {
  switch (status) {
    case 'ATIVA':
      return 'success'
    case 'TRANCADA':
      return 'warning'
    case 'CANCELADA':
      return 'danger'
    case 'CONCLUIDA':
      return 'info'
    default:
      return 'secondary'
  }
}

function getActivityLabel(kind) {
  switch (kind) {
    case 'matricula':
      return 'Matrícula'
    case 'pendencia':
      return 'Pendência'
    case 'aviso':
      return 'Aviso'
    default:
      return 'Atividade'
  }
}

function getDeadlineTone(value) {
  if (!value) return 'secondary'
  const today = new Date()
  const deadline = new Date(`${value}T00:00:00`)
  const diffDays = Math.ceil((deadline - new Date(today.getFullYear(), today.getMonth(), today.getDate())) / 86400000)
  if (diffDays <= 1) return 'danger'
  if (diffDays <= 3) return 'warning'
  return 'info'
}

function getDeadlineLabel(value) {
  if (!value) return 'Sem prazo'
  const today = new Date()
  const deadline = new Date(`${value}T00:00:00`)
  const diffDays = Math.ceil((deadline - new Date(today.getFullYear(), today.getMonth(), today.getDate())) / 86400000)
  if (diffDays <= 0) return 'Hoje'
  if (diffDays === 1) return 'Amanhã'
  return `${diffDays} dias`
}
