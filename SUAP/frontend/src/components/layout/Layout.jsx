import { useEffect, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { NavLink, Outlet, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '@/context/AuthContext'
import { Bell, ChevronDown, LogOut, Search, User } from 'lucide-react'
import { notificacoesApi } from '@/api/endpoints'
import { sidebarItems } from '@/components/layout/sidebarItems'
import { debugLog } from '@/utils/debug'

function normalizeText(value) {
  return String(value || '')
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase()
    .trim()
}

function getItemSearchText(item) {
  return [item.label, ...(item.searchTerms || []), item.state?.description]
    .filter(Boolean)
    .join(' ')
}

function collectGroupIds(item, forcedOpenIds) {
  if (!item?.items?.length) {
    return
  }

  forcedOpenIds.add(item.id)
  item.items.forEach((child) => collectGroupIds(child, forcedOpenIds))
}

function pruneDisabledSidebarItems(items) {
  return items.reduce((result, item) => {
    if (!item) {
      return result
    }

    if (!item.items?.length) {
      if (item.enabled === false) {
        return result
      }

      result.push(item)
      return result
    }

    const nextChildren = pruneDisabledSidebarItems(item.items)
    if (item.enabled === false || nextChildren.length === 0) {
      return result
    }

    result.push({
      ...item,
      items: nextChildren,
    })
    return result
  }, [])
}

function filterSidebarItems(items, query, forcedOpenIds) {
  if (!query) {
    return items
  }

  return items.reduce((result, item) => {
    const ownMatch = normalizeText(getItemSearchText(item)).includes(query)

    if (!item.items?.length) {
      if (ownMatch) {
        result.push(item)
      }

      return result
    }

    const filteredChildren = filterSidebarItems(item.items, query, forcedOpenIds)

    if (!ownMatch && filteredChildren.length === 0) {
      return result
    }

    if (ownMatch) {
      collectGroupIds(item, forcedOpenIds)
    } else if (filteredChildren.length > 0) {
      forcedOpenIds.add(item.id)
    }

    result.push({
      ...item,
      items: ownMatch ? item.items : filteredChildren,
    })

    return result
  }, [])
}

function getUserInitials(user) {
  const fullName = user?.nome_completo || user?.username || ''
  const parts = fullName.split(' ').filter(Boolean)
  const first = parts[0]?.[0] || ''
  const last = parts.length > 1 ? parts[parts.length - 1]?.[0] : parts[0]?.[1] || ''
  return `${first}${last}`.toUpperCase() || 'SU'
}

function getItemPath(item) {
  if (!item) return null
  if (typeof item.to === 'string') return item.to
  if (item.to?.pathname) return item.to.pathname
  if (item.href) return item.href
  return null
}

function isItemActive(item, pathname) {
  if (!item) return false

  if (item.items?.length) {
    return item.items.some((child) => isItemActive(child, pathname))
  }

  const activePrefixes = item.activePrefixes || []
  if (activePrefixes.length > 0) {
    return activePrefixes.some((prefix) => pathname === prefix || pathname.startsWith(`${prefix}/`))
  }

  const path = getItemPath(item)
  if (!path) return false
  if (item.exact) return pathname === path
  return pathname === path || pathname.startsWith(`${path}/`)
}

function buildRegistryLink(user) {
  if (!user?.id) {
    return '/rh/servidores'
  }

  return {
    pathname: '/rh/servidores',
    search: `?servidorId=${user.id}`,
  }
}

function SidebarLeaf({ item }) {
  const label = <span className="sidebar__label">{item.label}</span>

  if (item.type === 'external') {
    return (
      <a href={item.href} className="sidebar__link">
        {label}
      </a>
    )
  }

  return (
    <NavLink
      to={item.to}
      state={item.state}
      className={({ isActive }) =>
        `sidebar__link ${isActive || item.forceActive ? 'sidebar__link--active' : ''}`
      }
      end={item.exact}
    >
      {label}
    </NavLink>
  )
}

function SidebarNode({ item, depth, pathname, openGroups, setOpenGroups, forcedOpenIds }) {
  const active = isItemActive(item, pathname)

  if (!item.items?.length) {
    if (depth === 0) {
      return <SidebarLeaf item={item} />
    }

    if (item.type === 'external') {
      return (
        <li className="sidebar__tree-item">
          <a href={item.href} className={`sidebar__tree-link ${active ? 'sidebar__tree-link--active' : ''}`}>
            {item.label}
          </a>
        </li>
      )
    }

    return (
      <li className="sidebar__tree-item">
        <NavLink
          to={item.to}
          state={item.state}
          end={item.exact}
          className={({ isActive }) =>
            `sidebar__tree-link ${isActive || active ? 'sidebar__tree-link--active' : ''}`
          }
        >
          {item.label}
        </NavLink>
      </li>
    )
  }

  const isOpen = forcedOpenIds.has(item.id) || openGroups[item.id] === true
  const detailsClassName = depth === 0 ? 'sidebar__section' : 'sidebar__branch'
  const summaryClassName = depth === 0 ? 'sidebar__summary' : 'sidebar__tree-summary'

  const content = (
    <details
      className={detailsClassName}
      open={isOpen}
      onToggle={(event) => {
        const nextOpen = event.currentTarget?.open ?? false
        setOpenGroups((current) => ({
          ...current,
          [item.id]: nextOpen,
        }))
      }}
    >
      <summary className={`${summaryClassName} ${active ? 'sidebar__summary--active' : ''}`}>
        <span className="sidebar__label">{item.label}</span>
        <ChevronDown size={16} className="sidebar__caret" />
      </summary>

      <ul className={depth === 0 ? 'sidebar__tree' : 'sidebar__subtree'}>
        {item.items.map((child) => (
          <SidebarNode
            key={child.id}
            item={child}
            depth={depth + 1}
            pathname={pathname}
            openGroups={openGroups}
            setOpenGroups={setOpenGroups}
            forcedOpenIds={forcedOpenIds}
          />
        ))}
      </ul>
    </details>
  )

  if (depth === 0) {
    return content
  }

  return <li className="sidebar__tree-item">{content}</li>
}

export default function Layout() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [openGroups, setOpenGroups] = useState({})
  const [menuQuery, setMenuQuery] = useState('')

  const normalizedQuery = normalizeText(menuQuery)
  const forcedOpenIds = new Set()
  const enabledSidebarItems = pruneDisabledSidebarItems(sidebarItems)
  const visibleSidebarItems = filterSidebarItems(enabledSidebarItems, normalizedQuery, forcedOpenIds)
  const noResults = normalizedQuery && visibleSidebarItems.length === 0
  const { data: unreadNotifications = 0 } = useQuery({
    queryKey: ['layout', 'notifications', 'unread-count'],
    queryFn: () => notificacoesApi.list({ lida: false, page_size: 1 }).then((response) => response.data?.count || 0),
    staleTime: 60_000,
    refetchInterval: 60_000,
  })

  useEffect(() => {
    debugLog('info', 'layout.mounted', {
      pathname: location.pathname,
      username: user?.username,
      sidebarItems: visibleSidebarItems.length,
    })

    return () => {
      debugLog('info', 'layout.unmounted', {
        pathname: location.pathname,
      })
    }
  }, [])

  useEffect(() => {
    debugLog('info', 'layout.updated', {
      pathname: location.pathname,
      menuQuery,
      visibleSidebarItems: visibleSidebarItems.length,
    })
  }, [location.pathname, menuQuery, visibleSidebarItems.length])

  const handleLogout = () => {
    logout().finally(() => navigate('/login'))
  }

  const registryLink = buildRegistryLink(user)

  return (
    <div className="layout layout--legacy">
      <aside className="sidebar">
        <div className="sidebar__header">
          <span className="sidebar__wordmark">suap</span>
          <span className="sidebar__environment">HOMOLOG.</span>
          <span className="sidebar__header-spacer" aria-hidden="true" />
          <NavLink
            to="/comum/notificacoes"
            className={({ isActive }) => `sidebar__header-action ${isActive ? 'sidebar__header-action--active' : ''}`}
            title="Notificações"
            aria-label="Notificações"
          >
            <Bell size={15} />
            {unreadNotifications > 0 ? <span className="sidebar__notification-badge">{unreadNotifications > 99 ? '99+' : unreadNotifications}</span> : null}
          </NavLink>
        </div>

        <div className="sidebar__account-shortcuts">
          <>
            <NavLink to={registryLink} className={({ isActive }) => `sidebar__account-primary ${isActive ? 'sidebar__account-primary--active' : ''}`}>
              <span className="sidebar__account-avatar">{getUserInitials(user)}</span>
              <span className="sidebar__account-copy">
                <strong>{user?.nome_completo || user?.username}</strong>
                <span>{user?.tipo_display || 'Usuario autenticado'}</span>
              </span>
            </NavLink>

            <NavLink
              to="/comum/minha_conta/"
              end
              className={({ isActive }) => `sidebar__account-secondary ${isActive ? 'sidebar__account-secondary--active' : ''}`}
              title="Minha conta"
              aria-label="Minha conta"
            >
              <User size={18} />
            </NavLink>
          </>
        </div>

        <div className="sidebar__search">
          <Search size={16} className="sidebar__search-icon" />
          <input
            className="sidebar__search-input"
            type="search"
            placeholder="Buscar menu..."
            aria-label="Buscar menu"
            value={menuQuery}
            onChange={(event) => setMenuQuery(event.target.value)}
          />
        </div>

        <nav className="sidebar__nav">
          <>
            {visibleSidebarItems.map((item) => (
              <SidebarNode
                key={item.id}
                item={item}
                depth={0}
                pathname={location.pathname}
                openGroups={openGroups}
                setOpenGroups={setOpenGroups}
                forcedOpenIds={forcedOpenIds}
              />
            ))}
            {noResults ? <p className="sidebar__search-empty">Nenhum item do menu corresponde a esta busca.</p> : null}
          </>
        </nav>

        <div className="sidebar__footer">
          <button className="sidebar__logout" onClick={handleLogout} title="Sair">
            <LogOut size={18} />
            <span>Sair</span>
          </button>
        </div>
      </aside>

      <div className="workspace">
        <main className="main-content">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
