/**
 * Dashboard principal — agrega contagens dos módulos já expostos pela API.
 */
import { useQueries } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { cursosApi, matriculasApi, turmasApi, unidadesApi, usuariosApi } from '@/api/endpoints'
import StatCard from '@/components/ui/StatCard'
import { useAuth } from '@/context/AuthContext'
import {
  ClipboardList, Users, BookOpen, GraduationCap,
  Building2
} from 'lucide-react'

const STATS_CONFIG = [
  { key: 'total_matriculas',          label: 'Matrículas Ativas',       icon: ClipboardList, color: '#1351B4' },
  { key: 'total_turmas',              label: 'Turmas Ativas',            icon: Users,         color: '#155BCB' },
  { key: 'total_cursos',              label: 'Cursos',                   icon: BookOpen,      color: '#0069D9' },
  { key: 'total_alunos',              label: 'Alunos',                   icon: GraduationCap, color: '#1A7F5A' },
  { key: 'total_unidades',            label: 'Unidades',                 icon: Building2,     color: '#345D96' },
]

export default function DashboardPage() {
  const { user } = useAuth()

  const results = useQueries({
    queries: [
      {
        queryKey: ['dashboard-stats', 'matriculas'],
        queryFn: () => matriculasApi.list({ page: 1, page_size: 1, status: 'ATIVA' }).then((r) => r.data),
        staleTime: 30_000,
        refetchInterval: 60_000,
      },
      {
        queryKey: ['dashboard-stats', 'turmas'],
        queryFn: () => turmasApi.list({ page: 1, page_size: 1, status: 'ATIVA' }).then((r) => r.data),
        staleTime: 30_000,
        refetchInterval: 60_000,
      },
      {
        queryKey: ['dashboard-stats', 'cursos'],
        queryFn: () => cursosApi.list({ page: 1, page_size: 1 }).then((r) => r.data),
        staleTime: 30_000,
        refetchInterval: 60_000,
      },
      {
        queryKey: ['dashboard-stats', 'alunos'],
        queryFn: () => usuariosApi.list({ page: 1, page_size: 1, tipo: 'ALUNO' }).then((r) => r.data),
        staleTime: 30_000,
        refetchInterval: 60_000,
      },
      {
        queryKey: ['dashboard-stats', 'unidades'],
        queryFn: () => unidadesApi.list({ page: 1, page_size: 1 }).then((r) => r.data),
        staleTime: 30_000,
        refetchInterval: 60_000,
      },
    ],
  })

  const [matriculasResult, turmasResult, cursosResult, alunosResult, unidadesResult] = results
  const isLoading = results.some((result) => result.isLoading)
  const isError = results.some((result) => result.isError)
  const stats = {
    total_matriculas: matriculasResult.data?.count ?? 0,
    total_turmas: turmasResult.data?.count ?? 0,
    total_cursos: cursosResult.data?.count ?? 0,
    total_alunos: alunosResult.data?.count ?? 0,
    total_unidades: unidadesResult.data?.count ?? 0,
  }

  return (
    <div className="dashboard-page">
      <div className="page-header">
        <h1 className="page-title">Dashboard</h1>
        <p className="page-subtitle">
          Bem-vindo(a), <strong>{user?.nome_completo || user?.username}</strong>
        </p>
      </div>

      {isError && (
        <div className="alert alert--error">
          Não foi possível carregar os dados do painel. Verifique a autenticação e a API.
        </div>
      )}

      <div className="stats-grid">
        {STATS_CONFIG.map(({ key, label, icon, color }) => (
          <StatCard
            key={key}
            label={label}
            value={stats?.[key]}
            icon={icon}
            color={color}
            loading={isLoading}
          />
        ))}
      </div>

      <div className="dashboard-grid">
        <RecentSection />
      </div>
    </div>
  )
}

function RecentSection() {
  const quickLinks = [
    { href: '/matriculas', label: 'Nova Matrícula' },
    { href: '/cursos', label: 'Consultar Cursos' },
    { href: '/turmas', label: 'Gerenciar Turmas' },
    { href: '/alunos', label: 'Consultar Alunos' },
  ]

  return (
    <div className="dashboard-card">
      <h2 className="dashboard-card__title">Acesso Rápido</h2>
      <div className="quick-links">
        {quickLinks.map(({ href, label }) => (
          <Link key={href} to={href} className="quick-link">
            {label}
          </Link>
        ))}
      </div>
    </div>
  )
}
