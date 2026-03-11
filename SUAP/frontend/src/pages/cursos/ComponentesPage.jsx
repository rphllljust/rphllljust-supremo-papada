import { useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { CircleHelp, Eye, FileSpreadsheet, Pencil, Plus } from 'lucide-react'
import { Link, useNavigate } from 'react-router-dom'

import { componentesApi } from '@/api/endpoints'

const TAB_ITEMS = [
  { key: 'TODOS', label: 'Todos' },
  { key: 'UTILIZADOS', label: 'Utilizados' },
  { key: 'NAO_UTILIZADOS', label: 'Não Utilizados' },
]

function exportRowsToExcel(rows) {
  const headers = ['ID', 'Sigla', 'Descrição', 'Nível de ensino', 'Grupo de Atuação', 'Hora/relógio', 'Hora/aula', 'Qtd. de créditos', 'Está ativo', 'Sigla do Q-Acadêmico', 'Observação']
  const body = rows.map((row) => [
    row.id,
    row.sigla,
    row.descricao,
    row.nivel_ensino,
    row.grupo_atuacao,
    row.carga_horaria,
    row.hora_aula,
    row.qtd_creditos,
    row.esta_ativo ? 'Sim' : 'Não',
    row.sigla_qacademico,
    row.observacao,
  ])
  const content = [headers, ...body]
    .map((columns) => columns.map((value) => `"${String(value ?? '').replaceAll('"', '""')}"`).join('\t'))
    .join('\n')

  const blob = new Blob([content], { type: 'application/vnd.ms-excel;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = 'componentes.xls'
  link.click()
  URL.revokeObjectURL(url)
}

function SummaryBadge({ count }) {
  return <span className="estagios-tab__count">{count || 0}</span>
}

export default function ComponentesPage() {
  const navigate = useNavigate()
  const [draftFilters, setDraftFilters] = useState({
    search: '',
    ativo: 'SIM',
    tipo_componente: '',
    nivel_ensino: '',
    matriz_curricular: '',
    grupo_atuacao: '',
  })
  const [filters, setFilters] = useState({
    search: '',
    ativo: 'SIM',
    tipo_componente: '',
    nivel_ensino: '',
    matriz_curricular: '',
    grupo_atuacao: '',
  })
  const [page, setPage] = useState(1)
  const [activeTab, setActiveTab] = useState('TODOS')

  const queryParams = useMemo(() => {
    const next = {
      ...filters,
      aba: activeTab,
      page,
    }

    Object.keys(next).forEach((key) => {
      if (next[key] === '') {
        delete next[key]
      }
    })

    return next
  }, [activeTab, filters, page])

  const openPlaceholder = (slug, title, description) => {
    navigate(`/indisponivel/${slug}`, {
      state: { title, description },
    })
  }

  const { data, isLoading, isError } = useQuery({
    queryKey: ['componentes', queryParams],
    queryFn: () => componentesApi.list(queryParams).then((response) => response.data),
    staleTime: 30_000,
  })

  const rows = data?.results || []
  const summary = data?.summary || {}
  const filterOptions = summary.filter_options || {}
  const tabCounts = summary.tab_counts || {}

  return (
    <div className="page page--wide area-cursos-page">
      <nav className="profile-breadcrumb">
        <Link to="/dashboard">Início</Link>
        <span className="profile-breadcrumb__sep">&gt;</span>
        <span>Componentes</span>
      </nav>

      <div className="page-header area-cursos-page__header">
        <div>
          <h1 className="page-title">Componentes</h1>
        </div>
        <div className="page-header__actions">
          <button
            type="button"
            className="btn btn--primary"
            onClick={() => openPlaceholder('novo-componente', 'Adicionar Componente', 'O formulário de cadastro de componente ainda não foi portado para o frontend React.')}
          >
            <Plus size={16} /> Adicionar Componente
          </button>
          <button type="button" className="btn btn--dark" onClick={() => exportRowsToExcel(rows)}>
            <FileSpreadsheet size={16} /> Exportar para XLS
          </button>
          <Link
            to="/indisponivel/ajuda-componentes"
            state={{
              title: 'Ajuda de Componentes',
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
        <div className="componentes-filters-grid">
          <label className="area-cursos-filter-field">
            <span className="area-cursos-filter-field__label">Texto:</span>
            <input value={draftFilters.search} onChange={(event) => setDraftFilters((current) => ({ ...current, search: event.target.value }))} />
          </label>
          <label className="area-cursos-filter-field">
            <span className="area-cursos-filter-field__label">Está ativo:</span>
            <select className="select" value={draftFilters.ativo} onChange={(event) => setDraftFilters((current) => ({ ...current, ativo: event.target.value }))}>
              <option value="">Todos</option>
              <option value="SIM">Sim</option>
              <option value="NAO">Não</option>
            </select>
          </label>
          <label className="area-cursos-filter-field">
            <span className="area-cursos-filter-field__label">Tipo do Componente:</span>
            <select className="select" value={draftFilters.tipo_componente} onChange={(event) => setDraftFilters((current) => ({ ...current, tipo_componente: event.target.value }))}>
              <option value="">Todos</option>
              {(filterOptions.tipos_componente || []).map((item) => (
                <option key={item.value} value={item.value}>{item.label}</option>
              ))}
            </select>
          </label>
          <label className="area-cursos-filter-field">
            <span className="area-cursos-filter-field__label">Nível de ensino:</span>
            <select className="select" value={draftFilters.nivel_ensino} onChange={(event) => setDraftFilters((current) => ({ ...current, nivel_ensino: event.target.value }))}>
              <option value="">Todos</option>
              {(filterOptions.niveis_ensino || []).map((item) => (
                <option key={item.value} value={item.value}>{item.label}</option>
              ))}
            </select>
          </label>
          <label className="area-cursos-filter-field">
            <span className="area-cursos-filter-field__label">Matriz Curricular:</span>
            <select className="select" value={draftFilters.matriz_curricular} onChange={(event) => setDraftFilters((current) => ({ ...current, matriz_curricular: event.target.value }))}>
              <option value="">Todos</option>
              {(filterOptions.matrizes_curriculares || []).map((item) => (
                <option key={item.value} value={item.value}>{item.label}</option>
              ))}
            </select>
          </label>
          <label className="area-cursos-filter-field">
            <span className="area-cursos-filter-field__label">Grupo de Atuação:</span>
            <select className="select" value={draftFilters.grupo_atuacao} onChange={(event) => setDraftFilters((current) => ({ ...current, grupo_atuacao: event.target.value }))}>
              <option value="">Todos</option>
              {(filterOptions.grupos_atuacao || []).map((item) => (
                <option key={item.value} value={item.value}>{item.label}</option>
              ))}
            </select>
          </label>
          <div className="estagios-filters-card__actions">
            <button
              type="button"
              className="btn btn--secondary"
              onClick={() => {
                setFilters(draftFilters)
                setPage(1)
              }}
            >
              Filtrar
            </button>
          </div>
        </div>
      </section>

      <div className="estagios-tabs">
        {TAB_ITEMS.map((tab) => (
          <button key={tab.key} type="button" className={`estagios-tab ${activeTab === tab.key ? 'estagios-tab--active' : ''}`} onClick={() => { setActiveTab(tab.key); setPage(1) }}>
            <span>{tab.label}</span>
            <SummaryBadge count={tabCounts[tab.key]} />
          </button>
        ))}
      </div>

      {isError ? (
        <div className="alert alert--error">Não foi possível carregar os componentes com as permissões atuais.</div>
      ) : null}

      <div className="area-cursos-page__summary">Mostrando {rows.length} Componente{rows.length !== 1 ? 's' : ''}</div>

      <section className="dashboard-card area-cursos-table-card">
        <div className="area-cursos-table-wrapper">
          <table className="area-cursos-table componentes-table">
            <thead>
              <tr>
                <th className="area-cursos-table__index">#</th>
                <th>ID</th>
                <th>Sigla</th>
                <th>Descrição</th>
                <th>Nível de ensino</th>
                <th>Grupo de Atuação</th>
                <th>Hora/relógio</th>
                <th>Hora/aula</th>
                <th>Qtd. de créditos</th>
                <th>Está ativo</th>
                <th>Sigla do Q-Acadêmico</th>
                <th>Observação</th>
              </tr>
            </thead>
            <tbody>
              {isLoading ? (
                <tr>
                  <td colSpan={12} className="area-cursos-table__empty">Carregando componentes...</td>
                </tr>
              ) : rows.length === 0 ? (
                <tr>
                  <td colSpan={12} className="area-cursos-table__empty">Nenhum componente encontrado.</td>
                </tr>
              ) : rows.map((row) => (
                <tr key={row.id}>
                  <td>
                    <div className="area-cursos-table__actions">
                      <button type="button" className="btn btn--outline btn--icon" onClick={() => navigate(`/componentes/${row.id}`)} aria-label={`Ver componente ${row.descricao}`}>
                        <Eye size={14} />
                      </button>
                      <button type="button" className="btn btn--outline btn--icon" onClick={() => navigate(`/componentes/${row.id}/editar`)} aria-label={`Editar componente ${row.descricao}`}>
                        <Pencil size={14} />
                      </button>
                    </div>
                  </td>
                  <td>{row.id}</td>
                  <td>{row.sigla || '-'}</td>
                  <td>{row.descricao}</td>
                  <td>{row.nivel_ensino || '-'}</td>
                  <td>{row.grupo_atuacao || '-'}</td>
                  <td>{row.carga_horaria || '-'}</td>
                  <td>{row.hora_aula || '-'}</td>
                  <td>{row.qtd_creditos || '-'}</td>
                  <td>{row.esta_ativo ? 'Sim' : 'Não'}</td>
                  <td>{row.sigla_qacademico || '-'}</td>
                  <td>{row.observacao || '-'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <div className="area-cursos-page__summary">Mostrando {rows.length} Componente{rows.length !== 1 ? 's' : ''}</div>

      {data ? (
        <div className="estagios-pagination">
          <button type="button" className="btn btn--secondary" disabled={!data.previous} onClick={() => setPage((current) => current - 1)}>Anterior</button>
          <span className="pagination__info">Página {page} • {data.count || 0} registros</span>
          <button type="button" className="btn btn--secondary" disabled={!data.next} onClick={() => setPage((current) => current + 1)}>Próxima</button>
        </div>
      ) : null}
    </div>
  )
}