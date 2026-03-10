/**
 * App root — define todas as rotas com React Router v6.
 * Usa lazy() + Suspense para code splitting automático por página.
 */
import { lazy, Suspense, useEffect } from 'react'
import { BrowserRouter, Routes, Route, Navigate, useLocation, useNavigationType } from 'react-router-dom'
import { MutationCache, QueryCache, QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ReactQueryDevtools } from '@tanstack/react-query-devtools'
import { Toaster } from 'react-hot-toast'

import { AuthProvider } from '@/context/AuthContext'
import { useAuth } from '@/context/AuthContext'
import AppErrorBoundary from '@/components/ui/AppErrorBoundary'
import DevDiagnosticsPanel from '@/components/ui/DevDiagnosticsPanel'
import ProtectedRoute from '@/components/ui/ProtectedRoute'
import Layout from '@/components/layout/Layout'
import PortalLayout from '@/components/layout/PortalLayout'
import { debugLog, normalizeError } from '@/utils/debug'

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
const UsuariosPage   = lazy(() => import('@/pages/usuarios/UsuariosPage'))
const UnidadesPage   = lazy(() => import('@/pages/unidades/UnidadesPage'))
const AgendaPage     = lazy(() => import('@/pages/agenda/AgendaPage'))
const ArquivoPage    = lazy(() => import('@/pages/arquivo/ArquivoPage'))
const InscricoesPage = lazy(() => import('@/pages/inscricoes/InscricoesPage'))
const EstagiosPage   = lazy(() => import('@/pages/estagios/EstagiosPage'))
const AvaExportPreviewPage = lazy(() => import('@/pages/access/AvaExportPreviewPage'))
const PlaceholderPage = lazy(() => import('@/pages/placeholder/PlaceholderPage'))

const queryClient = new QueryClient({
  queryCache: new QueryCache({
    onError: (error, query) => {
      debugLog('error', 'react_query.query_error', {
        queryKey: query.queryKey,
        error: normalizeError(error),
      })
    },
  }),
  mutationCache: new MutationCache({
    onError: (error, variables, _context, mutation) => {
      debugLog('error', 'react_query.mutation_error', {
        mutationKey: mutation.options.mutationKey,
        variables,
        error: normalizeError(error),
      })
    },
  }),
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

function RouteLoader() {
  return (
    <div className="page-loader" role="status" aria-live="polite">
      <div className="spinner" />
      <span>Carregando modulo...</span>
    </div>
  )
}

function RouteShell({ children }) {
  return (
    <AppErrorBoundary>
      <Suspense fallback={<RouteLoader />}>
        {children}
      </Suspense>
    </AppErrorBoundary>
  )
}

function RouterDiagnostics() {
  const location = useLocation()
  const navigationType = useNavigationType()

  useEffect(() => {
    debugLog('info', 'router.navigation', {
      pathname: location.pathname,
      search: location.search,
      hash: location.hash,
      navigationType,
      state: location.state,
    })
  }, [location, navigationType])

  return null
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
        <AppErrorBoundary>
          <BrowserRouter>
            <RouterDiagnostics />
            <DevDiagnosticsPanel />
            <Routes>
              <Route path="/" element={<HomeEntry />} />

              {/* ── Portal público ──────────────────────── */}
              <Route element={<PortalLayout />}>
                <Route path="/portal" element={<RouteShell><PortalHomeRedirect /></RouteShell>} />
                <Route path="/portal/cursos" element={<RouteShell><CursosPublicosPage /></RouteShell>} />
              </Route>

              {/* ── Auth ────────────────────────────────── */}
              <Route path="/accounts/login" element={<RouteShell><LoginPage /></RouteShell>} />
              <Route path="/login" element={<Navigate to="/accounts/login" replace />} />

              {/* ── Painel interno (JWT obrigatório) ─────── */}
              <Route element={<ProtectedRoute />}>
                <Route element={<Layout />}>
                  <Route path="/dashboard"  element={<RouteShell><DashboardPage /></RouteShell>} />
                  <Route path="/matriculas" element={<RouteShell><MatriculasPage /></RouteShell>} />
                  <Route path="/turmas"     element={<RouteShell><TurmasPage /></RouteShell>} />
                  <Route path="/cursos"     element={<RouteShell><CursosPage /></RouteShell>} />
                  <Route path="/alunos"     element={<RouteShell><AlunosPage /></RouteShell>} />
                  <Route path="/usuarios"   element={<RouteShell><UsuariosPage /></RouteShell>} />
                  <Route path="/unidades"   element={<RouteShell><UnidadesPage /></RouteShell>} />
                  <Route path="/agenda"     element={<RouteShell><AgendaPage /></RouteShell>} />
                  <Route path="/processos"  element={<RouteShell><ProcessosPage /></RouteShell>} />
                  <Route path="/arquivo"    element={<RouteShell><ArquivoPage /></RouteShell>} />
                  <Route path="/inscricoes" element={<RouteShell><InscricoesPage /></RouteShell>} />
                  <Route path="/estagio"    element={<RouteShell><EstagiosPage /></RouteShell>} />
                  <Route path="/access/ava-export/preview" element={<RouteShell><AvaExportPreviewPage /></RouteShell>} />
                  <Route path="/indisponivel/:slug" element={<RouteShell><PlaceholderPage /></RouteShell>} />
                  <Route path="/app/dashboard"  element={<Navigate to="/dashboard" replace />} />
                  <Route path="/app/matriculas" element={<Navigate to="/matriculas" replace />} />
                  <Route path="/app/turmas"     element={<Navigate to="/turmas" replace />} />
                  <Route path="/app/cursos"     element={<Navigate to="/cursos" replace />} />
                  <Route path="/app/alunos"     element={<Navigate to="/alunos" replace />} />
                  <Route path="/app/usuarios"   element={<Navigate to="/usuarios" replace />} />
                  <Route path="/app/unidades"   element={<Navigate to="/unidades" replace />} />
                  <Route path="/app/agenda"     element={<Navigate to="/agenda" replace />} />
                  <Route path="/app/processos"  element={<Navigate to="/processos" replace />} />
                  <Route path="/app/arquivo"    element={<Navigate to="/arquivo" replace />} />
                  <Route path="/app/inscricoes" element={<Navigate to="/inscricoes" replace />} />
                  <Route path="/app/estagios"   element={<Navigate to="/estagio" replace />} />
                  <Route path="/app/access/ava-export/preview" element={<Navigate to="/access/ava-export/preview" replace />} />
                </Route>
              </Route>

              {/* Fallback */}
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </BrowserRouter>
        </AppErrorBoundary>

        <Toaster position="top-right" toastOptions={{ duration: 4000 }} />
      </AuthProvider>

      {import.meta.env.DEV && <ReactQueryDevtools initialIsOpen={false} />}
    </QueryClientProvider>
  )
}
