import CursosPage from './CursosPage'

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
      listParams={{ tipo_curso: 'formacao_inicial' }}
      searchPlaceholder="Buscar curso inicial..."
      emptyMessage="Nenhum curso inicial encontrado."
      createPath="/ensino/cursoinicial/novo"
      editPathBuilder={(cursoId) => `/ensino/cursoinicial/${cursoId}/editar`}
      detailPathBuilder={(cursoId) => `/ensino/cursoinicial/${cursoId}`}
      beforeTableContent={null}
      moodleSyncConfig={{
        tipoCurso: 'formacao_inicial',
        tipoCursoLabel: 'Formacao inicial e continuada',
        rootCategoryIds: [399],
        syncLabel: 'Sincronizar cursos iniciais',
        successMessage: 'Cursos iniciais sincronizados a partir do Moodle.',
        description: 'Busca todos os cursos sob a categoria Moodle 399, incluindo subcategorias descendentes, persiste no banco local do SUAP e atualiza esta listagem.',
      }}
    />
  )
}