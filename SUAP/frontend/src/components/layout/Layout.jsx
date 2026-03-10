import { useEffect, useState } from 'react'
import { NavLink, Outlet, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '@/context/AuthContext'
import { ChevronDown, LogOut, Menu, Search, Settings, User, X } from 'lucide-react'
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

function SidebarLeaf({ item, sidebarOpen }) {
  const label = sidebarOpen ? <span className="sidebar__label">{item.label}</span> : null

  if (item.type === 'external') {
    return (
      <a href={item.href} className="sidebar__link">
        {item.icon ? <item.icon size={18} className="sidebar__icon" /> : null}
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
      {item.icon ? <item.icon size={18} className="sidebar__icon" /> : null}
      {label}
    </NavLink>
  )
}

function SidebarNode({ item, depth, pathname, sidebarOpen, openGroups, setOpenGroups, forcedOpenIds }) {
  const active = isItemActive(item, pathname)

  if (!item.items?.length) {
    if (depth === 0) {
      return <SidebarLeaf item={item} sidebarOpen={sidebarOpen} />
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

  const isOpen = sidebarOpen && (forcedOpenIds.has(item.id) || (openGroups[item.id] ?? active))
  const detailsClassName = depth === 0 ? 'sidebar__section' : 'sidebar__branch'
  const summaryClassName = depth === 0 ? 'sidebar__summary' : 'sidebar__tree-summary'

  const content = (
    <details
      className={detailsClassName}
      open={isOpen}
      onToggle={(event) => {
        if (!sidebarOpen) return
        const nextOpen = event.currentTarget?.open ?? false
        setOpenGroups((current) => ({
          ...current,
          [item.id]: nextOpen,
        }))
      }}
    >
      <summary className={`${summaryClassName} ${active ? 'sidebar__summary--active' : ''}`}>
        {depth === 0 && item.icon ? <item.icon size={18} className="sidebar__icon" /> : null}
        {sidebarOpen ? <span className="sidebar__label">{item.label}</span> : null}
        {sidebarOpen ? <ChevronDown size={16} className="sidebar__caret" /> : null}
      </summary>

      {sidebarOpen ? (
        <ul className={depth === 0 ? 'sidebar__tree' : 'sidebar__subtree'}>
          {item.items.map((child) => (
            <SidebarNode
              key={child.id}
              item={child}
              depth={depth + 1}
              pathname={pathname}
              sidebarOpen={sidebarOpen}
              openGroups={openGroups}
              setOpenGroups={setOpenGroups}
              forcedOpenIds={forcedOpenIds}
            />
          ))}
        </ul>
      ) : null}
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
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [openGroups, setOpenGroups] = useState({})
  const [menuQuery, setMenuQuery] = useState('')

  const normalizedQuery = normalizeText(menuQuery)
  const forcedOpenIds = new Set()
  const enabledSidebarItems = pruneDisabledSidebarItems(sidebarItems)
  const visibleSidebarItems = filterSidebarItems(enabledSidebarItems, normalizedQuery, forcedOpenIds)
  const noResults = sidebarOpen && normalizedQuery && visibleSidebarItems.length === 0

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
      sidebarOpen,
      menuQuery,
      visibleSidebarItems: visibleSidebarItems.length,
    })
  }, [location.pathname, sidebarOpen, menuQuery, visibleSidebarItems.length])

  const handleLogout = () => {
    logout().finally(() => navigate('/login'))
  }

  return (
    <div className="layout">
      {/* Sidebar */}
      <aside className={`sidebar ${sidebarOpen ? 'sidebar--open' : 'sidebar--collapsed'}`}>
        <div className="sidebar__header">
          <div className="sidebar__brand">
            <img className="sidebar__brand-logo" src="/static/img/idep-ro-logo.png" alt="IDEP/RO" />
            {sidebarOpen ? (
              <div className="sidebar__brand-copy">
                <strong className="sidebar__brand-title">SUAP Escola</strong>
                <span className="sidebar__brand-subtitle">Portal institucional de gestao escolar</span>
              </div>
            ) : null}
          </div>
          <button className="sidebar__toggle" onClick={() => setSidebarOpen(!sidebarOpen)}>
            {sidebarOpen ? <X size={18} /> : <Menu size={18} />}
          </button>
        </div>

        {sidebarOpen ? (
          <details className="sidebar__user-menu">
            <summary className="sidebar__user-trigger">
              <span className="sidebar__user-avatar">{getUserInitials(user)}</span>
              <span className="sidebar__user-meta">
                <strong>{user?.nome_completo || user?.username}</strong>
                <span className="sidebar__user-role">{user?.tipo_display || 'Usuario autenticado'}</span>
              </span>
              <ChevronDown size={16} className="sidebar__user-caret" />
            </summary>

            <div className="sidebar__user-dropdown">
              <NavLink
                to="/rh/servidor/1221471/"
                className="sidebar__dropdown-link"
              >
                <User size={16} />
                <span>Meu perfil</span>
              </NavLink>
              <NavLink
                to="/indisponivel/configuracoes"
                state={{
                  title: 'Configuracoes',
                  description: 'As configuracoes do usuario ainda nao possuem uma tela dedicada neste frontend do SUAP.',
                }}
                className="sidebar__dropdown-link"
              >
                <Settings size={16} />
                <span>Configuracoes</span>
              </NavLink>
              <NavLink
                to="/indisponivel/alterar-senha"
                state={{
                  title: 'Alterar senha',
                  description: 'O fluxo de alteracao de senha do template Django ainda nao foi migrado para uma tela React dedicada.',
                }}
                className="sidebar__dropdown-link"
              >
                <Settings size={16} />
                <span>Alterar senha</span>
              </NavLink>
              <button type="button" className="sidebar__dropdown-button" onClick={handleLogout}>
                <LogOut size={16} />
                <span>Sair</span>
              </button>
            </div>
          </details>
        ) : null}

        {sidebarOpen ? (
          <div className="sidebar__search">
            <Search size={16} className="sidebar__search-icon" />
            <input
              className="sidebar__search-input"
              type="search"
              placeholder="Pesquisar modulo, pagina ou funcao"
              aria-label="Pesquisar modulo, pagina ou funcao"
              value={menuQuery}
              onChange={(event) => setMenuQuery(event.target.value)}
            />
          </div>
        ) : null}

        <nav className="sidebar__nav">
          {visibleSidebarItems.map((item) => (
            <SidebarNode
              key={item.id}
              item={item}
              depth={0}
              pathname={location.pathname}
              sidebarOpen={sidebarOpen}
              openGroups={openGroups}
              setOpenGroups={setOpenGroups}
              forcedOpenIds={forcedOpenIds}
            />
          ))}
          {noResults ? <p className="sidebar__search-empty">Nenhum item do menu corresponde a esta busca.</p> : null}
        </nav>

        <div className="sidebar__footer">
          {sidebarOpen && (
            <div className="sidebar__user">
              <span className="sidebar__user-name">{user?.nome_completo || user?.username}</span>
              <span className="sidebar__user-role">{user?.tipo_display}</span>
            </div>
          )}
          <button className="sidebar__logout" onClick={handleLogout} title="Sair">
            <LogOut size={18} />
            {sidebarOpen && <span>Sair</span>}
          </button>
        </div>
      </aside>

      {/* Conteúdo principal */}
      <main className="main-content">
        <Outlet />
      </main>
    </div>
  )
}
