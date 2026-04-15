import { useState, useMemo, useCallback, useEffect, useRef, memo } from 'react'
import { useNavigate } from 'react-router-dom'
import { componentesApi } from '@/api/endpoints'
import './suap-componentes.css'

function useDebounce(value, ms = 350) {
  const [dv, setDv] = useState(value)

  useEffect(() => {
    const t = setTimeout(() => setDv(value), ms)
    return () => clearTimeout(t)
  }, [value, ms])

  return dv
}

function mapOptions(summary) {
  const filterOptions = summary?.filter_options || {}
  return {
    niveis: (filterOptions.niveis_ensino || []).map((item) => ({ id: item.value, nome: item.label })),
    tipos: (filterOptions.tipos_componente || []).map((item) => ({ id: item.value, nome: item.label })),
    grupos: (filterOptions.grupos_atuacao || []).map((item) => ({ id: item.value, nome: item.label })),
    matrizes: (filterOptions.matrizes_curriculares || []).map((item) => ({ id: item.value, nome: item.label })),
    eixos: (filterOptions.eixos_tecnologicos || []).map((item) => ({ id: item.value, nome: item.label })),
  }
}

function mapRow(row) {
  return {
    id: row.id,
    sigla: row.sigla,
    descricao: row.descricao || row.nome,
    tipo: row.tipo_componente_nome || row.tipo_componente,
    nivel: row.nivel_ensino_nome || row.nivel_ensino,
    eixo: row.eixo_tecnologico,
    grupo: row.grupo_atuacao,
    hora_relogio: row.carga_horaria,
    hora_aula: row.hora_aula,
    qtd_creditos: row.qtd_creditos,
    ativo: row.esta_ativo,
    sigla_q_academico: row.sigla_qacademico,
    observacao: row.observacao,
  }
}

function useOpcoes() {
  const [opcoes, setOpcoes] = useState({ niveis: [], tipos: [], grupos: [], matrizes: [], eixos: [] })

  useEffect(() => {
    let isMounted = true
    componentesApi.list({}).then((response) => {
      if (!isMounted) return
      setOpcoes(mapOptions(response.data?.summary))
    }).catch(() => {
      if (!isMounted) return
      setOpcoes({ niveis: [], tipos: [], grupos: [], matrizes: [], eixos: [] })
    })

    return () => {
      isMounted = false
    }
  }, [])

  return opcoes
}

function useComponentes(params) {
  const [rows, setRows] = useState([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const abortRef = useRef(null)
  const key = useMemo(() => JSON.stringify(params), [params])

  useEffect(() => {
    abortRef.current = { cancelled: false }
    const current = abortRef.current

    setLoading(true)
    setError(null)

    componentesApi.list(params)
      .then((response) => {
        if (current.cancelled) return
        setRows((response.data?.results || []).map(mapRow))
        setTotal(response.data?.count || 0)
      })
      .catch((err) => {
        if (current.cancelled) return
        setError(err?.response?.data?.detail || String(err?.message || err))
      })
      .finally(() => {
        if (current.cancelled) return
        setLoading(false)
      })

    return () => {
      current.cancelled = true
    }
  }, [key, params])

  return { rows, total, loading, error }
}

const ActionButtons = memo(({ onView, onEdit }) => (
  <div className="action-btns">
    <button className="btn-action btn-action--orange" title="Visualizar" onClick={onView}>👁</button>
    <button className="btn-action btn-action--blue" title="Editar" onClick={onEdit}>✏</button>
  </div>
))

const StatusDot = memo(({ active }) => (
  <span className={`status-dot ${active ? 'status-dot--active' : 'status-dot--inactive'}`} />
))

const TableRow = memo(({ row, onView, onEdit }) => (
  <tr>
    <td><ActionButtons onView={onView} onEdit={onEdit} /></td>
    <td>{row.id}</td>
    <td className="td--link" onClick={onView}>{row.sigla}</td>
    <td>{row.descricao}</td>
    <td>{row.tipo}</td>
    <td>{row.nivel}</td>
    <td className="td--dash">{row.eixo || '-'}</td>
    <td className="td--dash">{row.grupo || '-'}</td>
    <td className="td--center">{row.hora_relogio}</td>
    <td className="td--center">{row.hora_aula}</td>
    <td className="td--center">{row.qtd_creditos}</td>
    <td className="td--center"><StatusDot active={row.ativo} /></td>
    <td className="td--dash">{row.sigla_q_academico || '-'}</td>
    <td className="td--dash">{row.observacao || '-'}</td>
  </tr>
))

const FilterSelect = memo(({ label, value, options, onChange }) => (
  <div className="filter-group">
    <label>{label}</label>
    <select value={value} onChange={(e) => onChange(e.target.value)}>
      <option value="">Todos</option>
      {options.map((o) => <option key={o.id} value={o.id}>{o.nome}</option>)}
    </select>
  </div>
))

const Pagination = memo(({ page, totalPages, onPrev, onNext }) => (
  <div className="pagination">
    <button className="pagination__btn" disabled={page <= 1} onClick={onPrev}>‹ Anterior</button>
    <span className="pagination__info">Página {page} de {totalPages}</span>
    <button className="pagination__btn" disabled={page >= totalPages} onClick={onNext}>Próxima ›</button>
  </div>
))

export default function ComponentesPage() {
  const navigate = useNavigate()
  const [tab, setTab] = useState('todos')
  const [draftFilters, setDraftFilters] = useState({
    sigla: '',
    search: '',
    ativo: 'SIM',
    nivel: '',
    tipo: '',
    grupo: '',
    eixo: '',
    matriz: '',
  })
  const [filters, setFilters] = useState({
    sigla: '',
    search: '',
    ativo: 'SIM',
    nivel: '',
    tipo: '',
    grupo: '',
    eixo: '',
    matriz: '',
  })
  const [page, setPage] = useState(1)
  const [sort, setSort] = useState('id')
  const [dir, setDir] = useState('ASC')

  const sigla = useDebounce(filters.sigla, 250)
  const qDebounced = useDebounce(filters.search, 250)
  const opcoes = useOpcoes()

  const queryParams = useMemo(() => ({
    ...(tab === 'utilizados' ? { ativo: 'SIM' } : {}),
    ...(tab === 'nao-utilizados' ? { ativo: 'NAO' } : {}),
    ...(tab === 'todos' && filters.ativo ? { ativo: filters.ativo } : {}),
    ...(sigla ? { sigla } : {}),
    ...(qDebounced ? { q: qDebounced } : {}),
    ...(filters.nivel ? { nivel_id: filters.nivel } : {}),
    ...(filters.tipo ? { tipo_id: filters.tipo } : {}),
    ...(filters.grupo ? { grupo_id: filters.grupo } : {}),
    ...(filters.eixo ? { eixo_id: filters.eixo } : {}),
    ...(filters.matriz ? { matriz_id: filters.matriz } : {}),
    page,
    sort,
    dir,
  }), [tab, filters.ativo, filters.nivel, filters.tipo, filters.grupo, filters.eixo, filters.matriz, sigla, qDebounced, page, sort, dir])

  const { rows, total, loading, error } = useComponentes(queryParams)

  const onTab = useCallback((value) => { setTab(value); setPage(1) }, [])
  const updateDraftFilter = useCallback((field, value) => {
    setDraftFilters((current) => ({ ...current, [field]: value }))
  }, [])

  const applyFilters = useCallback(() => {
    setFilters(draftFilters)
    setPage(1)
  }, [draftFilters])

  const clearFilters = useCallback(() => {
    const initialFilters = {
      sigla: '',
      search: '',
      ativo: 'SIM',
      nivel: '',
      tipo: '',
      grupo: '',
      eixo: '',
      matriz: '',
    }

    setDraftFilters(initialFilters)
    setFilters(initialFilters)
    setPage(1)
  }, [])

  const toggleSort = useCallback((col) => {
    setSort((prev) => {
      setDir(prev === col && dir === 'ASC' ? 'DESC' : 'ASC')
      return col
    })
    setPage(1)
  }, [dir])

  const totalPages = Math.max(1, Math.ceil(total / 10))

  const COLS = [
    { key: 'actions', label: '#' },
    { key: 'id', label: 'ID', sortable: true },
    { key: 'sigla', label: 'Sigla', sortable: true },
    { key: 'descricao', label: 'Descrição', sortable: true },
    { key: 'tipo', label: 'Tipo do componente' },
    { key: 'nivel', label: 'Nível de ensino' },
    { key: 'eixo', label: 'Eixo tecnológico' },
    { key: 'grupo', label: 'Grupo de Atuação' },
    { key: 'hora_relogio', label: 'Hora/relógio', sortable: true },
    { key: 'hora_aula', label: 'Hora/aula', sortable: true },
    { key: 'qtd_creditos', label: 'Qtd. créditos', sortable: true },
    { key: 'ativo', label: 'Está ativo', sortable: true },
    { key: 'siglaQ', label: 'Sigla Q-Acadêmico' },
    { key: 'obs', label: 'Observação' },
  ]

  return (
    <div className="componentes-page page page--wide suap-componentes-shell">
      <div className="componentes-page__toolbar">
        <button className="componentes-page__toolbar-btn componentes-page__toolbar-btn--green" onClick={() => navigate('/ensino/componentes/novo')}>
          + Adicionar Componente
        </button>
        <button className="componentes-page__toolbar-btn componentes-page__toolbar-btn--dgreen">Exportar para XLS</button>
        <button className="componentes-page__toolbar-btn componentes-page__toolbar-btn--blue">? Ajuda</button>
      </div>

      <div className="componentes-page__breadcrumb">
        Início &rsaquo; Ensino &rsaquo; Cursos, Matrizes e Componentes &rsaquo; Componentes
      </div>

      <div className="componentes-page__content">
        <h2 className="componentes-page__title">Componentes</h2>

        <div className="filters">
          <div className="filters__header">
            <div className="filters__title">Filtros de busca</div>
            <div className="filters__subtitle">Refine a listagem por sigla, texto livre, tipo, matriz curricular e demais atributos.</div>
          </div>
          <div className="filters__row">
            <div className="filter-group">
              <label>Sigla</label>
              <input value={draftFilters.sigla} onChange={(e) => updateDraftFilter('sigla', e.target.value)} placeholder="ex: LIC" />
            </div>

            <div className="filter-group">
              <label>Texto</label>
              <input className="filter-group__fulltext" value={draftFilters.search} onChange={(e) => updateDraftFilter('search', e.target.value)} placeholder="ex: matemática" />
            </div>

            <FilterSelect label="Está ativo" value={draftFilters.ativo} options={[{ id: 'SIM', nome: 'Sim' }, { id: 'NAO', nome: 'Não' }]} onChange={(value) => updateDraftFilter('ativo', value)} />
            <FilterSelect label="Tipo" value={draftFilters.tipo} options={opcoes.tipos} onChange={(value) => updateDraftFilter('tipo', value)} />
            <FilterSelect label="Nível de ensino" value={draftFilters.nivel} options={opcoes.niveis} onChange={(value) => updateDraftFilter('nivel', value)} />
            <FilterSelect label="Eixo tecnológico" value={draftFilters.eixo} options={opcoes.eixos} onChange={(value) => updateDraftFilter('eixo', value)} />
            <FilterSelect label="Matriz curricular" value={draftFilters.matriz} options={opcoes.matrizes} onChange={(value) => updateDraftFilter('matriz', value)} />
            <FilterSelect label="Grupo" value={draftFilters.grupo} options={opcoes.grupos} onChange={(value) => updateDraftFilter('grupo', value)} />
          </div>

          <div className="filters__actions">
            <button type="button" className="filters__button filters__button--primary" onClick={applyFilters}>Filtrar</button>
            <button type="button" className="filters__button" onClick={clearFilters}>Limpar</button>
          </div>
        </div>

        <div className="tabs">
          {[['todos', 'Todos'], ['utilizados', 'Utilizados'], ['nao-utilizados', 'Não Utilizados']].map(([k, l]) => (
            <button key={k} onClick={() => onTab(k)} className={`tab ${tab === k ? 'tab--active' : ''}`}>{l}</button>
          ))}
        </div>

        <div className="table-wrapper">
          <div className={`table-info ${error ? 'table-info--error' : ''}`}>
            {loading
              ? 'Consultando componentes...'
              : error
                ? error
                : `Mostrando ${rows.length} de ${total} Componentes`}
          </div>

          <div className="table-scroll">
            <table>
              <thead>
                <tr>
                  {COLS.map((col) => (
                    <th key={col.key} className={col.sortable ? 'sortable' : ''} onClick={() => col.sortable && toggleSort(col.key)}>
                      {col.label}
                      {col.sortable && sort === col.key && <span className="sort-arrow">{dir === 'ASC' ? '▲' : '▼'}</span>}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {rows.map((row) => <TableRow key={row.id} row={row} onView={() => navigate(`/componentes/${row.id}`)} onEdit={() => navigate(`/componentes/${row.id}/editar`)} />)}
                {!loading && !rows.length && (
                  <tr><td colSpan={COLS.length} className="td-empty">Nenhum componente encontrado.</td></tr>
                )}
              </tbody>
            </table>
          </div>

          {totalPages > 1 && (
            <Pagination page={page} totalPages={totalPages} onPrev={() => setPage((p) => p - 1)} onNext={() => setPage((p) => p + 1)} />
          )}

          <div className="table-info">
            Mostrando {rows.length} de {total} Componentes
          </div>
        </div>

        <div className="footer-actions">
          <button className="btn btn--red">⚠ Reportar erro</button>
          <button className="btn btn--blue" onClick={() => window.print()}>🖨 Imprimir</button>
          <button className="btn btn--gray" onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}>↑ Topo</button>
        </div>
      </div>
    </div>
  )
}
