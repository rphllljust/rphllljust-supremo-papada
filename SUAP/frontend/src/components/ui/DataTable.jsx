/**
 * Tabela reutilizável com busca, paginação e loading skeleton.
 */
import { useState } from 'react'
import { Search, ChevronLeft, ChevronRight } from 'lucide-react'

export default function DataTable({
  columns,
  data,
  isLoading,
  onSearch,
  searchPlaceholder = 'Buscar...',
  actions,
  rowActions,
  rowActionsLabel = 'Acoes',
  emptyMessage = 'Nenhum registro encontrado.',
}) {
  const [search, setSearch] = useState('')

  const handleSearch = (e) => {
    setSearch(e.target.value)
    onSearch?.(e.target.value)
  }

  if (isLoading) {
    return (
      <div className="table-skeleton">
        {Array.from({ length: 6 }).map((_, i) => (
          <div key={i} className="skeleton-row" />
        ))}
      </div>
    )
  }

  const rows = data?.results ?? data ?? []
  const count = data?.count ?? rows.length
  const hasRowActions = typeof rowActions === 'function'

  return (
    <div className="data-table">
      <div className="data-table__toolbar">
        <div className="search-input">
          <Search size={16} />
          <input
            type="text"
            value={search}
            onChange={handleSearch}
            placeholder={searchPlaceholder}
          />
        </div>
        {actions}
      </div>

      <div className="table-wrapper">
        <table>
          <thead>
            <tr>
              {columns.map((col) => (
                <th key={col.key}>{col.label}</th>
              ))}
              {hasRowActions ? <th className="data-table__actions-header">{rowActionsLabel}</th> : null}
            </tr>
          </thead>
          <tbody>
            {rows.length === 0 ? (
              <tr>
                <td colSpan={columns.length + (hasRowActions ? 1 : 0)} className="empty-state">
                  {emptyMessage}
                </td>
              </tr>
            ) : (
              rows.map((row, i) => (
                <tr key={row.id ?? i}>
                  {columns.map((col) => (
                    <td key={col.key}>
                      {col.render ? col.render(row) : row[col.key]}
                    </td>
                  ))}
                  {hasRowActions ? <td className="data-table__actions-cell">{rowActions(row)}</td> : null}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {data?.next || data?.previous ? (
        <div className="pagination">
          <span className="pagination__info">{count} registros</span>
        </div>
      ) : null}
    </div>
  )
}
