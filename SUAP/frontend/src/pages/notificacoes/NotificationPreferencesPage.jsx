import { useEffect, useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { CheckCircle2, Mail, MonitorDot, Settings2 } from 'lucide-react'
import { Link } from 'react-router-dom'
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

function StatusPill({ enabled, channel }) {
  return (
    <span className={`notifications-channel-pill ${enabled ? 'notifications-channel-pill--on' : 'notifications-channel-pill--off'}`}>
      {channel === 'suap' ? <MonitorDot size={14} /> : <Mail size={14} />}
      {enabled ? 'Ativo' : 'Inativo'}
    </span>
  )
}

export default function NotificationPreferencesPage() {
  const queryClient = useQueryClient()
  const [search, setSearch] = useState('')
  const [page, setPage] = useState(1)
  const [viaSuap, setViaSuap] = useState('')
  const [viaEmail, setViaEmail] = useState('')
  const [ano, setAno] = useState('')

  useEffect(() => {
    setPage(1)
  }, [search, viaSuap, viaEmail, ano])

  const filters = useMemo(
    () => ({
      search: search || undefined,
      via_suap: viaSuap || undefined,
      via_email: viaEmail || undefined,
      ano: ano || undefined,
      page,
      page_size: 10,
    }),
    [search, viaSuap, viaEmail, ano, page],
  )

  const { data, isLoading, isError } = useQuery({
    queryKey: ['notificacoes-preferencias', filters],
    queryFn: () => notificacoesApi.preferences(filters).then((response) => response.data),
    staleTime: 30_000,
  })

  const rows = data?.results || []

  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: ['notificacoes-preferencias'] })
    queryClient.invalidateQueries({ queryKey: ['notificacoes', 'preferencias', 'options'] })
  }

  const updatePreferenceMutation = useMutation({
    mutationFn: ({ id, payload }) => notificacoesApi.updatePreference(id, payload),
    onSuccess: () => {
      invalidate()
      toast.success('Preferência atualizada.')
    },
  })

  const bulkMutation = useMutation({
    mutationFn: ({ canal, enabled }) => notificacoesApi.bulkUpdatePreferences({ canal, enabled }),
    onSuccess: (response, variables) => {
      invalidate()
      toast.success(`${response.data.updated || 0} preferências atualizadas para ${variables.canal === 'via_suap' ? 'SUAP' : 'E-mail'}.`)
    },
  })

  return (
    <div className="page page--wide">
      <nav className="profile-breadcrumb">
        <Link to="/dashboard">Inicio</Link>
        <span className="profile-breadcrumb__sep">&gt;</span>
        <span>Comum</span>
        <span className="profile-breadcrumb__sep">&gt;</span>
        <Link to="/comum/notificacoes">Notificacoes nao lidas</Link>
        <span className="profile-breadcrumb__sep">&gt;</span>
        <span>Preferencias de Notificacoes</span>
      </nav>

      <div className="page-header notifications-page__header">
        <div>
          <h1 className="page-title">Preferencias de Notificacoes</h1>
          <p className="page-subtitle">Defina por categoria se o aviso deve sair via SUAP, E-mail ou ambos.</p>
        </div>
        <div className="page-header__actions">
          <button type="button" className="btn btn--danger" onClick={() => bulkMutation.mutate({ canal: 'via_suap', enabled: false })}>
            <Settings2 size={16} /> Desativar envio padrao via SUAP
          </button>
          <button type="button" className="btn btn--danger" onClick={() => bulkMutation.mutate({ canal: 'via_email', enabled: false })}>
            <Settings2 size={16} /> Desativar envio padrao via E-mail
          </button>
          <button type="button" className="btn btn--secondary" onClick={() => bulkMutation.mutate({ canal: 'via_email', enabled: true })}>
            <CheckCircle2 size={16} /> Reativar E-mail
          </button>
        </div>
      </div>

      <section className="dashboard-card notifications-filters-card">
        <div className="notifications-filters-grid notifications-filters-grid--preferences">
          <label className="filter-group">
            <span>Texto</span>
            <input className="form-control" value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Categoria ou descricao" />
          </label>
          <label className="filter-group">
            <span>Via SUAP</span>
            <select className="form-control" value={viaSuap} onChange={(event) => setViaSuap(event.target.value)}>
              <option value="">Todos</option>
              <option value="true">Ativo</option>
              <option value="false">Inativo</option>
            </select>
          </label>
          <label className="filter-group">
            <span>Via E-mail</span>
            <select className="form-control" value={viaEmail} onChange={(event) => setViaEmail(event.target.value)}>
              <option value="">Todos</option>
              <option value="true">Ativo</option>
              <option value="false">Inativo</option>
            </select>
          </label>
          <label className="filter-group">
            <span>Ano de atualizacao</span>
            <input className="form-control" value={ano} onChange={(event) => setAno(event.target.value)} placeholder="2026" />
          </label>
        </div>
      </section>

      {isError ? <div className="alert alert--error">Nao foi possivel carregar suas preferencias de notificacao.</div> : null}

      <section className="dashboard-card preferences-table-card">
        {isLoading ? <div className="table-skeleton">{Array.from({ length: 6 }).map((_, index) => <div key={index} className="skeleton-row" />)}</div> : null}

        {!isLoading ? (
          <div className="table-wrapper notifications-table-wrapper">
            <table>
              <thead>
                <tr>
                  <th>Categoria</th>
                  <th>Descricao</th>
                  <th>Atualizada em</th>
                  <th>Via SUAP</th>
                  <th>Via E-mail</th>
                  <th>Opcoes</th>
                </tr>
              </thead>
              <tbody>
                {rows.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="empty-state">Nenhuma preferencia encontrada.</td>
                  </tr>
                ) : rows.map((row) => (
                  <tr key={row.id}>
                    <td>{row.categoria_titulo}</td>
                    <td>{row.categoria_descricao || '-'}</td>
                    <td>{formatDateTime(row.atualizado_em)}</td>
                    <td><StatusPill enabled={row.via_suap} channel="suap" /></td>
                    <td><StatusPill enabled={row.via_email} channel="email" /></td>
                    <td>
                      <div className="table-actions">
                        <button
                          type="button"
                          className="btn btn--outline btn--sm"
                          onClick={() => updatePreferenceMutation.mutate({ id: row.id, payload: { via_suap: !row.via_suap } })}
                        >
                          {row.via_suap ? 'Desativar SUAP' : 'Ativar SUAP'}
                        </button>
                        <button
                          type="button"
                          className="btn btn--secondary btn--sm"
                          onClick={() => updatePreferenceMutation.mutate({ id: row.id, payload: { via_email: !row.via_email } })}
                        >
                          {row.via_email ? 'Desativar E-mail' : 'Ativar E-mail'}
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : null}
      </section>

      {data ? (
        <div className="pagination">
          <button className="btn btn--secondary" disabled={!data.previous} onClick={() => setPage((current) => current - 1)}>Anterior</button>
          <span className="pagination__info">Pagina {page} — {data.count} registros</span>
          <button className="btn btn--secondary" disabled={!data.next} onClick={() => setPage((current) => current + 1)}>Proxima</button>
        </div>
      ) : null}
    </div>
  )
}