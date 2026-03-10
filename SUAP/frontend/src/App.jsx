/**
 * App root — define todas as rotas com React Router v6.
 * Usa lazy() + Suspense para code splitting automático por página.
 */
import { lazy, Suspense, useEffect } from 'react'
import { BrowserRouter, Routes, Route, Navigate, useLocation, useNavigate, useNavigationType, useParams } from 'react-router-dom'
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
import { AUTH_REDIRECT_EVENT, buildLoginPath } from '@/utils/authNavigation'
import { debugLog, normalizeError } from '@/utils/debug'

// ── Portal público (sem autenticação) ─────────────────
const PortalHomeRedirect = lazy(() => import('@/pages/portal/PortalHomeRedirect'))
const CursosPublicosPage = lazy(() => import('@/pages/portal/CursosPublicosPage'))

// ── Auth ───────────────────────────────────────────────
const LoginPage      = lazy(() => import('@/pages/auth/LoginPage'))

// ── Painel interno (requer JWT) ────────────────────────
const DashboardPage  = lazy(() => import('@/pages/dashboard/DashboardPage'))
const MatriculasPage = lazy(() => import('@/pages/matriculas/MatriculasPage'))
const NotasPage      = lazy(() => import('@/pages/notas/NotasPage'))
const FrequenciaPage = lazy(() => import('@/pages/frequencia/FrequenciaPage'))
const TurmasPage     = lazy(() => import('@/pages/turmas/TurmasPage'))
const ProcessosPage  = lazy(() => import('@/pages/processos/ProcessosPage'))
const CursosPage     = lazy(() => import('@/pages/cursos/CursosPage'))
const AtaProfessoresPage = lazy(() => import('@/pages/ata-professores/AtaProfessoresPage'))
const AtaProfessoresAssistantPage = lazy(() => import('@/pages/ata-professores/AtaProfessoresAssistantPage'))
const AlunosPage     = lazy(() => import('@/pages/alunos/AlunosPage'))
const ServidoresPage = lazy(() => import('@/pages/servidores/ServidoresPage'))
const SetoresPage    = lazy(() => import('@/pages/setores/SetoresPage'))
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

function AuthRedirectHandler() {
  const navigate = useNavigate()

  useEffect(() => {
    const handleRedirect = (event) => {
      navigate(event.detail?.target || buildLoginPath(), { replace: true })
    }

    window.addEventListener(AUTH_REDIRECT_EVENT, handleRedirect)
    return () => window.removeEventListener(AUTH_REDIRECT_EVENT, handleRedirect)
  }, [navigate])

  return null
}

function HomeEntry() {
  const { isAuthenticated, loading } = useAuth()

  if (loading) {
    return <PageLoader />
  }

  return <Navigate to={isAuthenticated ? '/dashboard' : '/login'} replace />
}

function LegacyAtaDetailRedirect() {
  const { ataId } = useParams()
  return <Navigate to={`/ata-professores?ata=${encodeURIComponent(ataId || '')}`} replace />
}

function LegacyAtaEditRedirect() {
  const { ataId } = useParams()
  return <Navigate to={`/ata-professores/${ataId}/editar`} replace />
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <AppErrorBoundary>
          <BrowserRouter>
            <AuthRedirectHandler />
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
              <Route path="/login" element={<RouteShell><LoginPage /></RouteShell>} />
              <Route path="/accounts/login" element={<Navigate to="/login" replace />} />

              {/* ── Painel interno (JWT obrigatório) ─────── */}
              <Route element={<ProtectedRoute />}>
                <Route element={<Layout />}>
                  <Route path="/dashboard"  element={<RouteShell><DashboardPage /></RouteShell>} />
                  <Route path="/matriculas" element={<RouteShell><MatriculasPage /></RouteShell>} />
                  <Route path="/notas"      element={<RouteShell><NotasPage /></RouteShell>} />
                  <Route path="/frequencia" element={<RouteShell><FrequenciaPage /></RouteShell>} />
                  <Route path="/turmas"     element={<RouteShell><TurmasPage /></RouteShell>} />
                  <Route path="/cursos"     element={<RouteShell><CursosPage /></RouteShell>} />
                  <Route path="/alunos"     element={<RouteShell><AlunosPage /></RouteShell>} />
                  <Route path="/servidores" element={<RouteShell><ServidoresPage /></RouteShell>} />
                  <Route path="/setores"    element={<RouteShell><SetoresPage /></RouteShell>} />
                  <Route path="/usuarios"   element={<RouteShell><UsuariosPage /></RouteShell>} />
                  <Route path="/unidades"   element={<RouteShell><UnidadesPage /></RouteShell>} />
                  <Route path="/agenda"     element={<RouteShell><AgendaPage /></RouteShell>} />
                  <Route path="/ata-professores" element={<RouteShell><AtaProfessoresPage /></RouteShell>} />
                  <Route path="/ata-professores/nova" element={<RouteShell><AtaProfessoresAssistantPage /></RouteShell>} />
                  <Route path="/ata-professores/:ataId/editar" element={<RouteShell><AtaProfessoresAssistantPage /></RouteShell>} />
                  <Route path="/processos"  element={<RouteShell><ProcessosPage /></RouteShell>} />
                  <Route path="/arquivo"    element={<RouteShell><ArquivoPage /></RouteShell>} />
                  <Route path="/inscricoes" element={<RouteShell><InscricoesPage /></RouteShell>} />
                  <Route path="/estagio"    element={<RouteShell><EstagiosPage /></RouteShell>} />
                  <Route path="/access/ava-export/preview" element={<RouteShell><AvaExportPreviewPage /></RouteShell>} />
                  <Route path="/rh/servidor/*" element={<Navigate to="/servidores" replace />} />
                  <Route path="/rh/setor/*" element={<Navigate to="/setores" replace />} />
                  <Route path="/rh/instituicao/*" element={<Navigate to="/unidades" replace />} />
                  <Route path="/documentos/atas" element={<Navigate to="/ata-professores" replace />} />
                  <Route path="/documentos/atas/novo" element={<Navigate to="/ata-professores/nova" replace />} />
                  <Route path="/documentos/atas/:ataId/editar" element={<LegacyAtaEditRedirect />} />
                  <Route path="/documentos/atas/:ataId" element={<LegacyAtaDetailRedirect />} />
                  <Route path="/indisponivel/notas" element={<Navigate to="/notas" replace />} />
                  <Route path="/indisponivel/frequencia" element={<Navigate to="/frequencia" replace />} />
                  <Route path="/indisponivel/ata-professores" element={<Navigate to="/ata-professores" replace />} />
                  <Route path="/indisponivel/:slug" element={<RouteShell><PlaceholderPage /></RouteShell>} />
                  <Route path="/app/dashboard"  element={<Navigate to="/dashboard" replace />} />
                  <Route path="/app/matriculas" element={<Navigate to="/matriculas" replace />} />
                  <Route path="/app/notas"     element={<Navigate to="/notas" replace />} />
                  <Route path="/app/frequencia" element={<Navigate to="/frequencia" replace />} />
                  <Route path="/app/turmas"     element={<Navigate to="/turmas" replace />} />
                  <Route path="/app/cursos"     element={<Navigate to="/cursos" replace />} />
                  <Route path="/app/alunos"     element={<Navigate to="/alunos" replace />} />
                  <Route path="/app/servidores" element={<Navigate to="/servidores" replace />} />
                  <Route path="/app/setores"    element={<Navigate to="/setores" replace />} />
                  <Route path="/app/usuarios"   element={<Navigate to="/usuarios" replace />} />
                  <Route path="/app/unidades"   element={<Navigate to="/unidades" replace />} />
                  <Route path="/app/agenda"     element={<Navigate to="/agenda" replace />} />
                  <Route path="/app/ata-professores" element={<Navigate to="/ata-professores" replace />} />
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
