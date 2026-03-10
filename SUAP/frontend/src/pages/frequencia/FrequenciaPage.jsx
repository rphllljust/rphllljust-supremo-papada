import { useEffect, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Eye, Pencil, Plus, Trash2 } from 'lucide-react'
import toast from 'react-hot-toast'

import { frequenciasApi, matriculasApi } from '@/api/endpoints'
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
  const queryClient = useQueryClient()
  const [search, setSearch] = useState('')
  const [page, setPage] = useState(1)
  const [selectedFrequenciaId, setSelectedFrequenciaId] = useState(null)
  const [presencaFiltro, setPresencaFiltro] = useState('')
  const [editingFrequenciaId, setEditingFrequenciaId] = useState(null)
  const [isCreating, setIsCreating] = useState(false)
  const [matriculaSearch, setMatriculaSearch] = useState('')
  const [formData, setFormData] = useState({
    matricula: '',
    data: '',
    presente: 'true',
    observacao: '',
  })

  function getErrorMessage(error, fallback) {
    const data = error?.response?.data
    if (!data) return fallback
    if (typeof data.detail === 'string') return data.detail
    const firstValue = Object.values(data)[0]
    return Array.isArray(firstValue) ? firstValue[0] : (firstValue || fallback)
  }

  const { data, isLoading, isError } = useQuery({
    queryKey: ['frequencias', { search, page, presente: presencaFiltro }],
    queryFn: () => frequenciasApi.list({ search, page, presente: presencaFiltro || undefined }).then((response) => response.data),
    staleTime: 30_000,
  })

  const { data: matriculasData } = useQuery({
    queryKey: ['matriculas', 'frequencias-options', matriculaSearch],
    queryFn: () => matriculasApi.list({ page_size: 10, search: matriculaSearch || undefined }).then((response) => response.data),
    staleTime: 60_000,
  })

  const { data: selectedFrequencia, isLoading: isLoadingDetails, isError: isErrorDetails } = useQuery({
    queryKey: ['frequencia', selectedFrequenciaId],
    queryFn: () => frequenciasApi.get(selectedFrequenciaId).then((response) => response.data),
    enabled: Boolean(selectedFrequenciaId),
    staleTime: 30_000,
  })

  const { data: editingFrequencia } = useQuery({
    queryKey: ['frequencia-edit', editingFrequenciaId],
    queryFn: () => frequenciasApi.get(editingFrequenciaId).then((response) => response.data),
    enabled: Boolean(editingFrequenciaId),
    staleTime: 0,
  })

  useEffect(() => {
    if (!editingFrequencia) return
    setFormData({
      matricula: editingFrequencia.matricula ? String(editingFrequencia.matricula) : '',
      data: editingFrequencia.data || '',
      presente: editingFrequencia.presente ? 'true' : 'false',
      observacao: editingFrequencia.observacao || '',
    })
  }, [editingFrequencia])

  const saveMutation = useMutation({
    mutationFn: ({ id, payload }) => (id ? frequenciasApi.update(id, payload) : frequenciasApi.create(payload)),
    onSuccess: (_response, variables) => {
      queryClient.invalidateQueries({ queryKey: ['frequencias'] })
      if (variables.id) {
        queryClient.invalidateQueries({ queryKey: ['frequencia', variables.id] })
      }
      setEditingFrequenciaId(null)
      setIsCreating(false)
      setFormData({ matricula: '', data: '', presente: 'true', observacao: '' })
      toast.success(variables.id ? 'Frequencia atualizada com sucesso.' : 'Frequencia criada com sucesso.')
    },
    onError: (error) => toast.error(getErrorMessage(error, 'Nao foi possivel salvar a frequencia.')),
  })

  const deleteMutation = useMutation({
    mutationFn: (id) => frequenciasApi.remove(id),
    onSuccess: (_response, id) => {
      queryClient.invalidateQueries({ queryKey: ['frequencias'] })
      queryClient.invalidateQueries({ queryKey: ['frequencia', id] })
      setSelectedFrequenciaId((current) => (current === id ? null : current))
      setEditingFrequenciaId((current) => (current === id ? null : current))
      setIsCreating(false)
      toast.success('Frequencia excluida com sucesso.')
    },
    onError: (error) => toast.error(getErrorMessage(error, 'Nao foi possivel excluir a frequencia.')),
  })

  const matriculas = matriculasData?.results || []
  const selectedMatriculaOption = formData.matricula && editingFrequencia ? {
    id: editingFrequencia.matricula,
    numero_matricula: editingFrequencia.numero_matricula,
    aluno_nome: editingFrequencia.aluno_nome,
  } : null

  const openCreateForm = () => {
    setSelectedFrequenciaId(null)
    setEditingFrequenciaId(null)
    setIsCreating(true)
    setFormData({ matricula: '', data: '', presente: 'true', observacao: '' })
  }

  const openEditForm = (id) => {
    setSelectedFrequenciaId(null)
    setIsCreating(false)
    setEditingFrequenciaId(id)
  }

  const closeForm = () => {
    setEditingFrequenciaId(null)
    setIsCreating(false)
    setFormData({ matricula: '', data: '', presente: 'true', observacao: '' })
  }

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
          <select className="select" value={presencaFiltro} onChange={(event) => { setPresencaFiltro(event.target.value); setPage(1) }}>
            <option value="">Todas as presencas</option>
            <option value="true">Presentes</option>
            <option value="false">Faltas</option>
          </select>
          <button type="button" className="btn btn--primary" onClick={openCreateForm}>
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
            <button type="button" className="btn btn--secondary btn--sm" onClick={() => openEditForm(row.id)}>
              <Pencil size={14} /> Editar
            </button>
            <button type="button" className="btn btn--danger btn--sm" onClick={() => window.confirm(`Excluir o lancamento de frequencia de ${row.aluno_nome}?`) && deleteMutation.mutate(row.id)}>
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

      {(isCreating || editingFrequenciaId) ? (
        <EntityFormPanel
          title={editingFrequenciaId ? 'Editar frequencia' : 'Nova frequencia'}
          subtitle="Lance presenca ou falta por matricula e data."
          onSubmit={(event) => {
            event.preventDefault()
            saveMutation.mutate({
              id: editingFrequenciaId,
              payload: {
                matricula: Number(formData.matricula),
                data: formData.data,
                presente: formData.presente === 'true',
                observacao: formData.observacao,
              },
            })
          }}
          onCancel={closeForm}
          submitLabel={editingFrequenciaId ? 'Salvar alteracoes' : 'Criar frequencia'}
          isSubmitting={saveMutation.isPending}
        >
          <SearchableRemoteSelect
            id="frequencia-matricula"
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
          <div className="form-field">
            <label>Data</label>
            <input type="date" value={formData.data} onChange={(event) => setFormData((current) => ({ ...current, data: event.target.value }))} />
          </div>
          <div className="form-field">
            <label>Presenca</label>
            <select className="select" value={formData.presente} onChange={(event) => setFormData((current) => ({ ...current, presente: event.target.value }))}>
              <option value="true">Presente</option>
              <option value="false">Falta</option>
            </select>
          </div>
          <div className="form-field form-field--full">
            <label>Observacao</label>
            <textarea rows="3" value={formData.observacao} onChange={(event) => setFormData((current) => ({ ...current, observacao: event.target.value }))} />
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