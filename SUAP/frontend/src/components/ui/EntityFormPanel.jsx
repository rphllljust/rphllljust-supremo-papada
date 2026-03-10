export default function EntityFormPanel({
  title,
  subtitle,
  onSubmit,
  onCancel,
  submitLabel,
  isSubmitting,
  children,
}) {
  return (
    <section className="form-panel">
      <div className="form-panel__header">
        <div>
          <h2 className="form-panel__title">{title}</h2>
          {subtitle ? <p className="form-panel__subtitle">{subtitle}</p> : null}
        </div>
        {onCancel ? (
          <button type="button" className="btn btn--outline btn--sm" onClick={onCancel}>
            Cancelar
          </button>
        ) : null}
      </div>

      <form onSubmit={onSubmit} className="form-panel__body">
        <div className="form-panel__grid">
          {children}
        </div>

        <div className="form-panel__actions">
          <button type="submit" className="btn btn--primary" disabled={isSubmitting}>
            {isSubmitting ? 'Salvando...' : submitLabel}
          </button>
          {onCancel ? (
            <button type="button" className="btn btn--secondary" onClick={onCancel} disabled={isSubmitting}>
              Fechar
            </button>
          ) : null}
        </div>
      </form>
    </section>
  )
}