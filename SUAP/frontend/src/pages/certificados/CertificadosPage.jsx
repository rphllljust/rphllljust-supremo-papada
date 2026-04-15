import { useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Ban, Eye, FileDown, KeyRound, Plus, Printer, QrCode, RefreshCw } from 'lucide-react'
import toast from 'react-hot-toast'
import { Link } from 'react-router-dom'

import { certificadosApi, cursosApi, matriculasApi, turmasApi } from '@/api/endpoints'
import CertificadoPreview from '@/components/certificados/CertificadoPreview'
import EmitirCertificadoModal from '@/components/certificados/EmitirCertificadoModal'
import DataTable from '@/components/ui/DataTable'
import EntityDetailsPanel from '@/components/ui/EntityDetailsPanel'

const COLUMNS = [
  { key: 'tipo_documento_display', label: 'Documento' },
  { key: 'numero_registro', label: 'Registro' },
  { key: 'aluno_nome', label: 'Aluno' },
  { key: 'curso_nome', label: 'Curso' },
  { key: 'status_documento_display', label: 'Situacao' },
  { key: 'data_emissao', label: 'Emissao' },
  { key: 'codigo_validacao', label: 'Codigo validacao' },
]

const STATUS_DOCUMENTO_OPTIONS = [
  { value: '', label: 'Todos os status documentais' },
  { value: 'RASCUNHO', label: 'Rascunho' },
  { value: 'EMITIDO', label: 'Emitido' },
  { value: 'CANCELADO', label: 'Cancelado' },
  { value: 'REEMITIDO', label: 'Reemitido' },
]

const DOCUMENTO_OPTIONS = [
  { value: '', label: 'Todos os documentos' },
  { value: 'DIPLOMA', label: 'Diploma' },
  { value: 'HISTORICO', label: 'Historico Escolar' },
]

function getErrorMessage(error, fallback) {
  const data = error?.response?.data
  if (!data) return fallback
  if (typeof data.detail === 'string') return data.detail
  const firstValue = Object.values(data)[0]
  return Array.isArray(firstValue) ? firstValue[0] : (firstValue || fallback)
}

function abrirBlob(blob, mimeType = 'application/octet-stream', nome = 'arquivo.bin') {
  const blobValue = blob instanceof Blob ? blob : new Blob([blob], { type: mimeType })
  const url = URL.createObjectURL(blobValue)
  const win = window.open(url, '_blank', 'noopener,noreferrer')
  if (!win) {
    const link = document.createElement('a')
    link.href = url
    link.download = nome
    link.click()
  }
  setTimeout(() => URL.revokeObjectURL(url), 10000)
}

function buildInitialEmissao() {
  return {
    modelo_id: '',
    tipo: 'individual',
    tipo_documento: 'DIPLOMA',
    matricula_id: '',
    turma_id: '',
    sobrescritas: {
      data_inicio: '',
      data_fim: '',
      data_conclusao: '',
      cidade: '',
      estado: '',
      livro: '',
      folha: '',
      pagina: '',
      observacoes: '',
      texto_certificado: '',
      somente_concluintes: true,
    },
    gerar_pdf: true,
  }
}

export default function CertificadosPage() {
  const queryClient = useQueryClient()

  const [search, setSearch] = useState('')
  const [page, setPage] = useState(1)
  const [filters, setFilters] = useState({
    tipo_documento: '',
    status_documento: '',
    curso: '',
    turma: '',
    matricula: '',
    livro: '',
    folha: '',
    pagina: '',
    numero_registro: '',
    periodo: '',
  })
  const [previewHtml, setPreviewHtml] = useState('')
  const [previewTitle, setPreviewTitle] = useState('Pre-visualizacao do certificado')
  const [previewLoadingId, setPreviewLoadingId] = useState(null)
  const [previewCache, setPreviewCache] = useState({})
  const [showEmissionModal, setShowEmissionModal] = useState(false)
  const [emissao, setEmissao] = useState(buildInitialEmissao)
  const [selectedDocumentId, setSelectedDocumentId] = useState(null)

  const { data, isLoading, isError, error } = useQuery({
    queryKey: ['certificados-emitidos', { search, page, filters }],
    queryFn: () => certificadosApi.emitidos.list({ search, page, ...filters }).then((response) => response.data),
    staleTime: 15_000,
  })

  const listErrorMessage = (() => {
    const payload = error?.response?.data
    if (!payload) return 'Nao foi possivel carregar os documentos emitidos.'
    if (typeof payload.detail === 'string') return payload.detail
    const firstValue = Object.values(payload)[0]
    if (Array.isArray(firstValue)) return firstValue[0]
    return firstValue || 'Nao foi possivel carregar os documentos emitidos.'
  })()

  const { data: documentoDetalhe, isLoading: isLoadingDetalhe } = useQuery({
    queryKey: ['certificado-detalhe', selectedDocumentId],
    queryFn: () => certificadosApi.emitidos.get(selectedDocumentId).then((response) => response.data),
    enabled: Boolean(selectedDocumentId),
    staleTime: 15_000,
  })

  const { data: modelosData } = useQuery({
    queryKey: ['certificados-modelos-ativos'],
    queryFn: () => certificadosApi.modelos.list({ ativo: true, page_size: 200 }).then((response) => response.data),
    staleTime: 60_000,
  })

  const { data: matriculasData } = useQuery({
    queryKey: ['certificados-matriculas', search],
    queryFn: () => matriculasApi.list({ page_size: 200, search: search || undefined }).then((response) => response.data),
    staleTime: 30_000,
  })

  const { data: turmasData } = useQuery({
    queryKey: ['certificados-turmas'],
    queryFn: () => turmasApi.list({ page_size: 200 }).then((response) => response.data),
    staleTime: 60_000,
  })

  const { data: cursosData } = useQuery({
    queryKey: ['certificados-cursos'],
    queryFn: () => cursosApi.list({ page_size: 200 }).then((response) => response.data),
    staleTime: 60_000,
  })

  const modelos = useMemo(() => modelosData?.results || [], [modelosData])
  const matriculas = useMemo(() => matriculasData?.results || [], [matriculasData])
  const turmas = useMemo(() => turmasData?.results || [], [turmasData])
  const cursos = useMemo(() => cursosData?.results || [], [cursosData])

  const emitirMutation = useMutation({
    mutationFn: (payload) => (
      payload.tipo === 'lote'
        ? certificadosApi.emitirLote(payload.data)
        : certificadosApi.emitir(payload.data)
    ),
    onSuccess: (response, payload) => {
      queryClient.invalidateQueries({ queryKey: ['certificados-emitidos'] })
      if (payload.tipo === 'lote') {
        toast.success(`Emissao em lote concluida (${response.data.total_emitidos} emitidos).`)
      } else {
        toast.success(`${payload.data.tipo_documento === 'HISTORICO' ? 'Historico' : 'Diploma'} emitido com sucesso.`)
      }
      setShowEmissionModal(false)
      setEmissao(buildInitialEmissao())
    },
    onError: (error) => toast.error(getErrorMessage(error, 'Nao foi possivel emitir o documento.')),
  })

  const previewRascunhoMutation = useMutation({
    mutationFn: (payload) => certificadosApi.previewRascunho(payload),
    onSuccess: (response) => {
      setPreviewHtml(response.data.html || '')
      toast.success('Preview carregado.')
    },
    onError: (error) => toast.error(getErrorMessage(error, 'Falha ao gerar preview.')),
  })

  const previewEmitidoMutation = useMutation({
    mutationFn: (id) => certificadosApi.emitidos.preview(id),
    onError: (error) => toast.error(getErrorMessage(error, 'Falha ao abrir preview do documento.')),
  })

  const pdfMutation = useMutation({
    mutationFn: ({ id, numero }) => certificadosApi.emitidos.pdf(id).then((response) => ({ blob: response.data, numero })),
    onSuccess: ({ blob, numero }) => {
      abrirBlob(blob, 'application/pdf', `${numero || 'documento'}.pdf`)
      toast.success('PDF pronto para visualizacao.')
    },
    onError: (error) => toast.error(getErrorMessage(error, 'Nao foi possivel gerar/baixar o PDF.')),
  })

  const qrcodeMutation = useMutation({
    mutationFn: ({ id, numero }) => certificadosApi.emitidos.qrcode(id).then((response) => ({ blob: response.data, numero })),
    onSuccess: ({ blob, numero }) => {
      abrirBlob(blob, 'image/png', `qrcode-${numero || 'documento'}.png`)
      toast.success('QR Code aberto com sucesso.')
    },
    onError: (error) => toast.error(getErrorMessage(error, 'Nao foi possivel obter o QR Code.')),
  })

  const reimprimirMutation = useMutation({
    mutationFn: (id) => certificadosApi.emitidos.reimprimir(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['certificados-emitidos'] })
      toast.success('Reimpressao registrada com sucesso.')
    },
    onError: (error) => toast.error(getErrorMessage(error, 'Nao foi possivel registrar reimpressao.')),
  })

  const cancelarMutation = useMutation({
    mutationFn: ({ id, motivo }) => certificadosApi.emitidos.cancelar(id, { motivo }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['certificados-emitidos'] })
      if (selectedDocumentId) {
        queryClient.invalidateQueries({ queryKey: ['certificado-detalhe', selectedDocumentId] })
      }
      toast.success('Documento cancelado com sucesso.')
    },
    onError: (error) => toast.error(getErrorMessage(error, 'Nao foi possivel cancelar o documento.')),
  })

  const reemitirMutation = useMutation({
    mutationFn: (id) => certificadosApi.emitidos.reemitir(id, { gerar_pdf: true }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['certificados-emitidos'] })
      toast.success('Documento reemitido com sucesso.')
    },
    onError: (error) => toast.error(getErrorMessage(error, 'Nao foi possivel reemitir o documento.')),
  })

  const statusValidacaoMutation = useMutation({
    mutationFn: (id) => certificadosApi.emitidos.statusValidacao(id),
    onSuccess: (response) => {
      const statusLabel = response.data?.autenticidade === 'valido' ? 'VALIDO' : 'INVALIDO'
      toast.success(`Status de validacao: ${statusLabel}`)
    },
    onError: (error) => toast.error(getErrorMessage(error, 'Nao foi possivel consultar o status de validacao.')),
  })

  const validarFormularioEmissao = () => {
    if (!emissao.modelo_id) {
      toast.error('Selecione um modelo.')
      return false
    }
    if (!emissao.tipo_documento) {
      toast.error('Selecione o tipo de documento.')
      return false
    }
    if (emissao.tipo === 'individual' && !emissao.matricula_id) {
      toast.error('Selecione a matricula para emissao individual.')
      return false
    }
    if (emissao.tipo === 'lote' && !emissao.turma_id) {
      toast.error('Selecione a turma para emissao em lote.')
      return false
    }
    return true
  }

  const handleEmitir = () => {
    if (!validarFormularioEmissao()) return

    emitirMutation.mutate({
      tipo: emissao.tipo,
      data: {
        modelo_id: Number(emissao.modelo_id),
        tipo_documento: emissao.tipo_documento,
        matricula_id: emissao.tipo === 'individual' ? Number(emissao.matricula_id) : undefined,
        turma_id: emissao.tipo === 'lote' ? Number(emissao.turma_id) : undefined,
        sobrescritas: emissao.sobrescritas,
        gerar_pdf: emissao.gerar_pdf,
      },
    })
  }

  const handlePreviewEmissao = () => {
    if (!emissao.modelo_id) {
      toast.error('Selecione um modelo para preview.')
      return
    }
    if (emissao.tipo === 'individual' && !emissao.matricula_id) {
      toast.error('Selecione uma matricula para preview.')
      return
    }

    previewRascunhoMutation.mutate({
      modelo_id: Number(emissao.modelo_id),
      tipo_documento: emissao.tipo_documento,
      matricula_id: emissao.tipo === 'individual' ? Number(emissao.matricula_id) : undefined,
      sobrescritas: emissao.sobrescritas,
    })
  }

  const abrirEmissao = (tipoDocumento) => {
    setEmissao((current) => ({ ...current, tipo_documento: tipoDocumento }))
    setShowEmissionModal(true)
  }

  const handlePreviewEmitido = (row) => {
    if (previewLoadingId !== null) return

    const title = `Pre-visualizacao de ${row.numero_registro || row.numero_certificado || 'documento'}`
    setPreviewTitle(title)

    const cachedHtml = previewCache[row.id]
    if (cachedHtml) {
      setPreviewHtml(cachedHtml)
      return
    }

    setPreviewLoadingId(row.id)
    previewEmitidoMutation.mutate(row.id, {
      onSuccess: (response) => {
        const html = response?.data?.html || ''
        setPreviewCache((current) => ({ ...current, [row.id]: html }))
        setPreviewHtml(html)
      },
      onSettled: () => {
        setPreviewLoadingId(null)
      },
    })
  }

  const counts = useMemo(() => {
    const rows = data?.results || []
    const diplomas = rows.filter((row) => row.tipo_documento === 'DIPLOMA').length
    const historicos = rows.filter((row) => row.tipo_documento === 'HISTORICO').length
    return { diplomas, historicos }
  }, [data])

  const detalhesHistorico = documentoDetalhe?.dados_dinamicos || {}
  const disciplinasResumo = Array.isArray(detalhesHistorico.disciplinas)
    ? detalhesHistorico.disciplinas
      .slice(0, 5)
      .map((item) => `${item.descricao || '-'} (${item.nota || '-'})`)
      .join(' | ')
    : ''
  const detailsFields = [
    { label: 'Aluno', value: documentoDetalhe?.aluno_nome },
    { label: 'CPF', value: documentoDetalhe?.cpf_aluno_snapshot },
    { label: 'Curso', value: documentoDetalhe?.curso_nome },
    { label: 'Tipo', value: documentoDetalhe?.tipo_documento_display },
    { label: 'Numero registro', value: documentoDetalhe?.numero_registro },
    { label: 'Livro', value: documentoDetalhe?.livro },
    { label: 'Folha', value: documentoDetalhe?.folha },
    { label: 'Pagina', value: documentoDetalhe?.pagina },
    { label: 'Data emissao', value: documentoDetalhe?.data_emissao },
    { label: 'Data registro', value: documentoDetalhe?.data_registro },
    { label: 'Codigo validacao', value: documentoDetalhe?.codigo_validacao },
    { label: 'Hash integridade', value: documentoDetalhe?.hash_integridade },
    { label: 'URL validacao', value: documentoDetalhe?.url_validacao },
    { label: 'Observacoes', value: documentoDetalhe?.observacoes },
  ]

  if (documentoDetalhe?.tipo_documento === 'HISTORICO') {
    detailsFields.push(
      { label: 'Media final', value: detalhesHistorico.media_final || '-' },
      { label: 'Frequencia final', value: detalhesHistorico.frequencia_final || '-' },
      { label: 'Situacao final', value: detalhesHistorico.situacao_final_display || detalhesHistorico.situacao_final || '-' },
      { label: 'Qtd. disciplinas', value: detalhesHistorico.quantidade_disciplinas || 0 },
      { label: 'Disciplinas (resumo)', value: disciplinasResumo || '-' },
    )
  }

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <h1 className="page-title">Documentos com QR Code</h1>
          <p className="page-subtitle">Emissao, validacao, reemissao e cancelamento de diplomas e historicos escolares.</p>
        </div>

        <div className="page-header__actions">
          <Link to="/certificados/modelos" className="btn btn--outline">Modelos</Link>
          <button type="button" className="btn btn--outline" onClick={() => abrirEmissao('HISTORICO')}>
            <Plus size={16} /> Emitir historico
          </button>
          <button type="button" className="btn btn--primary" onClick={() => abrirEmissao('DIPLOMA')}>
            <Plus size={16} /> Emitir diploma
          </button>
        </div>
      </div>

      <section className="form-panel" style={{ marginTop: 20 }}>
        <div className="form-panel__body">
          <div className="table-actions" style={{ marginBottom: 12 }}>
            <button
              type="button"
              className={`btn ${filters.tipo_documento === 'DIPLOMA' ? 'btn--primary' : 'btn--outline'}`}
              onClick={() => {
                setFilters((current) => ({ ...current, tipo_documento: 'DIPLOMA' }))
                setPage(1)
              }}
            >
              Diplomas ({counts.diplomas})
            </button>
            <button
              type="button"
              className={`btn ${filters.tipo_documento === 'HISTORICO' ? 'btn--primary' : 'btn--outline'}`}
              onClick={() => {
                setFilters((current) => ({ ...current, tipo_documento: 'HISTORICO' }))
                setPage(1)
              }}
            >
              Historicos ({counts.historicos})
            </button>
            <button
              type="button"
              className={`btn ${filters.tipo_documento === '' ? 'btn--secondary' : 'btn--outline'}`}
              onClick={() => {
                setFilters((current) => ({ ...current, tipo_documento: '' }))
                setPage(1)
              }}
            >
              Todos
            </button>
          </div>

          <div className="form-panel__grid">
            <div className="form-field">
              <label>Tipo documento</label>
              <select
                className="select"
                value={filters.tipo_documento}
                onChange={(event) => {
                  setFilters((current) => ({ ...current, tipo_documento: event.target.value }))
                  setPage(1)
                }}
              >
                {DOCUMENTO_OPTIONS.map((option) => (
                  <option key={option.value || 'todos'} value={option.value}>{option.label}</option>
                ))}
              </select>
            </div>

            <div className="form-field">
              <label>Status documento</label>
              <select
                className="select"
                value={filters.status_documento}
                onChange={(event) => {
                  setFilters((current) => ({ ...current, status_documento: event.target.value }))
                  setPage(1)
                }}
              >
                {STATUS_DOCUMENTO_OPTIONS.map((statusOption) => (
                  <option key={statusOption.value || 'todos'} value={statusOption.value}>{statusOption.label}</option>
                ))}
              </select>
            </div>

            <div className="form-field">
              <label>Curso</label>
              <select
                className="select"
                value={filters.curso}
                onChange={(event) => {
                  setFilters((current) => ({ ...current, curso: event.target.value }))
                  setPage(1)
                }}
              >
                <option value="">Todos</option>
                {cursos.map((curso) => (
                  <option key={curso.id} value={curso.id}>{curso.nome}</option>
                ))}
              </select>
            </div>

            <div className="form-field">
              <label>Turma</label>
              <select
                className="select"
                value={filters.turma}
                onChange={(event) => {
                  setFilters((current) => ({ ...current, turma: event.target.value }))
                  setPage(1)
                }}
              >
                <option value="">Todas</option>
                {turmas.map((turma) => (
                  <option key={turma.id} value={turma.id}>{turma.nome}</option>
                ))}
              </select>
            </div>

            <div className="form-field">
              <label>Matricula</label>
              <select
                className="select"
                value={filters.matricula}
                onChange={(event) => {
                  setFilters((current) => ({ ...current, matricula: event.target.value }))
                  setPage(1)
                }}
              >
                <option value="">Todas</option>
                {matriculas.map((matricula) => (
                  <option key={matricula.id} value={matricula.id}>{matricula.numero_matricula} - {matricula.aluno_nome}</option>
                ))}
              </select>
            </div>

            <div className="form-field">
              <label>Numero registro</label>
              <input
                type="text"
                value={filters.numero_registro}
                onChange={(event) => {
                  setFilters((current) => ({ ...current, numero_registro: event.target.value }))
                  setPage(1)
                }}
              />
            </div>

            <div className="form-field">
              <label>Livro</label>
              <input
                type="text"
                value={filters.livro}
                onChange={(event) => {
                  setFilters((current) => ({ ...current, livro: event.target.value }))
                  setPage(1)
                }}
              />
            </div>

            <div className="form-field">
              <label>Folha</label>
              <input
                type="text"
                value={filters.folha}
                onChange={(event) => {
                  setFilters((current) => ({ ...current, folha: event.target.value }))
                  setPage(1)
                }}
              />
            </div>

            <div className="form-field">
              <label>Pagina</label>
              <input
                type="text"
                value={filters.pagina}
                onChange={(event) => {
                  setFilters((current) => ({ ...current, pagina: event.target.value }))
                  setPage(1)
                }}
              />
            </div>

            <div className="form-field">
              <label>Periodo (ano)</label>
              <input
                type="number"
                placeholder="Ex: 2026"
                value={filters.periodo}
                onChange={(event) => {
                  setFilters((current) => ({ ...current, periodo: event.target.value }))
                  setPage(1)
                }}
              />
            </div>
          </div>
        </div>
      </section>

      {isError ? <div className="alert alert--error">{listErrorMessage}</div> : null}

      <DataTable
        columns={COLUMNS}
        data={data}
        isLoading={isLoading}
        onSearch={(value) => {
          setSearch(value)
          setPage(1)
        }}
        searchPlaceholder="Buscar por aluno, matricula, curso, registro, livro, folha, pagina ou codigo..."
        emptyMessage="Nenhum documento encontrado."
        rowActions={(row) => (
          <div className="table-actions">
            <button type="button" className="btn btn--outline btn--sm" onClick={() => setSelectedDocumentId(row.id)}>
              <Eye size={14} /> Detalhes
            </button>
            <button
              type="button"
              className="btn btn--outline btn--sm"
              onClick={() => handlePreviewEmitido(row)}
              disabled={previewLoadingId !== null}
            >
              <Eye size={14} /> {previewLoadingId === row.id ? 'Carregando...' : 'Preview'}
            </button>
            <button
              type="button"
              className="btn btn--secondary btn--sm"
              onClick={() => pdfMutation.mutate({ id: row.id, numero: row.numero_registro || row.numero_certificado })}
            >
              <FileDown size={14} /> PDF
            </button>
            <button
              type="button"
              className="btn btn--secondary btn--sm"
              onClick={() => qrcodeMutation.mutate({ id: row.id, numero: row.numero_registro || row.numero_certificado })}
            >
              <QrCode size={14} /> QR
            </button>
            <button type="button" className="btn btn--secondary btn--sm" onClick={() => statusValidacaoMutation.mutate(row.id)}>
              <KeyRound size={14} /> Status
            </button>
            <button type="button" className="btn btn--secondary btn--sm" onClick={() => reemitirMutation.mutate(row.id)}>
              <RefreshCw size={14} /> Reemitir
            </button>
            <button
              type="button"
              className="btn btn--outline btn--sm"
              onClick={() => {
                const motivo = window.prompt('Motivo do cancelamento (opcional):', '') || ''
                cancelarMutation.mutate({ id: row.id, motivo })
              }}
            >
              <Ban size={14} /> Cancelar
            </button>
            <button type="button" className="btn btn--secondary btn--sm" onClick={() => reimprimirMutation.mutate(row.id)}>
              <Printer size={14} /> Reimprimir
            </button>
          </div>
        )}
      />

      {data ? (
        <div className="pagination">
          <button className="btn btn--secondary" disabled={!data.previous} onClick={() => setPage((current) => current - 1)}>
            Anterior
          </button>
          <span className="pagination__info">Pagina {page} - {data.count || 0} registros</span>
          <button className="btn btn--secondary" disabled={!data.next} onClick={() => setPage((current) => current + 1)}>
            Proxima
          </button>
        </div>
      ) : null}

      <EmitirCertificadoModal
        isOpen={showEmissionModal}
        onClose={() => setShowEmissionModal(false)}
        emissao={emissao}
        setEmissao={setEmissao}
        modelos={modelos}
        matriculas={matriculas}
        turmas={turmas}
        isSubmitting={emitirMutation.isPending}
        isPreviewPending={previewRascunhoMutation.isPending}
        onSubmit={handleEmitir}
        onPreview={handlePreviewEmissao}
      />

      {previewHtml ? (
        <CertificadoPreview
          html={previewHtml}
          title={previewTitle}
          onClose={() => setPreviewHtml('')}
        />
      ) : null}

      {selectedDocumentId ? (
        <EntityDetailsPanel
          title={`Documento ${documentoDetalhe?.numero_registro || documentoDetalhe?.numero_certificado || ''}`}
          subtitle={`${documentoDetalhe?.tipo_documento_display || ''} - ${documentoDetalhe?.status_documento_display || ''}`}
          isLoading={isLoadingDetalhe}
          onClose={() => setSelectedDocumentId(null)}
          fields={detailsFields}
        />
      ) : null}
    </div>
  )
}
