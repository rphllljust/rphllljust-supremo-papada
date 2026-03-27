import FormField from '@/modules/configurar-curso/components/FormField'

export default function SearchSelect({
  id,
  label,
  value,
  onChange,
  options,
  getOptionValue = (item) => item.id,
  getOptionLabel = (item) => item.nome,
  emptyOptionLabel = 'Selecione',
  searchLabel = 'Buscar',
  searchValue,
  onSearchChange,
  required = false,
  error,
  disabled = false,
}) {
  return (
    <div className="grid gap-3">
      <FormField id={`${id}-search`} label={searchLabel}>
        <input
          id={`${id}-search`}
          type="search"
          value={searchValue || ''}
          onChange={(event) => onSearchChange?.(event.target.value)}
          className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm outline-none transition focus:border-emerald-500 focus:ring-2 focus:ring-emerald-100"
          placeholder="Digite para filtrar"
          disabled={disabled}
        />
      </FormField>

      <FormField id={id} label={label} required={required} error={error}>
        <select
          id={id}
          value={value || ''}
          onChange={(event) => onChange?.(event.target.value)}
          className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm outline-none transition focus:border-emerald-500 focus:ring-2 focus:ring-emerald-100"
          disabled={disabled}
        >
          <option value="">{emptyOptionLabel}</option>
          {(options || []).map((option) => (
            <option key={getOptionValue(option)} value={getOptionValue(option)}>
              {getOptionLabel(option)}
            </option>
          ))}
        </select>
      </FormField>
    </div>
  )
}
