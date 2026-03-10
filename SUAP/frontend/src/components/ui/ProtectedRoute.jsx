/**
 * Rota protegida — redireciona para /login se não autenticado.
 * Usa Suspense + lazy() para code splitting por página.
 */
import { Navigate, Outlet } from 'react-router-dom'
import { useAuth } from '@/context/AuthContext'
import { useLocation } from 'react-router-dom'
import { buildLoginPath } from '@/utils/authNavigation'

export default function ProtectedRoute() {
  const { isAuthenticated, loading } = useAuth()
  const location = useLocation()

  if (loading) {
    return (
      <div className="loading-screen">
        <div className="spinner" />
        <span>Carregando...</span>
      </div>
    )
  }

  return isAuthenticated ? <Outlet /> : <Navigate to={buildLoginPath(`${location.pathname}${location.search}${location.hash}`)} replace />
}
