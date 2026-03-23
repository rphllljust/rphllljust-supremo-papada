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
const DocumentosPage = lazy(() => import('@/pages/documentos/DocumentosPage'))
const DeclaracoesPage = lazy(() => import('@/pages/documentos/DeclaracoesPage'))
const HistoricosPage = lazy(() => import('@/pages/documentos/HistoricosPage'))
const HistoricosDigitaisPage = lazy(() => import('@/pages/documentos/HistoricosDigitaisPage'))
const GuiasTransferenciaPage = lazy(() => import('@/pages/documentos/GuiasTransferenciaPage'))
const MatriculasPage = lazy(() => import('@/pages/matriculas/MatriculasPage'))
const DiariosPage    = lazy(() => import('@/pages/diarios/DiariosPage'))
const DiarioDetailPage = lazy(() => import('@/pages/diarios/DiarioDetailPage'))
const NotasPage      = lazy(() => import('@/pages/notas/NotasPage'))
const FrequenciaPage = lazy(() => import('@/pages/frequencia/FrequenciaPage'))
const TurmasPage     = lazy(() => import('@/pages/turmas/TurmasPage'))
const TurmaCreatePage = lazy(() => import('@/pages/turmas/TurmaCreatePage'))
const ProcessosPage  = lazy(() => import('@/pages/processos/ProcessosPage'))
const ProcessoCreatePage = lazy(() => import('@/pages/processos/ProcessoCreatePage'))
const CatalogoCursosTecnicosPage = lazy(() => import('@/pages/cursos/CatalogoCursosTecnicosPage'))
const CursosIniciaisPage = lazy(() => import('@/pages/cursos/CursosIniciaisPage'))
const CursoEditPage = lazy(() => import('@/pages/cursos/CursoEditPage'))
const CursoCreatePage = lazy(() => import('@/pages/cursos/CursoCreatePage'))
const CursoUpdatePage = lazy(() => import('@/pages/cursos/CursoUpdatePage'))
const CursoDetailPage = lazy(() => import('@/pages/cursos/CursoDetailPage'))
const AreasCursosPage = lazy(() => import('@/pages/cursos/AreasCursosPage'))
const AreaCursoDetailPage = lazy(() => import('@/pages/cursos/AreaCursoDetailPage'))
const AreaCursoEditPage = lazy(() => import('@/pages/cursos/AreaCursoEditPage'))
const EixosTecnologicosPage = lazy(() => import('@/pages/cursos/EixosTecnologicosPage'))
const TipoComponentesPage = lazy(() => import('@/pages/cursos/TipoComponentesPage'))
const NiveisEnsinoPage = lazy(() => import('@/pages/cursos/NiveisEnsinoPage'))
const CursosFormacaoSuperiorPage = lazy(() => import('@/pages/cursos/CursosFormacaoSuperiorPage'))
const ComponentesPage = lazy(() => import('@/pages/cursos/ComponentesPage'))
const ComponenteDetailPage = lazy(() => import('@/pages/cursos/ComponenteDetailPage'))
const ComponenteEditPage = lazy(() => import('@/pages/cursos/ComponenteEditPage'))
const ComponenteVinculacaoPage = lazy(() => import('@/pages/cursos/ComponenteVinculacaoPage'))
const MatrizesCurricularesPage = lazy(() => import('@/pages/cursos/MatrizesCurricularesPage'))
const MatrizCurricularDetailPage = lazy(() => import('@/pages/cursos/MatrizCurricularDetailPage'))
const MatrizCurricularEditPage = lazy(() => import('@/pages/cursos/MatrizCurricularEditPage'))
const OfertasCursosPage = lazy(() => import('@/pages/cursos/OfertasCursosPage'))
const OfertaCursoDetailPage = lazy(() => import('@/pages/cursos/OfertaCursoDetailPage'))
const OfertaCursoEditPage = lazy(() => import('@/pages/cursos/OfertaCursoEditPage'))
const MoodleCategoriasPanel = lazy(() => import('@/pages/cursos/MoodleCategoriasPanel'))
const MoodleCategoriasCursosPanel = lazy(() => import('@/pages/cursos/MoodleCategoriasCursosPanel'))
const MoodleSettingsPage = lazy(() => import('@/pages/cursos/MoodleSettingsPage'))
const AtaProfessoresPage = lazy(() => import('@/pages/ata-professores/AtaProfessoresPage'))
const AtaProfessoresAssistantPage = lazy(() => import('@/pages/ata-professores/AtaProfessoresAssistantPage'))
const AlunosPage     = lazy(() => import('@/pages/alunos/AlunosPage'))
const NotificationsPage = lazy(() => import('@/pages/notificacoes/NotificationsPage'))
const NotificationPreferencesPage = lazy(() => import('@/pages/notificacoes/NotificationPreferencesPage'))
const ChangePasswordPage = lazy(() => import('@/pages/auth/ChangePasswordPage'))
const MinhaContaPage = lazy(() => import('@/pages/conta/MinhaContaPage'))
const ServidorProfilePage = lazy(() => import('@/pages/servidores/ServidorProfilePage'))
const ServidorDetailPage = lazy(() => import('@/pages/servidores/ServidorDetailPage'))
const ServidorEditPage = lazy(() => import('@/pages/servidores/ServidorEditPage'))
const ServidoresPage = lazy(() => import('@/pages/servidores/ServidoresPage'))
const SetoresPage    = lazy(() => import('@/pages/setores/SetoresPage'))
const UsuariosPage   = lazy(() => import('@/pages/usuarios/UsuariosPage'))
const UnidadesPage   = lazy(() => import('@/pages/unidades/UnidadesPage'))
const AgendaPage     = lazy(() => import('@/pages/agenda/AgendaPage'))
const EventoCreatePage = lazy(() => import('@/pages/agenda/EventoCreatePage'))
const ArquivoPage    = lazy(() => import('@/pages/arquivo/ArquivoPage'))
const GuardaCreatePage = lazy(() => import('@/pages/arquivo/GuardaCreatePage'))
const InscricoesPage = lazy(() => import('@/pages/inscricoes/InscricoesPage'))
const PublicacoesPage = lazy(() => import('@/pages/inscricoes/PublicacoesPage'))
const PublicacaoDetailPage = lazy(() => import('@/pages/inscricoes/PublicacaoDetailPage'))
const PublicacaoCreatePage = lazy(() => import('@/pages/inscricoes/PublicacaoCreatePage'))
const PublicacaoEditPage = lazy(() => import('@/pages/inscricoes/PublicacaoEditPage'))
const InscricaoCreatePage = lazy(() => import('@/pages/inscricoes/InscricaoCreatePage'))
const EstagiosPage   = lazy(() => import('@/pages/estagios/EstagiosPage'))
const EstagioDetailPage = lazy(() => import('@/pages/estagios/EstagioDetailPage'))
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
                  <Route path="/documentos" element={<RouteShell><DocumentosPage /></RouteShell>} />
                  <Route path="/documentos/declaracoes" element={<RouteShell><DeclaracoesPage /></RouteShell>} />
                  <Route path="/documentos/declaracoes/nova" element={<RouteShell><DeclaracoesPage /></RouteShell>} />
                  <Route path="/documentos/historicos" element={<RouteShell><HistoricosPage /></RouteShell>} />
                  <Route path="/documentos/historicos/novo" element={<RouteShell><HistoricosPage /></RouteShell>} />
                  <Route path="/documentos/historicos-digitais" element={<RouteShell><HistoricosDigitaisPage /></RouteShell>} />
                  <Route path="/documentos/guias" element={<RouteShell><GuiasTransferenciaPage /></RouteShell>} />
                  <Route path="/documentos/guias/nova" element={<RouteShell><GuiasTransferenciaPage /></RouteShell>} />
                  <Route path="/matriculas" element={<RouteShell><MatriculasPage /></RouteShell>} />
                  <Route path="/matriculas/nova" element={<RouteShell><MatriculasPage /></RouteShell>} />
                  <Route path="/diarios" element={<RouteShell><DiariosPage /></RouteShell>} />
                  <Route path="/diarios/:diarioId" element={<RouteShell><DiarioDetailPage /></RouteShell>} />
                  <Route path="/ensino/diarios" element={<Navigate to="/diarios" replace />} />
                  <Route path="/ensino/diarios/" element={<Navigate to="/diarios" replace />} />
                  <Route path="/ensino/diarios/:diarioId" element={<RouteShell><DiarioDetailPage /></RouteShell>} />
                  <Route path="/notas"      element={<RouteShell><NotasPage /></RouteShell>} />
                  <Route path="/notas/nova" element={<RouteShell><NotasPage /></RouteShell>} />
                  <Route path="/ensino/notas" element={<Navigate to="/notas" replace />} />
                  <Route path="/ensino/notas/" element={<Navigate to="/notas" replace />} />
                  <Route path="/ensino/notas/nova" element={<Navigate to="/notas/nova" replace />} />
                  <Route path="/ensino/notas/nova/" element={<Navigate to="/notas/nova" replace />} />
                  <Route path="/frequencia" element={<RouteShell><FrequenciaPage /></RouteShell>} />
                  <Route path="/frequencia/nova" element={<RouteShell><FrequenciaPage /></RouteShell>} />
                  <Route path="/ensino/frequencia" element={<Navigate to="/frequencia" replace />} />
                  <Route path="/ensino/frequencia/" element={<Navigate to="/frequencia" replace />} />
                  <Route path="/ensino/frequencia/nova" element={<Navigate to="/frequencia/nova" replace />} />
                  <Route path="/ensino/frequencia/nova/" element={<Navigate to="/frequencia/nova" replace />} />
                  <Route path="/turmas"     element={<RouteShell><TurmasPage /></RouteShell>} />
                  <Route path="/turmas/nova" element={<RouteShell><TurmaCreatePage /></RouteShell>} />
                  <Route path="/cursos"     element={<Navigate to="/ensino/cursoinicial/" replace />} />
                  <Route path="/cursos/"     element={<Navigate to="/ensino/cursoinicial/" replace />} />
                  <Route path="/ensino/cursotecnico" element={<RouteShell><CatalogoCursosTecnicosPage /></RouteShell>} />
                  <Route path="/ensino/cursotecnico/" element={<RouteShell><CatalogoCursosTecnicosPage /></RouteShell>} />
                  <Route path="/ensino/cursotecnico/novo" element={<RouteShell><CursoEditPage /></RouteShell>} />
                  <Route path="/ensino/cursotecnico/novo/" element={<RouteShell><CursoEditPage /></RouteShell>} />
                  <Route path="/ensino/cursotecnico/:cursoId/editar" element={<RouteShell><CursoEditPage /></RouteShell>} />
                  <Route path="/ensino/cursotecnico/:cursoId/editar/" element={<RouteShell><CursoEditPage /></RouteShell>} />
                  <Route path="/ensino/cursoinicial" element={<RouteShell><CursosIniciaisPage /></RouteShell>} />
                  <Route path="/ensino/cursoinicial/" element={<RouteShell><CursosIniciaisPage /></RouteShell>} />
                  <Route path="/ensino/areacurso" element={<RouteShell><AreasCursosPage /></RouteShell>} />
                  <Route path="/ensino/areacurso/" element={<RouteShell><AreasCursosPage /></RouteShell>} />
                  <Route path="/ensino/cursoinicial/novo" element={<RouteShell><CursoCreatePage /></RouteShell>} />
                  <Route path="/ensino/cursoinicial/novo/" element={<RouteShell><CursoCreatePage /></RouteShell>} />
                  <Route path="/ensino/areacurso/nova" element={<RouteShell><AreaCursoEditPage /></RouteShell>} />
                  <Route path="/ensino/areacurso/nova/" element={<RouteShell><AreaCursoEditPage /></RouteShell>} />
                  <Route path="/ensino/areacurso/:areaCursoId" element={<RouteShell><AreaCursoDetailPage /></RouteShell>} />
                  <Route path="/ensino/areacurso/:areaCursoId/" element={<RouteShell><AreaCursoDetailPage /></RouteShell>} />
                  <Route path="/ensino/cursoinicial/:cursoId/editar" element={<RouteShell><CursoUpdatePage /></RouteShell>} />
                  <Route path="/ensino/cursoinicial/:cursoId/editar/" element={<RouteShell><CursoUpdatePage /></RouteShell>} />
                  <Route path="/ensino/cursoinicial/:cursoId" element={<RouteShell><CursoDetailPage /></RouteShell>} />
                  <Route path="/ensino/cursoinicial/:cursoId/" element={<RouteShell><CursoDetailPage /></RouteShell>} />
                  <Route path="/ensino/areacurso/:areaCursoId/editar" element={<RouteShell><AreaCursoEditPage /></RouteShell>} />
                  <Route path="/ensino/areacurso/:areaCursoId/editar/" element={<RouteShell><AreaCursoEditPage /></RouteShell>} />
                  <Route path="/ensino/eixotecnologico" element={<RouteShell><EixosTecnologicosPage /></RouteShell>} />
                  <Route path="/ensino/eixotecnologico/" element={<RouteShell><EixosTecnologicosPage /></RouteShell>} />
                  <Route path="/ensino/tipos-componente" element={<RouteShell><TipoComponentesPage /></RouteShell>} />
                  <Route path="/ensino/tipos-componente/" element={<RouteShell><TipoComponentesPage /></RouteShell>} />
                  <Route path="/ensino/niveis-ensino" element={<RouteShell><NiveisEnsinoPage /></RouteShell>} />
                  <Route path="/ensino/niveis-ensino/" element={<RouteShell><NiveisEnsinoPage /></RouteShell>} />
                  <Route path="/ensino/cursoitinerante" element={<RouteShell><CursosFormacaoSuperiorPage /></RouteShell>} />
                  <Route path="/ensino/cursoitinerante/" element={<RouteShell><CursosFormacaoSuperiorPage /></RouteShell>} />
                  <Route path="/ensino/cursoformacaosuperior" element={<RouteShell><CursosFormacaoSuperiorPage /></RouteShell>} />
                  <Route path="/ensino/cursoformacaosuperior/" element={<RouteShell><CursosFormacaoSuperiorPage /></RouteShell>} />
                  <Route path="/cursoitinerante" element={<RouteShell><CursosFormacaoSuperiorPage /></RouteShell>} />
                  <Route path="/cursoitinerante/" element={<RouteShell><CursosFormacaoSuperiorPage /></RouteShell>} />
                  <Route path="/cursoformacaosuperior" element={<RouteShell><CursosFormacaoSuperiorPage /></RouteShell>} />
                  <Route path="/cursoformacaosuperior/" element={<RouteShell><CursosFormacaoSuperiorPage /></RouteShell>} />
                  <Route path="/ensino/cursoitinerante/novo" element={<RouteShell><CursoEditPage /></RouteShell>} />
                  <Route path="/ensino/cursoitinerante/novo/" element={<RouteShell><CursoEditPage /></RouteShell>} />
                  <Route path="/ensino/cursoitinerante/:cursoId/editar" element={<RouteShell><CursoEditPage /></RouteShell>} />
                  <Route path="/ensino/cursoitinerante/:cursoId/editar/" element={<RouteShell><CursoEditPage /></RouteShell>} />
                  <Route path="/ensino/componentes/novo" element={<RouteShell><ComponenteEditPage /></RouteShell>} />
                  <Route path="/ensino/componentes/novo/" element={<RouteShell><ComponenteEditPage /></RouteShell>} />
                  <Route path="/componentes/novo" element={<RouteShell><ComponenteEditPage /></RouteShell>} />
                  <Route path="/componentes/novo/" element={<RouteShell><ComponenteEditPage /></RouteShell>} />
                  <Route path="/ensino/componentes" element={<RouteShell><ComponentesPage /></RouteShell>} />
                  <Route path="/ensino/componentes/" element={<RouteShell><ComponentesPage /></RouteShell>} />
                  <Route path="/componentes" element={<RouteShell><ComponentesPage /></RouteShell>} />
                  <Route path="/componentes/" element={<RouteShell><ComponentesPage /></RouteShell>} />
                  <Route path="/ensino/matrizes-curriculares" element={<RouteShell><MatrizesCurricularesPage /></RouteShell>} />
                  <Route path="/ensino/matrizes-curriculares/" element={<RouteShell><MatrizesCurricularesPage /></RouteShell>} />
                  <Route path="/ensino/matrizes-curriculares/nova" element={<RouteShell><MatrizCurricularEditPage /></RouteShell>} />
                  <Route path="/ensino/matrizes-curriculares/nova/" element={<RouteShell><MatrizCurricularEditPage /></RouteShell>} />
                  <Route path="/ensino/matrizes-curriculares/:matrizId" element={<RouteShell><MatrizCurricularDetailPage /></RouteShell>} />
                  <Route path="/ensino/matrizes-curriculares/:matrizId/" element={<RouteShell><MatrizCurricularDetailPage /></RouteShell>} />
                  <Route path="/ensino/matrizes-curriculares/:matrizId/editar" element={<RouteShell><MatrizCurricularEditPage /></RouteShell>} />
                  <Route path="/ensino/matrizes-curriculares/:matrizId/editar/" element={<RouteShell><MatrizCurricularEditPage /></RouteShell>} />
                  <Route path="/ensino/moodle-categorias" element={<RouteShell><MoodleCategoriasPanel /></RouteShell>} />
                  <Route path="/ensino/ofertas" element={<RouteShell><OfertasCursosPage /></RouteShell>} />
                  <Route path="/ensino/ofertas/" element={<RouteShell><OfertasCursosPage /></RouteShell>} />
                  <Route path="/ensino/ofertas/nova" element={<RouteShell><OfertaCursoEditPage /></RouteShell>} />
                  <Route path="/ensino/ofertas/nova/" element={<RouteShell><OfertaCursoEditPage /></RouteShell>} />
                  <Route path="/ensino/ofertas/:ofertaId" element={<RouteShell><OfertaCursoDetailPage /></RouteShell>} />
                  <Route path="/ensino/ofertas/:ofertaId/" element={<RouteShell><OfertaCursoDetailPage /></RouteShell>} />
                  <Route path="/ensino/ofertas/:ofertaId/editar" element={<RouteShell><OfertaCursoEditPage /></RouteShell>} />
                  <Route path="/ensino/ofertas/:ofertaId/editar/" element={<RouteShell><OfertaCursoEditPage /></RouteShell>} />
                  <Route path="/ensino/moodle-categorias/" element={<RouteShell><MoodleCategoriasPanel /></RouteShell>} />
                  <Route path="/ti/moodle/categorias" element={<RouteShell><MoodleCategoriasPanel /></RouteShell>} />
                  <Route path="/ti/moodle/categorias/" element={<RouteShell><MoodleCategoriasPanel /></RouteShell>} />
                  <Route path="/ensino/moodle-categorias-cursos" element={<RouteShell><MoodleCategoriasCursosPanel /></RouteShell>} />
                  <Route path="/ensino/moodle-categorias-cursos/" element={<RouteShell><MoodleCategoriasCursosPanel /></RouteShell>} />
                  <Route path="/ti/moodle/catalogo" element={<RouteShell><MoodleCategoriasCursosPanel /></RouteShell>} />
                  <Route path="/ti/moodle/catalogo/" element={<RouteShell><MoodleCategoriasCursosPanel /></RouteShell>} />
                  <Route path="/ensino/moodle-config" element={<RouteShell><MoodleSettingsPage /></RouteShell>} />
                  <Route path="/ensino/moodle-config/" element={<RouteShell><MoodleSettingsPage /></RouteShell>} />
                  <Route path="/ti/moodle/configuracoes" element={<RouteShell><MoodleSettingsPage /></RouteShell>} />
                  <Route path="/ti/moodle/configuracoes/" element={<RouteShell><MoodleSettingsPage /></RouteShell>} />
                  <Route path="/ensino/componentes/:componenteId" element={<RouteShell><ComponenteDetailPage /></RouteShell>} />
                  <Route path="/ensino/componentes/:componenteId/" element={<RouteShell><ComponenteDetailPage /></RouteShell>} />
                  <Route path="/ensino/componentes/:componenteId/editar" element={<RouteShell><ComponenteEditPage /></RouteShell>} />
                  <Route path="/ensino/componentes/:componenteId/editar/" element={<RouteShell><ComponenteEditPage /></RouteShell>} />
                  <Route path="/ensino/componentes/:componenteId/vinculacao" element={<RouteShell><ComponenteVinculacaoPage /></RouteShell>} />
                  <Route path="/ensino/componentes/:componenteId/vinculacao/" element={<RouteShell><ComponenteVinculacaoPage /></RouteShell>} />
                  <Route path="/componentes/:componenteId" element={<RouteShell><ComponenteDetailPage /></RouteShell>} />
                  <Route path="/componentes/:componenteId/" element={<RouteShell><ComponenteDetailPage /></RouteShell>} />
                  <Route path="/componentes/:componenteId/editar" element={<RouteShell><ComponenteEditPage /></RouteShell>} />
                  <Route path="/componentes/:componenteId/editar/" element={<RouteShell><ComponenteEditPage /></RouteShell>} />
                  <Route path="/componentes/:componenteId/vinculacao" element={<RouteShell><ComponenteVinculacaoPage /></RouteShell>} />
                  <Route path="/componentes/:componenteId/vinculacao/" element={<RouteShell><ComponenteVinculacaoPage /></RouteShell>} />
                  <Route path="/alunos"     element={<RouteShell><AlunosPage /></RouteShell>} />
                  <Route path="/alunos/novo" element={<RouteShell><AlunosPage /></RouteShell>} />
                  <Route path="/servidores" element={<Navigate to="/rh/servidores" replace />} />
                  <Route path="/setores"    element={<Navigate to="/rh/setores" replace />} />
                  <Route path="/usuarios"   element={<RouteShell><UsuariosPage /></RouteShell>} />
                  <Route path="/unidades"   element={<RouteShell><UnidadesPage /></RouteShell>} />
                  <Route path="/agenda"     element={<RouteShell><AgendaPage /></RouteShell>} />
                  <Route path="/agenda/novo" element={<RouteShell><EventoCreatePage /></RouteShell>} />
                  <Route path="/ata-professores" element={<RouteShell><AtaProfessoresPage /></RouteShell>} />
                  <Route path="/ata-professores/nova" element={<RouteShell><AtaProfessoresAssistantPage /></RouteShell>} />
                  <Route path="/ata-professores/:ataId/editar" element={<RouteShell><AtaProfessoresAssistantPage /></RouteShell>} />
                  <Route path="/processos"  element={<RouteShell><ProcessosPage /></RouteShell>} />
                  <Route path="/processos/novo" element={<RouteShell><ProcessoCreatePage /></RouteShell>} />
                  <Route path="/arquivo"    element={<RouteShell><ArquivoPage /></RouteShell>} />
                  <Route path="/arquivo/novo" element={<RouteShell><GuardaCreatePage /></RouteShell>} />
                  <Route path="/inscricoes" element={<RouteShell><InscricoesPage /></RouteShell>} />
                  <Route path="/inscricoes/editais" element={<RouteShell><PublicacoesPage /></RouteShell>} />
                  <Route path="/inscricoes/editais/" element={<RouteShell><PublicacoesPage /></RouteShell>} />
                  <Route path="/inscricoes/editais/novo" element={<RouteShell><PublicacaoCreatePage /></RouteShell>} />
                  <Route path="/inscricoes/editais/novo/" element={<RouteShell><PublicacaoCreatePage /></RouteShell>} />
                  <Route path="/inscricoes/editais/:publicacaoId" element={<RouteShell><PublicacaoDetailPage /></RouteShell>} />
                  <Route path="/inscricoes/editais/:publicacaoId/" element={<RouteShell><PublicacaoDetailPage /></RouteShell>} />
                  <Route path="/inscricoes/editais/:publicacaoId/editar" element={<RouteShell><PublicacaoEditPage /></RouteShell>} />
                  <Route path="/inscricoes/editais/:publicacaoId/editar/" element={<RouteShell><PublicacaoEditPage /></RouteShell>} />
                  <Route path="/inscricoes/nova" element={<RouteShell><InscricaoCreatePage /></RouteShell>} />
                  <Route path="/estagio"    element={<RouteShell><EstagiosPage /></RouteShell>} />
                  <Route path="/estagio/:estagioId" element={<RouteShell><EstagioDetailPage /></RouteShell>} />
                  <Route path="/estagio/:estagioId/" element={<RouteShell><EstagioDetailPage /></RouteShell>} />
                  <Route path="/access/ava-export/preview" element={<RouteShell><AvaExportPreviewPage /></RouteShell>} />
                  <Route path="/rh/servidores" element={<RouteShell><ServidoresPage /></RouteShell>} />
                  <Route path="/rh/servidores/novo" element={<RouteShell><ServidoresPage /></RouteShell>} />
                  <Route path="/rh/servidores/:servidorId" element={<RouteShell><ServidorDetailPage /></RouteShell>} />
                  <Route path="/rh/servidores/:servidorId/editar" element={<RouteShell><ServidorEditPage /></RouteShell>} />
                  <Route path="/comum/notificacoes" element={<RouteShell><NotificationsPage /></RouteShell>} />
                  <Route path="/comum/notificacoes/preferencias" element={<RouteShell><NotificationPreferencesPage /></RouteShell>} />
                  <Route path="/comum/minha_conta" element={<RouteShell><MinhaContaPage /></RouteShell>} />
                  <Route path="/comum/minha_conta/" element={<RouteShell><MinhaContaPage /></RouteShell>} />
                  <Route path="/comum/alterar-senha" element={<RouteShell><ChangePasswordPage /></RouteShell>} />
                  <Route path="/comum/minha-conta" element={<Navigate to="/comum/minha_conta/" replace />} />
                  <Route path="/rh/notificacoes" element={<Navigate to="/comum/notificacoes" replace />} />
                  <Route path="/rh/notificacoes/preferencias" element={<Navigate to="/comum/notificacoes/preferencias" replace />} />
                  <Route path="/indisponivel/alterar-senha" element={<Navigate to="/comum/alterar-senha" replace />} />
                  <Route path="/rh/servidor/:matricula" element={<RouteShell><ServidorProfilePage /></RouteShell>} />
                  <Route path="/rh/servidor/:matricula/" element={<RouteShell><ServidorProfilePage /></RouteShell>} />
                  <Route path="/rh/setores" element={<RouteShell><SetoresPage /></RouteShell>} />
                  <Route path="/rh/setores/novo" element={<RouteShell><SetoresPage /></RouteShell>} />
                  <Route path="/rh/docentes" element={<Navigate to="/usuarios?tipo=PROFESSOR" replace />} />
                  <Route path="/rh/instituicoes" element={<RouteShell><UnidadesPage /></RouteShell>} />
                  <Route path="/rh/servidor/*" element={<Navigate to="/rh/servidores" replace />} />
                  <Route path="/rh/setor/*" element={<Navigate to="/rh/setores" replace />} />
                  <Route path="/rh/instituicao/*" element={<Navigate to="/rh/instituicoes" replace />} />
                  <Route path="/rh/:slug" element={<RouteShell><PlaceholderPage /></RouteShell>} />
                  <Route path="/documentos/atas" element={<Navigate to="/ata-professores" replace />} />
                  <Route path="/documentos/atas/novo" element={<Navigate to="/ata-professores/nova" replace />} />
                  <Route path="/documentos/atas/:ataId/editar" element={<LegacyAtaEditRedirect />} />
                  <Route path="/documentos/atas/:ataId" element={<LegacyAtaDetailRedirect />} />
                  <Route path="/indisponivel/notas" element={<Navigate to="/notas" replace />} />
                  <Route path="/indisponivel/frequencia" element={<Navigate to="/frequencia" replace />} />
                  <Route path="/indisponivel/ata-professores" element={<Navigate to="/ata-professores" replace />} />
                  <Route path="/indisponivel/:slug" element={<RouteShell><PlaceholderPage /></RouteShell>} />
                  <Route path="/app/dashboard"  element={<Navigate to="/dashboard" replace />} />
                  <Route path="/app/documentos" element={<Navigate to="/documentos" replace />} />
                  <Route path="/app/matriculas" element={<Navigate to="/matriculas" replace />} />
                  <Route path="/app/notas"     element={<Navigate to="/notas" replace />} />
                  <Route path="/app/frequencia" element={<Navigate to="/frequencia" replace />} />
                  <Route path="/app/turmas"     element={<Navigate to="/turmas" replace />} />
                  <Route path="/app/cursos"     element={<Navigate to="/ensino/cursoinicial/" replace />} />
                  <Route path="/app/alunos"     element={<Navigate to="/alunos" replace />} />
                  <Route path="/app/servidores" element={<Navigate to="/rh/servidores" replace />} />
                  <Route path="/app/setores"    element={<Navigate to="/rh/setores" replace />} />
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
