import { useEffect, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Eye, Pencil, Plus, Trash2 } from 'lucide-react'
import toast from 'react-hot-toast'
import { Link, useLocation, useNavigate } from 'react-router-dom'

import { historicosApi, matriculasApi } from '@/api/endpoints'
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
  { key: 'periodo_ref', label: 'Periodo' },
]

const TIPO_OPTIONS = [
  { value: 'COMPLETO', label: 'Historico Completo' },
  { value: 'PARCIAL', label: 'Historico Parcial' },
]

const DEFAULT_FORM = { tipo: 'COMPLETO', assunto: '', matricula: '', periodo_ref: '', observacao: '' }

function getErrorMessage(error, fallback) {
  const data = error?.response?.data
  if (!data) return fallback
  if (typeof data.detail === 'string') return data.detail
  const firstValue = Object.values(data)[0]
  return Array.isArray(firstValue) ? firstValue[0] : (firstValue || fallback)
}

export default function HistoricosPage() {
  const location = useLocation()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [search, setSearch] = useState('')
  const [page, setPage] = useState(1)
  const [selectedId, setSelectedId] = useState(null)
  const [editingId, setEditingId] = useState(null)
  const [formData, setFormData] = useState(DEFAULT_FORM)
  const [matriculaSearch, setMatriculaSearch] = useState('')
  const isCreatePage = location.pathname.endsWith('/documentos/historicos/novo')

  const { data, isLoading, isError } = useQuery({
    queryKey: ['historicos', { search, page }],
    queryFn: () => historicosApi.list({ search, page }).then((response) => response.data),
    staleTime: 30_000,
  })

  const { data: matriculasData } = useQuery({
    queryKey: ['matriculas', 'historico-options', matriculaSearch],
    queryFn: () => matriculasApi.list({ page_size: 10, search: matriculaSearch || undefined }).then((response) => response.data),
    staleTime: 60_000,
  })

  const { data: selectedItem, isLoading: isLoadingDetails, isError: isErrorDetails } = useQuery({
    queryKey: ['historico', selectedId],
    queryFn: () => historicosApi.get(selectedId).then((response) => response.data),
    enabled: Boolean(selectedId),
    staleTime: 30_000,
  })

  const { data: editingItem } = useQuery({
    queryKey: ['historico-edit', editingId],
    queryFn: () => historicosApi.get(editingId).then((response) => response.data),
    enabled: Boolean(editingId),
    staleTime: 0,
  })

  useEffect(() => {
    if (!editingItem) return
    setFormData({
      tipo: editingItem.tipo || 'COMPLETO',
      assunto: editingItem.assunto || '',
      matricula: editingItem.matricula ? String(editingItem.matricula) : '',
      periodo_ref: editingItem.periodo_ref || '',
      observacao: editingItem.observacao || '',
    })
  }, [editingItem])

  const saveMutation = useMutation({
    mutationFn: ({ id, payload }) => (id ? historicosApi.update(id, payload) : historicosApi.create(payload)),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['historicos'] })
      toast.success(editingId ? 'Historico atualizado com sucesso.' : 'Historico emitido com sucesso.')
      setEditingId(null)
      setFormData(DEFAULT_FORM)
      if (!editingId) {
        navigate('/documentos/historicos')
      }
    },
    onError: (error) => toast.error(getErrorMessage(error, 'Nao foi possivel salvar o historico.')),
  })

  const deleteMutation = useMutation({
    mutationFn: (id) => historicosApi.remove(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['historicos'] })
      setSelectedId(null)
      toast.success('Historico excluido com sucesso.')
    },
    onError: (error) => toast.error(getErrorMessage(error, 'Nao foi possivel excluir o historico.')),
  })

  const matriculas = matriculasData?.results || []
  const selectedMatriculaOption = formData.matricula && editingItem ? {
    id: editingItem.matricula,
    numero_matricula: editingItem.matricula_numero,
    aluno_nome: editingItem.aluno_nome,
  } : null

  if (isCreatePage) {
    return (
      <div className="page page--wide">
        <nav className="profile-breadcrumb">
          <Link to="/dashboard">Início</Link>
          <span className="profile-breadcrumb__sep">&gt;</span>
          <Link to="/documentos/historicos">Históricos</Link>
          <span className="profile-breadcrumb__sep">&gt;</span>
          <span>Novo Histórico</span>
        </nav>

        <div className="page-header">
          <div>
            <h1 className="page-title">Novo histórico</h1>
            <p className="page-subtitle">A emissão agora acontece em uma página separada da listagem.</p>
          </div>
          <div className="page-header__actions">
            <button type="button" className="btn btn--outline" onClick={() => navigate('/documentos/historicos')}>
              Voltar para históricos
            </button>
          </div>
        </div>

        <EntityFormPanel
          title="Emitir historico"
          subtitle="Preencha os dados do historico escolar."
          onSubmit={(event) => {
            event.preventDefault()
            saveMutation.mutate({ payload: { ...formData, matricula: Number(formData.matricula) } })
          }}
          onCancel={() => navigate('/documentos/historicos')}
          submitLabel="Emitir historico"
          isSubmitting={saveMutation.isPending}
        >
          <div className="form-field"><label>Tipo</label><select className="select" value={formData.tipo} onChange={(event) => setFormData((current) => ({ ...current, tipo: event.target.value }))}>{TIPO_OPTIONS.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}</select></div>
          <div className="form-field form-field--full"><label>Assunto</label><input type="text" value={formData.assunto} onChange={(event) => setFormData((current) => ({ ...current, assunto: event.target.value }))} /></div>
          <SearchableRemoteSelect id="historico-matricula" label="Matricula" searchLabel="Buscar matricula" searchPlaceholder="Digite matricula ou aluno" searchValue={matriculaSearch} onSearchChange={setMatriculaSearch} value={formData.matricula} onChange={(nextValue) => setFormData((current) => ({ ...current, matricula: nextValue }))} options={matriculas} getOptionLabel={(item) => `${item.numero_matricula} - ${item.aluno_nome}`} />
          <div className="form-field"><label>Periodo de referencia</label><input type="text" value={formData.periodo_ref} onChange={(event) => setFormData((current) => ({ ...current, periodo_ref: event.target.value }))} /></div>
          <div className="form-field form-field--full"><label>Observacao</label><textarea rows="3" value={formData.observacao} onChange={(event) => setFormData((current) => ({ ...current, observacao: event.target.value }))} /></div>
        </EntityFormPanel>
      </div>
    )
  }

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <h1 className="page-title">Historicos Escolares</h1>
          <p className="page-subtitle">Documentos eletronicos</p>
        </div>
        <div className="page-header__actions">
          <button type="button" className="btn btn--primary" onClick={() => navigate('/documentos/historicos/novo')}>
            <Plus size={16} /> Novo Historico
          </button>
        </div>
      </div>

      {isError ? <div className="alert alert--error">Nao foi possivel carregar os historicos.</div> : null}

      <DataTable
        columns={COLUMNS}
        data={data}
        isLoading={isLoading}
        onSearch={(value) => { setSearch(value); setPage(1) }}
        searchPlaceholder="Buscar por protocolo, assunto, periodo, aluno ou matricula..."
        emptyMessage="Nenhum historico encontrado."
        rowActions={(row) => (
          <div className="table-actions">
            <button type="button" className="btn btn--outline btn--sm" onClick={() => setSelectedId(row.id)}><Eye size={14} /> Visualizar</button>
            <button type="button" className="btn btn--secondary btn--sm" onClick={() => { setSelectedId(null); setEditingId(row.id) }}><Pencil size={14} /> Editar</button>
            <button type="button" className="btn btn--danger btn--sm" onClick={() => window.confirm(`Excluir o historico ${row.numero_protocolo}?`) && deleteMutation.mutate(row.id)}><Trash2 size={14} /> Excluir</button>
          </div>
        )}
      />

      {selectedId ? (
        <EntityDetailsPanel
          title="Detalhes do historico"
          subtitle={selectedItem?.assunto || 'Consultando historico selecionado'}
          fields={selectedItem ? [
            { label: 'Protocolo', value: selectedItem.numero_protocolo },
            { label: 'Tipo', value: selectedItem.tipo_display },
            { label: 'Assunto', value: selectedItem.assunto },
            { label: 'Matricula', value: selectedItem.matricula_numero },
            { label: 'Aluno', value: selectedItem.aluno_nome },
            { label: 'Periodo de referencia', value: selectedItem.periodo_ref || '-' },
            { label: 'Observacao', value: selectedItem.observacao || '-' },
            { label: 'Emitido por', value: selectedItem.emitido_por_nome || '-' },
          ] : []}
          isLoading={isLoadingDetails}
          errorMessage={isErrorDetails ? 'Nao foi possivel carregar os detalhes deste historico.' : ''}
          onClose={() => setSelectedId(null)}
        />
      ) : null}

      {editingId ? (
        <EntityFormPanel
          title="Editar historico"
          subtitle="Preencha os dados do historico escolar."
          onSubmit={(event) => {
            event.preventDefault()
            saveMutation.mutate({ id: editingId, payload: { ...formData, matricula: Number(formData.matricula) } })
          }}
          onCancel={() => { setEditingId(null); setFormData(DEFAULT_FORM) }}
          submitLabel="Salvar alteracoes"
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
            id="historico-matricula"
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
            <label>Periodo de referencia</label>
            <input type="text" value={formData.periodo_ref} onChange={(event) => setFormData((current) => ({ ...current, periodo_ref: event.target.value }))} />
          </div>
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