import { useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { ArrowRight, Bell, CalendarClock, ClipboardList, FileClock, School2, SlidersHorizontal, TriangleAlert } from 'lucide-react'

import { dashboardApi } from '@/api/endpoints'
import StatCard from '@/components/ui/StatCard'
import { useAuth } from '@/context/AuthContext'
import { sidebarItems } from '@/components/layout/sidebarItems'
import { getQuickAccessItems } from '@/utils/quickAccess'

const STATS_CONFIG = [
  { key: 'recent_enrollments', label: 'Matriculas (7 dias)', icon: ClipboardList, color: '#1a8d61' },
  { key: 'document_pending', label: 'Pendencias documentais', icon: FileClock, color: '#f59d0c' },
  { key: 'classes_without_students', label: 'Turmas sem alunos', icon: School2, color: '#8b5cf6' },
  { key: 'system_alerts', label: 'Avisos nao lidos', icon: Bell, color: '#2f73da' },
  { key: 'upcoming_deadlines', label: 'Prazos da semana', icon: CalendarClock, color: '#1c9b72' },
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
  const series = useMemo(() => buildEnrollmentSeries(data?.recent_matriculas || []), [data?.recent_matriculas])
  const periodTotal = Number(stats.recent_enrollments || 0)
  const periodAverage = periodTotal > 0 ? periodTotal / 7 : 0

  return (
    <div className="dashboard-page page page--wide dashboard-admin">
      <section className="dashboard-admin__heading">
        <div>
          <h1 className="dashboard-admin__title">Dashboard Administrativo</h1>
          <p className="dashboard-admin__subtitle">
            Visao geral da operacao academica e administrativa para <strong>{user?.nome_completo || user?.username}</strong>.
          </p>
        </div>
        <div className="dashboard-admin__heading-actions">
          <span className="dashboard-admin__date">{formatFullDate(new Date())}</span>
          <button type="button" className="btn btn--outline btn--sm">
            <SlidersHorizontal size={14} />
            <span>Personalizar</span>
          </button>
        </div>
      </section>

      {isError ? (
        <div className="alert alert--error">
          Nao foi possivel carregar os dados do painel. Verifique a autenticacao e a API.
        </div>
      ) : null}

      <div className="stats-grid stats-grid--legacy dashboard-admin__kpis">
        {STATS_CONFIG.map(({ key, label, icon, color }) => (
          <StatCard key={key} label={label} value={stats[key]} icon={icon} color={color} loading={isLoading} />
        ))}
      </div>

      <section className="dashboard-admin__core-grid">
        <article className="dashboard-card dashboard-admin__chart-card">
          <div className="dashboard-section-card__header dashboard-admin__section-headline">
            <h2 className="dashboard-card__title">
              <ClipboardList size={18} />
              <span>Resumo de matriculas</span>
            </h2>
            <div className="dashboard-admin__chart-filters">
              <button type="button" className="btn btn--outline btn--sm">Ultimos 7 dias</button>
              <button type="button" className="btn btn--outline btn--sm">Por dia</button>
            </div>
          </div>

          <EnrollmentChart series={series} />

          <div className="dashboard-admin__metrics-row">
            <MetricItem label="Total no periodo" value={formatInteger(periodTotal)} meta="matriculas" />
            <MetricItem label="Media diaria" value={formatDecimal(periodAverage)} meta="matriculas" />
            <MetricItem label="Maior pico" value={formatInteger(series.peak)} meta={`em ${series.peakLabel}`} />
            <MetricItem label="Variacao" value={series.changeLabel} meta="vs. inicio do periodo" highlight={series.change >= 0} />
          </div>
        </article>

        <article className="dashboard-card dashboard-section-card">
          <div className="dashboard-section-card__header dashboard-admin__section-headline">
            <h2 className="dashboard-card__title">
              <Bell size={18} />
              <span>Central de avisos</span>
            </h2>
            <Link to="/comum/notificacoes" className="dashboard-inline-link">
              Ver todos
              <ArrowRight size={14} />
            </Link>
          </div>

          {(data?.system_alerts || []).length ? (
            <div className="dashboard-admin__alerts-list">
              {(data?.system_alerts || []).map((item) => (
                <Link key={item.id} to={item.href} className={`dashboard-admin__alert-card dashboard-admin__alert-card--${getAlertTone(item)}`}>
                  <div className="dashboard-admin__alert-title">{item.titulo}</div>
                  <div className="dashboard-admin__alert-subtitle">{item.resumo || item.categoria_titulo}</div>
                  <div className="dashboard-admin__alert-meta">Publicado em {formatDateTime(item.data_evento)}</div>
                </Link>
              ))}
            </div>
          ) : (
            <p className="dashboard-empty">Nenhum aviso disponivel.</p>
          )}
        </article>
      </section>

      <section className="dashboard-admin__bottom-grid">
        <SectionCard title="Movimento recente" icon={ClipboardList} emptyMessage="Nenhuma matricula recente encontrada.">
          {(data?.recent_matriculas || []).map((item) => (
            <LinkedListItem
              key={item.id}
              to={item.href}
              title={item.aluno_nome}
              subtitle={`${item.numero_matricula} - ${item.curso_nome} - ${item.turma_nome}`}
              meta={formatDate(item.data_matricula)}
              badge={{ label: item.status_display, tone: getStatusTone(item.status) }}
            />
          ))}
        </SectionCard>

        <SectionCard title="Pendencias prioritarias" icon={TriangleAlert} emptyMessage="Nenhuma pendencia documental aberta.">
          {(data?.document_pending || []).map((item) => (
            <LinkedListItem
              key={item.id}
              to={item.href}
              title={item.descricao}
              subtitle={`${item.aluno_nome} - ${item.numero_matricula}`}
              meta={item.prazo ? `Prazo: ${formatDate(item.prazo)}` : 'Sem prazo definido'}
              badge={{ label: item.status_display, tone: 'warning' }}
            />
          ))}
        </SectionCard>

        <QuickLinksSection />
      </section>
    </div>
  )
}

function QuickLinksSection() {
  const { user } = useAuth()
  const quickLinks = getQuickAccessItems(user, sidebarItems, 6)

  return (
    <div className="dashboard-card dashboard-section-card">
      <div className="dashboard-section-card__header dashboard-admin__section-headline">
        <h2 className="dashboard-card__title">Acessos rapidos</h2>
      </div>
      {quickLinks.length > 0 ? (
        <div className="dashboard-admin__quick-grid">
          {quickLinks.map(({ id, to, label }) => (
            <Link key={id} to={to} className="dashboard-admin__quick-card">
              <span>{label}</span>
              <small>Acessar</small>
            </Link>
          ))}
        </div>
      ) : (
        <p className="dashboard-empty">Os atalhos serao preenchidos conforme voce acessar os modulos.</p>
      )}
    </div>
  )
}

function SectionCard({ title, icon: Icon, children, emptyMessage }) {
  const items = Array.isArray(children) ? children.filter(Boolean) : [children].filter(Boolean)

  return (
    <section className="dashboard-card dashboard-section-card">
      <div className="dashboard-section-card__header dashboard-admin__section-headline">
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

function EnrollmentChart({ series }) {
  if (!series.points.length) {
    return <p className="dashboard-empty">Sem dados suficientes para exibir o grafico no periodo.</p>
  }

  const maxValue = Math.max(...series.points.map((point) => point.value), 1)
  const pointDistance = series.points.length > 1 ? 100 / (series.points.length - 1) : 100
  const path = series.points
    .map((point, index) => {
      const x = index * pointDistance
      const y = 100 - (point.value / maxValue) * 100
      return `${x},${y}`
    })
    .join(' ')

  return (
    <div className="dashboard-admin__chart">
      <svg viewBox="0 0 100 100" preserveAspectRatio="none" aria-hidden="true">
        <polyline points={path} className="dashboard-admin__chart-line" />
      </svg>
      <div className="dashboard-admin__chart-labels">
        {series.points.map((point) => (
          <span key={point.label}>{point.label}</span>
        ))}
      </div>
    </div>
  )
}

function MetricItem({ label, value, meta, highlight = false }) {
  return (
    <div className="dashboard-admin__metric-item">
      <span>{label}</span>
      <strong className={highlight ? 'dashboard-admin__metric-value dashboard-admin__metric-value--positive' : 'dashboard-admin__metric-value'}>{value}</strong>
      <small>{meta}</small>
    </div>
  )
}

function buildEnrollmentSeries(items) {
  const today = new Date()
  const dayKeys = []
  const map = new Map()

  for (let index = 6; index >= 0; index -= 1) {
    const date = new Date(today)
    date.setDate(today.getDate() - index)
    const key = formatISODate(date)
    dayKeys.push(key)
    map.set(key, 0)
  }

  items.forEach((item) => {
    const key = formatISODate(new Date(`${item.data_matricula}T00:00:00`))
    if (map.has(key)) {
      map.set(key, map.get(key) + 1)
    }
  })

  let runningTotal = 0
  const points = dayKeys.map((key) => {
    runningTotal += map.get(key) || 0
    return {
      label: formatShortDateLabel(key),
      value: runningTotal,
      daily: map.get(key) || 0,
    }
  })

  const peakPoint = [...points].sort((left, right) => right.daily - left.daily)[0] || null
  const first = points[0]?.value || 0
  const last = points[points.length - 1]?.value || 0
  const change = first > 0 ? ((last - first) / first) * 100 : (last > 0 ? 100 : 0)

  return {
    points,
    peak: peakPoint?.daily || 0,
    peakLabel: peakPoint?.label || '-',
    change,
    changeLabel: `${change >= 0 ? '+' : ''}${formatDecimal(change)}%`,
  }
}

function formatISODate(date) {
  if (!(date instanceof Date) || Number.isNaN(date.getTime())) return ''
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

function formatShortDateLabel(value) {
  const date = new Date(`${value}T00:00:00`)
  if (Number.isNaN(date.getTime())) return value
  return new Intl.DateTimeFormat('pt-BR', { day: '2-digit', month: '2-digit' }).format(date)
}

function formatFullDate(value) {
  const date = value instanceof Date ? value : new Date(value)
  if (Number.isNaN(date.getTime())) return '-'
  const formatted = new Intl.DateTimeFormat('pt-BR', {
    weekday: 'long',
    day: '2-digit',
    month: 'long',
    year: 'numeric',
  }).format(date)
  return formatted.charAt(0).toUpperCase() + formatted.slice(1)
}

function formatInteger(value) {
  return new Intl.NumberFormat('pt-BR', { maximumFractionDigits: 0 }).format(Number(value || 0))
}

function formatDecimal(value) {
  return new Intl.NumberFormat('pt-BR', { maximumFractionDigits: 1, minimumFractionDigits: 1 }).format(Number(value || 0))
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

function getAlertTone(item) {
  const text = `${item?.tipo_display || ''} ${item?.categoria_titulo || ''}`.toLowerCase()
  if (text.includes('alerta') || text.includes('critico') || text.includes('urgente')) return 'warning'
  if (text.includes('sucesso')) return 'success'
  if (text.includes('info')) return 'info'
  return item?.is_unread ? 'warning' : 'info'
}

