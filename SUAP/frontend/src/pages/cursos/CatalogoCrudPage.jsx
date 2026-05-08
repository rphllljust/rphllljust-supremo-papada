import { useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import { CircleHelp, FileSpreadsheet, Pencil, Plus, Save, Trash2, X } from 'lucide-react'
import { Link } from 'react-router-dom'

function exportRowsToExcel(rows, filename) {
  const headers = ['#', 'Descrição']
  const body = rows.map((row, index) => [index + 1, row.descricao])
  const content = [headers, ...body]
    .map((columns) => columns.map((value) => `"${String(value ?? '').replaceAll('"', '""')}"`).join('\t'))
    .join('\n')

  const blob = new Blob([content], { type: 'application/vnd.ms-excel;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  link.click()
  URL.revokeObjectURL(url)
}

function parseListPayload(payload) {
  if (Array.isArray(payload)) {
    return {
      rows: payload,
      total: payload.length,
      next: null,
      previous: null,
    }
  }

  const rows = Array.isArray(payload?.results) ? payload.results : []
  const total = typeof payload?.count === 'number' ? payload.count : rows.length

  return {
    rows,
    total,
    next: payload?.next ?? null,
    previous: payload?.previous ?? null,
  }
}

export default function CatalogoCrudPage({
  title,
  singular,
  plural,
  api,
  queryKey,
  helpSlug,
  helpTitle,
  helpDescription,
  exportFileName,
  pageClassName = '',
}) {
  const queryClient = useQueryClient()
  const [draftSearch, setDraftSearch] = useState('')
  const [search, setSearch] = useState('')
  const [page, setPage] = useState(1)
  const [draftDescription, setDraftDescription] = useState('')
  const [editingRow, setEditingRow] = useState(null)
  const [isExporting, setIsExporting] = useState(false)

  const { data, isLoading, isError } = useQuery({
    queryKey: [queryKey, { search, page }],
    queryFn: () => api.list({ search, page }).then((response) => response.data),
    staleTime: 30_000,
  })

  const saveMutation = useMutation({
    mutationFn: ({ id, payload }) => (id ? api.patch(id, payload) : api.create(payload)),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: [queryKey] })
      toast.success(editingRow ? `${singular} atualizado com sucesso.` : `${singular} criado com sucesso.`)
      setEditingRow(null)
      setDraftDescription('')
    },
    onError: (error) => {
      const detail = error?.response?.data?.descricao?.[0] || error?.response?.data?.detail
      toast.error(detail || `Não foi possível salvar ${singular.toLowerCase()}.`)
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (id) => api.remove(id),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: [queryKey] })
      toast.success(`${singular} removido com sucesso.`)
    },
    onError: (error) => {
      const detail = error?.response?.data?.detail
      toast.error(detail || `Não foi possível remover ${singular.toLowerCase()}.`)
    },
  })

  const { rows, total, next, previous } = useMemo(() => parseListPayload(data), [data])
  const formTitle = useMemo(() => (editingRow ? `Editar ${singular.toLowerCase()}` : `Novo ${singular.toLowerCase()}`), [editingRow, singular])

  const startCreate = () => {
    setEditingRow(null)
    setDraftDescription('')
  }

  const startEdit = (row) => {
    setEditingRow(row)
    setDraftDescription(row.descricao)
  }

  const cancelForm = () => {
    setEditingRow(null)
    setDraftDescription('')
  }

  const handleSave = () => {
    const descricao = draftDescription.trim()
    if (!descricao) {
      toast.error(`Informe a descrição ${singular.toLowerCase()}.`)
      return
    }

    saveMutation.mutate({
      id: editingRow?.id,
      payload: { descricao },
    })
  }

  const handleDelete = (row) => {
    if (!window.confirm(`Deseja realmente remover ${singular.toLowerCase()} ${row.descricao}?`)) {
      return
    }
    deleteMutation.mutate(row.id)
  }

  const handleExport = async () => {
    if (isExporting) return

    try {
      setIsExporting(true)

      const firstResponse = await api.list({ search, page: 1 })
      const firstParsed = parseListPayload(firstResponse?.data)
      const exportedRows = [...firstParsed.rows]

      if (!Array.isArray(firstResponse?.data) && Array.isArray(firstResponse?.data?.results)) {
        const count = typeof firstResponse.data.count === 'number' ? firstResponse.data.count : exportedRows.length
        const pageSize = Math.max(exportedRows.length, 1)
        const totalPages = Math.max(1, Math.ceil(count / pageSize))

        for (let currentPage = 2; currentPage <= totalPages; currentPage += 1) {
          const pageResponse = await api.list({ search, page: currentPage })
          const pageRows = parseListPayload(pageResponse?.data).rows
          exportedRows.push(...pageRows)

          if (exportedRows.length >= count || pageRows.length === 0) {
            break
          }
        }
      }

      exportRowsToExcel(exportedRows, exportFileName)
      toast.success(`${exportedRows.length} registro(s) exportado(s).`)
    } catch (error) {
      const detail = error?.response?.data?.detail
      toast.error(detail || `NÃ£o foi possÃ­vel exportar ${plural.toLowerCase()}.`)
    } finally {
      setIsExporting(false)
    }
  }

  const pageClasses = ['page', 'page--wide', 'area-cursos-page', pageClassName].filter(Boolean).join(' ')

  return (
    <div className={pageClasses}>
      <nav className="profile-breadcrumb">
        <Link to="/dashboard">Início</Link>
        <span className="profile-breadcrumb__sep">&gt;</span>
        <span>{plural}</span>
      </nav>

      <div className="page-header area-cursos-page__header">
        <div>
          <h1 className="page-title">{title}</h1>
        </div>
        <div className="page-header__actions">
          <button type="button" className="btn btn--primary" onClick={startCreate}>
            <Plus size={16} /> Novo {singular}
          </button>
          <button type="button" className="btn btn--dark" onClick={handleExport} disabled={isExporting || isLoading}>
            <FileSpreadsheet size={16} /> {isExporting ? 'Exportando...' : 'Exportar para XLS'}
          </button>
          <Link
            to={`/indisponivel/${helpSlug}`}
            state={{
              title: helpTitle,
              description: helpDescription,
            }}
            className="btn btn--outline"
          >
            <CircleHelp size={16} /> Ajuda
          </Link>
        </div>
      </div>

      <section className="dashboard-card area-curso-edit-form">
        <div className="area-cursos-filters-card__title">{formTitle}</div>
        <div className="area-curso-edit-row">
          <label className="area-curso-edit-row__label">* Descrição</label>
          <div className="area-curso-edit-row__field">
            <input value={draftDescription} onChange={(event) => setDraftDescription(event.target.value)} />
          </div>
        </div>
        <div className="componente-edit-form__actions">
          <button type="button" className="btn btn--primary" onClick={handleSave} disabled={saveMutation.isPending}>
            <Save size={16} /> Salvar
          </button>
          {(editingRow || draftDescription) ? (
            <button type="button" className="btn btn--outline" onClick={cancelForm}>
              <X size={16} /> Cancelar
            </button>
          ) : null}
        </div>
      </section>

      <section className="dashboard-card area-cursos-filters-card">
        <div className="area-cursos-filters-card__title">Filtros:</div>
        <div className="area-cursos-filters-card__body">
          <label className="area-cursos-filter-field">
            <span className="area-cursos-filter-field__label">Texto:</span>
            <input value={draftSearch} onChange={(event) => setDraftSearch(event.target.value)} />
          </label>
          <button
            type="button"
            className="btn btn--secondary"
            onClick={() => {
              setSearch(draftSearch)
              setPage(1)
            }}
          >
            Filtrar
          </button>
        </div>
      </section>

      {isError ? (
        <div className="alert alert--error">Não foi possível carregar {plural.toLowerCase()} com as permissões atuais.</div>
      ) : null}

      {!isLoading && rows.length === 0 ? (
        <div className="area-cursos-empty-notice">Nenhum {singular} encontrado.</div>
      ) : null}

      {rows.length > 0 ? (
        <>
          <div className="area-cursos-page__summary">Mostrando {rows.length} {singular}{rows.length !== 1 ? 's' : ''}</div>

          <section className="dashboard-card area-cursos-table-card">
            <div className="area-cursos-table-wrapper">
              <table className="area-cursos-table">
                <thead>
                  <tr>
                    <th className="area-cursos-table__index">#</th>
                    <th>Descrição</th>
                    <th>Ações</th>
                  </tr>
                </thead>
                <tbody>
                  {isLoading ? (
                    <tr>
                      <td colSpan={3} className="area-cursos-table__empty">Carregando {plural.toLowerCase()}...</td>
                    </tr>
                  ) : rows.map((row, index) => (
                    <tr key={row.id}>
                      <td>{(page - 1) * 10 + index + 1}</td>
                      <td>{row.descricao}</td>
                      <td>
                        <div className="area-cursos-table__actions">
                          <button type="button" className="btn btn--outline btn--icon" onClick={() => startEdit(row)} aria-label={`Editar ${singular.toLowerCase()} ${row.descricao}`}>
                            <Pencil size={14} />
                          </button>
                          <button type="button" className="btn btn--outline btn--icon" onClick={() => handleDelete(row)} aria-label={`Remover ${singular.toLowerCase()} ${row.descricao}`} disabled={deleteMutation.isPending}>
                            <Trash2 size={14} />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>

          <div className="area-cursos-page__summary">Mostrando {rows.length} {singular}{rows.length !== 1 ? 's' : ''}</div>
        </>
      ) : null}

      {data ? (
        <div className="estagios-pagination">
          <button type="button" className="btn btn--secondary" disabled={!previous} onClick={() => setPage((current) => current - 1)}>
            Anterior
          </button>
          <span className="pagination__info">Página {page} • {total} registros</span>
          <button type="button" className="btn btn--secondary" disabled={!next} onClick={() => setPage((current) => current + 1)}>
            Próxima
          </button>
        </div>
      ) : null}
    </div>
  )
}
