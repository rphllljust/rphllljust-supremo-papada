import { WIZARD_STEPS } from '@/modules/configurar-curso/constants'

export default function StepperWizard({ currentStep }) {
  return (
    <ol className="grid grid-cols-1 gap-2 md:grid-cols-2 xl:grid-cols-7">
      {WIZARD_STEPS.map((step, index) => {
        const isDone = index < currentStep
        const isCurrent = index === currentStep

        return (
          <li
            key={step.key}
            className={`rounded-xl border px-3 py-3 transition-colors ${
              isCurrent
                ? 'border-emerald-400 bg-emerald-50'
                : isDone
                  ? 'border-emerald-200 bg-white'
                  : 'border-slate-200 bg-slate-50'
            }`}
          >
            <p className={`text-xs font-semibold ${isCurrent ? 'text-emerald-700' : 'text-slate-500'}`}>
              Etapa {index + 1}
            </p>
            <p className={`text-sm font-semibold ${isCurrent || isDone ? 'text-slate-900' : 'text-slate-500'}`}>
              {step.title}
            </p>
          </li>
        )
      })}
    </ol>
  )
}
