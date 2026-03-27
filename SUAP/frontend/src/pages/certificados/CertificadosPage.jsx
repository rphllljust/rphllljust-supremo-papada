import { useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Eye, FileDown, Plus, Printer } from 'lucide-react'
import toast from 'react-hot-toast'
import { Link } from 'react-router-dom'

import { certificadosApi, cursosApi, matriculasApi, turmasApi } from '@/api/endpoints'
import CertificadoPreview from '@/components/certificados/CertificadoPreview'
import EmitirCertificadoModal from '@/components/certificados/EmitirCertificadoModal'
import DataTable from '@/components/ui/DataTable'

const COLUMNS = [
  { key: 'numero_certificado', label: 'Numero' },
  { key: 'aluno_nome', label: 'Aluno' },
  { key: 'curso_nome', label: 'Curso' },
  { key: 'status_display', label: 'Status' },
  { key: 'data_emissao', label: 'Emissao' },
  { key: 'codigo_validacao', label: 'Codigo de validacao' },
]

const STATUS_OPTIONS = [
  { value: '', label: 'Todos os status' },
  { value: 'DIPLOMA_EM_PREPARACAO', label: 'Diploma em preparacao' },
  { value: 'DIPLOMA_REGISTRADO', label: 'Diploma registrado' },
  { value: 'DIPLOMA_DISPONIVEL_RETIRADA', label: 'Diploma disponivel para retirada' },
  { value: 'DIPLOMA_ENTREGUE', label: 'Diploma entregue' },
  { value: 'CERTIFICADO_CANCELADO', label: 'Certificado cancelado' },
]

function getErrorMessage(error, fallback) {
  const data = error?.response?.data
  if (!data) return fallback
  if (typeof data.detail === 'string') return data.detail
  const firstValue = Object.values(data)[0]
  return Array.isArray(firstValue) ? firstValue[0] : (firstValue || fallback)
}

function abrirBlobPdf(blob, nome = 'certificado.pdf') {
  const url = URL.createObjectURL(blob)
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
  const [filters, setFilters] = useState({ status: '', curso: '', turma: '', periodo: '' })
  const [previewHtml, setPreviewHtml] = useState('')
  const [showEmissionModal, setShowEmissionModal] = useState(false)
  const [emissao, setEmissao] = useState(buildInitialEmissao)

  const { data, isLoading, isError } = useQuery({
    queryKey: ['certificados-emitidos', { search, page, filters }],
    queryFn: () => certificadosApi.emitidos.list({ search, page, ...filters }).then((response) => response.data),
    staleTime: 15_000,
  })

  const { data: modelosData } = useQuery({
    queryKey: ['certificados-modelos-ativos'],
    queryFn: () => certificadosApi.modelos.list({ ativo: true, page_size: 200 }).then((response) => response.data),
    staleTime: 60_000,
  })

  const { data: matriculasData } = useQuery({
    queryKey: ['certificados-matriculas'],
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
        toast.success('Certificado emitido com sucesso.')
      }
      setShowEmissionModal(false)
      setEmissao(buildInitialEmissao())
    },
    onError: (error) => toast.error(getErrorMessage(error, 'Nao foi possivel emitir o certificado.')),
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
    onSuccess: (response) => setPreviewHtml(response.data.html || ''),
    onError: (error) => toast.error(getErrorMessage(error, 'Falha ao abrir preview do certificado.')),
  })

  const pdfMutation = useMutation({
    mutationFn: ({ id, numero }) => certificadosApi.emitidos.pdf(id).then((response) => ({ blob: response.data, numero })),
    onSuccess: ({ blob, numero }) => {
      abrirBlobPdf(blob, `${numero || 'certificado'}.pdf`)
      toast.success('PDF gerado com sucesso.')
    },
    onError: (error) => toast.error(getErrorMessage(error, 'Nao foi possivel gerar o PDF.')),
  })

  const reimprimirMutation = useMutation({
    mutationFn: (id) => certificadosApi.emitidos.reimprimir(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['certificados-emitidos'] })
      toast.success('Reimpressao registrada com sucesso.')
    },
    onError: (error) => toast.error(getErrorMessage(error, 'Nao foi possivel registrar reimpressao.')),
  })

  const validarFormularioEmissao = () => {
    if (!emissao.modelo_id) {
      toast.error('Selecione um modelo.')
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
      matricula_id: emissao.tipo === 'individual' ? Number(emissao.matricula_id) : undefined,
      sobrescritas: emissao.sobrescritas,
    })
  }

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <h1 className="page-title">Certificados</h1>
          <p className="page-subtitle">Listagem, emissao, preview e impressao de certificados institucionais.</p>
        </div>

        <div className="page-header__actions">
          <Link to="/certificados/modelos" className="btn btn--outline">Modelos</Link>
          <button type="button" className="btn btn--primary" onClick={() => setShowEmissionModal(true)}>
            <Plus size={16} /> Emitir certificado
          </button>
        </div>
      </div>

      <section className="form-panel" style={{ marginTop: 20 }}>
        <div className="form-panel__body">
          <div className="form-panel__grid">
            <div className="form-field">
              <label>Status</label>
              <select
                className="select"
                value={filters.status}
                onChange={(event) => {
                  setFilters((current) => ({ ...current, status: event.target.value }))
                  setPage(1)
                }}
              >
                {STATUS_OPTIONS.map((statusOption) => (
                  <option key={statusOption.value || 'todos'} value={statusOption.value}>
                    {statusOption.label}
                  </option>
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

      {isError ? <div className="alert alert--error">Nao foi possivel carregar os certificados emitidos.</div> : null}

      <DataTable
        columns={COLUMNS}
        data={data}
        isLoading={isLoading}
        onSearch={(value) => {
          setSearch(value)
          setPage(1)
        }}
        searchPlaceholder="Buscar por numero, aluno, curso, matricula ou codigo de validacao..."
        emptyMessage="Nenhum certificado encontrado."
        rowActions={(row) => (
          <div className="table-actions">
            <button type="button" className="btn btn--outline btn--sm" onClick={() => previewEmitidoMutation.mutate(row.id)}>
              <Eye size={14} /> Preview
            </button>
            <button
              type="button"
              className="btn btn--secondary btn--sm"
              onClick={() => pdfMutation.mutate({ id: row.id, numero: row.numero_certificado })}
            >
              <FileDown size={14} /> PDF
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
          onClose={() => setPreviewHtml('')}
        />
      ) : null}
    </div>
  )
}
