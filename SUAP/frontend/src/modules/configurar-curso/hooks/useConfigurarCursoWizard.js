import { useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { getStepIndex, WIZARD_STEPS } from '@/modules/configurar-curso/constants'
import { configurarCursoApi, extractErrorMessage } from '@/modules/configurar-curso/services/configurarCursoApi'

export function useConfigurarCursoWizard(initialWizardId = null) {
  const queryClient = useQueryClient()
  const [wizardId, setWizardId] = useState(initialWizardId)

  const wizardQuery = useQuery({
    queryKey: ['configurar-curso', 'wizard', wizardId],
    queryFn: () => configurarCursoApi.getWizard(wizardId).then((response) => response.data),
    enabled: Boolean(wizardId),
    staleTime: 20_000,
  })

  const createWizardMutation = useMutation({
    mutationFn: (payload) => configurarCursoApi.createWizard(payload),
    onSuccess: (response) => {
      const nextWizardId = response.data?.id
      if (nextWizardId) {
        setWizardId(nextWizardId)
        queryClient.setQueryData(['configurar-curso', 'wizard', nextWizardId], response.data)
      }
    },
  })

  const saveStepMutation = useMutation({
    mutationFn: ({ id, payload }) => configurarCursoApi.saveWizardStep(id, payload),
    onSuccess: (response, variables) => {
      queryClient.setQueryData(['configurar-curso', 'wizard', variables.id], response.data)
      queryClient.invalidateQueries({ queryKey: ['configurar-curso', 'wizard', variables.id] })
    },
  })

  const advanceStepMutation = useMutation({
    mutationFn: (id) => configurarCursoApi.advanceWizard(id),
    onSuccess: (response, id) => {
      queryClient.setQueryData(['configurar-curso', 'wizard', id], response.data)
      queryClient.invalidateQueries({ queryKey: ['configurar-curso', 'wizard', id] })
    },
  })

  const backStepMutation = useMutation({
    mutationFn: (id) => configurarCursoApi.backWizard(id),
    onSuccess: (response, id) => {
      queryClient.setQueryData(['configurar-curso', 'wizard', id], response.data)
      queryClient.invalidateQueries({ queryKey: ['configurar-curso', 'wizard', id] })
    },
  })

  const summaryMutation = useMutation({
    mutationFn: (id) => configurarCursoApi.getWizardSummary(id),
  })

  const concludeMutation = useMutation({
    mutationFn: (id) => configurarCursoApi.concludeWizard(id),
    onSuccess: (response, id) => {
      if (response.data?.wizard) {
        queryClient.setQueryData(['configurar-curso', 'wizard', id], response.data.wizard)
      }
      queryClient.invalidateQueries({ queryKey: ['configurar-curso', 'wizard', id] })
    },
  })

  const ensureWizardId = async (payload = {}) => {
    if (wizardId) {
      return wizardId
    }

    const response = await createWizardMutation.mutateAsync(payload)
    const createdId = response.data?.id

    if (!createdId) {
      throw new Error('Nao foi possivel inicializar o wizard.')
    }

    return createdId
  }

  const saveStep = async ({ step, payload = {}, relations = {} }) => {
    const ensuredId = await ensureWizardId({ etapa_atual: step })

    const response = await saveStepMutation.mutateAsync({
      id: ensuredId,
      payload: {
        etapa: step,
        payload,
        ...relations,
      },
    })

    return response.data
  }

  const advanceStep = async () => {
    const ensuredId = await ensureWizardId()
    const response = await advanceStepMutation.mutateAsync(ensuredId)
    return response.data
  }

  const goBackStep = async () => {
    if (!wizardId) return null
    const response = await backStepMutation.mutateAsync(wizardId)
    return response.data
  }

  const fetchSummary = async () => {
    const ensuredId = await ensureWizardId()
    const response = await summaryMutation.mutateAsync(ensuredId)
    return response.data
  }

  const concludeWizard = async () => {
    const ensuredId = await ensureWizardId()
    const response = await concludeMutation.mutateAsync(ensuredId)
    return response.data
  }

  const wizard = wizardQuery.data || null

  const currentStepIndex = useMemo(() => {
    if (!wizard?.etapa_atual) return 0

    if (wizard.etapa_atual === 'concluido') {
      return WIZARD_STEPS.length - 1
    }

    const index = getStepIndex(wizard.etapa_atual)
    return index >= 0 ? index : 0
  }, [wizard?.etapa_atual])

  const progressPercent = useMemo(() => {
    const total = WIZARD_STEPS.length
    return Math.round(((currentStepIndex + 1) / total) * 100)
  }, [currentStepIndex])

  const isBusy = [
    wizardQuery.isLoading,
    createWizardMutation.isPending,
    saveStepMutation.isPending,
    advanceStepMutation.isPending,
    backStepMutation.isPending,
    summaryMutation.isPending,
    concludeMutation.isPending,
  ].some(Boolean)

  const rawError =
    wizardQuery.error ||
    createWizardMutation.error ||
    saveStepMutation.error ||
    advanceStepMutation.error ||
    backStepMutation.error ||
    summaryMutation.error ||
    concludeMutation.error

  return {
    wizardId,
    setWizardId,
    wizard,
    currentStepIndex,
    progressPercent,
    isBusy,
    errorMessage: rawError ? extractErrorMessage(rawError) : '',
    summaryPayload: summaryMutation.data?.data || null,
    conclusionPayload: concludeMutation.data?.data || null,
    saveStep,
    advanceStep,
    goBackStep,
    fetchSummary,
    concludeWizard,
    refreshWizard: wizardQuery.refetch,
  }
}
