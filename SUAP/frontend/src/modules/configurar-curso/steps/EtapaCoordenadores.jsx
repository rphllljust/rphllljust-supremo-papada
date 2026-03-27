import { useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'

import AlertMessage from '@/modules/configurar-curso/components/AlertMessage'
import ConfirmDialog from '@/modules/configurar-curso/components/ConfirmDialog'
import DataTable from '@/modules/configurar-curso/components/DataTable'
import FormField from '@/modules/configurar-curso/components/FormField'
import { configurarCursoApi, extractErrorMessage, extractResults } from '@/modules/configurar-curso/services/configurarCursoApi'

const LINK_COLUMNS = [
  { key: 'coordenador_nome', label: 'Coordenador' },
  { key: 'inicio_vigencia', label: 'Inicio' },
  { key: 'fim_vigencia', label: 'Fim', render: (row) => row.fim_vigencia || '-' },
  { key: 'principal', label: 'Principal', render: (row) => (row.principal ? 'Sim' : 'Nao') },
]

const EMPTY_CREATE_COORD = {
  nome: '',
  email: '',
  matricula: '',
}

const EMPTY_LINK_FORM = {
  coordenador: '',
  principal: false,
  inicio_vigencia: '',
  fim_vigencia: '',
}

function todayISO() {
  const now = new Date()
  const local = new Date(now.getTime() - now.getTimezoneOffset() * 60_000)
  return local.toISOString().slice(0, 10)
}

export default function EtapaCoordenadores({ selectedCursoId }) {
  const queryClient = useQueryClient()
  const [search, setSearch] = useState('')
  const [coordForm, setCoordForm] = useState(EMPTY_CREATE_COORD)
  const [linkForm, setLinkForm] = useState({ ...EMPTY_LINK_FORM, inicio_vigencia: todayISO() })
  const [toDelete, setToDelete] = useState(null)

  const coordenadoresQuery = useQuery({
    queryKey: ['configurar-curso', 'coordenadores', search],
    queryFn: () => configurarCursoApi.listCoordenadores({ search, page_size: 100, ativo: true }).then((response) => response.data),
    staleTime: 20_000,
  })

  const vinculosQuery = useQuery({
    queryKey: ['configurar-curso', 'curso-coordenadores', selectedCursoId],
    queryFn: () => configurarCursoApi.listCursoCoordenadores(selectedCursoId).then((response) => response.data),
    enabled: Boolean(selectedCursoId),
    staleTime: 20_000,
  })

  const createCoordMutation = useMutation({
    mutationFn: (payload) => configurarCursoApi.createCoordenador(payload),
    onSuccess: (response) => {
      queryClient.invalidateQueries({ queryKey: ['configurar-curso', 'coordenadores'] })
      setCoordForm(EMPTY_CREATE_COORD)
      setLinkForm((current) => ({ ...current, coordenador: String(response.data.id) }))
      toast.success('Coordenador cadastrado e selecionado.')
    },
    onError: (error) => toast.error(extractErrorMessage(error, 'Nao foi possivel cadastrar coordenador.')),
  })

  const addLinkMutation = useMutation({
    mutationFn: ({ cursoId, payload }) => configurarCursoApi.addCursoCoordenador(cursoId, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['configurar-curso', 'curso-coordenadores', selectedCursoId] })
      setLinkForm({ ...EMPTY_LINK_FORM, inicio_vigencia: todayISO() })
      toast.success('Coordenador vinculado ao curso.')
    },
    onError: (error) => toast.error(extractErrorMessage(error, 'Nao foi possivel vincular coordenador ao curso.')),
  })

  const deleteLinkMutation = useMutation({
    mutationFn: (id) => configurarCursoApi.deleteCursoCoordenador(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['configurar-curso', 'curso-coordenadores', selectedCursoId] })
      setToDelete(null)
      toast.success('Vinculo removido do curso.')
    },
    onError: (error) => toast.error(extractErrorMessage(error, 'Falha ao remover vinculo.')),
  })

  const coordenadores = useMemo(() => extractResults(coordenadoresQuery.data) || [], [coordenadoresQuery.data])
  const vinculos = useMemo(
    () => (Array.isArray(vinculosQuery.data) ? vinculosQuery.data : extractResults(vinculosQuery.data) || []),
    [vinculosQuery.data],
  )

  if (!selectedCursoId) {
    return (
      <AlertMessage
        type="warning"
        title="Dependencia da etapa"
        message="Selecione ou cadastre um curso na etapa anterior para definir coordenadores."
      />
    )
  }

  return (
    <section className="grid gap-6">
      <AlertMessage
        type="info"
        title="Etapa 6"
        message="Um curso pode possuir um ou mais coordenadores. Defina tambem o coordenador principal e vigencia do vinculo."
      />

      <div className="grid gap-4 rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
        <h3 className="text-base font-semibold text-slate-900">Vincular coordenador ao curso</h3>

        <div className="grid gap-4 md:grid-cols-2">
          <FormField id="coord-search" label="Buscar coordenador">
            <input
              id="coord-search"
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-emerald-500 focus:ring-2 focus:ring-emerald-100"
              placeholder="Nome, email ou matricula"
            />
          </FormField>

          <FormField id="coord-select" label="Coordenador" required>
            <select
              id="coord-select"
              value={linkForm.coordenador}
              onChange={(event) => setLinkForm((current) => ({ ...current, coordenador: event.target.value }))}
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-emerald-500 focus:ring-2 focus:ring-emerald-100"
            >
              <option value="">Selecione</option>
              {coordenadores.map((item) => (
                <option key={item.id} value={item.id}>{`${item.nome} - ${item.matricula}`}</option>
              ))}
            </select>
          </FormField>

          <FormField id="coord-inicio" label="Inicio de vigencia" required>
            <input
              id="coord-inicio"
              type="date"
              value={linkForm.inicio_vigencia}
              onChange={(event) => setLinkForm((current) => ({ ...current, inicio_vigencia: event.target.value }))}
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-emerald-500 focus:ring-2 focus:ring-emerald-100"
            />
          </FormField>

          <FormField id="coord-fim" label="Fim de vigencia">
            <input
              id="coord-fim"
              type="date"
              value={linkForm.fim_vigencia}
              onChange={(event) => setLinkForm((current) => ({ ...current, fim_vigencia: event.target.value }))}
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-emerald-500 focus:ring-2 focus:ring-emerald-100"
            />
          </FormField>
        </div>

        <label className="inline-flex items-center gap-2 text-sm font-medium text-slate-700">
          <input
            type="checkbox"
            checked={linkForm.principal}
            onChange={(event) => setLinkForm((current) => ({ ...current, principal: event.target.checked }))}
          />
          Definir como coordenador principal
        </label>

        <div className="flex justify-end">
          <button
            type="button"
            onClick={() => {
              if (!linkForm.coordenador || !linkForm.inicio_vigencia) {
                toast.error('Selecione coordenador e informe inicio de vigencia.')
                return
              }

              addLinkMutation.mutate({
                cursoId: selectedCursoId,
                payload: {
                  curso: Number(selectedCursoId),
                  coordenador: Number(linkForm.coordenador),
                  principal: Boolean(linkForm.principal),
                  inicio_vigencia: linkForm.inicio_vigencia,
                  fim_vigencia: linkForm.fim_vigencia || null,
                },
              })
            }}
            disabled={addLinkMutation.isPending}
            className="rounded-lg bg-emerald-600 px-4 py-2 text-sm font-semibold text-white hover:bg-emerald-700 disabled:opacity-60"
          >
            {addLinkMutation.isPending ? 'Vinculando...' : 'Vincular coordenador'}
          </button>
        </div>
      </div>

      <div className="grid gap-4 rounded-2xl border border-emerald-200 bg-emerald-50 p-4 shadow-sm">
        <h3 className="text-base font-semibold text-slate-900">Cadastro rapido de coordenador</h3>

        <div className="grid gap-4 md:grid-cols-3">
          <FormField id="new-coord-nome" label="Nome" required>
            <input
              id="new-coord-nome"
              value={coordForm.nome}
              onChange={(event) => setCoordForm((current) => ({ ...current, nome: event.target.value }))}
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-emerald-500 focus:ring-2 focus:ring-emerald-100"
            />
          </FormField>

          <FormField id="new-coord-email" label="Email" required>
            <input
              id="new-coord-email"
              type="email"
              value={coordForm.email}
              onChange={(event) => setCoordForm((current) => ({ ...current, email: event.target.value }))}
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-emerald-500 focus:ring-2 focus:ring-emerald-100"
            />
          </FormField>

          <FormField id="new-coord-matricula" label="Matricula" required>
            <input
              id="new-coord-matricula"
              value={coordForm.matricula}
              onChange={(event) => setCoordForm((current) => ({ ...current, matricula: event.target.value }))}
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-emerald-500 focus:ring-2 focus:ring-emerald-100"
            />
          </FormField>
        </div>

        <div>
          <button
            type="button"
            onClick={() => {
              if (!coordForm.nome.trim() || !coordForm.email.trim() || !coordForm.matricula.trim()) {
                toast.error('Preencha nome, email e matricula do coordenador.')
                return
              }

              createCoordMutation.mutate({
                nome: coordForm.nome.trim(),
                email: coordForm.email.trim(),
                matricula: coordForm.matricula.trim(),
                ativo: true,
              })
            }}
            disabled={createCoordMutation.isPending}
            className="rounded-lg bg-emerald-600 px-4 py-2 text-sm font-semibold text-white hover:bg-emerald-700 disabled:opacity-60"
          >
            {createCoordMutation.isPending ? 'Salvando...' : 'Cadastrar coordenador'}
          </button>
        </div>
      </div>

      <div className="grid gap-3 rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
        <h3 className="text-base font-semibold text-slate-900">Coordenadores vinculados</h3>

        <DataTable
          columns={LINK_COLUMNS}
          rows={vinculos}
          emptyMessage="Nenhum coordenador vinculado ao curso."
          rowActions={(row) => (
            <div className="flex justify-end">
              <button
                type="button"
                onClick={() => setToDelete(row)}
                className="rounded-lg border border-red-200 bg-red-50 px-2 py-1 text-xs font-semibold text-red-700 hover:bg-red-100"
              >
                Remover
              </button>
            </div>
          )}
        />
      </div>

      <ConfirmDialog
        open={Boolean(toDelete)}
        title="Remover vinculo"
        description={toDelete ? `Remover ${toDelete.coordenador_nome} do curso?` : ''}
        danger
        onCancel={() => setToDelete(null)}
        onConfirm={() => toDelete && deleteLinkMutation.mutate(toDelete.id)}
      />
    </section>
  )
}
