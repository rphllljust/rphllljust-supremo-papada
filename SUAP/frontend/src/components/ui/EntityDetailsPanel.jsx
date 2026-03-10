import { X } from 'lucide-react'

function formatValue(value) {
  if (value === null || value === undefined || value === '') {
    return '-'
  }

  if (typeof value === 'boolean') {
    return value ? 'Sim' : 'Nao'
  }

  return String(value)
}

export default function EntityDetailsPanel({
  title,
  subtitle,
  fields,
  isLoading,
  errorMessage,
  onClose,
}) {
  return (
    <section className="details-panel" aria-live="polite">
      <div className="details-panel__header">
        <div>
          <h2 className="details-panel__title">{title}</h2>
          {subtitle ? <p className="details-panel__subtitle">{subtitle}</p> : null}
        </div>
        <button type="button" className="btn btn--icon" onClick={onClose} aria-label="Fechar detalhes">
          <X size={16} />
        </button>
      </div>

      {isLoading ? (
        <div className="details-panel__loading">Carregando detalhes...</div>
      ) : errorMessage ? (
        <div className="alert alert--error">{errorMessage}</div>
      ) : (
        <dl className="details-panel__grid">
          {fields.map((field) => (
            <div key={field.label} className="details-panel__item">
              <dt>{field.label}</dt>
              <dd>{formatValue(field.value)}</dd>
            </div>
          ))}
        </dl>
      )}
    </section>
  )
}