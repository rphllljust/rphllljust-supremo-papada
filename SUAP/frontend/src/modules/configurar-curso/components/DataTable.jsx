export default function DataTable({
  columns,
  rows,
  emptyMessage = 'Nenhum registro encontrado.',
  rowActions,
}) {
  return (
    <div className="overflow-hidden rounded-xl border border-slate-200 bg-white">
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-slate-200 text-sm">
          <thead className="bg-slate-50">
            <tr>
              {columns.map((column) => (
                <th key={column.key} className="px-3 py-2 text-left font-semibold text-slate-600">
                  {column.label}
                </th>
              ))}
              {rowActions ? <th className="px-3 py-2 text-right font-semibold text-slate-600">Acoes</th> : null}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {rows?.length ? (
              rows.map((row) => (
                <tr key={row.id} className="hover:bg-slate-50/70">
                  {columns.map((column) => (
                    <td key={column.key} className="px-3 py-2 text-slate-700">
                      {column.render ? column.render(row) : row[column.key]}
                    </td>
                  ))}
                  {rowActions ? <td className="px-3 py-2">{rowActions(row)}</td> : null}
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan={columns.length + (rowActions ? 1 : 0)} className="px-3 py-3 text-center text-slate-500">
                  {emptyMessage}
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
