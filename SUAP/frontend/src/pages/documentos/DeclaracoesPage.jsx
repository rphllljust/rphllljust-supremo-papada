import { useEffect, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Eye, Pencil, Plus, Trash2 } from 'lucide-react'
import toast from 'react-hot-toast'

import { declaracoesApi, matriculasApi } from '@/api/endpoints'
import DataTable from '@/components/ui/DataTable'
import EntityDetailsPanel from '@/components/ui/EntityDetailsPanel'
import EntityFormPanel from '@/components/ui/EntityFormPanel'
import SearchableRemoteSelect from '@/components/ui/SearchableRemoteSelect'

const COLUMNS = [
  { key: 'numero_protocolo', label: 'Protocolo' },
  { key: 'tipo_display', label: 'Tipo' },
  { key: 'assunto', label: 'Assunto' },
  { key: 'matricula_numero', label: 'Matricula' },
  { key: 'aluno_nome', label: 'Aluno' },
  { key: 'data_emissao', label: 'Emissao' },
]

const TIPO_OPTIONS = [
  { value: 'MATRICULA', label: 'Declaracao de Matricula' },
  { value: 'FREQUENCIA', label: 'Declaracao de Frequencia' },
  { value: 'CONCLUSAO', label: 'Declaracao de Conclusao de Curso' },
]

const DEFAULT_FORM = { tipo: 'MATRICULA', assunto: '', matricula: '', observacao: '' }

function getErrorMessage(error, fallback) {
  const data = error?.response?.data
  if (!data) return fallback
  if (typeof data.detail === 'string') return data.detail
  const firstValue = Object.values(data)[0]
  return Array.isArray(firstValue) ? firstValue[0] : (firstValue || fallback)
}

export default function DeclaracoesPage() {
  const queryClient = useQueryClient()
  const [search, setSearch] = useState('')
  const [page, setPage] = useState(1)
  const [selectedId, setSelectedId] = useState(null)
  const [editingId, setEditingId] = useState(null)
  const [isCreating, setIsCreating] = useState(false)
  const [formData, setFormData] = useState(DEFAULT_FORM)
  const [matriculaSearch, setMatriculaSearch] = useState('')

  const { data, isLoading, isError } = useQuery({
    queryKey: ['declaracoes', { search, page }],
    queryFn: () => declaracoesApi.list({ search, page }).then((response) => response.data),
    staleTime: 30_000,
  })

  const { data: matriculasData } = useQuery({
    queryKey: ['matriculas', 'documento-options', matriculaSearch],
    queryFn: () => matriculasApi.list({ page_size: 10, search: matriculaSearch || undefined }).then((response) => response.data),
    staleTime: 60_000,
  })

  const { data: selectedItem, isLoading: isLoadingDetails, isError: isErrorDetails } = useQuery({
    queryKey: ['declaracao', selectedId],
    queryFn: () => declaracoesApi.get(selectedId).then((response) => response.data),
    enabled: Boolean(selectedId),
    staleTime: 30_000,
  })

  const { data: editingItem } = useQuery({
    queryKey: ['declaracao-edit', editingId],
    queryFn: () => declaracoesApi.get(editingId).then((response) => response.data),
    enabled: Boolean(editingId),
    staleTime: 0,
  })

  useEffect(() => {
    if (!editingItem) return
    setFormData({
      tipo: editingItem.tipo || 'MATRICULA',
      assunto: editingItem.assunto || '',
      matricula: editingItem.matricula ? String(editingItem.matricula) : '',
      observacao: editingItem.observacao || '',
    })
  }, [editingItem])

  const saveMutation = useMutation({
    mutationFn: ({ id, payload }) => (id ? declaracoesApi.update(id, payload) : declaracoesApi.create(payload)),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['declaracoes'] })
      toast.success(editingId ? 'Declaracao atualizada com sucesso.' : 'Declaracao emitida com sucesso.')
      setEditingId(null)
      setIsCreating(false)
      setFormData(DEFAULT_FORM)
    },
    onError: (error) => toast.error(getErrorMessage(error, 'Nao foi possivel salvar a declaracao.')),
  })

  const deleteMutation = useMutation({
    mutationFn: (id) => declaracoesApi.remove(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['declaracoes'] })
      setSelectedId(null)
      toast.success('Declaracao excluida com sucesso.')
    },
    onError: (error) => toast.error(getErrorMessage(error, 'Nao foi possivel excluir a declaracao.')),
  })

  const matriculas = matriculasData?.results || []
  const selectedMatriculaOption = formData.matricula && editingItem ? {
    id: editingItem.matricula,
    numero_matricula: editingItem.matricula_numero,
    aluno_nome: editingItem.aluno_nome,
  } : null

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <h1 className="page-title">Declaracoes</h1>
          <p className="page-subtitle">Documentos eletronicos</p>
        </div>
        <div className="page-header__actions">
          <button type="button" className="btn btn--primary" onClick={() => { setEditingId(null); setIsCreating(true); setFormData(DEFAULT_FORM) }}>
            <Plus size={16} /> Nova Declaracao
          </button>
        </div>
      </div>

      {isError ? <div className="alert alert--error">Nao foi possivel carregar as declaracoes.</div> : null}

      <DataTable
        columns={COLUMNS}
        data={data}
        isLoading={isLoading}
        onSearch={(value) => { setSearch(value); setPage(1) }}
        searchPlaceholder="Buscar por protocolo, assunto, aluno ou matricula..."
        emptyMessage="Nenhuma declaracao encontrada."
        rowActions={(row) => (
          <div className="table-actions">
            <button type="button" className="btn btn--outline btn--sm" onClick={() => setSelectedId(row.id)}><Eye size={14} /> Visualizar</button>
            <button type="button" className="btn btn--secondary btn--sm" onClick={() => { setSelectedId(null); setIsCreating(false); setEditingId(row.id) }}><Pencil size={14} /> Editar</button>
            <button type="button" className="btn btn--danger btn--sm" onClick={() => window.confirm(`Excluir a declaracao ${row.numero_protocolo}?`) && deleteMutation.mutate(row.id)}><Trash2 size={14} /> Excluir</button>
          </div>
        )}
      />

      {selectedId ? (
        <EntityDetailsPanel
          title="Detalhes da declaracao"
          subtitle={selectedItem?.assunto || 'Consultando declaracao selecionada'}
          fields={selectedItem ? [
            { label: 'Protocolo', value: selectedItem.numero_protocolo },
            { label: 'Tipo', value: selectedItem.tipo_display },
            { label: 'Assunto', value: selectedItem.assunto },
            { label: 'Matricula', value: selectedItem.matricula_numero },
            { label: 'Aluno', value: selectedItem.aluno_nome },
            { label: 'Observacao', value: selectedItem.observacao || '-' },
            { label: 'Emitido por', value: selectedItem.emitido_por_nome || '-' },
          ] : []}
          isLoading={isLoadingDetails}
          errorMessage={isErrorDetails ? 'Nao foi possivel carregar os detalhes desta declaracao.' : ''}
          onClose={() => setSelectedId(null)}
        />
      ) : null}

      {(isCreating || editingId) ? (
        <EntityFormPanel
          title={editingId ? 'Editar declaracao' : 'Emitir declaracao'}
          subtitle="Preencha os dados do documento."
          onSubmit={(event) => {
            event.preventDefault()
            saveMutation.mutate({ id: editingId, payload: { ...formData, matricula: Number(formData.matricula) } })
          }}
          onCancel={() => { setEditingId(null); setIsCreating(false); setFormData(DEFAULT_FORM) }}
          submitLabel={editingId ? 'Salvar alteracoes' : 'Emitir declaracao'}
          isSubmitting={saveMutation.isPending}
        >
          <div className="form-field">
            <label>Tipo</label>
            <select className="select" value={formData.tipo} onChange={(event) => setFormData((current) => ({ ...current, tipo: event.target.value }))}>
              {TIPO_OPTIONS.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}
            </select>
          </div>
          <div className="form-field form-field--full">
            <label>Assunto</label>
            <input type="text" value={formData.assunto} onChange={(event) => setFormData((current) => ({ ...current, assunto: event.target.value }))} />
          </div>
          <SearchableRemoteSelect
            id="declaracao-matricula"
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
            <label>Observacao</label>
            <textarea rows="3" value={formData.observacao} onChange={(event) => setFormData((current) => ({ ...current, observacao: event.target.value }))} />
          </div>
        </EntityFormPanel>
      ) : null}

      {data ? <div className="pagination"><button className="btn btn--secondary" disabled={!data.previous} onClick={() => setPage((current) => current - 1)}>Anterior</button><span className="pagination__info">Pagina {page} — {data.count} registros</span><button className="btn btn--secondary" disabled={!data.next} onClick={() => setPage((current) => current + 1)}>Proxima</button></div> : null}
    </div>
  )
}