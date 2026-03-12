import { useEffect, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Eye, Pencil, Plus, Trash2 } from 'lucide-react'
import toast from 'react-hot-toast'
import { Link, useLocation, useNavigate } from 'react-router-dom'

import { guiasTransferenciaApi, matriculasApi, transferenciasApi } from '@/api/endpoints'
import DataTable from '@/components/ui/DataTable'
import EntityDetailsPanel from '@/components/ui/EntityDetailsPanel'
import EntityFormPanel from '@/components/ui/EntityFormPanel'
import SearchableRemoteSelect from '@/components/ui/SearchableRemoteSelect'

const COLUMNS = [
  { key: 'numero_protocolo', label: 'Protocolo' },
  { key: 'assunto', label: 'Assunto' },
  { key: 'matricula_numero', label: 'Matricula' },
  { key: 'aluno_nome', label: 'Aluno' },
  { key: 'escola_origem', label: 'Escola de origem' },
  { key: 'escola_destino', label: 'Escola de destino' },
]

const DEFAULT_FORM = {
  assunto: '',
  matricula: '',
  escola_origem: '',
  escola_destino: '',
  transferencia: '',
  observacao: '',
}

function getErrorMessage(error, fallback) {
  const data = error?.response?.data
  if (!data) return fallback
  if (typeof data.detail === 'string') return data.detail
  const firstValue = Object.values(data)[0]
  return Array.isArray(firstValue) ? firstValue[0] : (firstValue || fallback)
}

export default function GuiasTransferenciaPage() {
  const location = useLocation()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [search, setSearch] = useState('')
  const [page, setPage] = useState(1)
  const [selectedId, setSelectedId] = useState(null)
  const [editingId, setEditingId] = useState(null)
  const [formData, setFormData] = useState(DEFAULT_FORM)
  const [matriculaSearch, setMatriculaSearch] = useState('')
  const [transferenciaSearch, setTransferenciaSearch] = useState('')
  const isCreatePage = location.pathname.endsWith('/documentos/guias/nova')

  const { data, isLoading, isError } = useQuery({
    queryKey: ['guias-transferencia', { search, page }],
    queryFn: () => guiasTransferenciaApi.list({ search, page }).then((response) => response.data),
    staleTime: 30_000,
  })

  const { data: matriculasData } = useQuery({
    queryKey: ['matriculas', 'guia-options', matriculaSearch],
    queryFn: () => matriculasApi.list({ page_size: 10, search: matriculaSearch || undefined }).then((response) => response.data),
    staleTime: 60_000,
  })

  const { data: transferenciasData } = useQuery({
    queryKey: ['transferencias', 'guia-options', transferenciaSearch],
    queryFn: () => transferenciasApi.list({ page_size: 10, search: transferenciaSearch || undefined }).then((response) => response.data),
    staleTime: 60_000,
  })

  const { data: selectedItem, isLoading: isLoadingDetails, isError: isErrorDetails } = useQuery({
    queryKey: ['guia-transferencia', selectedId],
    queryFn: () => guiasTransferenciaApi.get(selectedId).then((response) => response.data),
    enabled: Boolean(selectedId),
    staleTime: 30_000,
  })

  const { data: editingItem } = useQuery({
    queryKey: ['guia-transferencia-edit', editingId],
    queryFn: () => guiasTransferenciaApi.get(editingId).then((response) => response.data),
    enabled: Boolean(editingId),
    staleTime: 0,
  })

  useEffect(() => {
    if (!editingItem) return
    setFormData({
      assunto: editingItem.assunto || '',
      matricula: editingItem.matricula ? String(editingItem.matricula) : '',
      escola_origem: editingItem.escola_origem || '',
      escola_destino: editingItem.escola_destino || '',
      transferencia: editingItem.transferencia ? String(editingItem.transferencia) : '',
      observacao: editingItem.observacao || '',
    })
  }, [editingItem])

  const saveMutation = useMutation({
    mutationFn: ({ id, payload }) => (id ? guiasTransferenciaApi.update(id, payload) : guiasTransferenciaApi.create(payload)),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['guias-transferencia'] })
      toast.success(editingId ? 'Guia atualizada com sucesso.' : 'Guia emitida com sucesso.')
      setEditingId(null)
      setFormData(DEFAULT_FORM)
      if (!editingId) {
        navigate('/documentos/guias')
      }
    },
    onError: (error) => toast.error(getErrorMessage(error, 'Nao foi possivel salvar a guia.')),
  })

  const deleteMutation = useMutation({
    mutationFn: (id) => guiasTransferenciaApi.remove(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['guias-transferencia'] })
      setSelectedId(null)
      toast.success('Guia excluida com sucesso.')
    },
    onError: (error) => toast.error(getErrorMessage(error, 'Nao foi possivel excluir a guia.')),
  })

  const matriculas = matriculasData?.results || []
  const transferencias = transferenciasData?.results || []
  const selectedMatriculaOption = formData.matricula && editingItem ? {
    id: editingItem.matricula,
    numero_matricula: editingItem.matricula_numero,
    aluno_nome: editingItem.aluno_nome,
  } : null
  const selectedTransferenciaOption = formData.transferencia && editingItem ? {
    id: editingItem.transferencia,
    matricula_numero: editingItem.matricula_numero,
    tipo_display: editingItem.transferencia_label || 'Transferencia vinculada',
    status_display: '',
  } : null

  if (isCreatePage) {
    return (
      <div className="page page--wide">
        <nav className="profile-breadcrumb">
          <Link to="/dashboard">Início</Link>
          <span className="profile-breadcrumb__sep">&gt;</span>
          <Link to="/documentos/guias">Guias de Transferência</Link>
          <span className="profile-breadcrumb__sep">&gt;</span>
          <span>Nova Guia</span>
        </nav>

        <div className="page-header">
          <div>
            <h1 className="page-title">Nova guia</h1>
            <p className="page-subtitle">A emissão agora acontece em uma página separada da listagem.</p>
          </div>
          <div className="page-header__actions">
            <button type="button" className="btn btn--outline" onClick={() => navigate('/documentos/guias')}>
              Voltar para guias
            </button>
          </div>
        </div>

        <EntityFormPanel
          title="Emitir guia de transferencia"
          subtitle="Preencha os dados da guia vinculada a matricula e transferencia."
          onSubmit={(event) => {
            event.preventDefault()
            saveMutation.mutate({
              payload: {
                ...formData,
                matricula: Number(formData.matricula),
                transferencia: formData.transferencia ? Number(formData.transferencia) : null,
              },
            })
          }}
          onCancel={() => navigate('/documentos/guias')}
          submitLabel="Emitir guia"
          isSubmitting={saveMutation.isPending}
        >
          <div className="form-field form-field--full"><label>Assunto</label><input type="text" value={formData.assunto} onChange={(event) => setFormData((current) => ({ ...current, assunto: event.target.value }))} /></div>
          <SearchableRemoteSelect id="guia-matricula" label="Matricula" searchLabel="Buscar matricula" searchPlaceholder="Digite matricula ou aluno" searchValue={matriculaSearch} onSearchChange={setMatriculaSearch} value={formData.matricula} onChange={(nextValue) => setFormData((current) => ({ ...current, matricula: nextValue }))} options={matriculas} getOptionLabel={(item) => `${item.numero_matricula} - ${item.aluno_nome}`} />
          <SearchableRemoteSelect id="guia-transferencia" label="Transferencia vinculada" searchLabel="Buscar transferencia" searchPlaceholder="Digite matricula, tipo ou status" searchValue={transferenciaSearch} onSearchChange={setTransferenciaSearch} value={formData.transferencia} onChange={(nextValue) => setFormData((current) => ({ ...current, transferencia: nextValue }))} options={transferencias} emptyOptionLabel="Sem transferencia" getOptionLabel={(item) => `${item.matricula_numero} - ${item.tipo_display}${item.status_display ? ` - ${item.status_display}` : ''}`} />
          <div className="form-field"><label>Escola de origem</label><input type="text" value={formData.escola_origem} onChange={(event) => setFormData((current) => ({ ...current, escola_origem: event.target.value }))} /></div>
          <div className="form-field"><label>Escola de destino</label><input type="text" value={formData.escola_destino} onChange={(event) => setFormData((current) => ({ ...current, escola_destino: event.target.value }))} /></div>
          <div className="form-field form-field--full"><label>Observacao</label><textarea rows="3" value={formData.observacao} onChange={(event) => setFormData((current) => ({ ...current, observacao: event.target.value }))} /></div>
        </EntityFormPanel>
      </div>
    )
  }

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <h1 className="page-title">Guias de Transferencia</h1>
          <p className="page-subtitle">Documentos eletronicos</p>
        </div>
        <div className="page-header__actions">
          <button type="button" className="btn btn--primary" onClick={() => navigate('/documentos/guias/nova')}>
            <Plus size={16} /> Nova Guia
          </button>
        </div>
      </div>

      {isError ? <div className="alert alert--error">Nao foi possivel carregar as guias.</div> : null}

      <DataTable
        columns={COLUMNS}
        data={data}
        isLoading={isLoading}
        onSearch={(value) => { setSearch(value); setPage(1) }}
        searchPlaceholder="Buscar por protocolo, assunto, aluno, matricula ou escola..."
        emptyMessage="Nenhuma guia encontrada."
        rowActions={(row) => (
          <div className="table-actions">
            <button type="button" className="btn btn--outline btn--sm" onClick={() => setSelectedId(row.id)}><Eye size={14} /> Visualizar</button>
            <button type="button" className="btn btn--secondary btn--sm" onClick={() => { setSelectedId(null); setEditingId(row.id) }}><Pencil size={14} /> Editar</button>
            <button type="button" className="btn btn--danger btn--sm" onClick={() => window.confirm(`Excluir a guia ${row.numero_protocolo}?`) && deleteMutation.mutate(row.id)}><Trash2 size={14} /> Excluir</button>
          </div>
        )}
      />

      {selectedId ? (
        <EntityDetailsPanel
          title="Detalhes da guia"
          subtitle={selectedItem?.assunto || 'Consultando guia selecionada'}
          fields={selectedItem ? [
            { label: 'Protocolo', value: selectedItem.numero_protocolo },
            { label: 'Assunto', value: selectedItem.assunto },
            { label: 'Matricula', value: selectedItem.matricula_numero },
            { label: 'Aluno', value: selectedItem.aluno_nome },
            { label: 'Escola de origem', value: selectedItem.escola_origem || '-' },
            { label: 'Escola de destino', value: selectedItem.escola_destino || '-' },
            { label: 'Transferencia vinculada', value: selectedItem.transferencia_label || '-' },
            { label: 'Observacao', value: selectedItem.observacao || '-' },
            { label: 'Emitido por', value: selectedItem.emitido_por_nome || '-' },
          ] : []}
          isLoading={isLoadingDetails}
          errorMessage={isErrorDetails ? 'Nao foi possivel carregar os detalhes desta guia.' : ''}
          onClose={() => setSelectedId(null)}
        />
      ) : null}

      {editingId ? (
        <EntityFormPanel
          title="Editar guia"
          subtitle="Preencha os dados da guia vinculada a matricula e transferencia."
          onSubmit={(event) => {
            event.preventDefault()
            saveMutation.mutate({
              id: editingId,
              payload: {
                ...formData,
                matricula: Number(formData.matricula),
                transferencia: formData.transferencia ? Number(formData.transferencia) : null,
              },
            })
          }}
          onCancel={() => { setEditingId(null); setFormData(DEFAULT_FORM) }}
          submitLabel="Salvar alteracoes"
          isSubmitting={saveMutation.isPending}
        >
          <div className="form-field form-field--full">
            <label>Assunto</label>
            <input type="text" value={formData.assunto} onChange={(event) => setFormData((current) => ({ ...current, assunto: event.target.value }))} />
          </div>
          <SearchableRemoteSelect
            id="guia-matricula"
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
          <SearchableRemoteSelect
            id="guia-transferencia"
            label="Transferencia vinculada"
            searchLabel="Buscar transferencia"
            searchPlaceholder="Digite matricula, tipo ou status"
            searchValue={transferenciaSearch}
            onSearchChange={setTransferenciaSearch}
            value={formData.transferencia}
            onChange={(nextValue) => setFormData((current) => ({ ...current, transferencia: nextValue }))}
            options={transferencias}
            selectedOption={selectedTransferenciaOption}
            emptyOptionLabel="Sem transferencia"
            getOptionLabel={(item) => `${item.matricula_numero} - ${item.tipo_display}${item.status_display ? ` - ${item.status_display}` : ''}`}
          />
          <div className="form-field">
            <label>Escola de origem</label>
            <input type="text" value={formData.escola_origem} onChange={(event) => setFormData((current) => ({ ...current, escola_origem: event.target.value }))} />
          </div>
          <div className="form-field">
            <label>Escola de destino</label>
            <input type="text" value={formData.escola_destino} onChange={(event) => setFormData((current) => ({ ...current, escola_destino: event.target.value }))} />
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