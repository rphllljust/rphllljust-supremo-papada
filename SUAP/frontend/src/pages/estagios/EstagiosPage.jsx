import { useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { CircleHelp, Eye, FileSpreadsheet } from 'lucide-react'
import { Link } from 'react-router-dom'

import { estagiosApi } from '@/api/endpoints'

const TAB_ITEMS = [
  { key: 'TODOS', label: 'Todos' },
  { key: 'EM_ANDAMENTO', label: 'Em Andamento' },
  { key: 'MATRICULAS_IRREGULARES', label: 'Matrículas Irregulares' },
  { key: 'DATA_PREVISTA_ATINGIDA', label: 'Atingiu a Data de Prevista de Encerramento' },
  { key: 'PENDENCIA_RELATORIO_ESTAGIARIO', label: 'Pendência de Relatório de Atividades do Estagiário' },
  { key: 'PENDENCIA_RELATORIO_SUPERVISOR', label: 'Pendência de Relatório de Atividades do Supervisor' },
  { key: 'SEM_ASSINATURA_RELATORIOS', label: 'Sem Assinatura em Relatórios de Atividades' },
  { key: 'APTO_ENCERRAMENTO', label: 'Apto para Encerramento' },
  { key: 'ENCERRADOS', label: 'Encerrados' },
]

const DEFAULT_FILTERS = {
  search: '',
  modalidade: '',
  status: '',
  matricula_status: '',
  curso: '',
  campus: '',
  possui_aditivo: '',
  tipo_aditivo: '',
  data_inicio_de: '',
  data_inicio_ate: '',
  data_prevista_de: '',
  data_prevista_ate: '',
  data_encerramento_de: '',
  data_encerramento_ate: '',
  convenio: '',
  aguardando_assinatura: '',
}

function formatDate(value) {
  if (!value) {
    return '-'
  }

  const date = new Date(`${value}T00:00:00`)
  if (Number.isNaN(date.getTime())) {
    return value
  }

  return new Intl.DateTimeFormat('pt-BR').format(date)
}

function exportRowsToExcel(rows) {
  const headers = [
    'Tipo',
    'Estagiario',
    'Situacao do Estagiario',
    'Situacao da Matricula no Periodo',
    'Campus',
    'Concedente',
    'Situacao do Convenio',
    'Professor Orientador',
    'Data de Inicio',
    'Data Prevista para Encerramento',
    'Data do Encerramento',
    'Aditivos Contratuais',
  ]

  const body = rows.map((row) => [
    row.tipo,
    `${row.aluno_nome} (${row.aluno_identificador})`,
    row.situacao_estagiario,
    row.situacao_matricula_periodo,
    row.campus_codigo || row.campus_nome,
    row.concedente_nome,
    row.situacao_convenio,
    row.professor_orientador,
    formatDate(row.data_inicio),
    formatDate(row.data_prevista_encerramento),
    formatDate(row.data_encerramento),
    row.aditivos_contratuais?.length
      ? row.aditivos_contratuais.map((item) => item.descricao).join(' | ')
      : '-',
  ])

  const content = [headers, ...body]
    .map((columns) => columns.map((value) => `"${String(value ?? '').replaceAll('"', '""')}"`).join('\t'))
    .join('\n')

  const blob = new Blob([content], { type: 'application/vnd.ms-excel;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = 'estagios.xls'
  link.click()
  URL.revokeObjectURL(url)
}

function FilterField({ label, children }) {
  return (
    <label className="estagios-filter-field">
      <span className="estagios-filter-field__label">{label}</span>
      {children}
    </label>
  )
}

function SummaryBadge({ count }) {
  return <span className="estagios-tab__count">{count || 0}</span>
}

export default function EstagiosPage() {
  const [draftFilters, setDraftFilters] = useState(DEFAULT_FILTERS)
  const [filters, setFilters] = useState(DEFAULT_FILTERS)
  const [page, setPage] = useState(1)
  const [activeTab, setActiveTab] = useState('TODOS')

  const queryParams = useMemo(() => {
    const next = {
      ...filters,
      aba: activeTab,
      page,
    }

    if (filters.tipo_aditivo === 'ADITADO' && !filters.possui_aditivo) {
      next.possui_aditivo = 'SIM'
    }

    Object.keys(next).forEach((key) => {
      if (next[key] === '') {
        delete next[key]
      }
    })

    delete next.tipo_aditivo

    return next
  }, [activeTab, filters, page])

  const { data, isLoading, isError } = useQuery({
    queryKey: ['estagios', queryParams],
    queryFn: () => estagiosApi.list(queryParams).then((response) => response.data),
    staleTime: 30_000,
  })

  const rows = data?.results || []
  const summary = data?.summary || {}
  const filterOptions = summary.filter_options || {}
  const tabCounts = summary.tab_counts || {}

  const updateDraftFilter = (field, value) => {
    setDraftFilters((current) => ({
      ...current,
      [field]: value,
    }))
  }

  const handleApplyFilters = () => {
    setFilters(draftFilters)
    setPage(1)
  }

  const handleTabChange = (tabKey) => {
    setActiveTab(tabKey)
    setPage(1)
  }

  return (
    <div className="page page--wide estagios-page">
      <nav className="profile-breadcrumb">
        <Link to="/dashboard">Inicio</Link>
        <span className="profile-breadcrumb__sep">&gt;</span>
        <span>Estágios</span>
      </nav>

      <div className="page-header estagios-page__header">
        <div>
          <h1 className="page-title">Estágios</h1>
        </div>
        <div className="page-header__actions">
          <button type="button" className="btn btn--dark" onClick={() => exportRowsToExcel(rows)}>
            <FileSpreadsheet size={16} /> Exportar para XLS
          </button>
          <Link
            to="/indisponivel/estagios-ajuda"
            state={{
              title: 'Ajuda de Estágios',
              description: 'A documentação detalhada de ajuda do módulo de estágios ainda será portada para o frontend React.',
            }}
            className="btn btn--outline"
          >
            <CircleHelp size={16} /> Ajuda
          </Link>
        </div>
      </div>

      <section className="dashboard-card estagios-filters-card">
        <div className="estagios-filters-card__title">Filtros:</div>

        <div className="estagios-filters-grid">
          <FilterField label="Texto:">
            <input type="text" value={draftFilters.search} onChange={(event) => updateDraftFilter('search', event.target.value)} />
          </FilterField>

          <FilterField label="O estágio é obrigatório:">
            <select className="select" value={draftFilters.modalidade} onChange={(event) => updateDraftFilter('modalidade', event.target.value)}>
              <option value="">Todos</option>
              {(filterOptions.modalidades || []).map((option) => (
                <option key={option.value} value={option.value}>{option.label}</option>
              ))}
            </select>
          </FilterField>

          <FilterField label="Situação:">
            <select className="select" value={draftFilters.status} onChange={(event) => updateDraftFilter('status', event.target.value)}>
              <option value="">Todos</option>
              {(filterOptions.status || []).map((option) => (
                <option key={option.value} value={option.value}>{option.label}</option>
              ))}
            </select>
          </FilterField>

          <FilterField label="Situação da Matrícula Período:">
            <select className="select" value={draftFilters.matricula_status} onChange={(event) => updateDraftFilter('matricula_status', event.target.value)}>
              <option value="">Todos</option>
              {(filterOptions.matricula_status || []).map((option) => (
                <option key={option.value} value={option.value}>{option.label}</option>
              ))}
            </select>
          </FilterField>

          <FilterField label="Curso:">
            <select className="select" value={draftFilters.curso} onChange={(event) => updateDraftFilter('curso', event.target.value)}>
              <option value="">Todos</option>
              {(filterOptions.cursos || []).map((option) => (
                <option key={option.value} value={option.value}>{option.label}</option>
              ))}
            </select>
          </FilterField>

          <FilterField label="Campus:">
            <select className="select" value={draftFilters.campus} onChange={(event) => updateDraftFilter('campus', event.target.value)}>
              <option value="">Todos</option>
              {(filterOptions.campi || []).map((option) => (
                <option key={option.value} value={option.value}>{option.label}</option>
              ))}
            </select>
          </FilterField>

          <FilterField label="Possui Aditivo Contratual?:">
            <select className="select" value={draftFilters.possui_aditivo} onChange={(event) => updateDraftFilter('possui_aditivo', event.target.value)}>
              <option value="">Todos</option>
              <option value="SIM">Sim</option>
              <option value="NAO">Não</option>
            </select>
          </FilterField>

          <FilterField label="Tipo de Aditivo Contratual:">
            <select className="select" value={draftFilters.tipo_aditivo} onChange={(event) => updateDraftFilter('tipo_aditivo', event.target.value)}>
              <option value="">Todos</option>
              <option value="ADITADO">Aditado</option>
            </select>
          </FilterField>

          <FilterField label="Data de Início:">
            <div className="estagios-date-range">
              <input type="date" value={draftFilters.data_inicio_de} onChange={(event) => updateDraftFilter('data_inicio_de', event.target.value)} />
              <input type="date" value={draftFilters.data_inicio_ate} onChange={(event) => updateDraftFilter('data_inicio_ate', event.target.value)} />
            </div>
          </FilterField>

          <FilterField label="Data Prevista para Encerramento:">
            <div className="estagios-date-range">
              <input type="date" value={draftFilters.data_prevista_de} onChange={(event) => updateDraftFilter('data_prevista_de', event.target.value)} />
              <input type="date" value={draftFilters.data_prevista_ate} onChange={(event) => updateDraftFilter('data_prevista_ate', event.target.value)} />
            </div>
          </FilterField>

          <FilterField label="Data do Encerramento:">
            <div className="estagios-date-range">
              <input type="date" value={draftFilters.data_encerramento_de} onChange={(event) => updateDraftFilter('data_encerramento_de', event.target.value)} />
              <input type="date" value={draftFilters.data_encerramento_ate} onChange={(event) => updateDraftFilter('data_encerramento_ate', event.target.value)} />
            </div>
          </FilterField>

          <FilterField label="Convênio:">
            <select className="select" value={draftFilters.convenio} onChange={(event) => updateDraftFilter('convenio', event.target.value)}>
              <option value="">Todos</option>
              {(filterOptions.convenios || []).map((option) => (
                <option key={option.value} value={option.value}>{option.label}</option>
              ))}
            </select>
          </FilterField>

          <FilterField label="Aguardando assinatura do coordenador do curso:">
            <select className="select" value={draftFilters.aguardando_assinatura} onChange={(event) => updateDraftFilter('aguardando_assinatura', event.target.value)}>
              <option value="">Todos</option>
              <option value="SIM">Sim</option>
              <option value="NAO">Não</option>
            </select>
          </FilterField>

          <div className="estagios-filters-card__actions">
            <button type="button" className="btn btn--secondary" onClick={handleApplyFilters}>Filtrar</button>
          </div>
        </div>
      </section>

      <div className="estagios-tabs">
        {TAB_ITEMS.map((tab) => (
          <button
            key={tab.key}
            type="button"
            className={`estagios-tab ${activeTab === tab.key ? 'estagios-tab--active' : ''}`}
            onClick={() => handleTabChange(tab.key)}
          >
            <span>{tab.label}</span>
            <SummaryBadge count={tabCounts[tab.key]} />
          </button>
        ))}
      </div>

      {isError ? (
        <div className="alert alert--error">Não foi possível carregar os estágios com os filtros informados.</div>
      ) : null}

      <section className="dashboard-card estagios-table-card">
        <div className="estagios-table-card__summary">Mostrando {data?.count || 0} Estágio{(data?.count || 0) === 1 ? '' : 's'}</div>

        <div className="table-wrapper estagios-table-wrapper">
          <table>
            <thead>
              <tr>
                <th>#</th>
                <th>Tipo</th>
                <th>Estagiário</th>
                <th>Situação do Estagiário</th>
                <th>Situação da Matrícula no Período</th>
                <th>Campus</th>
                <th>Concedente</th>
                <th>Situação do Convênio</th>
                <th>Professor Orientador</th>
                <th>Data de Início</th>
                <th>Data Prevista para Encerramento</th>
                <th>Data do Encerramento</th>
                <th>Aditivos Contratuais</th>
              </tr>
            </thead>
            <tbody>
              {isLoading ? (
                <tr>
                  <td colSpan="13" className="empty-state">Carregando estágios...</td>
                </tr>
              ) : rows.length === 0 ? (
                <tr>
                  <td colSpan="13" className="empty-state">Nenhum estágio encontrado.</td>
                </tr>
              ) : (
                rows.map((row) => (
                  <tr key={row.id}>
                    <td>
                      <Link
                        to={`/estagio/${row.id}`}
                        className="estagios-table__view"
                        aria-label={`Visualizar estágio de ${row.aluno_nome}`}
                      >
                        <Eye size={16} />
                      </Link>
                    </td>
                    <td>{row.tipo}</td>
                    <td>
                      <strong>{row.aluno_nome}</strong>
                      <div className="estagios-table__subtext">({row.aluno_identificador})</div>
                    </td>
                    <td>{row.situacao_estagiario}</td>
                    <td>{row.situacao_matricula_periodo}</td>
                    <td>{row.campus_codigo || row.campus_nome || '-'}</td>
                    <td>{row.concedente_nome}</td>
                    <td>{row.situacao_convenio}</td>
                    <td>{row.professor_orientador}</td>
                    <td>{formatDate(row.data_inicio)}</td>
                    <td>{formatDate(row.data_prevista_encerramento)}</td>
                    <td>{formatDate(row.data_encerramento)}</td>
                    <td>
                      {row.aditivos_contratuais?.length ? (
                        <ul className="estagios-aditivos-list">
                          {row.aditivos_contratuais.map((item) => (
                            <li key={item.id}>
                              <strong>Descrição:</strong> {item.descricao}
                            </li>
                          ))}
                        </ul>
                      ) : (
                        '-'
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {(data?.next || data?.previous) ? (
          <div className="pagination estagios-pagination">
            <button type="button" className="btn btn--secondary btn--sm" disabled={!data.previous} onClick={() => setPage((current) => current - 1)}>Anterior</button>
            <span className="pagination__info">Página {page} de {Math.max(1, Math.ceil((data?.count || 0) / 10))}</span>
            <button type="button" className="btn btn--secondary btn--sm" disabled={!data.next} onClick={() => setPage((current) => current + 1)}>Próxima</button>
          </div>
        ) : null}
      </section>
    </div>
  )
}
