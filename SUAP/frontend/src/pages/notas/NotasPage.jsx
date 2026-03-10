import { useEffect, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Eye, Pencil, Plus, Trash2 } from 'lucide-react'
import toast from 'react-hot-toast'

import { matriculasApi, notasApi } from '@/api/endpoints'
import DataTable from '@/components/ui/DataTable'
import EntityDetailsPanel from '@/components/ui/EntityDetailsPanel'
import EntityFormPanel from '@/components/ui/EntityFormPanel'
import SearchableRemoteSelect from '@/components/ui/SearchableRemoteSelect'

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
  const queryClient = useQueryClient()
  const [search, setSearch] = useState('')
  const [page, setPage] = useState(1)
  const [selectedNotaId, setSelectedNotaId] = useState(null)
  const [editingNotaId, setEditingNotaId] = useState(null)
  const [isCreating, setIsCreating] = useState(false)
  const [matriculaSearch, setMatriculaSearch] = useState('')
  const [formData, setFormData] = useState({
    matricula: '',
    descricao: '',
    valor: '',
    peso: '1.00',
    data_lancamento: '',
  })

  function getErrorMessage(error, fallback) {
    const data = error?.response?.data
    if (!data) return fallback
    if (typeof data.detail === 'string') return data.detail
    const firstValue = Object.values(data)[0]
    return Array.isArray(firstValue) ? firstValue[0] : (firstValue || fallback)
  }

  const { data, isLoading, isError } = useQuery({
    queryKey: ['notas', { search, page }],
    queryFn: () => notasApi.list({ search, page }).then((response) => response.data),
    staleTime: 30_000,
  })

  const { data: matriculasData } = useQuery({
    queryKey: ['matriculas', 'notas-options', matriculaSearch],
    queryFn: () => matriculasApi.list({ page_size: 10, search: matriculaSearch || undefined }).then((response) => response.data),
    staleTime: 60_000,
  })

  const { data: selectedNota, isLoading: isLoadingDetails, isError: isErrorDetails } = useQuery({
    queryKey: ['nota', selectedNotaId],
    queryFn: () => notasApi.get(selectedNotaId).then((response) => response.data),
    enabled: Boolean(selectedNotaId),
    staleTime: 30_000,
  })

  const { data: editingNota } = useQuery({
    queryKey: ['nota-edit', editingNotaId],
    queryFn: () => notasApi.get(editingNotaId).then((response) => response.data),
    enabled: Boolean(editingNotaId),
    staleTime: 0,
  })

  useEffect(() => {
    if (!editingNota) return
    setFormData({
      matricula: editingNota.matricula ? String(editingNota.matricula) : '',
      descricao: editingNota.descricao || '',
      valor: editingNota.valor ? String(editingNota.valor) : '',
      peso: editingNota.peso ? String(editingNota.peso) : '1.00',
      data_lancamento: editingNota.data_lancamento || '',
    })
  }, [editingNota])

  const saveMutation = useMutation({
    mutationFn: ({ id, payload }) => (id ? notasApi.update(id, payload) : notasApi.create(payload)),
    onSuccess: (_response, variables) => {
      queryClient.invalidateQueries({ queryKey: ['notas'] })
      if (variables.id) {
        queryClient.invalidateQueries({ queryKey: ['nota', variables.id] })
      }
      setEditingNotaId(null)
      setIsCreating(false)
      setFormData({ matricula: '', descricao: '', valor: '', peso: '1.00', data_lancamento: '' })
      toast.success(variables.id ? 'Nota atualizada com sucesso.' : 'Nota criada com sucesso.')
    },
    onError: (error) => toast.error(getErrorMessage(error, 'Nao foi possivel salvar a nota.')),
  })

  const deleteMutation = useMutation({
    mutationFn: (id) => notasApi.remove(id),
    onSuccess: (_response, id) => {
      queryClient.invalidateQueries({ queryKey: ['notas'] })
      queryClient.invalidateQueries({ queryKey: ['nota', id] })
      setSelectedNotaId((current) => (current === id ? null : current))
      setEditingNotaId((current) => (current === id ? null : current))
      setIsCreating(false)
      toast.success('Nota excluida com sucesso.')
    },
    onError: (error) => toast.error(getErrorMessage(error, 'Nao foi possivel excluir a nota.')),
  })

  const matriculas = matriculasData?.results || []
  const selectedMatriculaOption = formData.matricula && editingNota ? {
    id: editingNota.matricula,
    numero_matricula: editingNota.numero_matricula,
    aluno_nome: editingNota.aluno_nome,
  } : null

  const openCreateForm = () => {
    setSelectedNotaId(null)
    setEditingNotaId(null)
    setIsCreating(true)
    setFormData({ matricula: '', descricao: '', valor: '', peso: '1.00', data_lancamento: '' })
  }

  const openEditForm = (id) => {
    setSelectedNotaId(null)
    setIsCreating(false)
    setEditingNotaId(id)
  }

  const closeForm = () => {
    setEditingNotaId(null)
    setIsCreating(false)
    setFormData({ matricula: '', descricao: '', valor: '', peso: '1.00', data_lancamento: '' })
  }

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
          <button type="button" className="btn btn--primary" onClick={openCreateForm}>
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
            <button type="button" className="btn btn--secondary btn--sm" onClick={() => openEditForm(row.id)}>
              <Pencil size={14} /> Editar
            </button>
            <button type="button" className="btn btn--danger btn--sm" onClick={() => window.confirm(`Excluir a nota ${row.descricao}?`) && deleteMutation.mutate(row.id)}>
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

      {(isCreating || editingNotaId) ? (
        <EntityFormPanel
          title={editingNotaId ? 'Editar nota' : 'Nova nota'}
          subtitle="Lance uma avaliacao vinculada a matricula do aluno."
          onSubmit={(event) => {
            event.preventDefault()
            saveMutation.mutate({
              id: editingNotaId,
              payload: {
                matricula: Number(formData.matricula),
                descricao: formData.descricao,
                valor: formData.valor,
                peso: formData.peso,
                data_lancamento: formData.data_lancamento,
              },
            })
          }}
          onCancel={closeForm}
          submitLabel={editingNotaId ? 'Salvar alteracoes' : 'Criar nota'}
          isSubmitting={saveMutation.isPending}
        >
          <SearchableRemoteSelect
            id="nota-matricula"
            label="Matricula"
            searchLabel="Buscar matricula"
            searchPlaceholder="Digite matricula ou aluno"
            searchValue={matriculaSearch}
            onSearchChange={setMatriculaSearch}
            value={formData.matricula}
            onChange={(nextValue) => setFormData((current) => ({ ...current, matricula: nextValue }))}
            options={matriculas}
            selectedOption={selectedMatriculaOption}
            getOptionLabel={(item) => `${item.numero_matricula} - ${item.aluno_nome}`}
          />
          <div className="form-field form-field--full">
            <label>Avaliacao</label>
            <input type="text" value={formData.descricao} onChange={(event) => setFormData((current) => ({ ...current, descricao: event.target.value }))} />
          </div>
          <div className="form-field">
            <label>Nota</label>
            <input type="number" step="0.01" min="0" value={formData.valor} onChange={(event) => setFormData((current) => ({ ...current, valor: event.target.value }))} />
          </div>
          <div className="form-field">
            <label>Peso</label>
            <input type="number" step="0.01" min="0" value={formData.peso} onChange={(event) => setFormData((current) => ({ ...current, peso: event.target.value }))} />
          </div>
          <div className="form-field">
            <label>Data de lancamento</label>
            <input type="date" value={formData.data_lancamento} onChange={(event) => setFormData((current) => ({ ...current, data_lancamento: event.target.value }))} />
          </div>
        </EntityFormPanel>
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