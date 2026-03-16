import CursosPage from './CursosPage'

const BREADCRUMBS = [
  { label: 'Inicio', to: '/dashboard' },
  { label: 'Ensino' },
  { label: 'Cadastros Gerais' },
  { label: 'Catálogo de cursos técnicos' },
]

export default function CatalogoCursosTecnicosPage() {
  return (
    <CursosPage
      title="Catálogo de cursos técnicos"
      subtitle="Ensino • Cadastros Gerais"
      breadcrumbs={BREADCRUMBS}
      queryScope="catalogo-tecnico"
      listParams={{ apenas_tecnicos: true }}
      searchPlaceholder="Buscar curso técnico..."
      emptyMessage="Nenhum curso técnico encontrado."
      createPath="/ensino/cursotecnico/novo"
      editPathBuilder={(cursoId) => `/ensino/cursotecnico/${cursoId}/editar`}
    />
  )
}