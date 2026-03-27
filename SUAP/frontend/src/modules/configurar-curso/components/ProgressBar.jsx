export default function ProgressBar({ value = 0 }) {
  const safeValue = Number.isFinite(value) ? Math.min(100, Math.max(0, value)) : 0

  return (
    <div className="w-full">
      <div className="mb-2 flex items-center justify-between text-xs text-slate-600">
        <span>Progresso do wizard</span>
        <span>{safeValue}%</span>
      </div>
      <div className="h-2 w-full overflow-hidden rounded-full bg-emerald-100">
        <div
          className="h-full rounded-full bg-gradient-to-r from-emerald-600 to-emerald-400 transition-all duration-300"
          style={{ width: `${safeValue}%` }}
        />
      </div>
    </div>
  )
}
