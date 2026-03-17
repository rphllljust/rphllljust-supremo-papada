import { useMutation, useQueryClient } from '@tanstack/react-query'
import { RefreshCw } from 'lucide-react'
import toast from 'react-hot-toast'

import { moodleIntegrationApi } from '@/api/endpoints'

import CursosPage from './CursosPage'

const BREADCRUMBS = [
  { label: 'Inicio', to: '/dashboard' },
  { label: 'Ensino' },
  { label: 'Cadastros Gerais' },
  { label: 'Cursos iniciais' },
]

export default function CursosIniciaisPage() {
  const queryClient = useQueryClient()

  const syncCursosMutation = useMutation({
    mutationFn: () => moodleIntegrationApi.importCursos({ unidade_codigo: 'sede', integrar_catalogo_interno: true }),
    onSuccess: async (response) => {
      const summary = response.data?.summary || {}
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ['cursos'] }),
        queryClient.invalidateQueries({ queryKey: ['curso'] }),
      ])
      toast.success(
        `Atualizacao concluida. Criados: ${summary.created || 0}, atualizados: ${summary.updated || 0}, vinculados: ${summary.linked_existing || 0}.`
      )
    },
    onError: (error) => {
      const detail = error?.response?.data?.detail
      toast.error(detail || 'Nao foi possivel atualizar os cursos iniciais a partir do Moodle.')
    },
  })

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
      extraHeaderActions={(
        <button
          type="button"
          className="btn btn--secondary"
          onClick={() => syncCursosMutation.mutate()}
          disabled={syncCursosMutation.isPending}
        >
          <RefreshCw size={16} /> {syncCursosMutation.isPending ? 'Atualizando...' : 'Atualizar do Moodle'}
        </button>
      )}
    />
  )
}