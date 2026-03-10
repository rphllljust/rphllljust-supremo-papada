/**
 * Hooks reutilizáveis para React Query + endpoints da API.
 */
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'

/**
 * Hook genérico para listagens com paginação/busca.
 * @param {string} queryKey - chave do React Query
 * @param {function} apiFn - função que recebe params e retorna Promise
 * @param {object} params - parâmetros de filtro/busca/paginação
 * @param {object} options - opções extras do useQuery
 */
export function useList(queryKey, apiFn, params = {}, options = {}) {
  return useQuery({
    queryKey: [queryKey, params],
    queryFn: () => apiFn(params).then((r) => r.data),
    staleTime: 30_000,
    ...options,
  })
}

/**
 * Hook genérico para buscar um único item.
 */
export function useDetail(queryKey, apiFn, id, options = {}) {
  return useQuery({
    queryKey: [queryKey, id],
    queryFn: () => apiFn(id).then((r) => r.data),
    enabled: Boolean(id),
    staleTime: 30_000,
    ...options,
  })
}

/**
 * Hook genérico para mutations (create/update/delete).
 * Invalida automaticamente o queryKey após sucesso.
 */
export function useCrudMutation(queryKey, mutationFn, { successMessage, errorMessage } = {}) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [queryKey] })
      if (successMessage) toast.success(successMessage)
    },
    onError: (error) => {
      const msg = error.response?.data?.detail
        || Object.values(error.response?.data || {})[0]
        || errorMessage
        || 'Ocorreu um erro.'
      toast.error(Array.isArray(msg) ? msg[0] : msg)
    },
  })
}

/**
 * Hook para paginação simples (page number).
 */
export function usePagination(initialPage = 1) {
  const [page, setPage] = useState(initialPage)
  const [search, setSearch] = useState('')

  const nextPage = () => setPage((p) => p + 1)
  const prevPage = () => setPage((p) => Math.max(1, p - 1))
  const goToPage = (n) => setPage(n)
  const resetPage = () => setPage(1)

  return { page, search, setSearch, nextPage, prevPage, goToPage, resetPage }
}
