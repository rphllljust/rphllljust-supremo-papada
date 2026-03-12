const QUICK_ACCESS_STORAGE_PREFIX = 'suap.quick-access.v1'
const EXCLUDED_ITEM_IDS = new Set([
  'inicio',
  'acesso-rapido',
  'programa-gestao',
  'painel-controle',
])

const EXCLUDED_PARENT_IDS = new Set(['acesso-rapido'])

function normalizePath(path) {
  if (!path) return '/'
  return path.length > 1 && path.endsWith('/') ? path.slice(0, -1) : path
}

function getItemPath(item) {
  if (!item) return null
  if (typeof item.to === 'string') return item.to
  if (item.to?.pathname) return item.to.pathname
  if (item.href) return item.href
  return null
}

function getStorageKey(user) {
  const userKey = user?.id || user?.username || 'anon'
  return `${QUICK_ACCESS_STORAGE_PREFIX}.${userKey}`
}

function readStats(user) {
  if (!user) return {}

  try {
    const raw = localStorage.getItem(getStorageKey(user))
    return raw ? JSON.parse(raw) : {}
  } catch {
    return {}
  }
}

function writeStats(user, stats) {
  if (!user) return

  try {
    localStorage.setItem(getStorageKey(user), JSON.stringify(stats))
  } catch {
    // Ignore storage errors and keep navigation working.
  }
}

function flattenNavigableItems(items, parentIds = []) {
  return items.flatMap((item) => {
    if (!item || item.enabled === false) {
      return []
    }

    const nextParents = [...parentIds, item.id]
    if (item.items?.length) {
      return flattenNavigableItems(item.items, nextParents)
    }

    if (item.type === 'external' || EXCLUDED_ITEM_IDS.has(item.id) || parentIds.some((parentId) => EXCLUDED_PARENT_IDS.has(parentId))) {
      return []
    }

    const path = getItemPath(item)
    if (!path || path === '/login') {
      return []
    }

    return [{
      id: item.id,
      label: item.label,
      to: item.to,
      state: item.state,
      activePrefixes: (item.activePrefixes || []).map(normalizePath),
      path: normalizePath(path),
    }]
  })
}

function resolveVisitedItem(items, pathname) {
  const normalizedPathname = normalizePath(pathname)

  return [...items]
    .sort((left, right) => {
      const leftScore = Math.max(left.path.length, ...left.activePrefixes.map((prefix) => prefix.length), 0)
      const rightScore = Math.max(right.path.length, ...right.activePrefixes.map((prefix) => prefix.length), 0)
      return rightScore - leftScore
    })
    .find((item) => {
      if (item.path && (normalizedPathname === item.path || normalizedPathname.startsWith(`${item.path}/`))) {
        return true
      }

      return item.activePrefixes.some((prefix) => normalizedPathname === prefix || normalizedPathname.startsWith(`${prefix}/`))
    })
}

export function trackQuickAccessVisit(user, sidebarItems, pathname) {
  if (!user || !pathname) return

  const items = flattenNavigableItems(sidebarItems)
  const visitedItem = resolveVisitedItem(items, pathname)
  if (!visitedItem) return

  const stats = readStats(user)
  const current = stats[visitedItem.id] || { count: 0, lastVisitedAt: null }

  stats[visitedItem.id] = {
    count: current.count + 1,
    lastVisitedAt: Date.now(),
  }

  writeStats(user, stats)
}

export function getQuickAccessItems(user, sidebarItems, limit = 7) {
  const items = flattenNavigableItems(sidebarItems)
  const stats = readStats(user)

  const ranked = items
    .filter((item) => stats[item.id])
    .sort((left, right) => {
      const leftStats = stats[left.id]
      const rightStats = stats[right.id]

      if (rightStats.count !== leftStats.count) {
        return rightStats.count - leftStats.count
      }

      return Number(rightStats.lastVisitedAt || 0) - Number(leftStats.lastVisitedAt || 0)
    })

  return ranked.slice(0, limit)
}