import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { Eye, Pencil, Plus, Trash2 } from 'lucide-react'

import { frequenciasApi } from '@/api/endpoints'
import DataTable from '@/components/ui/DataTable'
import EntityDetailsPanel from '@/components/ui/EntityDetailsPanel'

function formatDate(value) {
  if (!value) {
    return '-'
  }

  return new Date(`${value}T00:00:00`).toLocaleDateString('pt-BR')
}

const PRESENCA_BADGE = {
  Presente: 'badge--success',
  Falta: 'badge--danger',
}

const COLUMNS = [
  { key: 'numero_matricula', label: 'Matricula' },
  { key: 'aluno_nome', label: 'Aluno' },
  { key: 'curso_nome', label: 'Curso' },
  {
    key: 'data',
    label: 'Data',
    render: (row) => formatDate(row.data),
  },
  {
    key: 'presente_label',
    label: 'Presenca',
    render: (row) => (
      <span className={`badge ${PRESENCA_BADGE[row.presente_label] || ''}`}>
        {row.presente_label}
      </span>
    ),
  },
  { key: 'observacao', label: 'Observacao' },
]

export default function FrequenciaPage() {
  const navigate = useNavigate()
  const [search, setSearch] = useState('')
  const [page, setPage] = useState(1)
  const [selectedFrequenciaId, setSelectedFrequenciaId] = useState(null)

  const openPlaceholder = (slug, title, description) => {
    navigate(`/indisponivel/${slug}`, {
      state: { title, description },
    })
  }

  const { data, isLoading, isError } = useQuery({
    queryKey: ['frequencias', { search, page }],
    queryFn: () => frequenciasApi.list({ search, page }).then((response) => response.data),
    staleTime: 30_000,
  })

  const { data: selectedFrequencia, isLoading: isLoadingDetails, isError: isErrorDetails } = useQuery({
    queryKey: ['frequencia', selectedFrequenciaId],
    queryFn: () => frequenciasApi.get(selectedFrequenciaId).then((response) => response.data),
    enabled: Boolean(selectedFrequenciaId),
    staleTime: 30_000,
  })

  const detailsFields = selectedFrequencia
    ? [
        { label: 'ID', value: selectedFrequencia.id },
        { label: 'Matricula', value: selectedFrequencia.numero_matricula },
        { label: 'Aluno', value: selectedFrequencia.aluno_nome },
        { label: 'Curso', value: selectedFrequencia.curso_nome },
        { label: 'Turma', value: selectedFrequencia.turma_nome },
        { label: 'Data', value: formatDate(selectedFrequencia.data) },
        { label: 'Presenca', value: selectedFrequencia.presente_label },
        { label: 'Observacao', value: selectedFrequencia.observacao || '-' },
      ]
    : []

  return (
    <div className="page">
      <div className="page-header">
        <h1 className="page-title">Frequencia</h1>
        <div className="page-header__actions">
          <button
            className="btn btn--primary"
            onClick={() => openPlaceholder('nova-frequencia', 'Nova Frequencia', 'O formulario de lancamento de frequencia ainda nao foi portado para o frontend.')}
          >
            <Plus size={16} /> Nova Frequencia
          </button>
        </div>
      </div>

      {isError ? (
        <div className="alert alert--error">
          Nao foi possivel carregar os lancamentos de frequencia com as permissoes atuais.
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
        searchPlaceholder="Buscar frequencia, aluno ou matricula..."
        emptyMessage="Nenhum lancamento de frequencia encontrado."
        rowActions={(row) => (
          <div className="table-actions">
            <button type="button" className="btn btn--outline btn--sm" onClick={() => setSelectedFrequenciaId(row.id)}>
              <Eye size={14} /> Detalhes
            </button>
            <button
              type="button"
              className="btn btn--secondary btn--sm"
              onClick={() => openPlaceholder(`frequencia-${row.id}-editar`, 'Editar Frequencia', `A edicao do lancamento de frequencia de ${row.aluno_nome} ainda nao foi portada para o frontend.`)}
            >
              <Pencil size={14} /> Editar
            </button>
            <button
              type="button"
              className="btn btn--danger btn--sm"
              onClick={() => openPlaceholder(`frequencia-${row.id}-excluir`, 'Excluir Frequencia', `A exclusao do lancamento de frequencia de ${row.aluno_nome} ainda nao foi portada para o frontend.`)}
            >
              <Trash2 size={14} /> Excluir
            </button>
          </div>
        )}
      />

      {selectedFrequenciaId ? (
        <EntityDetailsPanel
          title="Detalhes da frequencia"
          subtitle={selectedFrequencia?.aluno_nome || 'Consultando frequencia selecionada'}
          fields={detailsFields}
          isLoading={isLoadingDetails}
          errorMessage={isErrorDetails ? 'Nao foi possivel carregar os detalhes desta frequencia.' : ''}
          onClose={() => setSelectedFrequenciaId(null)}
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