/**
 * Rota protegida — redireciona para /login se não autenticado.
 * Usa Suspense + lazy() para code splitting por página.
 */
import { Navigate, Outlet } from 'react-router-dom'
import { useAuth } from '@/context/AuthContext'

export default function ProtectedRoute() {
  const { isAuthenticated, loading } = useAuth()

  if (loading) {
    return (
      <div className="loading-screen">
        <div className="spinner" />
        <span>Carregando...</span>
      </div>
    )
  }

  return isAuthenticated ? <Outlet /> : <Navigate to="/accounts/login" replace />
}
