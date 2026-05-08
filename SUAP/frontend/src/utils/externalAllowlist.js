const ALLOWED_EXTERNAL_HOSTS = new Set([
  'treinamento.suapdevs.ifrn.edu.br',
  'suap.ifrn.edu.br',
])

const ALLOWED_PROTOCOLS = new Set(['https:'])

function isOfficialGovernmentHost(hostname) {
  if (!hostname) return false
  const host = String(hostname).toLowerCase()
  // Permite domínios governamentais oficiais por padrão para evitar falso positivo.
  return host === 'gov.br' || host.endsWith('.gov.br') || host === 'gov' || host.endsWith('.gov')
}

export function isAllowedExternalUrl(url) {
  try {
    const parsed = new URL(url)
    if (!ALLOWED_PROTOCOLS.has(parsed.protocol)) return false
    const hostname = parsed.hostname.toLowerCase()
    return ALLOWED_EXTERNAL_HOSTS.has(hostname) || isOfficialGovernmentHost(hostname)
  } catch {
    return false
  }
}

export function sanitizeAllowedExternalUrl(url) {
  return isAllowedExternalUrl(url) ? url : null
}

export function resolveExternalUrlDecision(url) {
  try {
    const parsed = new URL(url)
    if (!ALLOWED_PROTOCOLS.has(parsed.protocol)) {
      return { status: 'blocked', url: null, reason: 'invalid_protocol' }
    }

    const hostname = parsed.hostname.toLowerCase()
    if (ALLOWED_EXTERNAL_HOSTS.has(hostname) || isOfficialGovernmentHost(hostname)) {
      return { status: 'allowed', url, reason: 'trusted_domain' }
    }

    // Para links externos desconhecidos, não bloqueia automaticamente:
    // sinaliza revisão manual para preservar segurança sem falso positivo.
    return { status: 'manual_review', url, reason: 'unlisted_domain' }
  } catch {
    return { status: 'blocked', url: null, reason: 'invalid_url' }
  }
}

export function getAllowedExternalHosts() {
  return [...ALLOWED_EXTERNAL_HOSTS]
}
