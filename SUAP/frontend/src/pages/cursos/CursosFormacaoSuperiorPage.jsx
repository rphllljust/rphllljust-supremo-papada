import CursosPage from './CursosPage'

const BREADCRUMBS = [
  { label: 'Inicio', to: '/dashboard' },
  { label: 'Ensino' },
  { label: 'Cadastros Gerais' },
  { label: 'Cursos itinerantes' },
]

export default function CursosFormacaoSuperiorPage() {
  return (
    <CursosPage
      title="Cursos itinerantes"
      subtitle="Ensino • Cadastros Gerais"
      breadcrumbs={BREADCRUMBS}
      queryScope="cursos-itinerantes"
      listParams={{ tipo_curso: 'itinerante' }}
      searchPlaceholder="Buscar curso itinerante..."
      emptyMessage="Nenhum curso itinerante encontrado."
      createPath="/ensino/cursoitinerante/novo"
      editPathBuilder={(cursoId) => `/ensino/cursoitinerante/${cursoId}/editar`}
      moodleSyncConfig={{
        tipoCurso: 'itinerante',
        tipoCursoLabel: 'Qualificacao profissional itinerante',
        rootCategoryIds: [415],
        syncLabel: 'Sincronizar cursos itinerantes',
        successMessage: 'Cursos itinerantes sincronizados a partir do Moodle.',
        description: 'Busca todos os cursos sob a categoria Moodle 415, incluindo subcategorias descendentes, persiste no banco local do SUAP e atualiza esta listagem.',
      }}
    />
  )
}