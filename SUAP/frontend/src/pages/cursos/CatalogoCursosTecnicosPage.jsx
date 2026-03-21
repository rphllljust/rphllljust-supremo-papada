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
      listParams={{ tipo_curso: 'tecnico' }}
      searchPlaceholder="Buscar curso técnico..."
      emptyMessage="Nenhum curso técnico encontrado."
      createPath="/ensino/cursotecnico/novo"
      editPathBuilder={(cursoId) => `/ensino/cursotecnico/${cursoId}/editar`}
      moodleSyncConfig={{
        tipoCurso: 'tecnico',
        tipoCursoLabel: 'Educacao profissional tecnica',
        rootCategoryIds: [387],
        syncLabel: 'Sincronizar cursos técnicos',
        successMessage: 'Cursos técnicos sincronizados a partir do Moodle.',
        description: 'Busca todos os cursos sob a categoria Moodle 387, incluindo subcategorias descendentes, persiste no banco local do SUAP e atualiza esta listagem.',
      }}
    />
  )
}