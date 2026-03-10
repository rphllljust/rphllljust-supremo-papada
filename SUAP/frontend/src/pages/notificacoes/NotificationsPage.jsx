import { useEffect, useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Eye, EyeOff, Mail, Settings2, ShieldAlert, Trash2 } from 'lucide-react'
import { Link, useNavigate } from 'react-router-dom'
import toast from 'react-hot-toast'

import { notificacoesApi } from '@/api/endpoints'

function formatDateTime(value) {
  if (!value) {
    return '-'
  }

  const date = new Date(value)
  if (Number.isNaN(date.getTime())) {
    return value
  }

  return new Intl.DateTimeFormat('pt-BR', {
    dateStyle: 'long',
    timeStyle: 'short',
  }).format(date)
}

function channelLabel(notification) {
  if (notification.via_suap && notification.via_email) {
    return 'SUAP e E-mail'
  }
  if (notification.via_email) {
    return 'E-mail'
  }
  return 'SUAP'
}

function messageLines(message) {
  return String(message || '').split('\n').filter(Boolean)
}

export default function NotificationsPage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [search, setSearch] = useState('')
  const [page, setPage] = useState(1)
  const [categoria, setCategoria] = useState('')
  const [viaSuap, setViaSuap] = useState('')
  const [viaEmail, setViaEmail] = useState('')
  const [ano, setAno] = useState('')
  const [mes, setMes] = useState('')
  const [showOnlyUnread, setShowOnlyUnread] = useState(true)
  const [selectedId, setSelectedId] = useState(null)

  useEffect(() => {
    setPage(1)
  }, [search, categoria, viaSuap, viaEmail, ano, mes, showOnlyUnread])

  const filters = useMemo(
    () => ({
      search: search || undefined,
      categoria: categoria || undefined,
      via_suap: viaSuap || undefined,
      via_email: viaEmail || undefined,
      ano: ano || undefined,
      mes: mes || undefined,
      unread: showOnlyUnread ? true : undefined,
      page,
      page_size: 10,
    }),
    [search, categoria, viaSuap, viaEmail, ano, mes, showOnlyUnread, page],
  )

  const { data: notificationsData, isLoading, isError } = useQuery({
    queryKey: ['notificacoes', filters],
    queryFn: () => notificacoesApi.list(filters).then((response) => response.data),
    staleTime: 30_000,
  })

  const { data: preferencesData } = useQuery({
    queryKey: ['notificacoes', 'preferencias', 'options'],
    queryFn: () => notificacoesApi.preferences({ page_size: 10 }).then((response) => response.data),
    staleTime: 60_000,
  })

  const rows = notificationsData?.results || []
  const categories = preferencesData?.results || []

  useEffect(() => {
    if (!rows.length) {
      setSelectedId(null)
      return
    }

    if (!rows.some((item) => item.id === selectedId)) {
      setSelectedId(rows[0].id)
    }
  }, [rows, selectedId])

  const selectedNotification = rows.find((item) => item.id === selectedId) || null

  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: ['notificacoes'] })
  }

  const markReadMutation = useMutation({
    mutationFn: ({ id, lida }) => notificacoesApi.markRead(id, lida),
    onSuccess: (_, variables) => {
      invalidate()
      toast.success(variables.lida ? 'Notificação marcada como lida.' : 'Notificação marcada como não lida.')
    },
  })

  const markAllReadMutation = useMutation({
    mutationFn: () => notificacoesApi.markAllRead(filters),
    onSuccess: (response) => {
      invalidate()
      toast.success(`${response.data.updated || 0} notificações marcadas como lidas.`)
    },
  })

  const hideMutation = useMutation({
    mutationFn: (id) => notificacoesApi.hide(id),
    onSuccess: () => {
      invalidate()
      toast.success('Notificação removida da sua caixa.')
    },
  })

  return (
    <div className="page page--wide">
      <nav className="profile-breadcrumb">
        <Link to="/dashboard">Inicio</Link>
        <span className="profile-breadcrumb__sep">&gt;</span>
        <span>Comum</span>
        <span className="profile-breadcrumb__sep">&gt;</span>
        <span>Notificacoes nao lidas</span>
      </nav>

      <div className="page-header notifications-page__header">
        <div>
          <h1 className="page-title">Notificacoes {showOnlyUnread ? 'nao lidas' : 'do servidor'}</h1>
          <p className="page-subtitle">Central SUAP com filtros por categoria, canal e periodo.</p>
        </div>
        <div className="page-header__actions">
          <button
            type="button"
            className="btn btn--primary"
            onClick={() => markAllReadMutation.mutate()}
            disabled={markAllReadMutation.isPending || rows.length === 0}
          >
            <Eye size={16} /> Marcar todas como lidas
          </button>
          <button
            type="button"
            className="btn btn--secondary"
            onClick={() => navigate('/comum/notificacoes/preferencias')}
          >
            <Settings2 size={16} /> Preferencias de recebimento
          </button>
          <button
            type="button"
            className="btn btn--outline"
            onClick={() => setShowOnlyUnread((current) => !current)}
          >
            <EyeOff size={16} /> {showOnlyUnread ? 'Todas as notificacoes' : 'Somente nao lidas'}
          </button>
        </div>
      </div>

      <section className="dashboard-card notifications-filters-card">
        <div className="notifications-filters-grid">
          <label className="filter-group">
            <span>Texto</span>
            <input className="form-control" value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Buscar por titulo, categoria ou conteudo" />
          </label>
          <label className="filter-group">
            <span>Categoria</span>
            <select className="form-control" value={categoria} onChange={(event) => setCategoria(event.target.value)}>
              <option value="">Todas</option>
              {categories.map((item) => (
                <option key={item.id} value={item.categoria_slug}>{item.categoria_titulo}</option>
              ))}
            </select>
          </label>
          <label className="filter-group">
            <span>Via SUAP</span>
            <select className="form-control" value={viaSuap} onChange={(event) => setViaSuap(event.target.value)}>
              <option value="">Todas</option>
              <option value="true">Sim</option>
              <option value="false">Nao</option>
            </select>
          </label>
          <label className="filter-group">
            <span>Via E-mail</span>
            <select className="form-control" value={viaEmail} onChange={(event) => setViaEmail(event.target.value)}>
              <option value="">Todas</option>
              <option value="true">Sim</option>
              <option value="false">Nao</option>
            </select>
          </label>
          <label className="filter-group">
            <span>Ano</span>
            <input className="form-control" value={ano} onChange={(event) => setAno(event.target.value)} placeholder="2026" />
          </label>
          <label className="filter-group">
            <span>Mes</span>
            <select className="form-control" value={mes} onChange={(event) => setMes(event.target.value)}>
              <option value="">Todos</option>
              {Array.from({ length: 12 }).map((_, index) => (
                <option key={index + 1} value={index + 1}>{String(index + 1).padStart(2, '0')}</option>
              ))}
            </select>
          </label>
        </div>
      </section>

      {isError ? <div className="alert alert--error">Nao foi possivel carregar suas notificacoes.</div> : null}

      <section className="notifications-shell">
        <article className="dashboard-card notifications-detail-card">
          {selectedNotification ? (
            <>
              <div className="notifications-detail-card__status-row">
                <span className={`badge ${selectedNotification.is_unread ? 'badge--success' : 'badge--secondary'}`}>
                  {selectedNotification.is_unread ? 'Nao lida' : 'Lida'}
                </span>
                <span className="badge badge--outline">{selectedNotification.categoria_titulo || 'Sistema'}</span>
              </div>

              <div className="page-header page-header--compact notifications-detail-card__header">
                <div>
                  <h2 className="page-title">{selectedNotification.titulo}</h2>
                  <p className="page-subtitle">{formatDateTime(selectedNotification.data_evento)}</p>
                </div>
                <div className="notifications-actions-inline">
                  <button
                    type="button"
                    className="btn btn--outline btn--sm"
                    onClick={() => markReadMutation.mutate({ id: selectedNotification.id, lida: selectedNotification.is_unread })}
                  >
                    {selectedNotification.is_unread ? <Eye size={14} /> : <EyeOff size={14} />}
                    {selectedNotification.is_unread ? 'Marcar como lida' : 'Marcar como nao lida'}
                  </button>
                  <button
                    type="button"
                    className="btn btn--danger btn--sm"
                    onClick={() => hideMutation.mutate(selectedNotification.id)}
                  >
                    <Trash2 size={14} /> Remover
                  </button>
                </div>
              </div>

              <div className="notifications-detail-card__meta">
                <div className="notifications-meta-pill"><ShieldAlert size={14} /> {selectedNotification.tipo_display}</div>
                <div className="notifications-meta-pill"><Mail size={14} /> {channelLabel(selectedNotification)}</div>
              </div>

              {selectedNotification.resumo ? <p className="notifications-detail-card__summary">{selectedNotification.resumo}</p> : null}

              <div className="notifications-message">
                {messageLines(selectedNotification.mensagem).map((line, index) => (
                  <p key={`${selectedNotification.id}-${index}`}>{line}</p>
                ))}
              </div>

              {selectedNotification.link ? (
                <div className="notifications-detail-card__footer">
                  <Link to={selectedNotification.link} className="btn btn--primary btn--sm">
                    {selectedNotification.link_label || 'Abrir destino'}
                  </Link>
                </div>
              ) : null}
            </>
          ) : (
            <div className="empty-state-card">
              <h2>Nenhuma notificacao selecionada</h2>
              <p>{isLoading ? 'Carregando notificacoes...' : 'Nao ha itens para os filtros atuais.'}</p>
            </div>
          )}
        </article>

        <aside className="dashboard-card notifications-list-card">
          {isLoading ? <div className="table-skeleton">{Array.from({ length: 6 }).map((_, index) => <div key={index} className="skeleton-row" />)}</div> : null}

          {!isLoading && rows.length === 0 ? (
            <div className="empty-state-card">
              <h2>Sem notificacoes</h2>
              <p>Nenhuma notificacao corresponde aos filtros informados.</p>
            </div>
          ) : null}

          {!isLoading ? rows.map((item) => (
            <button
              key={item.id}
              type="button"
              className={`notification-list-item ${item.id === selectedId ? 'notification-list-item--active' : ''} ${item.is_unread ? 'notification-list-item--unread' : ''}`}
              onClick={() => setSelectedId(item.id)}
            >
              <div className="notification-list-item__title-row">
                <strong>{item.titulo}</strong>
                <span className={`notification-dot notification-dot--${item.tipo.toLowerCase()}`}></span>
              </div>
              <p className="notification-list-item__summary">{item.resumo || item.categoria_titulo || 'Notificacao SUAP'}</p>
              <span className="notification-list-item__date">{formatDateTime(item.data_evento)}</span>
            </button>
          )) : null}
        </aside>
      </section>

      {notificationsData ? (
        <div className="pagination">
          <button className="btn btn--secondary" disabled={!notificationsData.previous} onClick={() => setPage((current) => current - 1)}>Anterior</button>
          <span className="pagination__info">Pagina {page} — {notificationsData.count} registros</span>
          <button className="btn btn--secondary" disabled={!notificationsData.next} onClick={() => setPage((current) => current + 1)}>Proxima</button>
        </div>
      ) : null}
    </div>
  )
}