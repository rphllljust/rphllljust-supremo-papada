import { NavLink } from 'react-router-dom'

export default function PortalNavbar() {
  const dashboardHref = typeof window !== 'undefined' && window.location.port === '5173'
    ? 'http://localhost:8000/'
    : '/'

  return (
    <>
      {/* Barra gov.br */}
      <div className="govbar">
        <div className="govbar-inner">
          <div className="govbar-left">
            <a href="#">Portal do Governo</a>
            <span className="govbar-sep">|</span>
            <a href="#">Acesso à Informação</a>
          </div>
          <div className="govbar-right">
            <a href="#">Webmail</a>
            <span className="govbar-sep">|</span>
            <a href="/dashboard/login/">SUAP</a>
          </div>
        </div>
      </div>

      {/* Navbar principal */}
      <nav className="portal-navbar">
        <div className="portal-navbar__inner">
          <div className="portal-navbar__brand">
            <span className="portal-navbar__logo">IDEP</span>
            <div className="portal-navbar__name">
              <div className="portal-navbar__title">IDEP-ETEC</div>
              <div className="portal-navbar__subtitle">
                Instituto Estadual de Desenvolvimento da Educação Profissional
              </div>
            </div>
          </div>

          <ul className="portal-navbar__menu">
            <li><a href={dashboardHref}>Inicio</a></li>
            <li><NavLink to="/portal/cursos" className={({ isActive }) => isActive ? 'active' : ''}>Cursos</NavLink></li>
            <li><NavLink to="/portal/pesquisa">Pesquisa</NavLink></li>
            <li><NavLink to="/portal/extensao">Extensão</NavLink></li>
            <li><NavLink to="/portal/editais">Editais</NavLink></li>
          </ul>
        </div>
      </nav>
    </>
  )
}
