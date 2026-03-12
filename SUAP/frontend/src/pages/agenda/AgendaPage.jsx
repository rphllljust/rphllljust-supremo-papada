import { useEffect, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Eye, Pencil, Plus, Trash2 } from 'lucide-react'
import toast from 'react-hot-toast'
import { useNavigate } from 'react-router-dom'

import { eventosApi, turmasApi } from '@/api/endpoints'
import DataTable from '@/components/ui/DataTable'
import EntityDetailsPanel from '@/components/ui/EntityDetailsPanel'
import EntityFormPanel from '@/components/ui/EntityFormPanel'
import SearchableRemoteSelect from '@/components/ui/SearchableRemoteSelect'

const COLUMNS = [
  { key: 'titulo',     label: 'Evento' },
  { key: 'turma_nome', label: 'Turma' },
  { key: 'curso_nome', label: 'Curso' },
  { key: 'inicio',     label: 'Início', render: (row) => formatDateTime(row.inicio) },
  { key: 'fim',        label: 'Fim',    render: (row) => formatDateTime(row.fim) },
]

const DEFAULT_FORM = {
  titulo: '',
  descricao: '',
  turma: '',
  inicio: '',
  fim: '',
}

function formatDateTime(value) {
  if (!value) return '-'
  return new Date(value).toLocaleString('pt-BR')
}

function toDateTimeLocal(value) {
  if (!value) return ''

  const date = new Date(value)
  const offset = date.getTimezoneOffset()
  const localDate = new Date(date.getTime() - offset * 60_000)
  return localDate.toISOString().slice(0, 16)
}

function getErrorMessage(error, fallback) {
  const data = error?.response?.data
  if (!data) return fallback
  if (typeof data.detail === 'string') return data.detail
  const firstValue = Object.values(data)[0]
  return Array.isArray(firstValue) ? firstValue[0] : (firstValue || fallback)
}

export default function AgendaPage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [search, setSearch] = useState('')
  const [page, setPage] = useState(1)
  const [selectedEventoId, setSelectedEventoId] = useState(null)
  const [editingEventoId, setEditingEventoId] = useState(null)
  const [formData, setFormData] = useState(DEFAULT_FORM)
  const [turmaSearch, setTurmaSearch] = useState('')

  const { data, isLoading, isError } = useQuery({
    queryKey: ['eventos', { search, page }],
    queryFn: () => eventosApi.list({ search, page }).then((r) => r.data),
    staleTime: 30_000,
  })

  const { data: turmasData } = useQuery({
    queryKey: ['turmas', 'agenda-options', turmaSearch],
    queryFn: () => turmasApi.list({ page_size: 10, search: turmaSearch || undefined }).then((response) => response.data),
    staleTime: 60_000,
  })

  const { data: selectedEvento, isLoading: isLoadingDetails, isError: isErrorDetails } = useQuery({
    queryKey: ['evento', selectedEventoId],
    queryFn: () => eventosApi.get(selectedEventoId).then((response) => response.data),
    enabled: Boolean(selectedEventoId),
    staleTime: 30_000,
  })

  const { data: editingEvento } = useQuery({
    queryKey: ['evento-edit', editingEventoId],
    queryFn: () => eventosApi.get(editingEventoId).then((response) => response.data),
    enabled: Boolean(editingEventoId),
    staleTime: 0,
  })

  useEffect(() => {
    if (!editingEvento) return

    setFormData({
      titulo: editingEvento.titulo || '',
      descricao: editingEvento.descricao || '',
      turma: editingEvento.turma ? String(editingEvento.turma) : '',
      inicio: toDateTimeLocal(editingEvento.inicio),
      fim: toDateTimeLocal(editingEvento.fim),
    })
  }, [editingEvento])

  const saveMutation = useMutation({
    mutationFn: ({ id, payload }) => (id ? eventosApi.patch(id, payload) : eventosApi.create(payload)),
    onSuccess: (_response, variables) => {
      queryClient.invalidateQueries({ queryKey: ['eventos'] })
      if (variables.id) {
        queryClient.invalidateQueries({ queryKey: ['evento', variables.id] })
      }
      toast.success(variables.id ? 'Evento atualizado com sucesso.' : 'Evento criado com sucesso.')
      setEditingEventoId(null)
      setFormData(DEFAULT_FORM)
    },
    onError: (error) => toast.error(getErrorMessage(error, 'Não foi possível salvar o evento.')),
  })

  const deleteMutation = useMutation({
    mutationFn: (id) => eventosApi.remove(id),
    onSuccess: (_response, id) => {
      queryClient.invalidateQueries({ queryKey: ['eventos'] })
      queryClient.invalidateQueries({ queryKey: ['evento', id] })
      setSelectedEventoId((current) => (current === id ? null : current))
      setEditingEventoId((current) => (current === id ? null : current))
      setFormData(DEFAULT_FORM)
      toast.success('Evento excluído com sucesso.')
    },
    onError: (error) => toast.error(getErrorMessage(error, 'Não foi possível excluir o evento.')),
  })

  const turmas = turmasData?.results || []

  const selectedTurmaOption = formData.turma && editingEvento ? {
    id: editingEvento.turma,
    nome: editingEvento.turma_nome,
    curso_nome: editingEvento.curso_nome,
  } : null

  const detailsFields = selectedEvento ? [
    { label: 'ID', value: selectedEvento.id },
    { label: 'Evento', value: selectedEvento.titulo },
    { label: 'Descrição', value: selectedEvento.descricao || '-' },
    { label: 'Turma', value: selectedEvento.turma_nome },
    { label: 'Curso', value: selectedEvento.curso_nome },
    { label: 'Professor', value: selectedEvento.professor_nome || '-' },
    { label: 'Início', value: formatDateTime(selectedEvento.inicio) },
    { label: 'Fim', value: formatDateTime(selectedEvento.fim) },
  ] : []

  return (
    <div className="page">
      <div className="page-header">
        <h1 className="page-title">Agenda</h1>
        <button type="button" className="btn btn--primary" onClick={() => navigate('/agenda/novo')}>
          <Plus size={16} /> Novo Evento
        </button>
      </div>

      {isError ? <div className="alert alert--error">Não foi possível carregar os eventos.</div> : null}

      <DataTable
        columns={COLUMNS}
        data={data}
        isLoading={isLoading}
        onSearch={(v) => { setSearch(v); setPage(1) }}
        searchPlaceholder="Buscar evento..."
        emptyMessage="Nenhum evento encontrado."
        rowActions={(row) => (
          <div className="table-actions">
            <button type="button" className="btn btn--outline btn--sm" onClick={() => setSelectedEventoId(row.id)}>
              <Eye size={14} /> Detalhes
            </button>
            <button type="button" className="btn btn--secondary btn--sm" onClick={() => { setSelectedEventoId(null); setEditingEventoId(row.id) }}>
              <Pencil size={14} /> Editar
            </button>
            <button type="button" className="btn btn--danger btn--sm" onClick={() => window.confirm(`Excluir o evento ${row.titulo}?`) && deleteMutation.mutate(row.id)}>
              <Trash2 size={14} /> Excluir
            </button>
          </div>
        )}
      />

      {selectedEventoId ? (
        <EntityDetailsPanel
          title="Detalhes do evento"
          subtitle={selectedEvento?.titulo || 'Consultando evento selecionado'}
          fields={detailsFields}
          isLoading={isLoadingDetails}
          errorMessage={isErrorDetails ? 'Não foi possível carregar os detalhes deste evento.' : ''}
          onClose={() => setSelectedEventoId(null)}
        />
      ) : null}

      {editingEventoId ? (
        <EntityFormPanel
          title="Editar evento"
          subtitle="Associe o evento a uma turma e defina período e descrição."
          onSubmit={(event) => {
            event.preventDefault()

            if (!formData.titulo.trim() || !formData.turma || !formData.inicio || !formData.fim) {
              toast.error('Informe título, turma, início e fim do evento.')
              return
            }

            saveMutation.mutate({
              id: editingEventoId,
              payload: {
                titulo: formData.titulo.trim(),
                descricao: formData.descricao.trim(),
                turma: Number(formData.turma),
                inicio: new Date(formData.inicio).toISOString(),
                fim: new Date(formData.fim).toISOString(),
              },
            })
          }}
          onCancel={() => { setEditingEventoId(null); setFormData(DEFAULT_FORM) }}
          submitLabel="Salvar alterações"
          isSubmitting={saveMutation.isPending}
        >
          <SearchableRemoteSelect
            id="agenda-turma"
            label="Turma"
            searchLabel="Buscar turma"
            searchPlaceholder="Digite nome da turma ou curso"
            searchValue={turmaSearch}
            onSearchChange={setTurmaSearch}
            value={formData.turma}
            onChange={(nextValue) => setFormData((current) => ({ ...current, turma: nextValue }))}
            options={turmas}
            selectedOption={selectedTurmaOption}
            getOptionLabel={(item) => `${item.nome} - ${item.curso_nome}`}
          />

          <div className="form-field form-field--full">
            <label htmlFor="agenda-titulo">Título</label>
            <input id="agenda-titulo" className="form-control" value={formData.titulo} onChange={(event) => setFormData((current) => ({ ...current, titulo: event.target.value }))} />
          </div>

          <div className="form-field">
            <label htmlFor="agenda-inicio">Início</label>
            <input id="agenda-inicio" type="datetime-local" className="form-control" value={formData.inicio} onChange={(event) => setFormData((current) => ({ ...current, inicio: event.target.value }))} />
          </div>

          <div className="form-field">
            <label htmlFor="agenda-fim">Fim</label>
            <input id="agenda-fim" type="datetime-local" className="form-control" value={formData.fim} onChange={(event) => setFormData((current) => ({ ...current, fim: event.target.value }))} />
          </div>

          <div className="form-field form-field--full">
            <label htmlFor="agenda-descricao">Descrição</label>
            <textarea id="agenda-descricao" className="form-control" rows={4} value={formData.descricao} onChange={(event) => setFormData((current) => ({ ...current, descricao: event.target.value }))} />
          </div>
        </EntityFormPanel>
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
