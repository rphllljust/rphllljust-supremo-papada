/**
 * Context de autenticação — gerencia login, logout e usuário atual.
 * Usa localStorage para persistir os tokens JWT.
 */
import { createContext, useContext, useState, useEffect, useCallback } from 'react'
import { authApi } from '@/api/endpoints'

const AuthContext = createContext(null)

const PROFILE_LABELS = {
  ALUNO: 'Aluno',
  PROFESSOR: 'Professor',
  SECRETARIA: 'Secretaria',
  COORDENACAO: 'Coordenacao/Consulta',
  ADMIN: 'Administrador',
}

function normalizeUser(user) {
  if (!user) return null

  const nomeCompleto = [user.first_name, user.last_name].filter(Boolean).join(' ').trim()

  return {
    ...user,
    nome_completo: user.nome_completo || nomeCompleto || user.username,
    tipo_display: user.tipo_display || PROFILE_LABELS[user.perfil] || PROFILE_LABELS[user.tipo] || user.perfil || user.tipo,
  }
}

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  // Carrega usuário na inicialização se tiver token salvo
  useEffect(() => {
    const token = localStorage.getItem('access_token')
    if (token) {
      authApi.me()
        .then((res) => setUser(normalizeUser(res.data)))
        .catch(() => {
          localStorage.clear()
          setUser(null)
        })
        .finally(() => setLoading(false))
    } else {
      setLoading(false)
    }
  }, [])

  const login = useCallback(async ({ cpf, password, perfil }) => {
    const { data } = await authApi.login({ cpf, password, perfil })
    localStorage.setItem('access_token', data.access)
    localStorage.setItem('refresh_token', data.refresh)
    const normalizedUser = normalizeUser(data.user)
    setUser(normalizedUser)
    return normalizedUser
  }, [])

  const logout = useCallback(async () => {
    const refreshToken = localStorage.getItem('refresh_token')

    if (refreshToken) {
      try {
        await authApi.logout(refreshToken)
      } catch {
        // Limpeza local continua mesmo se o backend já tiver invalidado o token.
      }
    }

    localStorage.clear()
    setUser(null)
  }, [])

  const isAuthenticated = Boolean(user)

  return (
    <AuthContext.Provider value={{ user, loading, isAuthenticated, login, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth deve ser usado dentro de <AuthProvider>')
  return ctx
}
