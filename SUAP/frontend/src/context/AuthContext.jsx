/**
 * Context de autenticação — gerencia login, logout e usuário atual.
 * Usa localStorage para persistir os tokens JWT.
 */
import { createContext, useContext, useState, useEffect, useCallback } from 'react'
import { authApi } from '@/api/endpoints'
import { debugLog, normalizeError } from '@/utils/debug'

const AuthContext = createContext(null)

const PROFILE_LABELS = {
  ALUNO: 'Aluno',
  PROFESSOR: 'Professor',
  SECRETARIA: 'Secretaria',
  COORDENACAO: 'Coordenacao/Consulta',
  ADMIN: 'Administrador',
}

function clearAuthStorage() {
  localStorage.removeItem('access_token')
  localStorage.removeItem('refresh_token')
}

function normalizeUser(user) {
  if (!user) return null

  const nomeCompleto = [user.first_name, user.last_name].filter(Boolean).join(' ').trim()

  return {
    ...user,
    must_change_password: Boolean(user.must_change_password),
    nome_completo: user.nome_completo || nomeCompleto || user.username,
    tipo_display: user.tipo_display || PROFILE_LABELS[user.perfil] || PROFILE_LABELS[user.tipo] || user.perfil || user.tipo,
  }
}

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  const refreshUser = useCallback(async () => {
    const { data } = await authApi.me()
    const normalizedUser = normalizeUser(data)
    setUser(normalizedUser)
    return normalizedUser
  }, [])

  // Carrega usuário na inicialização se tiver token salvo
  useEffect(() => {
    const token = localStorage.getItem('access_token')
    debugLog('info', 'auth.bootstrap.begin', { hasToken: Boolean(token) })
    if (token) {
      refreshUser()
        .then((normalizedUser) => {
          debugLog('info', 'auth.bootstrap.success', {
            userId: normalizedUser?.id,
            username: normalizedUser?.username,
            tipo: normalizedUser?.tipo,
          })
        })
        .catch((error) => {
          debugLog('error', 'auth.bootstrap.failed', {
            error: normalizeError(error),
          })
          clearAuthStorage()
          setUser(null)
        })
        .finally(() => {
          debugLog('info', 'auth.bootstrap.finished')
          setLoading(false)
        })
    } else {
      debugLog('info', 'auth.bootstrap.no_token')
      setLoading(false)
    }
  }, [refreshUser])

  const login = useCallback(async ({ cpf, password, perfil }) => {
    debugLog('info', 'auth.login.begin', { cpf, perfil })
    const { data } = await authApi.login({ cpf, password, perfil })
    localStorage.setItem('access_token', data.access)
    localStorage.setItem('refresh_token', data.refresh)
    const normalizedUser = normalizeUser(data.user)
    debugLog('info', 'auth.login.success', {
      userId: normalizedUser?.id,
      username: normalizedUser?.username,
      tipo: normalizedUser?.tipo,
    })
    setUser(normalizedUser)
    return normalizedUser
  }, [])

  const logout = useCallback(async () => {
    const refreshToken = localStorage.getItem('refresh_token')
    debugLog('info', 'auth.logout.begin', { hasRefreshToken: Boolean(refreshToken) })

    if (refreshToken) {
      try {
        await authApi.logout(refreshToken)
      } catch (error) {
        debugLog('warn', 'auth.logout.backend_failed', {
          error: normalizeError(error),
        })
        // Limpeza local continua mesmo se o backend já tiver invalidado o token.
      }
    }

    clearAuthStorage()
    setUser(null)
    debugLog('info', 'auth.logout.finished')
  }, [])

  const isAuthenticated = Boolean(user)

  return (
    <AuthContext.Provider value={{ user, loading, isAuthenticated, login, logout, refreshUser }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth deve ser usado dentro de <AuthProvider>')
  return ctx
}
