import { useEffect, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Eye, Pencil, Plus, Trash2 } from 'lucide-react'
import toast from 'react-hot-toast'
import { useNavigate } from 'react-router-dom'

import { processosApi, usuariosApi } from '@/api/endpoints'
import DataTable from '@/components/ui/DataTable'
import EntityDetailsPanel from '@/components/ui/EntityDetailsPanel'
import EntityFormPanel from '@/components/ui/EntityFormPanel'
import SearchableRemoteSelect from '@/components/ui/SearchableRemoteSelect'

const STATUS_BADGE = {
  ABERTO:        'badge--info',
  EM_TRAMITACAO: 'badge--warning',
  CONCLUIDO:     'badge--success',
  ARQUIVADO:     'badge--secondary',
}

const STATUS_OPTIONS = [
  { value: 'ABERTO', label: 'Aberto' },
  { value: 'EM_TRAMITACAO', label: 'Em Tramitação' },
  { value: 'CONCLUIDO', label: 'Concluído' },
  { value: 'ARQUIVADO', label: 'Arquivado' },
]

const TIPO_OPTIONS = [
  { value: 'REQUERIMENTO', label: 'Requerimento' },
  { value: 'RECURSO', label: 'Recurso' },
  { value: 'TRANSFERENCIA', label: 'Transferência' },
  { value: 'SOLICITACAO', label: 'Solicitação Geral' },
  { value: 'OUTROS', label: 'Outros' },
]

const TRAMITACAO_OPTIONS = [
  { value: 'RECEBIDO', label: 'Recebido' },
  { value: 'ENCAMINHADO', label: 'Encaminhado' },
  { value: 'RESPONDIDO', label: 'Respondido' },
  { value: 'ARQUIVADO', label: 'Arquivado' },
  { value: 'DEVOLVIDO', label: 'Devolvido' },
]

const DEFAULT_FORM = {
  tipo: 'REQUERIMENTO',
  requerente: '',
  assunto: '',
  descricao: '',
  status: 'ABERTO',
  data_conclusao: '',
}

const DEFAULT_TRAMITACAO_FORM = {
  acao: 'ENCAMINHADO',
  setor_destino: '',
  observacao: '',
}

function formatDate(value) {
  if (!value) return '-'
  return new Date(`${value}T00:00:00`).toLocaleDateString('pt-BR')
}

function formatDateTime(value) {
  if (!value) return '-'
  return new Date(value).toLocaleString('pt-BR')
}

function getErrorMessage(error, fallback) {
  const data = error?.response?.data
  if (!data) return fallback
  if (typeof data.detail === 'string') return data.detail
  const firstValue = Object.values(data)[0]
  return Array.isArray(firstValue) ? firstValue[0] : (firstValue || fallback)
}

const COLUMNS = [
  { key: 'numero',         label: 'Nº Processo' },
  { key: 'tipo_display',   label: 'Tipo' },
  { key: 'assunto',        label: 'Assunto' },
  { key: 'requerente_nome',label: 'Requerente' },
  {
    key: 'status',
    label: 'Status',
    render: (row) => (
      <span className={`badge ${STATUS_BADGE[row.status] || ''}`}>
        {row.status_display || row.status}
      </span>
    ),
  },
  { key: 'data_abertura', label: 'Abertura', render: (row) => formatDate(row.data_abertura) },
]

export default function ProcessosPage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [page, setPage] = useState(1)
  const [selectedProcessoId, setSelectedProcessoId] = useState(null)
  const [editingProcessoId, setEditingProcessoId] = useState(null)
  const [tramitingProcessoId, setTramitingProcessoId] = useState(null)
  const [formData, setFormData] = useState(DEFAULT_FORM)
  const [tramitacaoForm, setTramitacaoForm] = useState(DEFAULT_TRAMITACAO_FORM)
  const [requerenteSearch, setRequerenteSearch] = useState('')

  const { data, isLoading, isError } = useQuery({
    queryKey: ['processos', { search, status: statusFilter, page }],
    queryFn: () => processosApi.list({ search, status: statusFilter || undefined, page }).then((r) => r.data),
    staleTime: 30_000,
  })

  const { data: requerentesData } = useQuery({
    queryKey: ['usuarios', 'processos-options', requerenteSearch],
    queryFn: () => usuariosApi.list({ page_size: 10, search: requerenteSearch || undefined }).then((response) => response.data),
    staleTime: 60_000,
  })

  const { data: selectedProcesso, isLoading: isLoadingDetails, isError: isErrorDetails } = useQuery({
    queryKey: ['processo', selectedProcessoId],
    queryFn: () => processosApi.get(selectedProcessoId).then((response) => response.data),
    enabled: Boolean(selectedProcessoId),
    staleTime: 30_000,
  })

  const { data: editingProcesso } = useQuery({
    queryKey: ['processo-edit', editingProcessoId],
    queryFn: () => processosApi.get(editingProcessoId).then((response) => response.data),
    enabled: Boolean(editingProcessoId),
    staleTime: 0,
  })

  useEffect(() => {
    if (!editingProcesso) return

    setFormData({
      tipo: editingProcesso.tipo || 'REQUERIMENTO',
      requerente: editingProcesso.requerente ? String(editingProcesso.requerente) : '',
      assunto: editingProcesso.assunto || '',
      descricao: editingProcesso.descricao || '',
      status: editingProcesso.status || 'ABERTO',
      data_conclusao: editingProcesso.data_conclusao || '',
    })
  }, [editingProcesso])

  const saveMutation = useMutation({
    mutationFn: ({ id, payload }) => (id ? processosApi.patch(id, payload) : processosApi.create(payload)),
    onSuccess: (_response, variables) => {
      queryClient.invalidateQueries({ queryKey: ['processos'] })
      if (variables.id) {
        queryClient.invalidateQueries({ queryKey: ['processo', variables.id] })
      }
      toast.success(variables.id ? 'Processo atualizado com sucesso.' : 'Processo aberto com sucesso.')
      setEditingProcessoId(null)
      setFormData(DEFAULT_FORM)
    },
    onError: (error) => toast.error(getErrorMessage(error, 'Não foi possível salvar o processo.')),
  })

  const deleteMutation = useMutation({
    mutationFn: (id) => processosApi.remove(id),
    onSuccess: (_response, id) => {
      queryClient.invalidateQueries({ queryKey: ['processos'] })
      queryClient.invalidateQueries({ queryKey: ['processo', id] })
      setSelectedProcessoId((current) => (current === id ? null : current))
      setEditingProcessoId((current) => (current === id ? null : current))
      setTramitingProcessoId((current) => (current === id ? null : current))
      setFormData(DEFAULT_FORM)
      toast.success('Processo removido com sucesso.')
    },
    onError: (error) => toast.error(getErrorMessage(error, 'Não foi possível remover o processo.')),
  })

  const tramitarMutation = useMutation({
    mutationFn: ({ id, payload }) => processosApi.tramitar(id, payload),
    onSuccess: (_response, variables) => {
      queryClient.invalidateQueries({ queryKey: ['processos'] })
      queryClient.invalidateQueries({ queryKey: ['processo', variables.id] })
      setTramitingProcessoId(null)
      setTramitacaoForm(DEFAULT_TRAMITACAO_FORM)
      toast.success('Tramitação registrada com sucesso.')
    },
    onError: (error) => toast.error(getErrorMessage(error, 'Não foi possível registrar a tramitação.')),
  })

  const requerentes = requerentesData?.results || []
  const selectedRequerenteOption = formData.requerente && editingProcesso ? {
    id: editingProcesso.requerente,
    nome_completo: editingProcesso.requerente_nome,
    username: '',
  } : null

  const detailsFields = selectedProcesso ? [
    { label: 'ID', value: selectedProcesso.id },
    { label: 'Número', value: selectedProcesso.numero },
    { label: 'Tipo', value: selectedProcesso.tipo_display },
    { label: 'Assunto', value: selectedProcesso.assunto },
    { label: 'Descrição', value: selectedProcesso.descricao || '-' },
    { label: 'Requerente', value: selectedProcesso.requerente_nome || '-' },
    { label: 'Status', value: selectedProcesso.status_display },
    { label: 'Abertura', value: formatDate(selectedProcesso.data_abertura) },
    { label: 'Conclusão', value: formatDate(selectedProcesso.data_conclusao) },
    {
      label: 'Tramitações',
      value: selectedProcesso.tramitacoes?.length
        ? selectedProcesso.tramitacoes.map((item) => `${formatDateTime(item.data)} • ${item.acao_display}${item.setor_destino ? ` • ${item.setor_destino}` : ''}${item.observacao ? ` • ${item.observacao}` : ''}`).join('\n')
        : 'Nenhuma tramitação registrada.',
    },
  ] : []

  return (
    <div className="page">
      <div className="page-header">
        <h1 className="page-title">Processos</h1>
        <div className="page-header__actions">
          <select className="select" value={statusFilter} onChange={(event) => { setStatusFilter(event.target.value); setPage(1) }}>
            <option value="">Todos os status</option>
            {STATUS_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>{option.label}</option>
            ))}
          </select>
          <button type="button" className="btn btn--primary" onClick={() => navigate('/processos/novo')}>
            <Plus size={16} /> Abrir Processo
          </button>
        </div>
      </div>

      {isError ? <div className="alert alert--error">Não foi possível carregar os processos.</div> : null}

      <DataTable
        columns={COLUMNS}
        data={data}
        isLoading={isLoading}
        onSearch={(v) => { setSearch(v); setPage(1) }}
        searchPlaceholder="Buscar por número ou assunto..."
        emptyMessage="Nenhum processo encontrado."
        rowActions={(row) => (
          <div className="table-actions">
            <button type="button" className="btn btn--outline btn--sm" onClick={() => setSelectedProcessoId(row.id)}>
              <Eye size={14} /> Detalhes
            </button>
            <button type="button" className="btn btn--secondary btn--sm" onClick={() => { setSelectedProcessoId(null); setEditingProcessoId(row.id) }}>
              <Pencil size={14} /> Editar
            </button>
            <button type="button" className="btn btn--secondary btn--sm" onClick={() => { setSelectedProcessoId(null); setEditingProcessoId(null); setTramitingProcessoId(row.id); setTramitacaoForm(DEFAULT_TRAMITACAO_FORM) }}>
              Tramitar
            </button>
            <button type="button" className="btn btn--danger btn--sm" onClick={() => window.confirm(`Remover o processo ${row.numero}?`) && deleteMutation.mutate(row.id)}>
              <Trash2 size={14} /> Excluir
            </button>
          </div>
        )}
      />

      {selectedProcessoId ? (
        <EntityDetailsPanel
          title="Detalhes do processo"
          subtitle={selectedProcesso?.numero || 'Consultando processo selecionado'}
          fields={detailsFields}
          isLoading={isLoadingDetails}
          errorMessage={isErrorDetails ? 'Não foi possível carregar os detalhes deste processo.' : ''}
          onClose={() => setSelectedProcessoId(null)}
        />
      ) : null}

      {editingProcessoId ? (
        <EntityFormPanel
          title="Editar processo"
          subtitle="Preencha o tipo, o requerente e os dados principais do processo."
          onSubmit={(event) => {
            event.preventDefault()

            if (!formData.tipo || !formData.assunto.trim()) {
              toast.error('Informe o tipo e o assunto do processo.')
              return
            }

            saveMutation.mutate({
              id: editingProcessoId,
              payload: {
                tipo: formData.tipo,
                requerente: formData.requerente ? Number(formData.requerente) : null,
                assunto: formData.assunto.trim(),
                descricao: formData.descricao.trim(),
                status: formData.status,
                data_conclusao: formData.data_conclusao || null,
              },
            })
          }}
          onCancel={() => { setEditingProcessoId(null); setFormData(DEFAULT_FORM) }}
          submitLabel="Salvar alterações"
          isSubmitting={saveMutation.isPending}
        >
          <div className="form-field">
            <label htmlFor="processo-tipo">Tipo</label>
            <select id="processo-tipo" className="select" value={formData.tipo} onChange={(event) => setFormData((current) => ({ ...current, tipo: event.target.value }))}>
              {TIPO_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>{option.label}</option>
              ))}
            </select>
          </div>

          <div className="form-field">
            <label htmlFor="processo-status">Status</label>
            <select id="processo-status" className="select" value={formData.status} onChange={(event) => setFormData((current) => ({ ...current, status: event.target.value }))}>
              {STATUS_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>{option.label}</option>
              ))}
            </select>
          </div>

          <SearchableRemoteSelect
            id="processo-requerente"
            label="Requerente"
            searchLabel="Buscar requerente"
            searchPlaceholder="Digite nome, CPF ou usuário"
            searchValue={requerenteSearch}
            onSearchChange={setRequerenteSearch}
            value={formData.requerente}
            onChange={(nextValue) => setFormData((current) => ({ ...current, requerente: nextValue }))}
            options={requerentes}
            selectedOption={selectedRequerenteOption}
            getOptionLabel={(item) => item.username ? `${item.nome_completo} - ${item.username}` : item.nome_completo}
            emptyOptionLabel="Sem requerente"
          />

          <div className="form-field form-field--full">
            <label htmlFor="processo-assunto">Assunto</label>
            <input id="processo-assunto" className="form-control" value={formData.assunto} onChange={(event) => setFormData((current) => ({ ...current, assunto: event.target.value }))} />
          </div>

          <div className="form-field">
            <label htmlFor="processo-data-conclusao">Data de conclusão</label>
            <input id="processo-data-conclusao" type="date" className="form-control" value={formData.data_conclusao} onChange={(event) => setFormData((current) => ({ ...current, data_conclusao: event.target.value }))} />
          </div>

          <div className="form-field form-field--full">
            <label htmlFor="processo-descricao">Descrição</label>
            <textarea id="processo-descricao" className="form-control" rows={4} value={formData.descricao} onChange={(event) => setFormData((current) => ({ ...current, descricao: event.target.value }))} />
          </div>
        </EntityFormPanel>
      ) : null}

      {tramitingProcessoId ? (
        <EntityFormPanel
          title="Registrar tramitação"
          subtitle="Registre a movimentação do processo sem perder o histórico existente."
          onSubmit={(event) => {
            event.preventDefault()
            tramitarMutation.mutate({ id: tramitingProcessoId, payload: tramitacaoForm })
          }}
          onCancel={() => { setTramitingProcessoId(null); setTramitacaoForm(DEFAULT_TRAMITACAO_FORM) }}
          submitLabel="Registrar tramitação"
          isSubmitting={tramitarMutation.isPending}
        >
          <div className="form-field">
            <label htmlFor="tramitacao-acao">Ação</label>
            <select id="tramitacao-acao" className="select" value={tramitacaoForm.acao} onChange={(event) => setTramitacaoForm((current) => ({ ...current, acao: event.target.value }))}>
              {TRAMITACAO_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>{option.label}</option>
              ))}
            </select>
          </div>

          <div className="form-field form-field--full">
            <label htmlFor="tramitacao-setor">Setor de destino</label>
            <input id="tramitacao-setor" className="form-control" value={tramitacaoForm.setor_destino} onChange={(event) => setTramitacaoForm((current) => ({ ...current, setor_destino: event.target.value }))} />
          </div>

          <div className="form-field form-field--full">
            <label htmlFor="tramitacao-observacao">Observação</label>
            <textarea id="tramitacao-observacao" className="form-control" rows={4} value={tramitacaoForm.observacao} onChange={(event) => setTramitacaoForm((current) => ({ ...current, observacao: event.target.value }))} />
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
