import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import { useNavigate } from 'react-router-dom'
import { cursosApi } from '@/api/endpoints'
import DataTable from '@/components/ui/DataTable'
import EntityDetailsPanel from '@/components/ui/EntityDetailsPanel'
import { Eye, Pencil, Plus, Trash2 } from 'lucide-react'
import { Link } from 'react-router-dom'

const COLUMNS = [
  { key: 'nome',        label: 'Curso' },
  { key: 'sigla',       label: 'Sigla' },
  { key: 'unidade_nome',label: 'Unidade' },
  { key: 'area_curso_nome', label: 'Área do Curso' },
  { key: 'eixo_tecnologico', label: 'Eixo Tecnológico' },
  { key: 'carga_horaria', label: 'Carga Horária (h)' },
]

export default function CursosPage({
  title = 'Cursos',
  subtitle = '',
  breadcrumbs = null,
  queryScope = 'geral',
  listParams = {},
  searchPlaceholder = 'Buscar curso...',
  emptyMessage = 'Nenhum curso encontrado.',
  createPath = null,
  editPathBuilder = null,
  extraHeaderActions = null,
}) {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [search, setSearch] = useState('')
  const [page, setPage] = useState(1)
  const [selectedCourseId, setSelectedCourseId] = useState(null)

  const deleteMutation = useMutation({
    mutationFn: (cursoId) => cursosApi.remove(cursoId),
    onSuccess: async (_, cursoId) => {
      if (selectedCourseId === cursoId) {
        setSelectedCourseId(null)
      }
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ['cursos'] }),
        queryClient.invalidateQueries({ queryKey: ['curso'] }),
      ])
      toast.success('Curso removido com sucesso.')
    },
    onError: (error) => {
      const detail = error?.response?.data?.detail
      toast.error(detail || 'Não foi possível remover o curso.')
    },
  })

  const handleDelete = (row) => {
    if (!window.confirm(`Deseja realmente remover o curso ${row.nome}?`)) {
      return
    }
    deleteMutation.mutate(row.id)
  }

  const { data, isLoading, isError } = useQuery({
    queryKey: ['cursos', queryScope, { ...listParams, search, page }],
    queryFn: () => cursosApi.list({ ...listParams, search, page }).then((r) => r.data),
    staleTime: 30_000,
  })

  const { data: selectedCourse, isLoading: isLoadingDetails, isError: isErrorDetails } = useQuery({
    queryKey: ['curso', selectedCourseId],
    queryFn: () => cursosApi.get(selectedCourseId).then((response) => response.data),
    enabled: Boolean(selectedCourseId),
    staleTime: 30_000,
  })

  const detailsFields = selectedCourse
    ? [
        { label: 'ID', value: selectedCourse.id },
        { label: 'Curso', value: selectedCourse.nome },
        { label: 'Sigla', value: selectedCourse.sigla },
        { label: 'Unidade', value: selectedCourse.unidade_nome },
        { label: 'Área do Curso', value: selectedCourse.area_curso_nome },
        { label: 'Eixo Tecnologico', value: selectedCourse.eixo_tecnologico },
        { label: 'Carga Horaria', value: selectedCourse.carga_horaria ? `${selectedCourse.carga_horaria}h` : null },
      ]
    : []

  return (
    <div className="page">
      {breadcrumbs ? (
        <nav className="profile-breadcrumb">
          {breadcrumbs.map((item, index) => (
            <span key={`${item.label}-${index}`}>
              {index > 0 ? <span className="profile-breadcrumb__sep">&gt;</span> : null}
              {item.to ? <Link to={item.to}>{item.label}</Link> : <span>{item.label}</span>}
            </span>
          ))}
        </nav>
      ) : null}

      <div className="page-header">
        <div>
          <h1 className="page-title">{title}</h1>
          {subtitle ? <p className="page-subtitle">{subtitle}</p> : null}
        </div>
        <div className="page-header__actions">
          {extraHeaderActions}
          <button
            className="btn btn--primary"
            onClick={() => (createPath ? navigate(createPath) : null)}
            disabled={!createPath}
          >
            <Plus size={16} /> Novo Curso
          </button>
        </div>
      </div>

      {isError ? (
        <div className="alert alert--error">
          Nao foi possivel carregar os cursos com as permissoes atuais.
        </div>
      ) : null}

      <DataTable
        columns={COLUMNS}
        data={data}
        isLoading={isLoading}
        onSearch={(v) => { setSearch(v); setPage(1) }}
        searchPlaceholder={searchPlaceholder}
        emptyMessage={emptyMessage}
        rowActions={(row) => (
          <div className="table-actions">
            <button type="button" className="btn btn--outline btn--sm" onClick={() => setSelectedCourseId(row.id)}>
              <Eye size={14} /> Detalhes
            </button>
            <button
              type="button"
              className="btn btn--secondary btn--sm"
              onClick={() => (editPathBuilder ? navigate(editPathBuilder(row.id)) : null)}
              disabled={!editPathBuilder}
            >
              <Pencil size={14} /> Editar
            </button>
            <button
              type="button"
              className="btn btn--danger btn--sm"
              onClick={() => handleDelete(row)}
              disabled={deleteMutation.isPending}
            >
              <Trash2 size={14} /> Excluir
            </button>
          </div>
        )}
      />

      {selectedCourseId ? (
        <EntityDetailsPanel
          title="Detalhes do curso"
          subtitle={selectedCourse?.nome || 'Consultando curso selecionado'}
          fields={detailsFields}
          isLoading={isLoadingDetails}
          errorMessage={isErrorDetails ? 'Nao foi possivel carregar os detalhes deste curso.' : ''}
          onClose={() => setSelectedCourseId(null)}
        />
      ) : null}

      {data && (
        <div className="pagination">
          <button className="btn btn--secondary" disabled={!data.previous} onClick={() => setPage((p) => p - 1)}>Anterior</button>
          <span className="pagination__info">Página {page} — {data.count} registros</span>
          <button className="btn btn--secondary" disabled={!data.next} onClick={() => setPage((p) => p + 1)}>Próxima</button>
        </div>
      )}
    </div>
  )
}
