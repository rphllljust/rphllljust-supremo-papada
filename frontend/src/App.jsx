/**
 * App root — define todas as rotas com React Router v6.
 * Usa lazy() + Suspense para code splitting automático por página.
 */
import { lazy, Suspense } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ReactQueryDevtools } from '@tanstack/react-query-devtools'
import { Toaster } from 'react-hot-toast'

import { AuthProvider } from '@/context/AuthContext'
import { useAuth } from '@/context/AuthContext'
import ProtectedRoute from '@/components/ui/ProtectedRoute'
import Layout from '@/components/layout/Layout'
import PortalLayout from '@/components/layout/PortalLayout'

// ── Portal público (sem autenticação) ─────────────────
const PortalHomeRedirect = lazy(() => import('@/pages/portal/PortalHomeRedirect'))
const CursosPublicosPage = lazy(() => import('@/pages/portal/CursosPublicosPage'))

// ── Auth ───────────────────────────────────────────────
const LoginPage      = lazy(() => import('@/pages/auth/LoginPage'))

// ── Painel interno (requer JWT) ────────────────────────
const DashboardPage  = lazy(() => import('@/pages/dashboard/DashboardPage'))
const MatriculasPage = lazy(() => import('@/pages/matriculas/MatriculasPage'))
const TurmasPage     = lazy(() => import('@/pages/turmas/TurmasPage'))
const ProcessosPage  = lazy(() => import('@/pages/processos/ProcessosPage'))
const CursosPage     = lazy(() => import('@/pages/cursos/CursosPage'))
const AlunosPage     = lazy(() => import('@/pages/alunos/AlunosPage'))
const AgendaPage     = lazy(() => import('@/pages/agenda/AgendaPage'))
const ArquivoPage    = lazy(() => import('@/pages/arquivo/ArquivoPage'))
const InscricoesPage = lazy(() => import('@/pages/inscricoes/InscricoesPage'))
const EstagiosPage   = lazy(() => import('@/pages/estagios/EstagiosPage'))

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
})

function PageLoader() {
  return (
    <div className="loading-screen">
      <div className="spinner" />
    </div>
  )
}

function HomeEntry() {
  const { isAuthenticated, loading } = useAuth()

  if (loading) {
    return <PageLoader />
  }

  return <Navigate to={isAuthenticated ? '/dashboard' : '/accounts/login'} replace />
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <BrowserRouter>
          <Suspense fallback={<PageLoader />}>
            <Routes>
              <Route path="/" element={<HomeEntry />} />

              {/* ── Portal público ──────────────────────── */}
              <Route element={<PortalLayout />}>
                <Route path="/portal" element={<PortalHomeRedirect />} />
                <Route path="/portal/cursos" element={<CursosPublicosPage />} />
              </Route>

              {/* ── Auth ────────────────────────────────── */}
              <Route path="/accounts/login" element={<LoginPage />} />
              <Route path="/login" element={<Navigate to="/accounts/login" replace />} />

              {/* ── Painel interno (JWT obrigatório) ─────── */}
              <Route element={<ProtectedRoute />}>
                <Route element={<Layout />}>
                  <Route path="/dashboard"  element={<DashboardPage />} />
                  <Route path="/matriculas" element={<MatriculasPage />} />
                  <Route path="/turmas"     element={<TurmasPage />} />
                  <Route path="/cursos"     element={<CursosPage />} />
                  <Route path="/alunos"     element={<AlunosPage />} />
                  <Route path="/agenda"     element={<AgendaPage />} />
                  <Route path="/processos"  element={<ProcessosPage />} />
                  <Route path="/arquivo"    element={<ArquivoPage />} />
                  <Route path="/inscricoes" element={<InscricoesPage />} />
                  <Route path="/estagio"    element={<EstagiosPage />} />
                  <Route path="/app/dashboard"  element={<Navigate to="/dashboard" replace />} />
                  <Route path="/app/matriculas" element={<Navigate to="/matriculas" replace />} />
                  <Route path="/app/turmas"     element={<Navigate to="/turmas" replace />} />
                  <Route path="/app/cursos"     element={<Navigate to="/cursos" replace />} />
                  <Route path="/app/alunos"     element={<Navigate to="/alunos" replace />} />
                  <Route path="/app/agenda"     element={<Navigate to="/agenda" replace />} />
                  <Route path="/app/processos"  element={<Navigate to="/processos" replace />} />
                  <Route path="/app/arquivo"    element={<Navigate to="/arquivo" replace />} />
                  <Route path="/app/inscricoes" element={<Navigate to="/inscricoes" replace />} />
                  <Route path="/app/estagios"   element={<Navigate to="/estagio" replace />} />
                </Route>
              </Route>

              {/* Fallback */}
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </Suspense>
        </BrowserRouter>

        <Toaster position="top-right" toastOptions={{ duration: 4000 }} />
      </AuthProvider>

      {import.meta.env.DEV && <ReactQueryDevtools initialIsOpen={false} />}
    </QueryClientProvider>
  )
}
