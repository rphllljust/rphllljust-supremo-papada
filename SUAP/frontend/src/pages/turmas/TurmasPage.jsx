import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { turmasApi } from '@/api/endpoints'
import DataTable from '@/components/ui/DataTable'
import EntityDetailsPanel from '@/components/ui/EntityDetailsPanel'
import { Eye, Pencil, Plus, Trash2 } from 'lucide-react'

const STATUS_BADGE = {
  PLANEJADA: 'badge--info',
  ATIVA:     'badge--success',
  ENCERRADA: 'badge--secondary',
  CANCELADA: 'badge--danger',
}

const COLUMNS = [
  { key: 'nome',           label: 'Turma' },
  { key: 'curso_nome',     label: 'Curso' },
  { key: 'ano_letivo',     label: 'Ano Letivo' },
  { key: 'professor_nome', label: 'Professor' },
  {
    key: 'status',
    label: 'Status',
    render: (row) => (
      <span className={`badge ${STATUS_BADGE[row.status] || ''}`}>
        {row.status_display || row.status}
      </span>
    ),
  },
]

export default function TurmasPage() {
  const navigate = useNavigate()
  const [search, setSearch] = useState('')
  const [page, setPage] = useState(1)
  const [selectedTurmaId, setSelectedTurmaId] = useState(null)

  const openPlaceholder = (slug, title, description) => {
    navigate(`/indisponivel/${slug}`, {
      state: { title, description },
    })
  }

  const { data, isLoading, isError } = useQuery({
    queryKey: ['turmas', { search, page }],
    queryFn: () => turmasApi.list({ search, page }).then((r) => r.data),
    staleTime: 30_000,
  })

  const { data: selectedTurma, isLoading: isLoadingDetails, isError: isErrorDetails } = useQuery({
    queryKey: ['turma', selectedTurmaId],
    queryFn: () => turmasApi.get(selectedTurmaId).then((response) => response.data),
    enabled: Boolean(selectedTurmaId),
    staleTime: 30_000,
  })

  const turmaDetailsFields = selectedTurma
    ? [
        { label: 'ID', value: selectedTurma.id },
        { label: 'Turma', value: selectedTurma.nome },
        { label: 'Curso', value: selectedTurma.curso_nome },
        { label: 'Ano Letivo', value: selectedTurma.ano_letivo },
        { label: 'Professor', value: selectedTurma.professor_nome },
        { label: 'Status', value: selectedTurma.status_display || selectedTurma.status },
      ]
    : []

  return (
    <div className="page">
      <div className="page-header">
        <h1 className="page-title">Turmas</h1>
        <div className="page-header__actions">
          <button
            className="btn btn--primary"
            onClick={() => openPlaceholder('nova-turma', 'Nova Turma', 'O formulario de criacao de turmas ainda nao foi portado para o frontend.')}
          >
            <Plus size={16} /> Nova Turma
          </button>
        </div>
      </div>

      {isError ? (
        <div className="alert alert--error">
          Nao foi possivel carregar as turmas com as permissoes atuais.
        </div>
      ) : null}

      <DataTable
        columns={COLUMNS}
        data={data}
        isLoading={isLoading}
        onSearch={(v) => { setSearch(v); setPage(1) }}
        searchPlaceholder="Buscar turma..."
        emptyMessage="Nenhuma turma encontrada."
        rowActions={(row) => (
          <div className="table-actions">
            <button type="button" className="btn btn--outline btn--sm" onClick={() => setSelectedTurmaId(row.id)}>
              <Eye size={14} /> Detalhes
            </button>
            <button
              type="button"
              className="btn btn--secondary btn--sm"
              onClick={() => openPlaceholder(`turma-${row.id}-editar`, 'Editar Turma', `A edicao da turma ${row.nome} ainda nao foi portada para o frontend.`)}
            >
              <Pencil size={14} /> Editar
            </button>
            <button
              type="button"
              className="btn btn--danger btn--sm"
              onClick={() => openPlaceholder(`turma-${row.id}-excluir`, 'Excluir Turma', `A exclusao da turma ${row.nome} ainda nao foi portada para o frontend.`)}
            >
              <Trash2 size={14} /> Excluir
            </button>
          </div>
        )}
      />

      {selectedTurmaId ? (
        <EntityDetailsPanel
          title="Detalhes da turma"
          subtitle={selectedTurma?.nome || 'Consultando turma selecionada'}
          fields={turmaDetailsFields}
          isLoading={isLoadingDetails}
          errorMessage={isErrorDetails ? 'Nao foi possivel carregar os detalhes desta turma.' : ''}
          onClose={() => setSelectedTurmaId(null)}
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
