import { useEffect, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useNavigate, useSearchParams } from 'react-router-dom'
import toast from 'react-hot-toast'
import { Eye, Pencil, Plus, Trash2 } from 'lucide-react'

import { atasProfessoresApi } from '@/api/endpoints'
import DataTable from '@/components/ui/DataTable'
import EntityDetailsPanel from '@/components/ui/EntityDetailsPanel'

function formatDate(value) {
  if (!value) {
    return '-'
  }

  return new Date(`${value}T00:00:00`).toLocaleDateString('pt-BR')
}

const SITUACAO_BADGE = {
  Rascunho: 'badge--secondary',
  Emitido: 'badge--success',
}

const COLUMNS = [
  { key: 'numero_ata', label: 'Ata' },
  { key: 'assunto', label: 'Assunto' },
  {
    key: 'tipo_reuniao_label',
    label: 'Tipo de reuniao',
  },
  {
    key: 'data_reuniao',
    label: 'Data da reuniao',
    render: (row) => formatDate(row.data_reuniao),
  },
  {
    key: 'situacao_label',
    label: 'Situacao',
    render: (row) => (
      <span className={`badge ${SITUACAO_BADGE[row.situacao_label] || ''}`}>
        {row.situacao_label}
      </span>
    ),
  },
  { key: 'numero_protocolo', label: 'Protocolo' },
]

export default function AtaProfessoresPage() {
  const queryClient = useQueryClient()
  const navigate = useNavigate()
  const [searchParams, setSearchParams] = useSearchParams()
  const [search, setSearch] = useState('')
  const [page, setPage] = useState(1)
  const [selectedAtaId, setSelectedAtaId] = useState(searchParams.get('ata'))

  useEffect(() => {
    setSelectedAtaId(searchParams.get('ata'))
  }, [searchParams])

  const { data, isLoading, isError } = useQuery({
    queryKey: ['atas-professores', { search, page }],
    queryFn: () => atasProfessoresApi.list({ search, page }).then((response) => response.data),
    staleTime: 30_000,
  })

  const { data: selectedAta, isLoading: isLoadingDetails, isError: isErrorDetails } = useQuery({
    queryKey: ['ata-professores', selectedAtaId],
    queryFn: () => atasProfessoresApi.get(selectedAtaId).then((response) => response.data),
    enabled: Boolean(selectedAtaId),
    staleTime: 30_000,
  })

  const deleteMutation = useMutation({
    mutationFn: (id) => atasProfessoresApi.remove(id),
    onSuccess: (_response, id) => {
      queryClient.invalidateQueries({ queryKey: ['atas-professores'] })
      queryClient.invalidateQueries({ queryKey: ['ata-professores', id] })
      if (String(selectedAtaId) === String(id)) {
        setSelectedAtaId(null)
        setSearchParams({})
      }
      toast.success('Ata excluida com sucesso.')
    },
    onError: (error) => {
      const message = error.response?.data?.detail || 'Nao foi possivel excluir a ata.'
      toast.error(message)
    },
  })

  const detailsFields = selectedAta
    ? [
        { label: 'ID', value: selectedAta.id },
        { label: 'Numero da ata', value: selectedAta.numero_ata || '-' },
        { label: 'Protocolo', value: selectedAta.numero_protocolo },
        { label: 'Assunto', value: selectedAta.assunto },
        { label: 'Tipo de reuniao', value: selectedAta.tipo_reuniao_label },
        { label: 'Data da reuniao', value: formatDate(selectedAta.data_reuniao) },
        { label: 'Modalidade', value: selectedAta.modalidade_label || '-' },
        { label: 'Local', value: selectedAta.local_reuniao || '-' },
        { label: 'Presidente', value: selectedAta.presidente_reuniao || '-' },
        { label: 'Responsavel pela lavratura', value: selectedAta.responsavel_lavratura || '-' },
        { label: 'Situacao', value: selectedAta.situacao_label },
        { label: 'Emitido por', value: selectedAta.emitido_por_nome || '-' },
        { label: 'Processo vinculado', value: selectedAta.processo_numero || '-' },
        { label: 'Participantes registrados', value: selectedAta.participantes_count },
        { label: 'Observacao', value: selectedAta.observacao || '-' },
      ]
    : []

  return (
    <div className="page">
      <div className="page-header">
        <h1 className="page-title">Ata dos Professores</h1>
        <div className="page-header__actions">
          <button
            className="btn btn--primary"
            onClick={() => navigate('/ata-professores/nova')}
          >
            <Plus size={16} /> Nova Ata
          </button>
        </div>
      </div>

      {isError ? (
        <div className="alert alert--error">
          Nao foi possivel carregar as atas com as permissoes atuais.
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
        searchPlaceholder="Buscar ata, protocolo ou assunto..."
        emptyMessage="Nenhuma ata encontrada."
        rowActions={(row) => (
          <div className="table-actions">
            <button
              type="button"
              className="btn btn--outline btn--sm"
              onClick={() => {
                setSelectedAtaId(row.id)
                setSearchParams({ ata: String(row.id) })
              }}
            >
              <Eye size={14} /> Detalhes
            </button>
            <button
              type="button"
              className="btn btn--secondary btn--sm"
              onClick={() => navigate(`/ata-professores/${row.id}/editar`)}
            >
              <Pencil size={14} /> Editar
            </button>
            <button
              type="button"
              className="btn btn--danger btn--sm"
              onClick={() => {
                if (!window.confirm(`Deseja realmente excluir a ata ${row.numero_ata || row.numero_protocolo}?`)) {
                  return
                }
                deleteMutation.mutate(row.id)
              }}
            >
              <Trash2 size={14} /> Excluir
            </button>
          </div>
        )}
      />

      {selectedAtaId ? (
        <EntityDetailsPanel
          title="Detalhes da ata"
          subtitle={selectedAta?.assunto || 'Consultando ata selecionada'}
          fields={detailsFields}
          isLoading={isLoadingDetails}
          errorMessage={isErrorDetails ? 'Nao foi possivel carregar os detalhes desta ata.' : ''}
          onClose={() => {
            setSelectedAtaId(null)
            setSearchParams({})
          }}
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