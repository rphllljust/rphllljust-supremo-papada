import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { CircleHelp, FileSpreadsheet } from 'lucide-react'
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
  const [draftSearch, setDraftSearch] = useState('')
  const [search, setSearch] = useState('')
  const [page, setPage] = useState(1)

  const { data, isLoading, isError } = useQuery({
    queryKey: ['eixos-tecnologicos', { search, page }],
    queryFn: () => eixosTecnologicosApi.list({ search, page }).then((response) => response.data),
    staleTime: 30_000,
  })

  const rows = data?.results || []
  const total = data?.count || 0

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
                  </tr>
                </thead>
                <tbody>
                  {isLoading ? (
                    <tr>
                      <td colSpan={2} className="area-cursos-table__empty">Carregando eixos tecnológicos...</td>
                    </tr>
                  ) : rows.map((row, index) => (
                    <tr key={row.descricao}>
                      <td>{(page - 1) * 10 + index + 1}</td>
                      <td>{row.descricao}</td>
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