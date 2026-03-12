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
  }
}

function mapRow(row) {
  return {
    id: row.id,
    sigla: row.sigla,
    descricao: row.descricao || row.nome,
    nivel: row.nivel_ensino,
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
  const [opcoes, setOpcoes] = useState({ niveis: [], tipos: [], grupos: [] })

  useEffect(() => {
    let isMounted = true
    componentesApi.list({}).then((response) => {
      if (!isMounted) return
      setOpcoes(mapOptions(response.data?.summary))
    }).catch(() => {
      if (!isMounted) return
      setOpcoes({ niveis: [], tipos: [], grupos: [] })
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
    <td>{row.nivel}</td>
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
  const [siglaRaw, setSiglaRaw] = useState('')
  const [fullText, setFullText] = useState('')
  const [nivel, setNivel] = useState('')
  const [tipo, setTipo] = useState('')
  const [grupo, setGrupo] = useState('')
  const [page, setPage] = useState(1)
  const [sort, setSort] = useState('id')
  const [dir, setDir] = useState('ASC')
  const [ativoChip, setAtivoChip] = useState(true)

  const sigla = useDebounce(siglaRaw, 400)
  const qDebounced = useDebounce(fullText, 500)
  const opcoes = useOpcoes()

  const queryParams = useMemo(() => ({
    ...(tab === 'utilizados' ? { ativo: 'SIM' } : {}),
    ...(tab === 'nao-utilizados' ? { ativo: 'NAO' } : {}),
    ...(tab === 'todos' && ativoChip ? { ativo: 'SIM' } : {}),
    ...(sigla ? { sigla } : {}),
    ...(qDebounced ? { q: qDebounced } : {}),
    ...(nivel ? { nivel_id: nivel } : {}),
    ...(tipo ? { tipo_id: tipo } : {}),
    ...(grupo ? { grupo_id: grupo } : {}),
    page,
    sort,
    dir,
  }), [tab, ativoChip, sigla, qDebounced, nivel, tipo, grupo, page, sort, dir])

  const { rows, total, loading, error } = useComponentes(queryParams)

  const onTab = useCallback((value) => { setTab(value); setPage(1) }, [])
  const onNivel = useCallback((value) => { setNivel(value); setPage(1) }, [])
  const onTipo = useCallback((value) => { setTipo(value); setPage(1) }, [])
  const onGrupo = useCallback((value) => { setGrupo(value); setPage(1) }, [])

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
    { key: 'nivel', label: 'Nível de ensino' },
    { key: 'grupo', label: 'Grupo de Atuação' },
    { key: 'hora_relogio', label: 'Hora/relógio', sortable: true },
    { key: 'hora_aula', label: 'Hora/aula', sortable: true },
    { key: 'qtd_creditos', label: 'Qtd. créditos', sortable: true },
    { key: 'ativo', label: 'Está ativo', sortable: true },
    { key: 'siglaQ', label: 'Sigla Q-Acadêmico' },
    { key: 'obs', label: 'Observação' },
  ]

  return (
    <div className="componentes-page page page--wide">
      <div className="componentes-page__toolbar">
        <button className="componentes-page__toolbar-btn componentes-page__toolbar-btn--green" onClick={() => navigate('/ensino/componentes/novo')}>
          + Adicionar Componente
        </button>
        <button className="componentes-page__toolbar-btn componentes-page__toolbar-btn--dgreen">Exportar para XLS</button>
        <button className="componentes-page__toolbar-btn componentes-page__toolbar-btn--blue">? Ajuda</button>
      </div>

      <div className="componentes-page__breadcrumb">
        Início &rsaquo; Ensino &rsaquo; Componentes
      </div>

      <div className="componentes-page__content">
        <h2 className="componentes-page__title">Componentes</h2>

        <div className="filters">
          <div className="filters__title">Filtros</div>
          <div className="filters__row">
            <div className="filter-group">
              <label>Sigla</label>
              <input value={siglaRaw} onChange={(e) => { setSiglaRaw(e.target.value); setPage(1) }} placeholder="ex: LIC" />
            </div>

            <div className="filter-group">
              <label>Busca full-text (PostgreSQL)</label>
              <input className="filter-group__fulltext" value={fullText} onChange={(e) => { setFullText(e.target.value); setPage(1) }} placeholder="ex: matemática" />
            </div>

            <div className="filter-group">
              <label>Está ativo</label>
              <div className="filter-tag">
                <span>{ativoChip ? 'Sim' : 'Todos'}</span>
                <span className="filter-tag__remove" onClick={() => { setAtivoChip(false); setPage(1) }}>✕</span>
              </div>
            </div>

            <FilterSelect label="Tipo" value={tipo} options={opcoes.tipos} onChange={onTipo} />
            <FilterSelect label="Nível de ensino" value={nivel} options={opcoes.niveis} onChange={onNivel} />
            <FilterSelect label="Grupo" value={grupo} options={opcoes.grupos} onChange={onGrupo} />
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
              ? '⏳ Consultando PostgreSQL…'
              : error
                ? `❌ ${error}`
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
                  <tr><td colSpan={12} className="td-empty">Nenhum componente encontrado.</td></tr>
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