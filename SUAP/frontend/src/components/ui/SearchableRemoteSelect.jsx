import { useEffect, useMemo, useRef } from 'react'

export default function SearchableRemoteSelect({
  id,
  label,
  searchLabel,
  searchPlaceholder = 'Buscar...',
  searchValue,
  onSearchChange,
  value,
  onChange,
  options,
  selectedOption,
  getOptionValue = (option) => option.id,
  getOptionLabel = (option) => option.nome,
  emptyOptionLabel = 'Selecione',
  disabled = false,
}) {
  const seenOptionsRef = useRef(new Map())

  useEffect(() => {
    ;(options || []).forEach((option) => {
      seenOptionsRef.current.set(String(getOptionValue(option)), option)
    })

    if (selectedOption) {
      seenOptionsRef.current.set(String(getOptionValue(selectedOption)), selectedOption)
    }
  }, [getOptionValue, options, selectedOption])

  const mergedOptions = useMemo(() => {
    const normalizedOptions = options || []
    if (!selectedOption || !value) {
      if (!value) {
        return normalizedOptions
      }

      const cachedOption = seenOptionsRef.current.get(String(value))
      if (!cachedOption) {
        return normalizedOptions
      }

      const foundCached = normalizedOptions.some((option) => String(getOptionValue(option)) === String(value))
      return foundCached ? normalizedOptions : [cachedOption, ...normalizedOptions]
    }

    const selectedValue = String(getOptionValue(selectedOption))
    const found = normalizedOptions.some((option) => String(getOptionValue(option)) === selectedValue)
    if (found) {
      return normalizedOptions
    }

    return [selectedOption, ...normalizedOptions]
  }, [getOptionValue, options, selectedOption, value])

  return (
    <div className="form-field form-field--full remote-select-field">
      <label htmlFor={`${id}-search`}>{searchLabel || `${label} - busca`}</label>
      <input
        id={`${id}-search`}
        type="search"
        className="form-control"
        placeholder={searchPlaceholder}
        value={searchValue}
        onChange={(event) => onSearchChange(event.target.value)}
        disabled={disabled}
      />

      <label htmlFor={id}>{label}</label>
      <select id={id} className="select" value={value} onChange={(event) => onChange(event.target.value)} disabled={disabled}>
        <option value="">{emptyOptionLabel}</option>
        {mergedOptions.map((option) => (
          <option key={getOptionValue(option)} value={getOptionValue(option)}>
            {getOptionLabel(option)}
          </option>
        ))}
      </select>
    </div>
  )
}