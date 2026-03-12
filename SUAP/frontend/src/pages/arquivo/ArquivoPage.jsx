import { useEffect, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Eye, Pencil, Plus, Trash2 } from 'lucide-react'
import toast from 'react-hot-toast'
import { useNavigate } from 'react-router-dom'

import { guardaApi, matriculasApi, processosApi } from '@/api/endpoints'
import DataTable from '@/components/ui/DataTable'
import EntityDetailsPanel from '@/components/ui/EntityDetailsPanel'
import EntityFormPanel from '@/components/ui/EntityFormPanel'
import SearchableRemoteSelect from '@/components/ui/SearchableRemoteSelect'

const STATUS_OPTIONS = [
  { value: 'ATIVO', label: 'Ativo' },
  { value: 'EMPRESTADO', label: 'Emprestado' },
  { value: 'ELIMINADO', label: 'Eliminado' },
]

const TIPO_OPTIONS = [
  { value: 'PASTA_ALUNO', label: 'Pasta do Aluno' },
  { value: 'PROCESSO', label: 'Processo Administrativo' },
  { value: 'CONTRATO', label: 'Contrato' },
  { value: 'ATA', label: 'Ata' },
  { value: 'DECLARACAO', label: 'Declaração' },
  { value: 'HISTORICO', label: 'Histórico Escolar' },
  { value: 'OUTROS', label: 'Outros' },
]

const STATUS_BADGE = {
  ATIVO: 'badge--success',
  EMPRESTADO: 'badge--warning',
  ELIMINADO: 'badge--danger',
}

const DEFAULT_FORM = {
  tipo_documento: 'PASTA_ALUNO',
  descricao: '',
  numero_caixa: '',
  localizacao: '',
  data_eliminacao_prevista: '',
  status: 'ATIVO',
  matricula: '',
  processo: '',
}

const COLUMNS = [
  { key: 'numero_registro',  label: 'Nº Registro' },
  { key: 'tipo_documento_display', label: 'Tipo' },
  { key: 'descricao',        label: 'Descrição' },
  { key: 'localizacao',      label: 'Localização' },
  {
    key: 'status',
    label: 'Status',
    render: (row) => (
      <span className={`badge ${STATUS_BADGE[row.status] || ''}`}>
        {row.status_display}
      </span>
    ),
  },
  { key: 'data_arquivamento', label: 'Data', render: (row) => formatDate(row.data_arquivamento) },
]

function formatDate(value) {
  if (!value) return '-'
  return new Date(`${value}T00:00:00`).toLocaleDateString('pt-BR')
}

function getErrorMessage(error, fallback) {
  const data = error?.response?.data
  if (!data) return fallback
  if (typeof data.detail === 'string') return data.detail
  const firstValue = Object.values(data)[0]
  return Array.isArray(firstValue) ? firstValue[0] : (firstValue || fallback)
}

export default function ArquivoPage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [tipoFilter, setTipoFilter] = useState('')
  const [page, setPage] = useState(1)
  const [selectedGuardaId, setSelectedGuardaId] = useState(null)
  const [editingGuardaId, setEditingGuardaId] = useState(null)
  const [formData, setFormData] = useState(DEFAULT_FORM)
  const [matriculaSearch, setMatriculaSearch] = useState('')
  const [processoSearch, setProcessoSearch] = useState('')

  const { data, isLoading, isError } = useQuery({
    queryKey: ['guarda', { search, status: statusFilter, tipo_documento: tipoFilter, page }],
    queryFn: () => guardaApi.list({ search, status: statusFilter || undefined, tipo_documento: tipoFilter || undefined, page }).then((r) => r.data),
    staleTime: 30_000,
  })

  const { data: matriculasData } = useQuery({
    queryKey: ['matriculas', 'guarda-options', matriculaSearch],
    queryFn: () => matriculasApi.list({ page_size: 10, search: matriculaSearch || undefined }).then((response) => response.data),
    staleTime: 60_000,
  })

  const { data: processosData } = useQuery({
    queryKey: ['processos', 'guarda-options', processoSearch],
    queryFn: () => processosApi.list({ page_size: 10, search: processoSearch || undefined }).then((response) => response.data),
    staleTime: 60_000,
  })

  const { data: selectedGuarda, isLoading: isLoadingDetails, isError: isErrorDetails } = useQuery({
    queryKey: ['guarda', selectedGuardaId],
    queryFn: () => guardaApi.get(selectedGuardaId).then((response) => response.data),
    enabled: Boolean(selectedGuardaId),
    staleTime: 30_000,
  })

  const { data: editingGuarda } = useQuery({
    queryKey: ['guarda-edit', editingGuardaId],
    queryFn: () => guardaApi.get(editingGuardaId).then((response) => response.data),
    enabled: Boolean(editingGuardaId),
    staleTime: 0,
  })

  useEffect(() => {
    if (!editingGuarda) return

    setFormData({
      tipo_documento: editingGuarda.tipo_documento || 'PASTA_ALUNO',
      descricao: editingGuarda.descricao || '',
      numero_caixa: editingGuarda.numero_caixa || '',
      localizacao: editingGuarda.localizacao || '',
      data_eliminacao_prevista: editingGuarda.data_eliminacao_prevista || '',
      status: editingGuarda.status || 'ATIVO',
      matricula: editingGuarda.matricula ? String(editingGuarda.matricula) : '',
      processo: editingGuarda.processo ? String(editingGuarda.processo) : '',
    })
  }, [editingGuarda])

  const saveMutation = useMutation({
    mutationFn: ({ id, payload }) => (id ? guardaApi.patch(id, payload) : guardaApi.create(payload)),
    onSuccess: (_response, variables) => {
      queryClient.invalidateQueries({ queryKey: ['guarda'] })
      if (variables.id) {
        queryClient.invalidateQueries({ queryKey: ['guarda', variables.id] })
      }
      toast.success(variables.id ? 'Registro atualizado com sucesso.' : 'Registro arquivado com sucesso.')
      setEditingGuardaId(null)
      setFormData(DEFAULT_FORM)
    },
    onError: (error) => toast.error(getErrorMessage(error, 'Não foi possível salvar o registro documental.')),
  })

  const deleteMutation = useMutation({
    mutationFn: (id) => guardaApi.remove(id),
    onSuccess: (_response, id) => {
      queryClient.invalidateQueries({ queryKey: ['guarda'] })
      queryClient.invalidateQueries({ queryKey: ['guarda', id] })
      setSelectedGuardaId((current) => (current === id ? null : current))
      setEditingGuardaId((current) => (current === id ? null : current))
      setFormData(DEFAULT_FORM)
      toast.success('Registro excluído com sucesso.')
    },
    onError: (error) => toast.error(getErrorMessage(error, 'Não foi possível excluir o registro documental.')),
  })

  const matriculas = matriculasData?.results || []
  const processos = processosData?.results || []

  const selectedMatriculaOption = formData.matricula && editingGuarda ? {
    id: editingGuarda.matricula,
    numero_matricula: editingGuarda.matricula_numero,
    aluno_nome: '',
  } : null

  const selectedProcessoOption = formData.processo && editingGuarda ? {
    id: editingGuarda.processo,
    numero: editingGuarda.processo_numero,
    assunto: '',
  } : null

  const detailsFields = selectedGuarda ? [
    { label: 'ID', value: selectedGuarda.id },
    { label: 'Registro', value: selectedGuarda.numero_registro },
    { label: 'Tipo', value: selectedGuarda.tipo_documento_display },
    { label: 'Descrição', value: selectedGuarda.descricao },
    { label: 'Caixa', value: selectedGuarda.numero_caixa || '-' },
    { label: 'Localização', value: selectedGuarda.localizacao || '-' },
    { label: 'Arquivado em', value: formatDate(selectedGuarda.data_arquivamento) },
    { label: 'Eliminação prevista', value: formatDate(selectedGuarda.data_eliminacao_prevista) },
    { label: 'Status', value: selectedGuarda.status_display },
    { label: 'Responsável', value: selectedGuarda.responsavel_nome || '-' },
    { label: 'Matrícula vinculada', value: selectedGuarda.matricula_numero || '-' },
    { label: 'Processo vinculado', value: selectedGuarda.processo_numero || '-' },
  ] : []

  return (
    <div className="page">
      <div className="page-header">
        <h1 className="page-title">Arquivo / Guarda Documental</h1>
        <div className="page-header__actions">
          <select className="select" value={tipoFilter} onChange={(event) => { setTipoFilter(event.target.value); setPage(1) }}>
            <option value="">Todos os tipos</option>
            {TIPO_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>{option.label}</option>
            ))}
          </select>
          <select className="select" value={statusFilter} onChange={(event) => { setStatusFilter(event.target.value); setPage(1) }}>
            <option value="">Todos os status</option>
            {STATUS_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>{option.label}</option>
            ))}
          </select>
          <button type="button" className="btn btn--primary" onClick={() => navigate('/arquivo/novo')}>
            <Plus size={16} /> Arquivar Documento
          </button>
        </div>
      </div>

      {isError ? <div className="alert alert--error">Não foi possível carregar os registros documentais.</div> : null}

      <DataTable
        columns={COLUMNS}
        data={data}
        isLoading={isLoading}
        onSearch={(v) => { setSearch(v); setPage(1) }}
        searchPlaceholder="Buscar documento..."
        emptyMessage="Nenhum documento arquivado encontrado."
        rowActions={(row) => (
          <div className="table-actions">
            <button type="button" className="btn btn--outline btn--sm" onClick={() => setSelectedGuardaId(row.id)}>
              <Eye size={14} /> Detalhes
            </button>
            <button type="button" className="btn btn--secondary btn--sm" onClick={() => { setSelectedGuardaId(null); setEditingGuardaId(row.id) }}>
              <Pencil size={14} /> Editar
            </button>
            <button type="button" className="btn btn--danger btn--sm" onClick={() => window.confirm(`Excluir o registro ${row.numero_registro}?`) && deleteMutation.mutate(row.id)}>
              <Trash2 size={14} /> Excluir
            </button>
          </div>
        )}
      />

      {selectedGuardaId ? (
        <EntityDetailsPanel
          title="Detalhes do registro"
          subtitle={selectedGuarda?.numero_registro || 'Consultando registro selecionado'}
          fields={detailsFields}
          isLoading={isLoadingDetails}
          errorMessage={isErrorDetails ? 'Não foi possível carregar os detalhes deste registro.' : ''}
          onClose={() => setSelectedGuardaId(null)}
        />
      ) : null}

      {editingGuardaId ? (
        <EntityFormPanel
          title="Editar guarda documental"
          subtitle="Defina o tipo, a identificação física e os vínculos opcionais do registro documental."
          onSubmit={(event) => {
            event.preventDefault()

            if (!formData.tipo_documento || !formData.descricao.trim()) {
              toast.error('Informe o tipo e a descrição do documento.')
              return
            }

            saveMutation.mutate({
              id: editingGuardaId,
              payload: {
                tipo_documento: formData.tipo_documento,
                descricao: formData.descricao.trim(),
                numero_caixa: formData.numero_caixa.trim(),
                localizacao: formData.localizacao.trim(),
                data_eliminacao_prevista: formData.data_eliminacao_prevista || null,
                status: formData.status,
                matricula: formData.matricula ? Number(formData.matricula) : null,
                processo: formData.processo ? Number(formData.processo) : null,
              },
            })
          }}
          onCancel={() => { setEditingGuardaId(null); setFormData(DEFAULT_FORM) }}
          submitLabel="Salvar alterações"
          isSubmitting={saveMutation.isPending}
        >
          <div className="form-field">
            <label htmlFor="guarda-tipo">Tipo de documento</label>
            <select id="guarda-tipo" className="select" value={formData.tipo_documento} onChange={(event) => setFormData((current) => ({ ...current, tipo_documento: event.target.value }))}>
              {TIPO_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>{option.label}</option>
              ))}
            </select>
          </div>

          <div className="form-field">
            <label htmlFor="guarda-status">Status</label>
            <select id="guarda-status" className="select" value={formData.status} onChange={(event) => setFormData((current) => ({ ...current, status: event.target.value }))}>
              {STATUS_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>{option.label}</option>
              ))}
            </select>
          </div>

          <div className="form-field form-field--full">
            <label htmlFor="guarda-descricao">Descrição</label>
            <input id="guarda-descricao" className="form-control" value={formData.descricao} onChange={(event) => setFormData((current) => ({ ...current, descricao: event.target.value }))} />
          </div>

          <div className="form-field">
            <label htmlFor="guarda-numero-caixa">Número da caixa</label>
            <input id="guarda-numero-caixa" className="form-control" value={formData.numero_caixa} onChange={(event) => setFormData((current) => ({ ...current, numero_caixa: event.target.value }))} />
          </div>

          <div className="form-field">
            <label htmlFor="guarda-localizacao">Localização</label>
            <input id="guarda-localizacao" className="form-control" value={formData.localizacao} onChange={(event) => setFormData((current) => ({ ...current, localizacao: event.target.value }))} />
          </div>

          <div className="form-field">
            <label htmlFor="guarda-data-eliminacao">Data de eliminação prevista</label>
            <input id="guarda-data-eliminacao" type="date" className="form-control" value={formData.data_eliminacao_prevista} onChange={(event) => setFormData((current) => ({ ...current, data_eliminacao_prevista: event.target.value }))} />
          </div>

          <SearchableRemoteSelect
            id="guarda-matricula"
            label="Matrícula vinculada"
            searchLabel="Buscar matrícula"
            searchPlaceholder="Digite número, aluno ou curso"
            searchValue={matriculaSearch}
            onSearchChange={setMatriculaSearch}
            value={formData.matricula}
            onChange={(nextValue) => setFormData((current) => ({ ...current, matricula: nextValue }))}
            options={matriculas}
            selectedOption={selectedMatriculaOption}
            getOptionLabel={(item) => `${item.numero_matricula} - ${item.aluno_nome || ''}`.trim()}
            emptyOptionLabel="Não vincular"
          />

          <SearchableRemoteSelect
            id="guarda-processo"
            label="Processo vinculado"
            searchLabel="Buscar processo"
            searchPlaceholder="Digite número ou assunto"
            searchValue={processoSearch}
            onSearchChange={setProcessoSearch}
            value={formData.processo}
            onChange={(nextValue) => setFormData((current) => ({ ...current, processo: nextValue }))}
            options={processos}
            selectedOption={selectedProcessoOption}
            getOptionLabel={(item) => `${item.numero} - ${item.assunto || ''}`.trim()}
            emptyOptionLabel="Não vincular"
          />
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
