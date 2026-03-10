/**
 * Layout principal — Sidebar + Navbar + área de conteúdo.
 */
import { useState } from 'react'
import { Link, NavLink, Outlet, useNavigate } from 'react-router-dom'
import { useAuth } from '@/context/AuthContext'
import {
  LayoutDashboard, Users, BookOpen, GraduationCap,
  ClipboardList, Calendar, FileText, Archive,
  UserCheck, Briefcase, LogOut, Menu, X, ChevronRight
} from 'lucide-react'

const navItems = [
  { to: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/matriculas', label: 'Matrículas', icon: ClipboardList },
  { to: '/turmas', label: 'Turmas', icon: Users },
  { to: '/cursos', label: 'Cursos', icon: BookOpen },
  { to: '/alunos', label: 'Alunos', icon: GraduationCap },
]

export default function Layout() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const [sidebarOpen, setSidebarOpen] = useState(true)

  const handleLogout = () => {
    logout().finally(() => navigate('/accounts/login'))
  }

  return (
    <div className="layout">
      {/* Sidebar */}
      <aside className={`sidebar ${sidebarOpen ? 'sidebar--open' : 'sidebar--collapsed'}`}>
        <div className="sidebar__header">
          <span className="sidebar__logo">SUAP-IDEP</span>
          <button className="sidebar__toggle" onClick={() => setSidebarOpen(!sidebarOpen)}>
            {sidebarOpen ? <X size={18} /> : <Menu size={18} />}
          </button>
        </div>

        <nav className="sidebar__nav">
          {navItems.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                `sidebar__link ${isActive ? 'sidebar__link--active' : ''}`
              }
            >
              <Icon size={18} className="sidebar__icon" />
              {sidebarOpen && <span className="sidebar__label">{label}</span>}
            </NavLink>
          ))}
        </nav>

        <div className="sidebar__footer">
          {sidebarOpen && (
            <div className="sidebar__user">
              <span className="sidebar__user-name">{user?.nome_completo || user?.username}</span>
              <span className="sidebar__user-role">{user?.tipo_display}</span>
            </div>
          )}
          <button className="sidebar__logout" onClick={handleLogout} title="Sair">
            <LogOut size={18} />
            {sidebarOpen && <span>Sair</span>}
          </button>
        </div>
      </aside>

      {/* Conteúdo principal */}
      <main className="main-content">
        <Outlet />
      </main>
    </div>
  )
}
