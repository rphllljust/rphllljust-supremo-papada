import CursosPage from './CursosPage'
import MoodleCursosPanel from './MoodleCursosPanel'
import { Link } from 'react-router-dom'

const BREADCRUMBS = [
  { label: 'Inicio', to: '/dashboard' },
  { label: 'Ensino' },
  { label: 'Cadastros Gerais' },
  { label: 'Cursos iniciais' },
]

export default function CursosIniciaisPage() {
  return (
    <CursosPage
      title="Cursos iniciais"
      subtitle="Ensino • Cadastros Gerais"
      breadcrumbs={BREADCRUMBS}
      queryScope="cursos-iniciais"
      listParams={{ apenas_superiores: true }}
      searchPlaceholder="Buscar curso inicial..."
      emptyMessage="Nenhum curso inicial encontrado."
      createPath="/ensino/cursoinicial/novo"
      editPathBuilder={(cursoId) => `/ensino/cursoinicial/${cursoId}/editar`}
      detailPathBuilder={(cursoId) => `/ensino/cursoinicial/${cursoId}`}
      beforeTableContent={
        <>
          <MoodleCursosPanel />
        </>
      }
      extraHeaderActions={
        <Link className="btn btn--outline" to="/ensino/moodle-categorias">Categorias Moodle</Link>
      }
    />
  )
}