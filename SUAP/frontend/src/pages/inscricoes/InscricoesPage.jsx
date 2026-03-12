import { useEffect, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Eye, Pencil, Plus, Trash2 } from 'lucide-react'
import toast from 'react-hot-toast'
import { useNavigate, useSearchParams } from 'react-router-dom'

import { cursosApi, inscricoesApi, publicacoesApi } from '@/api/endpoints'
import DataTable from '@/components/ui/DataTable'
import EntityDetailsPanel from '@/components/ui/EntityDetailsPanel'
import EntityFormPanel from '@/components/ui/EntityFormPanel'
import SearchableRemoteSelect from '@/components/ui/SearchableRemoteSelect'
import ProcessosSeletivosTabs from '@/pages/inscricoes/ProcessosSeletivosTabs'

const TAB_PUBLICACOES = 'publicacoes'
const TAB_INSCRICOES = 'inscricoes'

const PUBLICACAO_STATUS_BADGE = {
  RASCUNHO: 'badge--secondary',
  PUBLICADO: 'badge--success',
  ENCERRADO: 'badge--danger',
}

const INSCRICAO_STATUS_BADGE = {
  PENDENTE: 'badge--warning',
  VALIDADA: 'badge--success',
  INDEFERIDA: 'badge--danger',
}

const PUBLICACAO_STATUS_OPTIONS = [
  { value: 'RASCUNHO', label: 'Rascunho' },
  { value: 'PUBLICADO', label: 'Publicado' },
  { value: 'ENCERRADO', label: 'Encerrado' },
]

const INSCRICAO_STATUS_OPTIONS = [
  { value: 'PENDENTE', label: 'Pendente de validação' },
  { value: 'VALIDADA', label: 'Validada' },
  { value: 'INDEFERIDA', label: 'Indeferida' },
]

const DEFAULT_PUBLICACAO_FORM = {
  curso: '',
  titulo: '',
  descricao: '',
  vagas: '0',
  data_inicio: '',
  data_fim: '',
  status: 'RASCUNHO',
}

const DEFAULT_INSCRICAO_FORM = {
  publicacao: '',
  nome_candidato: '',
  cpf: '',
  email: '',
  telefone: '',
  data_nascimento: '',
  status: 'PENDENTE',
  observacao: '',
}

const PUBLICACOES_COLUMNS = [
  { key: 'titulo', label: 'Edital' },
  { key: 'curso_nome', label: 'Curso' },
  { key: 'vagas', label: 'Vagas' },
  { key: 'data_inicio', label: 'Início', render: (row) => formatDate(row.data_inicio) },
  { key: 'data_fim', label: 'Fim', render: (row) => formatDate(row.data_fim) },
  {
    key: 'status',
    label: 'Status',
    render: (row) => (
      <span className={`badge ${PUBLICACAO_STATUS_BADGE[row.status] || ''}`}>
        {row.status_display || row.status}
      </span>
    ),
  },
]

const INSCRICOES_COLUMNS = [
  { key: 'numero_inscricao', label: 'Número' },
  { key: 'nome_candidato', label: 'Candidato' },
  { key: 'publicacao_titulo', label: 'Edital' },
  { key: 'curso_nome', label: 'Curso' },
  { key: 'data_inscricao', label: 'Data', render: (row) => formatDateTime(row.data_inscricao) },
  {
    key: 'status',
    label: 'Status',
    render: (row) => (
      <span className={`badge ${INSCRICAO_STATUS_BADGE[row.status] || ''}`}>
        {row.status_display || row.status}
      </span>
    ),
  },
]

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

export default function InscricoesPage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [searchParams, setSearchParams] = useSearchParams()
  const activeTab = searchParams.get('aba') === TAB_PUBLICACOES ? TAB_PUBLICACOES : TAB_INSCRICOES

  const [publicacaoSearch, setPublicacaoSearch] = useState('')
  const [publicacaoStatusFilter, setPublicacaoStatusFilter] = useState('')
  const [publicacaoPage, setPublicacaoPage] = useState(1)
  const [selectedPublicacaoId, setSelectedPublicacaoId] = useState(null)
  const [editingPublicacaoId, setEditingPublicacaoId] = useState(null)
  const [publicacaoForm, setPublicacaoForm] = useState(DEFAULT_PUBLICACAO_FORM)
  const [cursoSearch, setCursoSearch] = useState('')

  const [inscricaoSearch, setInscricaoSearch] = useState('')
  const [inscricaoStatusFilter, setInscricaoStatusFilter] = useState('')
  const [inscricaoPage, setInscricaoPage] = useState(1)
  const [selectedInscricaoId, setSelectedInscricaoId] = useState(null)
  const [editingInscricaoId, setEditingInscricaoId] = useState(null)
  const [inscricaoForm, setInscricaoForm] = useState(DEFAULT_INSCRICAO_FORM)
  const [editalSearch, setEditalSearch] = useState('')

  const { data: publicacoesData, isLoading: isLoadingPublicacoes, isError: isErrorPublicacoes } = useQuery({
    queryKey: ['publicacoes', { search: publicacaoSearch, status: publicacaoStatusFilter, page: publicacaoPage }],
    queryFn: () => publicacoesApi.list({ search: publicacaoSearch, status: publicacaoStatusFilter || undefined, page: publicacaoPage }).then((response) => response.data),
    staleTime: 30_000,
  })

  const { data: inscricoesData, isLoading: isLoadingInscricoes, isError: isErrorInscricoes } = useQuery({
    queryKey: ['inscricoes', { search: inscricaoSearch, status: inscricaoStatusFilter, page: inscricaoPage }],
    queryFn: () => inscricoesApi.list({ search: inscricaoSearch, status: inscricaoStatusFilter || undefined, page: inscricaoPage }).then((response) => response.data),
    staleTime: 30_000,
  })

  const { data: cursosData } = useQuery({
    queryKey: ['cursos', 'publicacoes-options', cursoSearch],
    queryFn: () => cursosApi.list({ page_size: 10, search: cursoSearch || undefined }).then((response) => response.data),
    staleTime: 60_000,
  })

  const { data: editaisData } = useQuery({
    queryKey: ['publicacoes', 'inscricoes-options', editalSearch],
    queryFn: () => publicacoesApi.list({ page_size: 10, search: editalSearch || undefined }).then((response) => response.data),
    staleTime: 60_000,
  })

  const { data: selectedPublicacao, isLoading: isLoadingPublicacaoDetails, isError: isErrorPublicacaoDetails } = useQuery({
    queryKey: ['publicacao', selectedPublicacaoId],
    queryFn: () => publicacoesApi.get(selectedPublicacaoId).then((response) => response.data),
    enabled: Boolean(selectedPublicacaoId),
    staleTime: 30_000,
  })

  const { data: editingPublicacao } = useQuery({
    queryKey: ['publicacao-edit', editingPublicacaoId],
    queryFn: () => publicacoesApi.get(editingPublicacaoId).then((response) => response.data),
    enabled: Boolean(editingPublicacaoId),
    staleTime: 0,
  })

  const { data: selectedInscricao, isLoading: isLoadingInscricaoDetails, isError: isErrorInscricaoDetails } = useQuery({
    queryKey: ['inscricao', selectedInscricaoId],
    queryFn: () => inscricoesApi.get(selectedInscricaoId).then((response) => response.data),
    enabled: Boolean(selectedInscricaoId),
    staleTime: 30_000,
  })

  const { data: editingInscricao } = useQuery({
    queryKey: ['inscricao-edit', editingInscricaoId],
    queryFn: () => inscricoesApi.get(editingInscricaoId).then((response) => response.data),
    enabled: Boolean(editingInscricaoId),
    staleTime: 0,
  })

  useEffect(() => {
    if (activeTab !== TAB_PUBLICACOES) return
    navigate('/inscricoes/editais', { replace: true })
  }, [activeTab, navigate])

  useEffect(() => {
    if (!editingPublicacao) return

    setPublicacaoForm({
      curso: editingPublicacao.curso ? String(editingPublicacao.curso) : '',
      titulo: editingPublicacao.titulo || '',
      descricao: editingPublicacao.descricao || '',
      vagas: String(editingPublicacao.vagas ?? 0),
      data_inicio: editingPublicacao.data_inicio || '',
      data_fim: editingPublicacao.data_fim || '',
      status: editingPublicacao.status || 'RASCUNHO',
    })
  }, [editingPublicacao])

  useEffect(() => {
    if (!editingInscricao) return

    setInscricaoForm({
      publicacao: editingInscricao.publicacao ? String(editingInscricao.publicacao) : '',
      nome_candidato: editingInscricao.nome_candidato || '',
      cpf: editingInscricao.cpf || '',
      email: editingInscricao.email || '',
      telefone: editingInscricao.telefone || '',
      data_nascimento: editingInscricao.data_nascimento || '',
      status: editingInscricao.status || 'PENDENTE',
      observacao: editingInscricao.observacao || '',
    })
  }, [editingInscricao])

  const savePublicacaoMutation = useMutation({
    mutationFn: ({ id, payload }) => (id ? publicacoesApi.patch(id, payload) : publicacoesApi.create(payload)),
    onSuccess: (_response, variables) => {
      queryClient.invalidateQueries({ queryKey: ['publicacoes'] })
      if (variables.id) {
        queryClient.invalidateQueries({ queryKey: ['publicacao', variables.id] })
      }
      toast.success(variables.id ? 'Edital atualizado com sucesso.' : 'Edital criado com sucesso.')
      setEditingPublicacaoId(null)
      setPublicacaoForm(DEFAULT_PUBLICACAO_FORM)
    },
    onError: (error) => toast.error(getErrorMessage(error, 'Nao foi possivel salvar o edital.')),
  })

  const deletePublicacaoMutation = useMutation({
    mutationFn: (id) => publicacoesApi.remove(id),
    onSuccess: (_response, id) => {
      queryClient.invalidateQueries({ queryKey: ['publicacoes'] })
      queryClient.invalidateQueries({ queryKey: ['publicacao', id] })
      setSelectedPublicacaoId((current) => (current === id ? null : current))
      setEditingPublicacaoId((current) => (current === id ? null : current))
      setPublicacaoForm(DEFAULT_PUBLICACAO_FORM)
      toast.success('Edital excluido com sucesso.')
    },
    onError: (error) => toast.error(getErrorMessage(error, 'Nao foi possivel excluir o edital.')),
  })

  const saveInscricaoMutation = useMutation({
    mutationFn: ({ id, payload }) => (id ? inscricoesApi.patch(id, payload) : inscricoesApi.create(payload)),
    onSuccess: (_response, variables) => {
      queryClient.invalidateQueries({ queryKey: ['inscricoes'] })
      if (variables.id) {
        queryClient.invalidateQueries({ queryKey: ['inscricao', variables.id] })
      }
      toast.success(variables.id ? 'Inscricao atualizada com sucesso.' : 'Inscricao criada com sucesso.')
      setEditingInscricaoId(null)
      setInscricaoForm(DEFAULT_INSCRICAO_FORM)
    },
    onError: (error) => toast.error(getErrorMessage(error, 'Nao foi possivel salvar a inscricao.')),
  })

  const deleteInscricaoMutation = useMutation({
    mutationFn: (id) => inscricoesApi.remove(id),
    onSuccess: (_response, id) => {
      queryClient.invalidateQueries({ queryKey: ['inscricoes'] })
      queryClient.invalidateQueries({ queryKey: ['inscricao', id] })
      setSelectedInscricaoId((current) => (current === id ? null : current))
      setEditingInscricaoId((current) => (current === id ? null : current))
      setInscricaoForm(DEFAULT_INSCRICAO_FORM)
      toast.success('Inscricao excluida com sucesso.')
    },
    onError: (error) => toast.error(getErrorMessage(error, 'Nao foi possivel excluir a inscricao.')),
  })

  const cursos = cursosData?.results || []
  const editais = editaisData?.results || []

  const selectedCursoOption = publicacaoForm.curso && editingPublicacao ? {
    id: editingPublicacao.curso,
    nome: editingPublicacao.curso_nome,
  } : null

  const selectedEditalOption = inscricaoForm.publicacao && editingInscricao ? {
    id: editingInscricao.publicacao,
    titulo: editingInscricao.publicacao_titulo,
    curso_nome: editingInscricao.curso_nome,
  } : null

  const publicacaoDetailsFields = selectedPublicacao ? [
    { label: 'ID', value: selectedPublicacao.id },
    { label: 'Título', value: selectedPublicacao.titulo },
    { label: 'Curso', value: selectedPublicacao.curso_nome },
    { label: 'Vagas', value: selectedPublicacao.vagas },
    { label: 'Início', value: formatDate(selectedPublicacao.data_inicio) },
    { label: 'Fim', value: formatDate(selectedPublicacao.data_fim) },
    { label: 'Status', value: selectedPublicacao.status_display },
    { label: 'Publicado por', value: selectedPublicacao.publicado_por_nome || '-' },
    { label: 'Inscrições', value: selectedPublicacao.inscricoes_count ?? 0 },
    { label: 'Descrição', value: selectedPublicacao.descricao || '-' },
  ] : []

  const inscricaoDetailsFields = selectedInscricao ? [
    { label: 'ID', value: selectedInscricao.id },
    { label: 'Número', value: selectedInscricao.numero_inscricao },
    { label: 'Candidato', value: selectedInscricao.nome_candidato },
    { label: 'CPF', value: selectedInscricao.cpf },
    { label: 'E-mail', value: selectedInscricao.email },
    { label: 'Telefone', value: selectedInscricao.telefone || '-' },
    { label: 'Data de nascimento', value: formatDate(selectedInscricao.data_nascimento) },
    { label: 'Edital', value: selectedInscricao.publicacao_titulo },
    { label: 'Curso', value: selectedInscricao.curso_nome },
    { label: 'Status', value: selectedInscricao.status_display },
    { label: 'Data da inscrição', value: formatDateTime(selectedInscricao.data_inscricao) },
    { label: 'Observação', value: selectedInscricao.observacao || '-' },
  ] : []

  const activeData = activeTab === TAB_PUBLICACOES ? publicacoesData : inscricoesData
  const activeColumns = activeTab === TAB_PUBLICACOES ? PUBLICACOES_COLUMNS : INSCRICOES_COLUMNS
  const activeLoading = activeTab === TAB_PUBLICACOES ? isLoadingPublicacoes : isLoadingInscricoes
  const activeSearchPlaceholder = activeTab === TAB_PUBLICACOES ? 'Buscar edital...' : 'Buscar por número, candidato, CPF ou edital...'
  const activeEmptyMessage = activeTab === TAB_PUBLICACOES ? 'Nenhum edital encontrado.' : 'Nenhuma inscricao encontrada.'

  return (
    <div className="page">
      <div className="page-header processos-seletivos-page__header">
        <div>
          <h1 className="page-title">Processos seletivos</h1>
          <p className="page-subtitle">Gerencie inscrições e editais a partir de uma navegação única do módulo.</p>
        </div>
        <div className="page-header__actions">
          {activeTab === TAB_PUBLICACOES ? (
            <>
              <select
                className="select"
                value={publicacaoStatusFilter}
                onChange={(event) => { setPublicacaoStatusFilter(event.target.value); setPublicacaoPage(1) }}
              >
                <option value="">Todos os status</option>
                {PUBLICACAO_STATUS_OPTIONS.map((option) => (
                  <option key={option.value} value={option.value}>{option.label}</option>
                ))}
              </select>
              <button type="button" className="btn btn--primary" onClick={() => navigate('/inscricoes/editais/novo')}>
                <Plus size={16} /> Novo Edital
              </button>
            </>
          ) : (
            <>
              <select
                className="select"
                value={inscricaoStatusFilter}
                onChange={(event) => { setInscricaoStatusFilter(event.target.value); setInscricaoPage(1) }}
              >
                <option value="">Todos os status</option>
                {INSCRICAO_STATUS_OPTIONS.map((option) => (
                  <option key={option.value} value={option.value}>{option.label}</option>
                ))}
              </select>
              <button type="button" className="btn btn--primary" onClick={() => navigate('/inscricoes/nova')}>
                <Plus size={16} /> Nova Inscrição
              </button>
            </>
          )}
        </div>
      </div>

      <ProcessosSeletivosTabs activeTab="inscricoes" />

      {activeTab === TAB_PUBLICACOES && isErrorPublicacoes ? <div className="alert alert--error">Nao foi possivel carregar os editais.</div> : null}
      {activeTab === TAB_INSCRICOES && isErrorInscricoes ? <div className="alert alert--error">Nao foi possivel carregar as inscricoes.</div> : null}

      <DataTable
        columns={activeColumns}
        data={activeData}
        isLoading={activeLoading}
        onSearch={(value) => {
          if (activeTab === TAB_PUBLICACOES) {
            setPublicacaoSearch(value)
            setPublicacaoPage(1)
            return
          }

          setInscricaoSearch(value)
          setInscricaoPage(1)
        }}
        searchPlaceholder={activeSearchPlaceholder}
        emptyMessage={activeEmptyMessage}
        rowActions={(row) => (
          <div className="table-actions">
            {activeTab === TAB_PUBLICACOES ? (
              <>
                <button type="button" className="btn btn--outline btn--sm" onClick={() => setSelectedPublicacaoId(row.id)}>
                  <Eye size={14} /> Detalhes
                </button>
                <button type="button" className="btn btn--secondary btn--sm" onClick={() => { setSelectedPublicacaoId(null); setEditingPublicacaoId(row.id) }}>
                  <Pencil size={14} /> Editar
                </button>
                <button type="button" className="btn btn--danger btn--sm" onClick={() => window.confirm(`Excluir o edital ${row.titulo}?`) && deletePublicacaoMutation.mutate(row.id)}>
                  <Trash2 size={14} /> Excluir
                </button>
              </>
            ) : (
              <>
                <button type="button" className="btn btn--outline btn--sm" onClick={() => setSelectedInscricaoId(row.id)}>
                  <Eye size={14} /> Detalhes
                </button>
                <button type="button" className="btn btn--secondary btn--sm" onClick={() => { setSelectedInscricaoId(null); setEditingInscricaoId(row.id) }}>
                  <Pencil size={14} /> Editar
                </button>
                <button type="button" className="btn btn--danger btn--sm" onClick={() => window.confirm(`Excluir a inscricao ${row.numero_inscricao}?`) && deleteInscricaoMutation.mutate(row.id)}>
                  <Trash2 size={14} /> Excluir
                </button>
              </>
            )}
          </div>
        )}
      />

      {selectedPublicacaoId ? (
        <EntityDetailsPanel
          title="Detalhes do edital"
          subtitle={selectedPublicacao?.titulo || 'Consultando edital selecionado'}
          fields={publicacaoDetailsFields}
          isLoading={isLoadingPublicacaoDetails}
          errorMessage={isErrorPublicacaoDetails ? 'Nao foi possivel carregar os detalhes deste edital.' : ''}
          onClose={() => setSelectedPublicacaoId(null)}
        />
      ) : null}

      {selectedInscricaoId ? (
        <EntityDetailsPanel
          title="Detalhes da inscricao"
          subtitle={selectedInscricao?.numero_inscricao || 'Consultando inscricao selecionada'}
          fields={inscricaoDetailsFields}
          isLoading={isLoadingInscricaoDetails}
          errorMessage={isErrorInscricaoDetails ? 'Nao foi possivel carregar os detalhes desta inscricao.' : ''}
          onClose={() => setSelectedInscricaoId(null)}
        />
      ) : null}

      {editingPublicacaoId ? (
        <EntityFormPanel
          title="Editar edital"
          subtitle="Defina curso, período de inscrição, vagas e status de publicação."
          onSubmit={(event) => {
            event.preventDefault()

            if (!publicacaoForm.curso || !publicacaoForm.titulo.trim() || !publicacaoForm.data_inicio || !publicacaoForm.data_fim) {
              toast.error('Informe curso, título, início e fim do edital.')
              return
            }

            savePublicacaoMutation.mutate({
              id: editingPublicacaoId,
              payload: {
                curso: Number(publicacaoForm.curso),
                titulo: publicacaoForm.titulo.trim(),
                descricao: publicacaoForm.descricao.trim(),
                vagas: Number(publicacaoForm.vagas || 0),
                data_inicio: publicacaoForm.data_inicio,
                data_fim: publicacaoForm.data_fim,
                status: publicacaoForm.status,
              },
            })
          }}
          onCancel={() => { setEditingPublicacaoId(null); setPublicacaoForm(DEFAULT_PUBLICACAO_FORM) }}
          submitLabel="Salvar alteracoes"
          isSubmitting={savePublicacaoMutation.isPending}
        >
          <SearchableRemoteSelect
            id="publicacao-curso"
            label="Curso"
            searchLabel="Buscar curso"
            searchPlaceholder="Digite nome ou sigla do curso"
            searchValue={cursoSearch}
            onSearchChange={setCursoSearch}
            value={publicacaoForm.curso}
            onChange={(nextValue) => setPublicacaoForm((current) => ({ ...current, curso: nextValue }))}
            options={cursos}
            selectedOption={selectedCursoOption}
            getOptionLabel={(item) => `${item.nome}${item.sigla ? ` - ${item.sigla}` : ''}`}
          />

          <div className="form-field form-field--full">
            <label htmlFor="publicacao-titulo">Título do edital</label>
            <input id="publicacao-titulo" className="form-control" value={publicacaoForm.titulo} onChange={(event) => setPublicacaoForm((current) => ({ ...current, titulo: event.target.value }))} />
          </div>

          <div className="form-field">
            <label htmlFor="publicacao-vagas">Vagas</label>
            <input id="publicacao-vagas" type="number" min="0" className="form-control" value={publicacaoForm.vagas} onChange={(event) => setPublicacaoForm((current) => ({ ...current, vagas: event.target.value }))} />
          </div>

          <div className="form-field">
            <label htmlFor="publicacao-status">Status</label>
            <select id="publicacao-status" className="select" value={publicacaoForm.status} onChange={(event) => setPublicacaoForm((current) => ({ ...current, status: event.target.value }))}>
              {PUBLICACAO_STATUS_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>{option.label}</option>
              ))}
            </select>
          </div>

          <div className="form-field">
            <label htmlFor="publicacao-data-inicio">Início das inscrições</label>
            <input id="publicacao-data-inicio" type="date" className="form-control" value={publicacaoForm.data_inicio} onChange={(event) => setPublicacaoForm((current) => ({ ...current, data_inicio: event.target.value }))} />
          </div>

          <div className="form-field">
            <label htmlFor="publicacao-data-fim">Fim das inscrições</label>
            <input id="publicacao-data-fim" type="date" className="form-control" value={publicacaoForm.data_fim} onChange={(event) => setPublicacaoForm((current) => ({ ...current, data_fim: event.target.value }))} />
          </div>

          <div className="form-field form-field--full">
            <label htmlFor="publicacao-descricao">Descrição / requisitos</label>
            <textarea id="publicacao-descricao" className="form-control" rows={4} value={publicacaoForm.descricao} onChange={(event) => setPublicacaoForm((current) => ({ ...current, descricao: event.target.value }))} />
          </div>
        </EntityFormPanel>
      ) : null}

      {editingInscricaoId ? (
        <EntityFormPanel
          title="Editar inscricao"
          subtitle="Associe o candidato a um edital e registre os dados básicos da inscrição."
          onSubmit={(event) => {
            event.preventDefault()

            if (!inscricaoForm.publicacao || !inscricaoForm.nome_candidato.trim() || !inscricaoForm.cpf.trim() || !inscricaoForm.email.trim()) {
              toast.error('Informe edital, candidato, CPF e e-mail.')
              return
            }

            saveInscricaoMutation.mutate({
              id: editingInscricaoId,
              payload: {
                publicacao: Number(inscricaoForm.publicacao),
                nome_candidato: inscricaoForm.nome_candidato.trim(),
                cpf: inscricaoForm.cpf.trim(),
                email: inscricaoForm.email.trim(),
                telefone: inscricaoForm.telefone.trim(),
                data_nascimento: inscricaoForm.data_nascimento || null,
                status: inscricaoForm.status,
                observacao: inscricaoForm.observacao.trim(),
              },
            })
          }}
          onCancel={() => { setEditingInscricaoId(null); setInscricaoForm(DEFAULT_INSCRICAO_FORM) }}
          submitLabel="Salvar alteracoes"
          isSubmitting={saveInscricaoMutation.isPending}
        >
          <SearchableRemoteSelect
            id="inscricao-edital"
            label="Edital"
            searchLabel="Buscar edital"
            searchPlaceholder="Digite título do edital"
            searchValue={editalSearch}
            onSearchChange={setEditalSearch}
            value={inscricaoForm.publicacao}
            onChange={(nextValue) => setInscricaoForm((current) => ({ ...current, publicacao: nextValue }))}
            options={editais}
            selectedOption={selectedEditalOption}
            getOptionLabel={(item) => `${item.titulo} - ${item.curso_nome}`}
          />

          <div className="form-field form-field--full">
            <label htmlFor="inscricao-candidato">Nome do candidato</label>
            <input id="inscricao-candidato" className="form-control" value={inscricaoForm.nome_candidato} onChange={(event) => setInscricaoForm((current) => ({ ...current, nome_candidato: event.target.value }))} />
          </div>

          <div className="form-field">
            <label htmlFor="inscricao-cpf">CPF</label>
            <input id="inscricao-cpf" className="form-control" value={inscricaoForm.cpf} onChange={(event) => setInscricaoForm((current) => ({ ...current, cpf: event.target.value }))} />
          </div>

          <div className="form-field">
            <label htmlFor="inscricao-email">E-mail</label>
            <input id="inscricao-email" type="email" className="form-control" value={inscricaoForm.email} onChange={(event) => setInscricaoForm((current) => ({ ...current, email: event.target.value }))} />
          </div>

          <div className="form-field">
            <label htmlFor="inscricao-telefone">Telefone</label>
            <input id="inscricao-telefone" className="form-control" value={inscricaoForm.telefone} onChange={(event) => setInscricaoForm((current) => ({ ...current, telefone: event.target.value }))} />
          </div>

          <div className="form-field">
            <label htmlFor="inscricao-data-nascimento">Data de nascimento</label>
            <input id="inscricao-data-nascimento" type="date" className="form-control" value={inscricaoForm.data_nascimento} onChange={(event) => setInscricaoForm((current) => ({ ...current, data_nascimento: event.target.value }))} />
          </div>

          <div className="form-field">
            <label htmlFor="inscricao-status">Status</label>
            <select id="inscricao-status" className="select" value={inscricaoForm.status} onChange={(event) => setInscricaoForm((current) => ({ ...current, status: event.target.value }))}>
              {INSCRICAO_STATUS_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>{option.label}</option>
              ))}
            </select>
          </div>

          <div className="form-field form-field--full">
            <label htmlFor="inscricao-observacao">Observação</label>
            <textarea id="inscricao-observacao" className="form-control" rows={4} value={inscricaoForm.observacao} onChange={(event) => setInscricaoForm((current) => ({ ...current, observacao: event.target.value }))} />
          </div>
        </EntityFormPanel>
      ) : null}

      {activeData ? (
        <div className="pagination">
          <button
            className="btn btn--secondary"
            disabled={!activeData.previous}
            onClick={() => {
              if (activeTab === TAB_PUBLICACOES) {
                setPublicacaoPage((current) => current - 1)
                return
              }

              setInscricaoPage((current) => current - 1)
            }}
          >
            Anterior
          </button>
          <span className="pagination__info">
            Página {activeTab === TAB_PUBLICACOES ? publicacaoPage : inscricaoPage} — {activeData.count} registros
          </span>
          <button
            className="btn btn--secondary"
            disabled={!activeData.next}
            onClick={() => {
              if (activeTab === TAB_PUBLICACOES) {
                setPublicacaoPage((current) => current + 1)
                return
              }

              setInscricaoPage((current) => current + 1)
            }}
          >
            Próxima
          </button>
        </div>
      ) : null}
    </div>
  )
}
