export default function FormField({
  id,
  label,
  error,
  required = false,
  helper,
  children,
}) {
  return (
    <div className="space-y-1.5">
      <label htmlFor={id} className="text-sm font-semibold text-slate-700">
        {label}
        {required ? <span className="ml-1 text-red-500">*</span> : null}
      </label>
      {children}
      {helper ? <p className="text-xs text-slate-500">{helper}</p> : null}
      {error ? <p className="text-xs font-medium text-red-600">{error}</p> : null}
    </div>
  )
}
