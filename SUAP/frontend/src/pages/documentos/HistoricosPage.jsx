import { useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Eye, FileDown, FilePlus2, RefreshCcw, ShieldX } from 'lucide-react'
import toast from 'react-hot-toast'

import { historicosApi, matriculasApi } from '@/api/endpoints'
import DataTable from '@/components/ui/DataTable'
import EntityDetailsPanel from '@/components/ui/EntityDetailsPanel'
import EntityFormPanel from '@/components/ui/EntityFormPanel'
import SearchableRemoteSelect from '@/components/ui/SearchableRemoteSelect'

const COLUMNS = [
  { key: 'numero_registro', label: 'Registro' },
  { key: 'aluno_nome', label: 'Aluno' },
  { key: 'cpf_aluno', label: 'CPF' },
  { key: 'matricula_numero', label: 'Matricula' },
  { key: 'curso_nome', label: 'Curso' },
  { key: 'versao', label: 'Versao' },
  { key: 'status_display', label: 'Status' },
  { key: 'data_emissao', label: 'Emissao' },
]

function formatDateTime(value) {
  if (!value) return '-'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return new Intl.DateTimeFormat('pt-BR', { dateStyle: 'short', timeStyle: 'short' }).format(date)
}

function formatDate(value) {
  if (!value) return '-'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return new Intl.DateTimeFormat('pt-BR', { dateStyle: 'short' }).format(date)
}

function getApiError(error, fallback) {
  return error?.response?.data?.detail || fallback
}

export default function HistoricosPage() {
  const queryClient = useQueryClient()
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [page, setPage] = useState(1)
  const [selectedId, setSelectedId] = useState(null)
  const [emissaoOpen, setEmissaoOpen] = useState(false)
  const [matriculaSearch, setMatriculaSearch] = useState('')
  const [matriculaId, setMatriculaId] = useState('')

  const { data, isLoading, isError } = useQuery({
    queryKey: ['historicos-tecnicos', { search, statusFilter, page }],
    queryFn: () =>
      historicosApi
        .list({ search: search || undefined, status: statusFilter || undefined, page })
        .then((response) => response.data),
    staleTime: 30_000,
  })

  const { data: selectedItem, isLoading: selectedLoading } = useQuery({
    queryKey: ['historico-tecnico', selectedId],
    queryFn: () => historicosApi.get(selectedId).then((response) => response.data),
    enabled: Boolean(selectedId),
  })

  const { data: matriculasData } = useQuery({
    queryKey: ['historico-matriculas-opcoes', matriculaSearch],
    queryFn: () =>
      matriculasApi
        .list({ search: matriculaSearch || undefined, page_size: 12 })
        .then((response) => response.data),
    staleTime: 60_000,
  })

  const { data: previewData, isFetching: previewLoading } = useQuery({
    queryKey: ['historico-preview-emissao', matriculaId],
    queryFn: () => historicosApi.previewEmissao({ matricula_id: matriculaId }).then((response) => response.data),
    enabled: emissaoOpen && Boolean(matriculaId),
    retry: false,
  })

  const emitirMutation = useMutation({
    mutationFn: (payload) => historicosApi.emitir(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['historicos-tecnicos'] })
      toast.success('Historico emitido com sucesso.')
      setEmissaoOpen(false)
      setMatriculaId('')
      setMatriculaSearch('')
    },
    onError: (error) => toast.error(getApiError(error, 'Falha ao emitir historico.')),
  })

  const reemitirMutation = useMutation({
    mutationFn: ({ id, motivo }) => historicosApi.reemitir(id, { motivo }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['historicos-tecnicos'] })
      toast.success('Historico reemitido com sucesso.')
    },
    onError: (error) => toast.error(getApiError(error, 'Falha ao reemitir historico.')),
  })

  const cancelarMutation = useMutation({
    mutationFn: ({ id, motivo }) => historicosApi.cancelar(id, { motivo }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['historicos-tecnicos'] })
      toast.success('Historico cancelado com sucesso.')
      setSelectedId(null)
    },
    onError: (error) => toast.error(getApiError(error, 'Falha ao cancelar historico.')),
  })

  const matriculaOptions = useMemo(() => matriculasData?.results || [], [matriculasData])

  const downloadPdf = async (id) => {
    try {
      const response = await historicosApi.pdf(id)
      const blob = new Blob([response.data], { type: 'application/pdf' })
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = `historico-${id}.pdf`
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)
    } catch (error) {
      toast.error(getApiError(error, 'Nao foi possivel baixar o PDF.'))
    }
  }

  return (
    <div className="page page--wide">
      <div className="page-header">
        <div>
          <h1 className="page-title">Historico Escolar Tecnico</h1>
          <p className="page-subtitle">Emissao, versionamento, validacao e auditoria de historicos oficiais.</p>
        </div>
        <div className="page-header__actions">
          <button type="button" className="btn btn--primary" onClick={() => setEmissaoOpen(true)}>
            <FilePlus2 size={16} /> Emitir historico
          </button>
        </div>
      </div>

      <div className="table-toolbar" style={{ marginBottom: '0.75rem', display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
        <label style={{ display: 'grid', gap: '0.35rem' }}>
          <span>Status</span>
          <select className="select" value={statusFilter} onChange={(event) => { setStatusFilter(event.target.value); setPage(1) }}>
            <option value="">Todos</option>
            <option value="RASCUNHO">Rascunho</option>
            <option value="EMITIDO">Emitido</option>
            <option value="CANCELADO">Cancelado</option>
            <option value="SUBSTITUIDO">Substituido</option>
          </select>
        </label>
      </div>

      {isError ? <div className="alert alert--error">Nao foi possivel carregar os historicos.</div> : null}

      <DataTable
        columns={COLUMNS}
        data={data}
        isLoading={isLoading}
        onSearch={(value) => {
          setSearch(value)
          setPage(1)
        }}
        searchPlaceholder="Buscar por aluno, CPF, matricula, curso ou numero de registro..."
        emptyMessage="Nenhum historico encontrado."
        rowActions={(row) => (
          <div className="table-actions">
            <button type="button" className="btn btn--outline btn--sm" onClick={() => setSelectedId(row.id)}>
              <Eye size={14} /> Visualizar
            </button>
            <button type="button" className="btn btn--secondary btn--sm" onClick={() => downloadPdf(row.id)}>
              <FileDown size={14} /> Gerar PDF
            </button>
            <button
              type="button"
              className="btn btn--secondary btn--sm"
              onClick={() => {
                const motivo = window.prompt('Motivo da reemissao:')
                if (!motivo) return
                reemitirMutation.mutate({ id: row.id, motivo })
              }}
              disabled={reemitirMutation.isPending}
            >
              <RefreshCcw size={14} /> Reemitir
            </button>
            <button
              type="button"
              className="btn btn--danger btn--sm"
              onClick={() => {
                const motivo = window.prompt('Motivo do cancelamento:')
                if (!motivo) return
                cancelarMutation.mutate({ id: row.id, motivo })
              }}
              disabled={cancelarMutation.isPending}
            >
              <ShieldX size={14} /> Cancelar
            </button>
          </div>
        )}
      />

      {data ? (
        <div className="pagination">
          <button className="btn btn--secondary" disabled={!data.previous} onClick={() => setPage((current) => current - 1)}>Anterior</button>
          <span className="pagination__info">Pagina {page} - {data.count} registros</span>
          <button className="btn btn--secondary" disabled={!data.next} onClick={() => setPage((current) => current + 1)}>Proxima</button>
        </div>
      ) : null}

      {selectedId ? (
        <EntityDetailsPanel
          title="Detalhes do historico"
          subtitle={selectedItem?.numero_registro || 'Historico escolar tecnico'}
          isLoading={selectedLoading}
          onClose={() => setSelectedId(null)}
          fields={selectedItem ? [
            { label: 'Registro', value: selectedItem.numero_registro },
            { label: 'Aluno', value: selectedItem.aluno_nome },
            { label: 'CPF', value: selectedItem.cpf_aluno },
            { label: 'Curso', value: selectedItem.curso_nome },
            { label: 'Eixo Tecnologico', value: selectedItem.eixo_tecnologico || '-' },
            { label: 'Matricula', value: selectedItem.matricula_numero },
            { label: 'Livro/Folha/Pagina', value: `${selectedItem.livro || '-'} / ${selectedItem.folha || '-'} / ${selectedItem.pagina || '-'}` },
            { label: 'Versao', value: selectedItem.versao },
            { label: 'Status', value: selectedItem.status_display },
            { label: 'Situacao final', value: selectedItem.situacao_final_display },
            { label: 'Carga horaria total', value: selectedItem.carga_horaria_total },
            { label: 'Data de conclusao', value: formatDate(selectedItem.data_conclusao) },
            { label: 'Data emissao', value: formatDateTime(selectedItem.data_emissao) },
            { label: 'Codigo validacao', value: selectedItem.codigo_validacao },
            { label: 'Hash', value: selectedItem.hash_documento },
            { label: 'Observacoes', value: selectedItem.observacoes || '-' },
          ] : []}
        />
      ) : null}

      {emissaoOpen ? (
        <EntityFormPanel
          title="Emitir historico escolar"
          subtitle="Selecione a matricula, confira o preview e confirme a emissao oficial."
          submitLabel="Emitir"
          isSubmitting={emitirMutation.isPending}
          onCancel={() => {
            setEmissaoOpen(false)
            setMatriculaId('')
            setMatriculaSearch('')
          }}
          onSubmit={(event) => {
            event.preventDefault()
            emitirMutation.mutate({ matricula_id: Number(matriculaId) })
          }}
        >
          <SearchableRemoteSelect
            id="historico-matricula-emissao"
            label="Matricula"
            searchLabel="Buscar matricula"
            searchPlaceholder="Digite nome do aluno, CPF ou matricula"
            searchValue={matriculaSearch}
            onSearchChange={setMatriculaSearch}
            value={matriculaId}
            onChange={setMatriculaId}
            options={matriculaOptions}
            getOptionLabel={(item) => `${item.numero_matricula} - ${item.aluno_nome} (${item.curso_nome})`}
          />

          {previewLoading ? <p>Carregando preview...</p> : null}

          {previewData ? (
            <div className="entity-details-grid" style={{ marginTop: '1rem' }}>
              <div className="entity-details-item"><span className="entity-details-item__label">Aluno</span><span className="entity-details-item__value">{previewData.aluno_nome}</span></div>
              <div className="entity-details-item"><span className="entity-details-item__label">CPF</span><span className="entity-details-item__value">{previewData.aluno_cpf}</span></div>
              <div className="entity-details-item"><span className="entity-details-item__label">Curso</span><span className="entity-details-item__value">{previewData.curso_nome}</span></div>
              <div className="entity-details-item"><span className="entity-details-item__label">Eixo Tecnologico</span><span className="entity-details-item__value">{previewData.eixo_tecnologico || '-'}</span></div>
              <div className="entity-details-item"><span className="entity-details-item__label">Carga Horaria</span><span className="entity-details-item__value">{previewData.carga_horaria_total}</span></div>
              <div className="entity-details-item"><span className="entity-details-item__label">Situacao Final</span><span className="entity-details-item__value">{previewData.situacao_final}</span></div>
              <div className="entity-details-item"><span className="entity-details-item__label">Data Conclusao</span><span className="entity-details-item__value">{formatDate(previewData.data_conclusao)}</span></div>
              <div className="entity-details-item"><span className="entity-details-item__label">Forma de Ingresso</span><span className="entity-details-item__value">{previewData.forma_ingresso || '-'}</span></div>
            </div>
          ) : null}
        </EntityFormPanel>
      ) : null}
    </div>
  )
}
