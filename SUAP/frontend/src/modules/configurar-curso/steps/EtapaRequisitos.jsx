import { useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'

import AlertMessage from '@/modules/configurar-curso/components/AlertMessage'
import ConfirmDialog from '@/modules/configurar-curso/components/ConfirmDialog'
import DataTable from '@/modules/configurar-curso/components/DataTable'
import FormField from '@/modules/configurar-curso/components/FormField'
import { configurarCursoApi, extractErrorMessage, extractResults } from '@/modules/configurar-curso/services/configurarCursoApi'

const REQUISITO_COLUMNS = [
  { key: 'componente_nome', label: 'Componente' },
  { key: 'requisito_nome', label: 'Requisito' },
]

export default function EtapaRequisitos({ selectedMatrizId }) {
  const queryClient = useQueryClient()
  const [preForm, setPreForm] = useState({ componente: '', requisito: '' })
  const [coForm, setCoForm] = useState({ componente: '', requisito: '' })
  const [toDeletePre, setToDeletePre] = useState(null)
  const [toDeleteCo, setToDeleteCo] = useState(null)

  const matrizComponentesQuery = useQuery({
    queryKey: ['configurar-curso', 'matriz-componentes-requisitos', selectedMatrizId],
    queryFn: () => configurarCursoApi.listMatrizComponentes(selectedMatrizId, { page_size: 200 }).then((response) => response.data),
    enabled: Boolean(selectedMatrizId),
    staleTime: 20_000,
  })

  const preRequisitosQuery = useQuery({
    queryKey: ['configurar-curso', 'pre-requisitos', selectedMatrizId],
    queryFn: () => configurarCursoApi.listPreRequisitos({ matriz: selectedMatrizId, page_size: 200 }).then((response) => response.data),
    enabled: Boolean(selectedMatrizId),
    staleTime: 20_000,
  })

  const coRequisitosQuery = useQuery({
    queryKey: ['configurar-curso', 'co-requisitos', selectedMatrizId],
    queryFn: () => configurarCursoApi.listCoRequisitos({ matriz: selectedMatrizId, page_size: 200 }).then((response) => response.data),
    enabled: Boolean(selectedMatrizId),
    staleTime: 20_000,
  })

  const createPreMutation = useMutation({
    mutationFn: (payload) => configurarCursoApi.createPreRequisito(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['configurar-curso', 'pre-requisitos', selectedMatrizId] })
      setPreForm({ componente: '', requisito: '' })
      toast.success('Pre-requisito cadastrado com sucesso.')
    },
    onError: (error) => toast.error(extractErrorMessage(error, 'Nao foi possivel cadastrar o pre-requisito.')),
  })

  const createCoMutation = useMutation({
    mutationFn: (payload) => configurarCursoApi.createCoRequisito(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['configurar-curso', 'co-requisitos', selectedMatrizId] })
      setCoForm({ componente: '', requisito: '' })
      toast.success('Co-requisito cadastrado com sucesso.')
    },
    onError: (error) => toast.error(extractErrorMessage(error, 'Nao foi possivel cadastrar o co-requisito.')),
  })

  const deletePreMutation = useMutation({
    mutationFn: (id) => configurarCursoApi.deletePreRequisito(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['configurar-curso', 'pre-requisitos', selectedMatrizId] })
      setToDeletePre(null)
      toast.success('Pre-requisito removido.')
    },
    onError: (error) => toast.error(extractErrorMessage(error, 'Falha ao remover pre-requisito.')),
  })

  const deleteCoMutation = useMutation({
    mutationFn: (id) => configurarCursoApi.deleteCoRequisito(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['configurar-curso', 'co-requisitos', selectedMatrizId] })
      setToDeleteCo(null)
      toast.success('Co-requisito removido.')
    },
    onError: (error) => toast.error(extractErrorMessage(error, 'Falha ao remover co-requisito.')),
  })

  const matrizComponentes = useMemo(() => extractResults(matrizComponentesQuery.data) || [], [matrizComponentesQuery.data])
  const preRequisitos = useMemo(() => extractResults(preRequisitosQuery.data) || [], [preRequisitosQuery.data])
  const coRequisitos = useMemo(() => extractResults(coRequisitosQuery.data) || [], [coRequisitosQuery.data])

  const componenteOptions = useMemo(
    () => matrizComponentes.map((item) => ({
      id: item.componente_curricular,
      nome: `${item.componente_curricular_codigo} - ${item.componente_curricular_nome}`,
    })),
    [matrizComponentes],
  )

  if (!selectedMatrizId) {
    return (
      <AlertMessage
        type="warning"
        title="Dependencia da etapa"
        message="Selecione uma matriz e vincule componentes para definir pre-requisitos e co-requisitos."
      />
    )
  }

  return (
    <section className="grid gap-6">
      <AlertMessage
        type="info"
        title="Etapa 4"
        message="Defina os requisitos entre os componentes da matriz. O servidor valida auto-referencia, ciclo e duplicidade."
      />

      <div className="grid gap-4 rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
        <h3 className="text-base font-semibold text-slate-900">Novo pre-requisito</h3>

        <div className="grid gap-4 md:grid-cols-2">
          <FormField id="pre-componente" label="Componente" required>
            <select
              id="pre-componente"
              value={preForm.componente}
              onChange={(event) => setPreForm((current) => ({ ...current, componente: event.target.value }))}
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-emerald-500 focus:ring-2 focus:ring-emerald-100"
            >
              <option value="">Selecione</option>
              {componenteOptions.map((item) => (
                <option key={item.id} value={item.id}>{item.nome}</option>
              ))}
            </select>
          </FormField>

          <FormField id="pre-requisito" label="Requisito" required>
            <select
              id="pre-requisito"
              value={preForm.requisito}
              onChange={(event) => setPreForm((current) => ({ ...current, requisito: event.target.value }))}
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-emerald-500 focus:ring-2 focus:ring-emerald-100"
            >
              <option value="">Selecione</option>
              {componenteOptions
                .filter((item) => String(item.id) !== String(preForm.componente || ''))
                .map((item) => (
                  <option key={item.id} value={item.id}>{item.nome}</option>
                ))}
            </select>
          </FormField>
        </div>

        <div className="flex justify-end">
          <button
            type="button"
            onClick={() => {
              if (!preForm.componente || !preForm.requisito) {
                toast.error('Selecione componente e requisito.')
                return
              }
              createPreMutation.mutate({ componente: Number(preForm.componente), requisito: Number(preForm.requisito) })
            }}
            disabled={createPreMutation.isPending}
            className="rounded-lg bg-emerald-600 px-4 py-2 text-sm font-semibold text-white hover:bg-emerald-700 disabled:opacity-60"
          >
            {createPreMutation.isPending ? 'Salvando...' : 'Adicionar pre-requisito'}
          </button>
        </div>

        <DataTable
          columns={REQUISITO_COLUMNS}
          rows={preRequisitos}
          emptyMessage="Nenhum pre-requisito cadastrado."
          rowActions={(row) => (
            <div className="flex justify-end">
              <button
                type="button"
                onClick={() => setToDeletePre(row)}
                className="rounded-lg border border-red-200 bg-red-50 px-2 py-1 text-xs font-semibold text-red-700 hover:bg-red-100"
              >
                Remover
              </button>
            </div>
          )}
        />
      </div>

      <div className="grid gap-4 rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
        <h3 className="text-base font-semibold text-slate-900">Novo co-requisito</h3>

        <div className="grid gap-4 md:grid-cols-2">
          <FormField id="co-componente" label="Componente" required>
            <select
              id="co-componente"
              value={coForm.componente}
              onChange={(event) => setCoForm((current) => ({ ...current, componente: event.target.value }))}
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-emerald-500 focus:ring-2 focus:ring-emerald-100"
            >
              <option value="">Selecione</option>
              {componenteOptions.map((item) => (
                <option key={item.id} value={item.id}>{item.nome}</option>
              ))}
            </select>
          </FormField>

          <FormField id="co-requisito" label="Requisito" required>
            <select
              id="co-requisito"
              value={coForm.requisito}
              onChange={(event) => setCoForm((current) => ({ ...current, requisito: event.target.value }))}
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-emerald-500 focus:ring-2 focus:ring-emerald-100"
            >
              <option value="">Selecione</option>
              {componenteOptions
                .filter((item) => String(item.id) !== String(coForm.componente || ''))
                .map((item) => (
                  <option key={item.id} value={item.id}>{item.nome}</option>
                ))}
            </select>
          </FormField>
        </div>

        <div className="flex justify-end">
          <button
            type="button"
            onClick={() => {
              if (!coForm.componente || !coForm.requisito) {
                toast.error('Selecione componente e requisito.')
                return
              }
              createCoMutation.mutate({ componente: Number(coForm.componente), requisito: Number(coForm.requisito) })
            }}
            disabled={createCoMutation.isPending}
            className="rounded-lg bg-emerald-600 px-4 py-2 text-sm font-semibold text-white hover:bg-emerald-700 disabled:opacity-60"
          >
            {createCoMutation.isPending ? 'Salvando...' : 'Adicionar co-requisito'}
          </button>
        </div>

        <DataTable
          columns={REQUISITO_COLUMNS}
          rows={coRequisitos}
          emptyMessage="Nenhum co-requisito cadastrado."
          rowActions={(row) => (
            <div className="flex justify-end">
              <button
                type="button"
                onClick={() => setToDeleteCo(row)}
                className="rounded-lg border border-red-200 bg-red-50 px-2 py-1 text-xs font-semibold text-red-700 hover:bg-red-100"
              >
                Remover
              </button>
            </div>
          )}
        />
      </div>

      <ConfirmDialog
        open={Boolean(toDeletePre)}
        title="Remover pre-requisito"
        description={toDeletePre ? `Remover ${toDeletePre.requisito_nome} como pre-requisito de ${toDeletePre.componente_nome}?` : ''}
        danger
        onCancel={() => setToDeletePre(null)}
        onConfirm={() => toDeletePre && deletePreMutation.mutate(toDeletePre.id)}
      />

      <ConfirmDialog
        open={Boolean(toDeleteCo)}
        title="Remover co-requisito"
        description={toDeleteCo ? `Remover relacao de ${toDeleteCo.componente_nome} com ${toDeleteCo.requisito_nome}?` : ''}
        danger
        onCancel={() => setToDeleteCo(null)}
        onConfirm={() => toDeleteCo && deleteCoMutation.mutate(toDeleteCo.id)}
      />
    </section>
  )
}
