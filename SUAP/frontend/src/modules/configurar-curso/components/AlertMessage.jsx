const TYPE_STYLES = {
  info: 'border-blue-200 bg-blue-50 text-blue-800',
  success: 'border-emerald-200 bg-emerald-50 text-emerald-800',
  warning: 'border-amber-200 bg-amber-50 text-amber-800',
  error: 'border-red-200 bg-red-50 text-red-800',
}

export default function AlertMessage({ type = 'info', message, title, onClose }) {
  if (!message) return null

  return (
    <div className={`rounded-xl border px-4 py-3 text-sm shadow-sm ${TYPE_STYLES[type] || TYPE_STYLES.info}`}>
      <div className="flex items-start justify-between gap-3">
        <div>
          {title ? <p className="mb-1 font-semibold">{title}</p> : null}
          <p>{message}</p>
        </div>
        {onClose ? (
          <button
            type="button"
            onClick={onClose}
            className="rounded-md px-2 py-1 text-xs font-medium hover:bg-black/5"
          >
            Fechar
          </button>
        ) : null}
      </div>
    </div>
  )
}
