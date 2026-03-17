import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { CircleHelp, Eye, FileSpreadsheet, Pencil, Plus } from 'lucide-react'
import { Link, useNavigate } from 'react-router-dom'

import { areasCursoApi } from '@/api/endpoints'

function exportRowsToExcel(rows) {
  const headers = ['#', 'Código CINE', 'CINE', 'Área detalhada', 'Área específica', 'Área geral']
  const body = rows.map((row) => [row.id, row.codigo_cine, row.cine || row.descricao, row.area_detalhada, row.area_especifica, row.area_geral])
  const content = [headers, ...body]
    .map((columns) => columns.map((value) => `"${String(value ?? '').replaceAll('"', '""')}"`).join('\t'))
    .join('\n')

  const blob = new Blob([content], { type: 'application/vnd.ms-excel;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = 'areas-de-curso.xls'
  link.click()
  URL.revokeObjectURL(url)
}

export default function AreasCursosPage() {
  const navigate = useNavigate()
  const [draftSearch, setDraftSearch] = useState('')
  const [search, setSearch] = useState('')
  const [page, setPage] = useState(1)

  const { data, isLoading, isError } = useQuery({
    queryKey: ['areas-curso', { search, page }],
    queryFn: () => areasCursoApi.list({ search, page }).then((response) => response.data),
    staleTime: 30_000,
  })

  const rows = data?.results || []
  const total = data?.count || 0

  return (
    <div className="page page--wide area-cursos-page">
      <nav className="profile-breadcrumb">
        <Link to="/dashboard">Início</Link>
        <span className="profile-breadcrumb__sep">&gt;</span>
        <span>Áreas de cursos</span>
      </nav>

      <div className="page-header area-cursos-page__header">
        <div>
          <h1 className="page-title">Áreas de cursos</h1>
        </div>
        <div className="page-header__actions">
          <button
            type="button"
            className="btn btn--primary"
            onClick={() => navigate('/ensino/areacurso/nova')}
          >
            <Plus size={16} /> Adicionar Área de curso
          </button>
          <button type="button" className="btn btn--dark" onClick={() => exportRowsToExcel(rows)}>
            <FileSpreadsheet size={16} /> Exportar para XLS
          </button>
          <Link
            to="/indisponivel/ajuda-areas-de-cursos"
            state={{
              title: 'Ajuda de Áreas de cursos',
              description: 'A ajuda detalhada desta funcionalidade ainda será portada para o frontend React.',
            }}
            className="btn btn--outline"
          >
            <CircleHelp size={16} /> Ajuda
          </Link>
        </div>
      </div>

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
        <div className="alert alert--error">Não foi possível carregar as áreas de cursos com as permissões atuais.</div>
      ) : null}

      <div className="area-cursos-page__summary">Mostrando {rows.length} área{rows.length !== 1 ? 's' : ''} de curso</div>

      <section className="dashboard-card area-cursos-table-card">
        <div className="area-cursos-table-wrapper">
          <table className="area-cursos-table">
            <thead>
              <tr>
                <th className="area-cursos-table__index">#</th>
                <th>Descrição</th>
              </tr>
            </thead>
            <tbody>
              {isLoading ? (
                <tr>
                  <td colSpan={2} className="area-cursos-table__empty">Carregando áreas de cursos...</td>
                </tr>
              ) : rows.length === 0 ? (
                <tr>
                  <td colSpan={2} className="area-cursos-table__empty">Nenhuma área de curso encontrada.</td>
                </tr>
              ) : rows.map((row) => (
                <tr key={row.id}>
                  <td>
                    <div className="area-cursos-table__actions">
                      <button type="button" className="btn btn--outline btn--icon" onClick={() => navigate(`/ensino/areacurso/${row.id}`)} aria-label={`Ver área ${row.descricao}`}>
                        <Eye size={14} />
                      </button>
                      <button
                        type="button"
                        className="btn btn--outline btn--icon"
                        onClick={() => navigate(`/ensino/areacurso/${row.id}/editar`)}
                        aria-label={`Editar área ${row.descricao}`}
                      >
                        <Pencil size={14} />
                      </button>
                    </div>
                  </td>
                  <td>{row.codigo_cine ? `${row.codigo_cine} - ${row.cine || row.descricao}` : (row.cine || row.descricao)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <div className="area-cursos-page__summary">Mostrando {rows.length} área{rows.length !== 1 ? 's' : ''} de curso</div>

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