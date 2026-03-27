const TONE_STYLES = {
  info: 'bg-blue-100 text-blue-700 border-blue-200',
  success: 'bg-emerald-100 text-emerald-700 border-emerald-200',
  warning: 'bg-amber-100 text-amber-700 border-amber-200',
  error: 'bg-red-100 text-red-700 border-red-200',
  neutral: 'bg-slate-100 text-slate-700 border-slate-200',
}

export default function StatusBadge({ label, tone = 'neutral' }) {
  return (
    <span className={`inline-flex items-center rounded-full border px-2.5 py-1 text-xs font-semibold ${TONE_STYLES[tone] || TONE_STYLES.neutral}`}>
      {label}
    </span>
  )
}
