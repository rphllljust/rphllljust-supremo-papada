export default function LoadingOverlay({ show, message = 'Carregando...' }) {
  if (!show) return null

  return (
    <div className="absolute inset-0 z-30 flex items-center justify-center rounded-2xl bg-slate-900/20 backdrop-blur-[1px]">
      <div className="flex items-center gap-3 rounded-xl border border-emerald-200 bg-white px-4 py-3 text-sm text-slate-700 shadow-wizard">
        <span className="inline-flex h-5 w-5 animate-spin rounded-full border-2 border-emerald-200 border-t-emerald-600" />
        {message}
      </div>
    </div>
  )
}
