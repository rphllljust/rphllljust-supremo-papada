import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { CircleHelp, Plus } from 'lucide-react'
import { Link, useNavigate } from 'react-router-dom'

import { areasCursoApi, cursosApi } from '@/api/endpoints'

export default function CursosFormacaoSuperiorPage() {
  const navigate = useNavigate()
  const [draftSearch, setDraftSearch] = useState('')
  const [draftArea, setDraftArea] = useState('')
  const [search, setSearch] = useState('')
  const [areaCurso, setAreaCurso] = useState('')
  const [page, setPage] = useState(1)

  const openPlaceholder = (slug, title, description) => {
    navigate(`/indisponivel/${slug}`, {
      state: { title, description },
    })
  }

  const { data, isLoading, isError } = useQuery({
    queryKey: ['cursos-formacao-superior', { search, areaCurso, page }],
    queryFn: () => cursosApi.list({ apenas_superiores: true, search, area_curso: areaCurso || undefined, page }).then((response) => response.data),
    staleTime: 30_000,
  })

  const { data: areasData } = useQuery({
    queryKey: ['areas-curso-options', 'formacao-superior'],
    queryFn: () => areasCursoApi.list({ page_size: 100 }).then((response) => response.data),
    staleTime: 60_000,
  })

  const rows = data?.results || []
  const total = data?.count || 0
  const areaOptions = areasData?.results || []

  return (
    <div className="page page--wide area-cursos-page">
      <nav className="profile-breadcrumb">
        <Link to="/dashboard">Início</Link>
        <span className="profile-breadcrumb__sep">&gt;</span>
        <span>Cursos de formação superior</span>
      </nav>

      <div className="page-header area-cursos-page__header">
        <div>
          <h1 className="page-title">Cursos de formação superior</h1>
        </div>
        <div className="page-header__actions">
          <button
            type="button"
            className="btn btn--primary"
            onClick={() => openPlaceholder('novo-curso-formacao-superior', 'Adicionar Curso de formação superior', 'O formulário de cadastro de curso de formação superior ainda não foi portado para o frontend React.')}
          >
            <Plus size={16} /> Adicionar Curso de formação superior
          </button>
          <Link
            to="/indisponivel/ajuda-cursos-formacao-superior"
            state={{
              title: 'Ajuda de Cursos de formação superior',
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
        <div className="cursos-superiores-filters-grid">
          <label className="area-cursos-filter-field">
            <span className="area-cursos-filter-field__label">Texto:</span>
            <input value={draftSearch} onChange={(event) => setDraftSearch(event.target.value)} />
          </label>

          <label className="area-cursos-filter-field">
            <span className="area-cursos-filter-field__label">Área do curso:</span>
            <select className="select" value={draftArea} onChange={(event) => setDraftArea(event.target.value)}>
              <option value="">Todos</option>
              {areaOptions.map((item) => (
                <option key={item.id} value={item.id}>{item.descricao}</option>
              ))}
            </select>
          </label>

          <div className="estagios-filters-card__actions">
            <button
              type="button"
              className="btn btn--secondary"
              onClick={() => {
                setSearch(draftSearch)
                setAreaCurso(draftArea)
                setPage(1)
              }}
            >
              Filtrar
            </button>
          </div>
        </div>
      </section>

      {isError ? (
        <div className="alert alert--error">Não foi possível carregar os cursos de formação superior com as permissões atuais.</div>
      ) : null}

      {!isLoading && rows.length === 0 ? (
        <div className="area-cursos-empty-notice">Nenhum Curso de formação superior encontrado.</div>
      ) : null}

      {rows.length > 0 ? (
        <>
          <div className="area-cursos-page__summary">Mostrando {rows.length} Curso de formação superior{rows.length !== 1 ? 'es' : ''}</div>

          <section className="dashboard-card area-cursos-table-card">
            <div className="area-cursos-table-wrapper">
              <table className="area-cursos-table cursos-superiores-table">
                <thead>
                  <tr>
                    <th className="area-cursos-table__index">#</th>
                    <th>Curso</th>
                    <th>Sigla</th>
                    <th>Área do curso</th>
                    <th>Unidade</th>
                    <th>Carga horária</th>
                  </tr>
                </thead>
                <tbody>
                  {rows.map((row, index) => (
                    <tr key={row.id}>
                      <td>{(page - 1) * 10 + index + 1}</td>
                      <td>{row.nome}</td>
                      <td>{row.sigla || '-'}</td>
                      <td>{row.area_curso_nome || '-'}</td>
                      <td>{row.unidade_nome}</td>
                      <td>{row.carga_horaria ? `${row.carga_horaria}h` : '-'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>

          <div className="area-cursos-page__summary">Mostrando {rows.length} Curso de formação superior{rows.length !== 1 ? 'es' : ''}</div>
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