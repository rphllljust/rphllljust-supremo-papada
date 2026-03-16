import { useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import { CircleHelp, FileSpreadsheet, Pencil, Plus, Save, Trash2, X } from 'lucide-react'
import { Link } from 'react-router-dom'

import { eixosTecnologicosApi } from '@/api/endpoints'

function exportRowsToExcel(rows) {
  const headers = ['#', 'Descrição']
  const body = rows.map((row, index) => [index + 1, row.descricao])
  const content = [headers, ...body]
    .map((columns) => columns.map((value) => `"${String(value ?? '').replaceAll('"', '""')}"`).join('\t'))
    .join('\n')

  const blob = new Blob([content], { type: 'application/vnd.ms-excel;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = 'eixos-tecnologicos.xls'
  link.click()
  URL.revokeObjectURL(url)
}

export default function EixosTecnologicosPage() {
  const queryClient = useQueryClient()
  const [draftSearch, setDraftSearch] = useState('')
  const [search, setSearch] = useState('')
  const [page, setPage] = useState(1)
  const [draftDescription, setDraftDescription] = useState('')
  const [editingRow, setEditingRow] = useState(null)

  const { data, isLoading, isError } = useQuery({
    queryKey: ['eixos-tecnologicos', { search, page }],
    queryFn: () => eixosTecnologicosApi.list({ search, page }).then((response) => response.data),
    staleTime: 30_000,
  })

  const saveMutation = useMutation({
    mutationFn: ({ id, payload }) => (id ? eixosTecnologicosApi.patch(id, payload) : eixosTecnologicosApi.create(payload)),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['eixos-tecnologicos'] })
      toast.success(editingRow ? 'Eixo tecnológico atualizado com sucesso.' : 'Eixo tecnológico criado com sucesso.')
      setEditingRow(null)
      setDraftDescription('')
    },
    onError: (error) => {
      const detail = error?.response?.data?.descricao?.[0] || error?.response?.data?.detail
      toast.error(detail || 'Não foi possível salvar o eixo tecnológico.')
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (id) => eixosTecnologicosApi.remove(id),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['eixos-tecnologicos'] })
      toast.success('Eixo tecnológico removido com sucesso.')
    },
    onError: (error) => {
      const detail = error?.response?.data?.detail
      toast.error(detail || 'Não foi possível remover o eixo tecnológico.')
    },
  })

  const rows = data?.results || []
  const total = data?.count || 0
  const formTitle = useMemo(() => (editingRow ? 'Editar eixo tecnológico' : 'Novo eixo tecnológico'), [editingRow])

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
      toast.error('Informe a descrição do eixo tecnológico.')
      return
    }

    saveMutation.mutate({
      id: editingRow?.id,
      payload: { descricao },
    })
  }

  const handleDelete = (row) => {
    if (!window.confirm(`Deseja realmente remover o eixo tecnológico ${row.descricao}? Os cursos vinculados ficarão sem eixo.`)) {
      return
    }
    deleteMutation.mutate(row.id)
  }

  return (
    <div className="page page--wide area-cursos-page">
      <nav className="profile-breadcrumb">
        <Link to="/dashboard">Início</Link>
        <span className="profile-breadcrumb__sep">&gt;</span>
        <span>Eixos Tecnológicos</span>
      </nav>

      <div className="page-header area-cursos-page__header">
        <div>
          <h1 className="page-title">Eixos Tecnológicos</h1>
        </div>
        <div className="page-header__actions">
          <button type="button" className="btn btn--primary" onClick={startCreate}>
            <Plus size={16} /> Novo Eixo
          </button>
          <button type="button" className="btn btn--dark" onClick={() => exportRowsToExcel(rows)}>
            <FileSpreadsheet size={16} /> Exportar para XLS
          </button>
          <Link
            to="/indisponivel/ajuda-eixos-tecnologicos"
            state={{
              title: 'Ajuda de Eixos Tecnológicos',
              description: 'A ajuda detalhada desta funcionalidade ainda será portada para o frontend React.',
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
        <div className="alert alert--error">Não foi possível carregar os eixos tecnológicos com as permissões atuais.</div>
      ) : null}

      {!isLoading && rows.length === 0 ? (
        <div className="area-cursos-empty-notice">Nenhum Eixo Tecnológico encontrado.</div>
      ) : null}

      {rows.length > 0 ? (
        <>
          <div className="area-cursos-page__summary">Mostrando {rows.length} Eixo Tecnológico{rows.length !== 1 ? 's' : ''}</div>

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
                      <td colSpan={3} className="area-cursos-table__empty">Carregando eixos tecnológicos...</td>
                    </tr>
                  ) : rows.map((row, index) => (
                    <tr key={row.id}>
                      <td>{(page - 1) * 10 + index + 1}</td>
                      <td>{row.descricao}</td>
                      <td>
                        <div className="area-cursos-table__actions">
                          <button type="button" className="btn btn--outline btn--icon" onClick={() => startEdit(row)} aria-label={`Editar eixo ${row.descricao}`}>
                            <Pencil size={14} />
                          </button>
                          <button type="button" className="btn btn--outline btn--icon" onClick={() => handleDelete(row)} aria-label={`Remover eixo ${row.descricao}`} disabled={deleteMutation.isPending}>
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

          <div className="area-cursos-page__summary">Mostrando {rows.length} Eixo Tecnológico{rows.length !== 1 ? 's' : ''}</div>
        </>
      ) : null}

      {data ? (
        <div className="estagios-pagination">
          <button type="button" className="btn btn--secondary" disabled={!data.previous} onClick={() => setPage((current) => current - 1)}>
            Anterior
          </button>
          <span className="pagination__info">Página {page} • {total} registros</span>
          <button type="button" className="btn btn--secondary" disabled={!data.next} onClick={() => setPage((current) => current + 1)}>
            Próxima
          </button>
        </div>
      ) : null}
    </div>
  )
}