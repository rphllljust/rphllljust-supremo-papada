import { useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'

import AlertMessage from '@/modules/configurar-curso/components/AlertMessage'
import ConfirmDialog from '@/modules/configurar-curso/components/ConfirmDialog'
import DataTable from '@/modules/configurar-curso/components/DataTable'
import FormField from '@/modules/configurar-curso/components/FormField'
import { COMPONENTE_TIPO_OPTIONS } from '@/modules/configurar-curso/constants'
import { configurarCursoApi, extractErrorMessage, extractResults } from '@/modules/configurar-curso/services/configurarCursoApi'

const LINKED_COLUMNS = [
  { key: 'componente_curricular_codigo', label: 'Codigo' },
  { key: 'componente_curricular_nome', label: 'Componente' },
  { key: 'periodo', label: 'Periodo' },
  { key: 'carga_horaria', label: 'CH' },
  { key: 'obrigatorio', label: 'Obrigatorio', render: (row) => (row.obrigatorio ? 'Sim' : 'Nao') },
]

const EMPTY_COMPONENT_FORM = {
  codigo: '',
  nome: '',
  carga_horaria: '',
  tipo: 'OBRIGATORIO',
  ementa: '',
}

export default function EtapaComponentes({ selectedMatrizId }) {
  const queryClient = useQueryClient()
  const [catalogSearch, setCatalogSearch] = useState('')
  const [selectedComponentes, setSelectedComponentes] = useState([])
  const [periodoPadrao, setPeriodoPadrao] = useState('1')
  const [ordemInicial, setOrdemInicial] = useState('1')
  const [modalOpen, setModalOpen] = useState(false)
  const [formData, setFormData] = useState(EMPTY_COMPONENT_FORM)
  const [toDeleteVinculo, setToDeleteVinculo] = useState(null)

  const componentesCatalogoQuery = useQuery({
    queryKey: ['configurar-curso', 'componentes-catalogo', catalogSearch],
    queryFn: () => configurarCursoApi.listComponentes({ search: catalogSearch, page_size: 100, ativo: true }).then((response) => response.data),
    staleTime: 20_000,
  })

  const matrizComponentesQuery = useQuery({
    queryKey: ['configurar-curso', 'matriz-componentes', selectedMatrizId],
    queryFn: () => configurarCursoApi.listMatrizComponentes(selectedMatrizId, { page_size: 200 }).then((response) => response.data),
    staleTime: 20_000,
    enabled: Boolean(selectedMatrizId),
  })

  const createComponenteMutation = useMutation({
    mutationFn: (payload) => configurarCursoApi.createComponente(payload),
    onSuccess: (response) => {
      queryClient.invalidateQueries({ queryKey: ['configurar-curso', 'componentes-catalogo'] })
      setModalOpen(false)
      setFormData(EMPTY_COMPONENT_FORM)
      setSelectedComponentes((current) => Array.from(new Set([...current, response.data.id])))
      toast.success('Componente cadastrado no catalogo.')
    },
    onError: (error) => toast.error(extractErrorMessage(error, 'Nao foi possivel cadastrar o componente.')),
  })

  const vincularMutation = useMutation({
    mutationFn: async ({ matrizId, componenteIds, componentesMap }) => {
      for (let index = 0; index < componenteIds.length; index += 1) {
        const componenteId = componenteIds[index]
        const componente = componentesMap.get(componenteId)

        await configurarCursoApi.createMatrizComponente(matrizId, {
          matriz_curricular: matrizId,
          componente_curricular: componenteId,
          periodo: Number(periodoPadrao),
          carga_horaria: Number(componente?.carga_horaria || 1),
          obrigatorio: true,
          ordem: Number(ordemInicial) + index,
        })
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['configurar-curso', 'matriz-componentes', selectedMatrizId] })
      setSelectedComponentes([])
      toast.success('Componentes vinculados a matriz curricular.')
    },
    onError: (error) => toast.error(extractErrorMessage(error, 'Falha ao vincular componentes.')),
  })

  const deleteVinculoMutation = useMutation({
    mutationFn: (vinculoId) => configurarCursoApi.deleteMatrizComponente(vinculoId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['configurar-curso', 'matriz-componentes', selectedMatrizId] })
      setToDeleteVinculo(null)
      toast.success('Vinculo removido da matriz.')
    },
    onError: (error) => toast.error(extractErrorMessage(error, 'Nao foi possivel remover o vinculo.')),
  })

  const componentesCatalogo = useMemo(() => extractResults(componentesCatalogoQuery.data) || [], [componentesCatalogoQuery.data])
  const componentesVinculados = useMemo(() => extractResults(matrizComponentesQuery.data) || [], [matrizComponentesQuery.data])

  const linkedIds = useMemo(
    () => new Set(componentesVinculados.map((item) => item.componente_curricular)),
    [componentesVinculados],
  )
  const componentesCatalogoById = useMemo(
    () => new Map(componentesCatalogo.map((item) => [item.id, item])),
    [componentesCatalogo],
  )

  if (!selectedMatrizId) {
    return (
      <AlertMessage
        type="warning"
        title="Dependencia da etapa"
        message="Selecione uma matriz curricular na etapa anterior para vincular componentes."
      />
    )
  }

  return (
    <section className="grid gap-6">
      <AlertMessage
        type="info"
        title="Etapa 3"
        message="Busque componentes existentes, cadastre novos quando necessario e vincule os componentes selecionados a matriz curricular."
      />

      <div className="grid gap-4 rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
        <div className="grid gap-3 md:grid-cols-[2fr_1fr_1fr_auto] md:items-end">
          <FormField id="componentes-catalogo-search" label="Buscar componente">
            <input
              id="componentes-catalogo-search"
              type="search"
              value={catalogSearch}
              onChange={(event) => setCatalogSearch(event.target.value)}
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-emerald-500 focus:ring-2 focus:ring-emerald-100"
              placeholder="Nome, codigo ou ementa"
            />
          </FormField>

          <FormField id="componentes-periodo" label="Periodo padrao">
            <input
              id="componentes-periodo"
              type="number"
              min="1"
              value={periodoPadrao}
              onChange={(event) => setPeriodoPadrao(event.target.value)}
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-emerald-500 focus:ring-2 focus:ring-emerald-100"
            />
          </FormField>

          <FormField id="componentes-ordem" label="Ordem inicial">
            <input
              id="componentes-ordem"
              type="number"
              min="1"
              value={ordemInicial}
              onChange={(event) => setOrdemInicial(event.target.value)}
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-emerald-500 focus:ring-2 focus:ring-emerald-100"
            />
          </FormField>

          <button
            type="button"
            onClick={() => setModalOpen(true)}
            className="rounded-lg border border-emerald-300 bg-emerald-50 px-4 py-2 text-sm font-semibold text-emerald-700 hover:bg-emerald-100"
          >
            Novo componente
          </button>
        </div>

        <div className="max-h-64 overflow-auto rounded-xl border border-slate-200">
          <ul className="divide-y divide-slate-100">
            {componentesCatalogo.map((componente) => {
              const alreadyLinked = linkedIds.has(componente.id)
              const checked = selectedComponentes.includes(componente.id)

              return (
                <li key={componente.id} className="flex items-center gap-3 px-3 py-2 text-sm">
                  <input
                    type="checkbox"
                    checked={checked}
                    onChange={(event) => {
                      if (event.target.checked) {
                        setSelectedComponentes((current) => [...current, componente.id])
                        return
                      }
                      setSelectedComponentes((current) => current.filter((item) => item !== componente.id))
                    }}
                    disabled={alreadyLinked}
                  />
                  <span className="font-medium text-slate-700">{componente.codigo}</span>
                  <span className="text-slate-700">{componente.nome}</span>
                  {alreadyLinked ? <span className="ml-auto text-xs font-semibold text-emerald-700">Ja vinculado</span> : null}
                </li>
              )
            })}
          </ul>
        </div>

        <div className="flex justify-end">
          <button
            type="button"
            onClick={() => {
              const componentesDisponiveis = selectedComponentes.filter((id) => !linkedIds.has(id))
              if (!componentesDisponiveis.length) {
                toast.error('Selecione ao menos um componente ainda nao vinculado.')
                return
              }

              vincularMutation.mutate({
                matrizId: selectedMatrizId,
                componenteIds: componentesDisponiveis,
                componentesMap: componentesCatalogoById,
              })
            }}
            disabled={vincularMutation.isPending}
            className="rounded-lg bg-emerald-600 px-4 py-2 text-sm font-semibold text-white hover:bg-emerald-700 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {vincularMutation.isPending ? 'Vinculando...' : 'Vincular componentes selecionados'}
          </button>
        </div>
      </div>

      <div className="grid gap-3 rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
        <h3 className="text-base font-semibold text-slate-900">Componentes vinculados a matriz</h3>

        <DataTable
          columns={LINKED_COLUMNS}
          rows={componentesVinculados}
          emptyMessage="Nenhum componente vinculado a matriz." 
          rowActions={(row) => (
            <div className="flex justify-end">
              <button
                type="button"
                onClick={() => setToDeleteVinculo(row)}
                className="rounded-lg border border-red-200 bg-red-50 px-2 py-1 text-xs font-semibold text-red-700 hover:bg-red-100"
              >
                Remover
              </button>
            </div>
          )}
        />
      </div>

      <div className="rounded-xl border border-slate-200 bg-slate-50 p-3 text-xs text-slate-600">
        Cada vinculo usa periodo e ordem para organizar os componentes na matriz curricular.
      </div>

      <ConfirmDialog
        open={Boolean(toDeleteVinculo)}
        title="Remover componente da matriz"
        description={toDeleteVinculo ? `Deseja remover ${toDeleteVinculo.componente_curricular_nome} desta matriz?` : ''}
        danger
        onCancel={() => setToDeleteVinculo(null)}
        onConfirm={() => toDeleteVinculo && deleteVinculoMutation.mutate(toDeleteVinculo.id)}
      />

      {modalOpen ? (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 px-4">
          <div className="w-full max-w-2xl rounded-2xl border border-slate-200 bg-white p-5 shadow-2xl">
            <h3 className="text-lg font-bold text-slate-900">Cadastro rapido de componente</h3>
            <p className="mt-1 text-sm text-slate-600">Crie o componente sem sair do wizard.</p>

            <div className="mt-4 grid gap-4 md:grid-cols-2">
              <FormField id="new-componente-codigo" label="Codigo" required>
                <input
                  id="new-componente-codigo"
                  value={formData.codigo}
                  onChange={(event) => setFormData((current) => ({ ...current, codigo: event.target.value }))}
                  className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-emerald-500 focus:ring-2 focus:ring-emerald-100"
                />
              </FormField>

              <FormField id="new-componente-tipo" label="Tipo" required>
                <select
                  id="new-componente-tipo"
                  value={formData.tipo}
                  onChange={(event) => setFormData((current) => ({ ...current, tipo: event.target.value }))}
                  className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-emerald-500 focus:ring-2 focus:ring-emerald-100"
                >
                  {COMPONENTE_TIPO_OPTIONS.map((option) => (
                    <option key={option.value} value={option.value}>{option.label}</option>
                  ))}
                </select>
              </FormField>

              <FormField id="new-componente-nome" label="Nome" required>
                <input
                  id="new-componente-nome"
                  value={formData.nome}
                  onChange={(event) => setFormData((current) => ({ ...current, nome: event.target.value }))}
                  className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-emerald-500 focus:ring-2 focus:ring-emerald-100"
                />
              </FormField>

              <FormField id="new-componente-ch" label="Carga horaria" required>
                <input
                  id="new-componente-ch"
                  type="number"
                  min="1"
                  value={formData.carga_horaria}
                  onChange={(event) => setFormData((current) => ({ ...current, carga_horaria: event.target.value }))}
                  className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-emerald-500 focus:ring-2 focus:ring-emerald-100"
                />
              </FormField>

              <div className="md:col-span-2">
                <FormField id="new-componente-ementa" label="Ementa">
                  <textarea
                    id="new-componente-ementa"
                    rows={4}
                    value={formData.ementa}
                    onChange={(event) => setFormData((current) => ({ ...current, ementa: event.target.value }))}
                    className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-emerald-500 focus:ring-2 focus:ring-emerald-100"
                  />
                </FormField>
              </div>
            </div>

            <div className="mt-5 flex justify-end gap-2">
              <button
                type="button"
                onClick={() => setModalOpen(false)}
                className="rounded-lg border border-slate-300 px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
              >
                Cancelar
              </button>
              <button
                type="button"
                onClick={() => {
                  if (!formData.codigo.trim() || !formData.nome.trim() || !formData.carga_horaria) {
                    toast.error('Preencha codigo, nome e carga horaria do componente.')
                    return
                  }

                  createComponenteMutation.mutate({
                    codigo: formData.codigo.trim(),
                    nome: formData.nome.trim(),
                    carga_horaria: Number(formData.carga_horaria),
                    tipo: formData.tipo,
                    ementa: formData.ementa.trim(),
                    ativo: true,
                  })
                }}
                disabled={createComponenteMutation.isPending}
                className="rounded-lg bg-emerald-600 px-3 py-2 text-sm font-semibold text-white hover:bg-emerald-700 disabled:opacity-60"
              >
                {createComponenteMutation.isPending ? 'Salvando...' : 'Salvar componente'}
              </button>
            </div>
          </div>
        </div>
      ) : null}
    </section>
  )
}
