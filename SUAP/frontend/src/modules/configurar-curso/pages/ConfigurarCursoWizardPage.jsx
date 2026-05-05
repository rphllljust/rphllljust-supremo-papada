import { useEffect, useMemo, useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import toast from 'react-hot-toast'

import AlertMessage from '@/modules/configurar-curso/components/AlertMessage'
import ConfirmDialog from '@/modules/configurar-curso/components/ConfirmDialog'
import LoadingOverlay from '@/modules/configurar-curso/components/LoadingOverlay'
import ProgressBar from '@/modules/configurar-curso/components/ProgressBar'
import StatusBadge from '@/modules/configurar-curso/components/StatusBadge'
import StepperWizard from '@/modules/configurar-curso/components/StepperWizard'
import { WIZARD_STEPS, WIZARD_STATUS_META } from '@/modules/configurar-curso/constants'
import { useConfigurarCursoWizard } from '@/modules/configurar-curso/hooks/useConfigurarCursoWizard'
import EtapaComponentes from '@/modules/configurar-curso/steps/EtapaComponentes'
import EtapaCoordenadores from '@/modules/configurar-curso/steps/EtapaCoordenadores'
import EtapaCurso from '@/modules/configurar-curso/steps/EtapaCurso'
import EtapaEstruturaCurso from '@/modules/configurar-curso/steps/EtapaEstruturaCurso'
import EtapaMatrizCurricular from '@/modules/configurar-curso/steps/EtapaMatrizCurricular'
import EtapaRequisitos from '@/modules/configurar-curso/steps/EtapaRequisitos'
import EtapaResumoFinal from '@/modules/configurar-curso/steps/EtapaResumoFinal'

function parseWizardIdFromLocation(locationSearch) {
  const params = new URLSearchParams(locationSearch)
  const value = Number(params.get('wizard') || '')
  return Number.isFinite(value) && value > 0 ? value : null
}

export default function ConfigurarCursoWizardPage() {
  const location = useLocation()
  const navigate = useNavigate()

  const initialWizardId = parseWizardIdFromLocation(location.search)

  const {
    wizardId,
    wizard,
    currentStepIndex,
    progressPercent,
    isBusy,
    errorMessage,
    summaryPayload,
    conclusionPayload,
    saveStep,
    advanceStep,
    goBackStep,
    fetchSummary,
    concludeWizard,
  } = useConfigurarCursoWizard(initialWizardId)

  const [selectedEstruturaId, setSelectedEstruturaId] = useState(null)
  const [selectedMatrizId, setSelectedMatrizId] = useState(null)
  const [selectedCursoId, setSelectedCursoId] = useState(null)
  const [showConcludeDialog, setShowConcludeDialog] = useState(false)

  useEffect(() => {
    if (!wizardId) return

    const params = new URLSearchParams(location.search)
    if (String(params.get('wizard')) === String(wizardId)) return

    params.set('wizard', wizardId)
    navigate({ pathname: location.pathname, search: params.toString() }, { replace: true })
  }, [wizardId, location.pathname, location.search, navigate])

  useEffect(() => {
    if (!wizard) return

    setSelectedEstruturaId(wizard.estrutura_curso || null)
    setSelectedMatrizId(wizard.matriz_curricular || null)
    setSelectedCursoId(wizard.curso || null)
  }, [wizard])

  const currentStep = WIZARD_STEPS[currentStepIndex] || WIZARD_STEPS[0]

  const statusMeta = WIZARD_STATUS_META[wizard?.status] || { label: 'Nao iniciado', tone: 'neutral' }

  const relationsPayload = useMemo(
    () => ({
      estrutura_curso: selectedEstruturaId || null,
      matriz_curricular: selectedMatrizId || null,
      curso: selectedCursoId || null,
    }),
    [selectedEstruturaId, selectedMatrizId, selectedCursoId],
  )

  useEffect(() => {
    if (currentStep.key === 'resumo' && wizardId) {
      fetchSummary().catch(() => {})
    }
  }, [currentStep.key, wizardId, fetchSummary])

  const canConclude = useMemo(() => {
    const resumo = summaryPayload?.resumo || conclusionPayload?.resumo
    if (!resumo) return false

    return Boolean(
      resumo.estrutura_curso?.id
      && resumo.matriz_curricular?.id
      && resumo.curso?.id
      && resumo.curso?.matriz_curricular
      && (resumo.componentes_vinculados?.length || 0) > 0
      && (resumo.coordenadores?.length || 0) > 0,
    )
  }, [summaryPayload, conclusionPayload])

  async function handleSaveDraft({ showSuccessToast = true } = {}) {
    try {
      await saveStep({
        step: currentStep.key,
        payload: {
          etapa_atual: currentStep.key,
          wizard_id: wizardId,
        },
        relations: relationsPayload,
      })

      if (showSuccessToast) {
        toast.success('Rascunho salvo com sucesso.')
      }
    } catch (error) {
      toast.error(errorMessage || 'Nao foi possivel salvar o rascunho desta etapa.')
      throw error
    }
  }

  async function handleAdvance() {
    try {
      await handleSaveDraft({ showSuccessToast: false })
      await advanceStep()
      toast.success('Etapa avancada com sucesso.')
    } catch (error) {
      toast.error(errorMessage || 'Nao foi possivel avancar para a proxima etapa.')
    }
  }

  async function handleBack() {
    try {
      await goBackStep()
      toast.success('Retornou para a etapa anterior.')
    } catch (error) {
      toast.error(errorMessage || 'Nao foi possivel voltar etapa.')
    }
  }

  async function handleRefreshSummary() {
    try {
      await saveStep({
        step: currentStep.key,
        payload: { etapa_atual: currentStep.key },
        relations: relationsPayload,
      })
      await fetchSummary()
      toast.success('Resumo atualizado.')
    } catch (error) {
      toast.error(errorMessage || 'Nao foi possivel atualizar o resumo.')
    }
  }

  async function handleConclude() {
    try {
      await handleRefreshSummary()
      await concludeWizard()
      setShowConcludeDialog(false)
      toast.success('Configuracao de curso concluida com sucesso.')
    } catch (error) {
      toast.error(errorMessage || 'Nao foi possivel concluir o wizard.')
    }
  }

  return (
    <div className="page">
      <div className="relative grid gap-6 rounded-2xl bg-gradient-to-br from-emerald-50 via-white to-slate-50 p-4 sm:p-6">
        <LoadingOverlay show={isBusy} message="Executando operacao no wizard..." />

        <header className="grid gap-4 rounded-2xl border border-emerald-100 bg-white p-4 shadow-sm">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <h1 className="text-2xl font-bold text-slate-900">Configurar Curso</h1>
              <p className="text-sm text-slate-600">Fluxo completo de secretaria escolar para estrutura, matriz, componentes e coordenacao.</p>
            </div>
            <div className="flex items-center gap-2">
              <StatusBadge label={statusMeta.label} tone={statusMeta.tone} />
              <span className="rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-xs font-semibold text-slate-600">
                Wizard #{wizardId || 'novo'}
              </span>
            </div>
          </div>

          <ProgressBar value={progressPercent} />
          <StepperWizard currentStep={currentStepIndex} />
        </header>

        {errorMessage ? <AlertMessage type="error" message={errorMessage} /> : null}

        <section className="grid gap-4 rounded-2xl border border-slate-200 bg-white p-4 shadow-sm lg:grid-cols-[1fr_260px]">
          <div className="min-h-[360px]">
            {currentStep.key === 'estrutura' ? (
              <EtapaEstruturaCurso
                selectedEstruturaId={selectedEstruturaId}
                onSelectEstrutura={(id) => setSelectedEstruturaId(id)}
              />
            ) : null}

            {currentStep.key === 'matriz' ? (
              <EtapaMatrizCurricular
                selectedEstruturaId={selectedEstruturaId}
                selectedMatrizId={selectedMatrizId}
                onSelectMatriz={(id) => setSelectedMatrizId(id)}
              />
            ) : null}

            {currentStep.key === 'componentes' ? (
              <EtapaComponentes selectedMatrizId={selectedMatrizId} />
            ) : null}

            {currentStep.key === 'requisitos' ? (
              <EtapaRequisitos selectedMatrizId={selectedMatrizId} />
            ) : null}

            {currentStep.key === 'curso' ? (
              <EtapaCurso
                selectedEstruturaId={selectedEstruturaId}
                selectedMatrizId={selectedMatrizId}
                selectedCursoId={selectedCursoId}
                onSelectCurso={(id) => setSelectedCursoId(id)}
              />
            ) : null}

            {currentStep.key === 'coordenadores' ? (
              <EtapaCoordenadores selectedCursoId={selectedCursoId} />
            ) : null}

            {currentStep.key === 'resumo' ? (
              <EtapaResumoFinal
                summaryPayload={summaryPayload || conclusionPayload}
                onRefreshSummary={handleRefreshSummary}
                isRefreshing={isBusy}
                canConclude={canConclude}
              />
            ) : null}
          </div>

          <aside className="space-y-3 rounded-xl border border-slate-200 bg-slate-50 p-3">
            <h2 className="text-sm font-bold text-slate-800">Resumo rapido</h2>

            <div className="space-y-2 text-xs text-slate-700">
              <p><strong>Etapa atual:</strong> {currentStep.title}</p>
              <p><strong>Estrutura:</strong> {selectedEstruturaId || '-'}</p>
              <p><strong>Matriz:</strong> {selectedMatrizId || '-'}</p>
              <p><strong>Curso:</strong> {selectedCursoId || '-'}</p>
              <p><strong>Status:</strong> {statusMeta.label}</p>
            </div>

            <div className="border-t border-slate-200 pt-2 text-xs text-slate-600">
              Salve rascunho antes de trocar de etapa para manter os dados sincronizados com o servidor.
            </div>
          </aside>
        </section>

        <footer className="flex flex-wrap items-center justify-between gap-2 rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
          <div className="flex gap-2">
            <button
              type="button"
              onClick={handleBack}
              disabled={isBusy || currentStepIndex === 0}
              className="rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-60"
            >
              Voltar
            </button>
            <button
              type="button"
              onClick={handleSaveDraft}
              disabled={isBusy}
              className="rounded-lg border border-amber-300 bg-amber-50 px-4 py-2 text-sm font-semibold text-amber-700 hover:bg-amber-100 disabled:cursor-not-allowed disabled:opacity-60"
            >
              Salvar rascunho
            </button>
          </div>

          <div className="flex gap-2">
            {currentStep.key === 'resumo' ? (
              <button
                type="button"
                onClick={() => setShowConcludeDialog(true)}
                disabled={isBusy}
                className="rounded-lg bg-emerald-600 px-4 py-2 text-sm font-semibold text-white hover:bg-emerald-700 disabled:cursor-not-allowed disabled:opacity-60"
              >
                Concluir configuracao
              </button>
            ) : (
              <button
                type="button"
                onClick={handleAdvance}
                disabled={isBusy}
                className="rounded-lg bg-emerald-600 px-4 py-2 text-sm font-semibold text-white hover:bg-emerald-700 disabled:cursor-not-allowed disabled:opacity-60"
              >
                Avancar etapa
              </button>
            )}
          </div>
        </footer>
      </div>

      <ConfirmDialog
        open={showConcludeDialog}
        title="Concluir configuracao de curso"
        description="Deseja concluir agora? O sistema validara matriz vinculada, requisitos e coordenadores obrigatorios."
        confirmLabel="Concluir"
        danger={false}
        onCancel={() => setShowConcludeDialog(false)}
        onConfirm={handleConclude}
      />
    </div>
  )
}
