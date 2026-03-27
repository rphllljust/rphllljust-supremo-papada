import { useEffect, useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Eye, Pencil, Plus, Trash2 } from 'lucide-react'
import toast from 'react-hot-toast'

import { alunosApi, pedagogiaApi, usuariosApi } from '@/api/endpoints'
import DataTable from '@/components/ui/DataTable'
import EntityDetailsPanel from '@/components/ui/EntityDetailsPanel'
import EntityFormPanel from '@/components/ui/EntityFormPanel'
import SearchableRemoteSelect from '@/components/ui/SearchableRemoteSelect'

const STATUS_OPTIONS = [
  { value: 'RISCO_REPROVACAO', label: 'Risco de reprovacao' },
  { value: 'RISCO_EVASAO', label: 'Risco de evasao' },
  { value: 'PLANO_RECUPERACAO', label: 'Plano de recuperacao' },
  { value: 'ACOMPANHAMENTO_PSICOPEDAGOGICO', label: 'Acompanhamento psicopedagogico' },
  { value: 'CONCLUIDO', label: 'Concluido' },
]

const STATUS_BADGE = {
  RISCO_REPROVACAO: 'badge--warning',
  RISCO_EVASAO: 'badge--danger',
  PLANO_RECUPERACAO: 'badge--info',
  ACOMPANHAMENTO_PSICOPEDAGOGICO: 'badge--secondary',
  CONCLUIDO: 'badge--success',
}

const EMPTY_FORM = {
  aluno: '',
  pedagogia_responsavel: '',
  data_atendimento: '',
  diagnostico: '',
  plano_acao: '',
  status: 'RISCO_REPROVACAO',
}

const COLUMNS = [
  { key: 'aluno_nome', label: 'Aluno' },
  { key: 'pedagogia_responsavel_nome', label: 'Pedagogia responsavel' },
  {
    key: 'data_atendimento',
    label: 'Data atendimento',
    render: (row) => formatDate(row.data_atendimento),
  },
  {
    key: 'status',
    label: 'Status',
    render: (row) => (
      <span className={`badge ${STATUS_BADGE[row.status] || ''}`}>
        {row.status_display || row.status}
      </span>
    ),
  },
]

function formatDate(value) {
  if (!value) return '-'
  return new Date(`${value}T00:00:00`).toLocaleDateString('pt-BR')
}

function getTodayIsoDate() {
  const now = new Date()
  const localTime = new Date(now.getTime() - now.getTimezoneOffset() * 60_000)
  return localTime.toISOString().slice(0, 10)
}

function getErrorMessage(error, fallback) {
  const data = error?.response?.data
  if (!data) return fallback
  if (typeof data.detail === 'string') return data.detail
  const firstValue = Object.values(data)[0]
  return Array.isArray(firstValue) ? firstValue[0] : (firstValue || fallback)
}

export default function PedagogiaPage() {
  const queryClient = useQueryClient()
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [page, setPage] = useState(1)
  const [selectedAtendimentoId, setSelectedAtendimentoId] = useState(null)
  const [editingAtendimentoId, setEditingAtendimentoId] = useState(null)
  const [creating, setCreating] = useState(false)
  const [alunoSearch, setAlunoSearch] = useState('')
  const [responsavelSearch, setResponsavelSearch] = useState('')
  const [formData, setFormData] = useState(EMPTY_FORM)

  const { data, isLoading, isError } = useQuery({
    queryKey: ['pedagogia', { search, status: statusFilter, page }],
    queryFn: () => pedagogiaApi.list({ search, status: statusFilter || undefined, page }).then((response) => response.data),
    staleTime: 30_000,
  })

  const { data: alunosData } = useQuery({
    queryKey: ['pedagogia', 'alunos-options', alunoSearch],
    queryFn: () => alunosApi.list({ page_size: 10, search: alunoSearch || undefined }).then((response) => response.data),
    staleTime: 60_000,
  })

  const { data: responsaveisData } = useQuery({
    queryKey: ['pedagogia', 'responsaveis-options', responsavelSearch],
    queryFn: () => usuariosApi.list({ page_size: 10, search: responsavelSearch || undefined }).then((response) => response.data),
    staleTime: 60_000,
  })

  const { data: selectedAtendimento, isLoading: isLoadingDetails, isError: isErrorDetails } = useQuery({
    queryKey: ['pedagogia-item', selectedAtendimentoId],
    queryFn: () => pedagogiaApi.get(selectedAtendimentoId).then((response) => response.data),
    enabled: Boolean(selectedAtendimentoId),
    staleTime: 30_000,
  })

  const { data: editingAtendimento } = useQuery({
    queryKey: ['pedagogia-edit', editingAtendimentoId],
    queryFn: () => pedagogiaApi.get(editingAtendimentoId).then((response) => response.data),
    enabled: Boolean(editingAtendimentoId),
    staleTime: 0,
  })

  useEffect(() => {
    if (!editingAtendimento) return

    setFormData({
      aluno: editingAtendimento.aluno ? String(editingAtendimento.aluno) : '',
      pedagogia_responsavel: editingAtendimento.pedagogia_responsavel ? String(editingAtendimento.pedagogia_responsavel) : '',
      data_atendimento: editingAtendimento.data_atendimento || getTodayIsoDate(),
      diagnostico: editingAtendimento.diagnostico || '',
      plano_acao: editingAtendimento.plano_acao || '',
      status: editingAtendimento.status || 'RISCO_REPROVACAO',
    })
  }, [editingAtendimento])

  const saveMutation = useMutation({
    mutationFn: ({ id, payload }) => (id ? pedagogiaApi.patch(id, payload) : pedagogiaApi.create(payload)),
    onSuccess: (_response, variables) => {
      queryClient.invalidateQueries({ queryKey: ['pedagogia'] })
      if (variables.id) {
        queryClient.invalidateQueries({ queryKey: ['pedagogia-item', variables.id] })
      }

      toast.success(variables.id ? 'Atendimento atualizado com sucesso.' : 'Atendimento cadastrado com sucesso.')
      setCreating(false)
      setEditingAtendimentoId(null)
      setFormData(EMPTY_FORM)
    },
    onError: (error) => toast.error(getErrorMessage(error, 'Nao foi possivel salvar o atendimento pedagogico.')),
  })

  const deleteMutation = useMutation({
    mutationFn: (id) => pedagogiaApi.remove(id),
    onSuccess: (_response, id) => {
      queryClient.invalidateQueries({ queryKey: ['pedagogia'] })
      queryClient.invalidateQueries({ queryKey: ['pedagogia-item', id] })
      setSelectedAtendimentoId((current) => (current === id ? null : current))
      setEditingAtendimentoId((current) => (current === id ? null : current))
      toast.success('Atendimento removido com sucesso.')
    },
    onError: (error) => toast.error(getErrorMessage(error, 'Nao foi possivel remover o atendimento.')),
  })

  const alunos = alunosData?.results || []
  const responsaveis = useMemo(
    () => (responsaveisData?.results || []).filter((item) => item.tipo !== 'ALUNO'),
    [responsaveisData],
  )

  const selectedAlunoOption = formData.aluno && editingAtendimento
    ? {
        id: editingAtendimento.aluno,
        nome_completo: editingAtendimento.aluno_nome,
        username: '',
      }
    : null

  const selectedResponsavelOption = formData.pedagogia_responsavel && editingAtendimento
    ? {
        id: editingAtendimento.pedagogia_responsavel,
        nome_completo: editingAtendimento.pedagogia_responsavel_nome,
        username: '',
      }
    : null

  const isFormVisible = creating || Boolean(editingAtendimentoId)
  const formTitle = creating ? 'Novo atendimento pedagogico' : 'Editar atendimento pedagogico'
  const formSubtitle = creating
    ? 'Registre acompanhamento de alunos em risco, plano de recuperacao e apoio psicopedagogico.'
    : 'Atualize os dados do atendimento pedagogico selecionado.'
  const submitLabel = creating ? 'Cadastrar atendimento' : 'Salvar alteracoes'

  const detailsFields = selectedAtendimento
    ? [
        { label: 'ID', value: selectedAtendimento.id },
        { label: 'Aluno', value: selectedAtendimento.aluno_nome },
        { label: 'Pedagogia responsavel', value: selectedAtendimento.pedagogia_responsavel_nome || '-' },
        { label: 'Data do atendimento', value: formatDate(selectedAtendimento.data_atendimento) },
        { label: 'Status', value: selectedAtendimento.status_display || selectedAtendimento.status },
        { label: 'Diagnostico', value: selectedAtendimento.diagnostico || '-' },
        { label: 'Plano de acao', value: selectedAtendimento.plano_acao || '-' },
      ]
    : []

  const openCreateForm = () => {
    setSelectedAtendimentoId(null)
    setEditingAtendimentoId(null)
    setCreating(true)
    setFormData({
      ...EMPTY_FORM,
      data_atendimento: getTodayIsoDate(),
    })
  }

  const openEditForm = (id) => {
    setSelectedAtendimentoId(null)
    setCreating(false)
    setEditingAtendimentoId(id)
  }

  const closeForm = () => {
    setCreating(false)
    setEditingAtendimentoId(null)
    setFormData(EMPTY_FORM)
  }

  return (
    <div className="page">
      <div className="page-header">
        <h1 className="page-title">Pedagogia</h1>
        <div className="page-header__actions">
          <select className="select" value={statusFilter} onChange={(event) => { setStatusFilter(event.target.value); setPage(1) }}>
            <option value="">Todos os status</option>
            {STATUS_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>{option.label}</option>
            ))}
          </select>
          <button type="button" className="btn btn--primary" onClick={openCreateForm}>
            <Plus size={16} /> Novo atendimento
          </button>
        </div>
      </div>

      {isError ? (
        <div className="alert alert--error">
          Nao foi possivel carregar os atendimentos pedagogicos.
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
        searchPlaceholder="Buscar por aluno, responsavel, diagnostico ou plano..."
        emptyMessage="Nenhum atendimento pedagogico encontrado."
        rowActions={(row) => (
          <div className="table-actions">
            <button type="button" className="btn btn--outline btn--sm" onClick={() => setSelectedAtendimentoId(row.id)}>
              <Eye size={14} /> Detalhes
            </button>
            <button type="button" className="btn btn--secondary btn--sm" onClick={() => openEditForm(row.id)}>
              <Pencil size={14} /> Editar
            </button>
            <button
              type="button"
              className="btn btn--danger btn--sm"
              onClick={() => window.confirm(`Excluir o atendimento de ${row.aluno_nome}?`) && deleteMutation.mutate(row.id)}
            >
              <Trash2 size={14} /> Excluir
            </button>
          </div>
        )}
      />

      {selectedAtendimentoId ? (
        <EntityDetailsPanel
          title="Detalhes do atendimento"
          subtitle={selectedAtendimento?.aluno_nome || 'Consultando atendimento selecionado'}
          fields={detailsFields}
          isLoading={isLoadingDetails}
          errorMessage={isErrorDetails ? 'Nao foi possivel carregar os detalhes deste atendimento.' : ''}
          onClose={() => setSelectedAtendimentoId(null)}
        />
      ) : null}

      {isFormVisible ? (
        <EntityFormPanel
          title={formTitle}
          subtitle={formSubtitle}
          onSubmit={(event) => {
            event.preventDefault()

            if (!formData.aluno || !formData.pedagogia_responsavel || !formData.data_atendimento || !formData.diagnostico.trim() || !formData.plano_acao.trim()) {
              toast.error('Preencha aluno, responsavel, data, diagnostico e plano de acao.')
              return
            }

            saveMutation.mutate({
              id: editingAtendimentoId || undefined,
              payload: {
                aluno: Number(formData.aluno),
                pedagogia_responsavel: Number(formData.pedagogia_responsavel),
                data_atendimento: formData.data_atendimento,
                diagnostico: formData.diagnostico.trim(),
                plano_acao: formData.plano_acao.trim(),
                status: formData.status,
              },
            })
          }}
          onCancel={closeForm}
          submitLabel={submitLabel}
          isSubmitting={saveMutation.isPending}
        >
          <SearchableRemoteSelect
            id="pedagogia-aluno"
            label="Aluno"
            searchLabel="Buscar aluno"
            searchPlaceholder="Digite nome, usuario ou CPF"
            searchValue={alunoSearch}
            onSearchChange={setAlunoSearch}
            value={formData.aluno}
            onChange={(nextValue) => setFormData((current) => ({ ...current, aluno: nextValue }))}
            options={alunos}
            selectedOption={selectedAlunoOption}
            getOptionLabel={(item) => item.username ? `${item.nome_completo} - ${item.username}` : item.nome_completo}
            emptyOptionLabel="Selecione um aluno"
          />

          <SearchableRemoteSelect
            id="pedagogia-responsavel"
            label="Pedagogia responsavel"
            searchLabel="Buscar responsavel"
            searchPlaceholder="Digite nome, usuario ou CPF"
            searchValue={responsavelSearch}
            onSearchChange={setResponsavelSearch}
            value={formData.pedagogia_responsavel}
            onChange={(nextValue) => setFormData((current) => ({ ...current, pedagogia_responsavel: nextValue }))}
            options={responsaveis}
            selectedOption={selectedResponsavelOption}
            getOptionLabel={(item) => item.username ? `${item.nome_completo} - ${item.username}` : item.nome_completo}
            emptyOptionLabel="Selecione um responsavel"
          />

          <div className="form-field">
            <label htmlFor="pedagogia-data-atendimento">Data do atendimento</label>
            <input
              id="pedagogia-data-atendimento"
              type="date"
              className="form-control"
              value={formData.data_atendimento}
              onChange={(event) => setFormData((current) => ({ ...current, data_atendimento: event.target.value }))}
            />
          </div>

          <div className="form-field">
            <label htmlFor="pedagogia-status">Status</label>
            <select
              id="pedagogia-status"
              className="select"
              value={formData.status}
              onChange={(event) => setFormData((current) => ({ ...current, status: event.target.value }))}
            >
              {STATUS_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>{option.label}</option>
              ))}
            </select>
          </div>

          <div className="form-field form-field--full">
            <label htmlFor="pedagogia-diagnostico">Diagnostico</label>
            <textarea
              id="pedagogia-diagnostico"
              className="form-control"
              rows={4}
              value={formData.diagnostico}
              onChange={(event) => setFormData((current) => ({ ...current, diagnostico: event.target.value }))}
            />
          </div>

          <div className="form-field form-field--full">
            <label htmlFor="pedagogia-plano-acao">Plano de acao</label>
            <textarea
              id="pedagogia-plano-acao"
              className="form-control"
              rows={4}
              value={formData.plano_acao}
              onChange={(event) => setFormData((current) => ({ ...current, plano_acao: event.target.value }))}
            />
          </div>
        </EntityFormPanel>
      ) : null}

      {data ? (
        <div className="pagination">
          <button className="btn btn--secondary" disabled={!data.previous} onClick={() => setPage((current) => current - 1)}>Anterior</button>
          <span className="pagination__info">Pagina {page} - {data.count} registros</span>
          <button className="btn btn--secondary" disabled={!data.next} onClick={() => setPage((current) => current + 1)}>Proxima</button>
        </div>
      ) : null}
    </div>
  )
}
