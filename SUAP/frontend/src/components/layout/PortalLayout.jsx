import { Outlet } from 'react-router-dom'
import PortalNavbar from '@/components/portal/PortalNavbar'

export default function PortalLayout() {
  return (
    <div>
      <PortalNavbar />
      <Outlet />
      <footer className="portal-footer">
        © {new Date().getFullYear()} IDEP-ETEC — Instituto Estadual de Desenvolvimento da Educação Profissional.
        Todos os direitos reservados.
      </footer>
    </div>
  )
}
