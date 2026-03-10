import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { Eye, Pencil, Plus, Trash2 } from 'lucide-react'

import { notasApi } from '@/api/endpoints'
import DataTable from '@/components/ui/DataTable'
import EntityDetailsPanel from '@/components/ui/EntityDetailsPanel'

function formatDate(value) {
  if (!value) {
    return '-'
  }

  return new Date(`${value}T00:00:00`).toLocaleDateString('pt-BR')
}

const COLUMNS = [
  { key: 'numero_matricula', label: 'Matricula' },
  { key: 'aluno_nome', label: 'Aluno' },
  { key: 'curso_nome', label: 'Curso' },
  { key: 'descricao', label: 'Avaliacao' },
  { key: 'valor', label: 'Nota' },
  { key: 'peso', label: 'Peso' },
  {
    key: 'data_lancamento',
    label: 'Lancamento',
    render: (row) => formatDate(row.data_lancamento),
  },
]

export default function NotasPage() {
  const navigate = useNavigate()
  const [search, setSearch] = useState('')
  const [page, setPage] = useState(1)
  const [selectedNotaId, setSelectedNotaId] = useState(null)

  const openPlaceholder = (slug, title, description) => {
    navigate(`/indisponivel/${slug}`, {
      state: { title, description },
    })
  }

  const { data, isLoading, isError } = useQuery({
    queryKey: ['notas', { search, page }],
    queryFn: () => notasApi.list({ search, page }).then((response) => response.data),
    staleTime: 30_000,
  })

  const { data: selectedNota, isLoading: isLoadingDetails, isError: isErrorDetails } = useQuery({
    queryKey: ['nota', selectedNotaId],
    queryFn: () => notasApi.get(selectedNotaId).then((response) => response.data),
    enabled: Boolean(selectedNotaId),
    staleTime: 30_000,
  })

  const detailsFields = selectedNota
    ? [
        { label: 'ID', value: selectedNota.id },
        { label: 'Matricula', value: selectedNota.numero_matricula },
        { label: 'Aluno', value: selectedNota.aluno_nome },
        { label: 'Curso', value: selectedNota.curso_nome },
        { label: 'Turma', value: selectedNota.turma_nome },
        { label: 'Avaliacao', value: selectedNota.descricao },
        { label: 'Nota', value: selectedNota.valor },
        { label: 'Peso', value: selectedNota.peso },
        { label: 'Data de lancamento', value: formatDate(selectedNota.data_lancamento) },
      ]
    : []

  return (
    <div className="page">
      <div className="page-header">
        <h1 className="page-title">Notas</h1>
        <div className="page-header__actions">
          <button
            className="btn btn--primary"
            onClick={() => openPlaceholder('nova-nota', 'Nova Nota', 'O formulario de lancamento de notas ainda nao foi portado para o frontend.')}
          >
            <Plus size={16} /> Nova Nota
          </button>
        </div>
      </div>

      {isError ? (
        <div className="alert alert--error">
          Nao foi possivel carregar as notas com as permissoes atuais.
        </div>
      ) : null}

      <DataTable
        columns={COLUMNS}
        data={data}
        isLoading={isLoading}
        onSearch={(value) => {
          setSearch(value)
          setPage(1)
        }}
        searchPlaceholder="Buscar nota, aluno ou matricula..."
        emptyMessage="Nenhuma nota encontrada."
        rowActions={(row) => (
          <div className="table-actions">
            <button type="button" className="btn btn--outline btn--sm" onClick={() => setSelectedNotaId(row.id)}>
              <Eye size={14} /> Detalhes
            </button>
            <button
              type="button"
              className="btn btn--secondary btn--sm"
              onClick={() => openPlaceholder(`nota-${row.id}-editar`, 'Editar Nota', `A edicao da nota ${row.descricao} ainda nao foi portada para o frontend.`)}
            >
              <Pencil size={14} /> Editar
            </button>
            <button
              type="button"
              className="btn btn--danger btn--sm"
              onClick={() => openPlaceholder(`nota-${row.id}-excluir`, 'Excluir Nota', `A exclusao da nota ${row.descricao} ainda nao foi portada para o frontend.`)}
            >
              <Trash2 size={14} /> Excluir
            </button>
          </div>
        )}
      />

      {selectedNotaId ? (
        <EntityDetailsPanel
          title="Detalhes da nota"
          subtitle={selectedNota?.descricao || 'Consultando nota selecionada'}
          fields={detailsFields}
          isLoading={isLoadingDetails}
          errorMessage={isErrorDetails ? 'Nao foi possivel carregar os detalhes desta nota.' : ''}
          onClose={() => setSelectedNotaId(null)}
        />
      ) : null}

      {data ? (
        <div className="pagination">
          <button className="btn btn--secondary" disabled={!data.previous} onClick={() => setPage((current) => current - 1)}>Anterior</button>
          <span className="pagination__info">Pagina {page} — {data.count} registros</span>
          <button className="btn btn--secondary" disabled={!data.next} onClick={() => setPage((current) => current + 1)}>Proxima</button>
        </div>
      ) : null}
    </div>
  )
}