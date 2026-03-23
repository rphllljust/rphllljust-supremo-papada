import { useEffect, useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { NavLink, Outlet, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '@/context/AuthContext'
import { Bell, ChevronDown, LogOut, Search, User } from 'lucide-react'
import { notificacoesApi } from '@/api/endpoints'
import { sidebarItems } from '@/components/layout/sidebarItems'
import { debugLog } from '@/utils/debug'
import { getQuickAccessItems, trackQuickAccessVisit } from '@/utils/quickAccess'

const BREADCRUMB_LABELS = {
  dashboard: 'Dashboard',
  documentos: 'Documentos',
  declaracoes: 'Declaracoes',
  historicos: 'Historicos',
  guias: 'Guias de Transferencia',
  matriculas: 'Matriculas',
  notas: 'Notas',
  frequencia: 'Frequencia',
  turmas: 'Turmas',
  alunos: 'Alunos',
  usuarios: 'Usuarios',
  unidades: 'Instituicoes',
  agenda: 'Agenda',
  processos: 'Processos',
  arquivo: 'Arquivo',
  inscricoes: 'Inscricoes',
  estagio: 'Estagios',
  servidores: 'Servidores',
  servidor: 'Servidor',
  setores: 'Setores',
  notificacoes: 'Notificacoes',
  preferencias: 'Preferencias',
  minha_conta: 'Minha Conta',
  'alterar-senha': 'Alterar Senha',
  ensino: 'Ensino',
  ti: 'Tecnologia da Informacao',
  moodle: 'Moodle',
  configuracoes: 'Central Moodle',
  categorias: 'Categorias Moodle',
  catalogo: 'Catalogo Moodle',
  diarios: 'Diarios',
  componentes: 'Componentes',
  areacurso: 'Areas de cursos',
  cursoinicial: 'Cursos iniciais',
  eixotecnologico: 'Eixos Tecnologicos',
  cursoformacaosuperior: 'Cursos itinerantes',
  cursoitinerante: 'Cursos itinerantes',
  cursotecnico: 'Catalogo de cursos tecnicos',
  editar: 'Editar',
  nova: 'Nova',
  access: 'Access',
  ava: 'AVA',
  export: 'Exportacao',
  preview: 'Previa',
  comum: 'Comum',
  rh: 'Gestao de Pessoas',
  indisponivel: 'Indisponivel',
}

const STATIC_BREADCRUMB_PREFIXES = [
  {
    prefix: '/rh/servidor',
    items: [
      { label: 'Gestao de Pessoas' },
      { label: 'Servidores', to: '/rh/servidores' },
    ],
  },
  {
    prefix: '/rh/setor',
    items: [
      { label: 'Gestao de Pessoas' },
      { label: 'Setores', to: '/rh/setores' },
    ],
  },
  {
    prefix: '/rh/instituicao',
    items: [
      { label: 'Gestao de Pessoas' },
      { label: 'Instituicoes', to: '/rh/instituicoes' },
    ],
  },
]

const ENVIRONMENT_LABELS = {
  development: 'DEV.',
  homolog: 'HOMOLOG.',
  production: 'PROD.',
}

function getEnvironmentLabel() {
  const rawEnvironment = (import.meta.env.VITE_APP_ENV || import.meta.env.MODE || 'development').trim().toLowerCase()
  return ENVIRONMENT_LABELS[rawEnvironment] || rawEnvironment.toUpperCase()
}

const SIDEBAR_ENVIRONMENT_LABEL = getEnvironmentLabel()

function normalizePath(path) {
  if (!path) return '/'
  return path.length > 1 && path.endsWith('/') ? path.slice(0, -1) : path
}

function getMatchedBase(item, pathname) {
  const normalizedPathname = normalizePath(pathname)
  const activePrefixes = (item.activePrefixes || []).map(normalizePath).sort((left, right) => right.length - left.length)

  for (const prefix of activePrefixes) {
    if (normalizedPathname === prefix || normalizedPathname.startsWith(`${prefix}/`)) {
      return prefix
    }
  }

  const path = normalizePath(getItemPath(item))
  if (!path || path === '/') {
    return null
  }

  if (item.exact) {
    return normalizedPathname === path ? path : null
  }

  return normalizedPathname === path || normalizedPathname.startsWith(`${path}/`) ? path : null
}

function findBreadcrumbTrail(items, pathname, parents = []) {
  for (const item of items) {
    const nextParents = item.label ? [...parents, { label: item.label, to: item.items?.length ? null : getItemPath(item) }] : parents

    if (item.items?.length) {
      const nestedMatch = findBreadcrumbTrail(item.items, pathname, nextParents)
      if (nestedMatch) {
        return nestedMatch
      }
    }

    const matchedBase = getMatchedBase(item, pathname)
    if (matchedBase) {
      return {
        items: nextParents,
        matchedBase,
      }
    }
  }

  return null
}

function prettifySegment(segment) {
  const decoded = decodeURIComponent(String(segment || ''))

  if (/^\d+$/.test(decoded)) {
    return `#${decoded}`
  }

  if (BREADCRUMB_LABELS[decoded]) {
    return BREADCRUMB_LABELS[decoded]
  }

  return decoded
    .replace(/[-_]+/g, ' ')
    .replace(/\b\w/g, (char) => char.toUpperCase())
}

function buildFallbackTrail(pathname) {
  const normalizedPathname = normalizePath(pathname)
  const staticPrefix = STATIC_BREADCRUMB_PREFIXES.find((entry) => normalizedPathname === entry.prefix || normalizedPathname.startsWith(`${entry.prefix}/`))

  if (!staticPrefix) {
    return null
  }

  return {
    items: staticPrefix.items,
    matchedBase: staticPrefix.prefix,
  }
}

function buildBreadcrumbItems(pathname, locationState, enabledItems) {
  const normalizedPathname = normalizePath(pathname)
  const baseItems = [{ label: 'Inicio', to: '/dashboard' }]
  const trailMatch = findBreadcrumbTrail(enabledItems, normalizedPathname) || buildFallbackTrail(normalizedPathname)

  const breadcrumbItems = [...baseItems]
  let matchedBase = ''

  if (trailMatch) {
    matchedBase = trailMatch.matchedBase
    for (const item of trailMatch.items) {
      if (item.label === 'Inicio') {
        continue
      }

      const previous = breadcrumbItems[breadcrumbItems.length - 1]
      if (!previous || previous.label !== item.label) {
        breadcrumbItems.push(item)
      }
    }
  }

  const matchedSegments = normalizePath(matchedBase).split('/').filter(Boolean)
  const pathnameSegments = normalizedPathname.split('/').filter(Boolean)
  const extraSegments = pathnameSegments.slice(matchedSegments.length)
  let accumulatedPath = matchedBase || ''

  extraSegments.forEach((segment, index) => {
    accumulatedPath = `${normalizePath(accumulatedPath || '')}/${segment}`.replace('//', '/')
    const isLast = index === extraSegments.length - 1
    const isUnavailableLeaf = isLast && pathnameSegments[0] === 'indisponivel' && locationState?.title

    breadcrumbItems.push({
      label: isUnavailableLeaf ? locationState.title : prettifySegment(segment),
      to: isLast ? null : accumulatedPath,
    })
  })

  if (breadcrumbItems.length === 1 && normalizedPathname === '/dashboard') {
    breadcrumbItems.push({ label: 'Dashboard', to: null })
  } else if (breadcrumbItems.length > 1) {
    breadcrumbItems[breadcrumbItems.length - 1] = {
      ...breadcrumbItems[breadcrumbItems.length - 1],
      to: null,
    }
  }

  return breadcrumbItems
}

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

  return `/rh/servidores/${user.id}`
}

function SidebarLeaf({ item, depth = 0 }) {
  const Icon = depth === 0 ? item.icon : null
  const label = (
    <>
      {Icon ? <Icon size={15} className="sidebar__item-icon" aria-hidden="true" /> : null}
      <span className="sidebar__label">{item.label}</span>
    </>
  )

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

  if (item.type === 'group' && (!item.items || item.items.length === 0)) {
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
          {depth === 0 && item.icon ? <item.icon size={15} className="sidebar__item-icon" aria-hidden="true" /> : null}
          <span className="sidebar__label">{item.label}</span>
          <ChevronDown size={16} className="sidebar__caret" />
        </summary>
        <p className="sidebar__search-empty">Nenhum item acessado ainda.</p>
      </details>
    )

    if (depth === 0) {
      return content
    }

    return <li className="sidebar__tree-item">{content}</li>
  }

  if (!item.items?.length) {
    if (depth === 0) {
      return <SidebarLeaf item={item} depth={depth} />
    }

    if (item.type === 'external') {
      return (
        <li className="sidebar__tree-item">
          <a href={item.href} className={`sidebar__tree-link ${active ? 'sidebar__tree-link--active' : ''}`}>
            <span className="sidebar__label">{item.label}</span>
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
          <span className="sidebar__label">{item.label}</span>
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
        {depth === 0 && item.icon ? <item.icon size={15} className="sidebar__item-icon" aria-hidden="true" /> : null}
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
  const [quickAccessItems, setQuickAccessItems] = useState([])

  const normalizedQuery = normalizeText(menuQuery)
  const forcedOpenIds = new Set()
  const baseSidebarItems = useMemo(() => pruneDisabledSidebarItems(sidebarItems), [])
  const enabledSidebarItems = useMemo(() => baseSidebarItems.map((item) => {
    if (item.id !== 'acesso-rapido') {
      return item
    }

    return {
      ...item,
      items: quickAccessItems.map((quickItem) => ({
        id: `quick-${quickItem.id}`,
        type: 'link',
        label: quickItem.label,
        to: quickItem.to,
        state: quickItem.state,
        activePrefixes: quickItem.activePrefixes,
      })),
    }
  }), [baseSidebarItems, quickAccessItems])
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

  useEffect(() => {
    if (!user) {
      setQuickAccessItems([])
      return
    }

    trackQuickAccessVisit(user, baseSidebarItems, location.pathname)
    setQuickAccessItems(getQuickAccessItems(user, baseSidebarItems, 7))
  }, [baseSidebarItems, location.pathname, user])

  const handleLogout = () => {
    logout().finally(() => navigate('/login'))
  }

  const registryLink = buildRegistryLink(user)
  const breadcrumbItems = useMemo(
    () => buildBreadcrumbItems(location.pathname, location.state, enabledSidebarItems),
    [enabledSidebarItems, location.pathname, location.state],
  )

  return (
    <div className="layout layout--legacy">
      <aside className="sidebar">
        <div className="sidebar__header">
          <span className="sidebar__wordmark">suap</span>
          <span className="sidebar__environment">{SIDEBAR_ENVIRONMENT_LABEL}</span>
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
          <nav className="app-breadcrumb" aria-label="Breadcrumb">
            {breadcrumbItems.map((item, index) => (
              <span key={`${item.label}-${index}`} className="app-breadcrumb__item">
                {index > 0 ? <span className="app-breadcrumb__sep">&gt;</span> : null}
                {item.to ? (
                  <NavLink to={item.to} className="app-breadcrumb__link">
                    {item.label}
                  </NavLink>
                ) : (
                  <span className="app-breadcrumb__current">{item.label}</span>
                )}
              </span>
            ))}
          </nav>
          <Outlet />
        </main>
      </div>
    </div>
  )
}
