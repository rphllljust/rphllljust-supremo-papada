import { useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'

import SearchSelect from '@/modules/configurar-curso/components/SearchSelect'
import FormField from '@/modules/configurar-curso/components/FormField'
import AlertMessage from '@/modules/configurar-curso/components/AlertMessage'
import { configurarCursoApi, extractErrorMessage, extractResults } from '@/modules/configurar-curso/services/configurarCursoApi'

const EMPTY_FORM = {
  nome: '',
  descricao: '',
}

export default function EtapaEstruturaCurso({ selectedEstruturaId, onSelectEstrutura }) {
  const queryClient = useQueryClient()
  const [search, setSearch] = useState('')
  const [newForm, setNewForm] = useState(EMPTY_FORM)

  const estruturasQuery = useQuery({
    queryKey: ['configurar-curso', 'estruturas', search],
    queryFn: () => configurarCursoApi.listEstruturas({ search, page_size: 100 }).then((response) => response.data),
    staleTime: 20_000,
  })

  const createMutation = useMutation({
    mutationFn: (payload) => configurarCursoApi.createEstrutura(payload),
    onSuccess: (response) => {
      const estrutura = response.data
      queryClient.invalidateQueries({ queryKey: ['configurar-curso', 'estruturas'] })
      onSelectEstrutura(estrutura.id, estrutura)
      setNewForm(EMPTY_FORM)
      toast.success('Estrutura de curso cadastrada e selecionada.')
    },
    onError: (error) => {
      toast.error(extractErrorMessage(error, 'Nao foi possivel cadastrar a estrutura de curso.'))
    },
  })

  const estruturas = useMemo(() => extractResults(estruturasQuery.data) || [], [estruturasQuery.data])

  return (
    <section className="grid gap-6">
      <AlertMessage
        type="info"
        title="Etapa 1"
        message="Verifique se a estrutura de curso ja existe. Caso nao exista, cadastre uma nova estrutura sem sair do fluxo."
      />

      <div className="grid gap-4 rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
        <SearchSelect
          id="wizard-estrutura-select"
          label="Estrutura de curso existente"
          searchLabel="Buscar estrutura"
          searchValue={search}
          onSearchChange={setSearch}
          value={selectedEstruturaId || ''}
          onChange={(value) => onSelectEstrutura(value ? Number(value) : null, null)}
          options={estruturas}
          getOptionValue={(item) => item.id}
          getOptionLabel={(item) => item.nome}
          emptyOptionLabel="Selecione uma estrutura"
          required
        />

        {estruturasQuery.isLoading ? <p className="text-sm text-slate-500">Carregando estruturas...</p> : null}
        {estruturasQuery.isError ? (
          <AlertMessage type="error" message="Falha ao carregar estruturas de curso." />
        ) : null}
      </div>

      <div className="grid gap-4 rounded-2xl border border-emerald-200 bg-emerald-50 p-4 shadow-sm">
        <h3 className="text-base font-semibold text-slate-900">Cadastro rapido de nova estrutura</h3>

        <div className="grid gap-4 md:grid-cols-2">
          <FormField id="wizard-estrutura-nome" label="Nome" required>
            <input
              id="wizard-estrutura-nome"
              value={newForm.nome}
              onChange={(event) => setNewForm((current) => ({ ...current, nome: event.target.value }))}
              className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm outline-none focus:border-emerald-500 focus:ring-2 focus:ring-emerald-100"
            />
          </FormField>

          <FormField id="wizard-estrutura-descricao" label="Descricao">
            <input
              id="wizard-estrutura-descricao"
              value={newForm.descricao}
              onChange={(event) => setNewForm((current) => ({ ...current, descricao: event.target.value }))}
              className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm outline-none focus:border-emerald-500 focus:ring-2 focus:ring-emerald-100"
            />
          </FormField>
        </div>

        <div>
          <button
            type="button"
            onClick={() => {
              if (!newForm.nome.trim()) {
                toast.error('Informe o nome da estrutura.')
                return
              }

              createMutation.mutate({
                nome: newForm.nome.trim(),
                descricao: newForm.descricao.trim(),
                ativo: true,
              })
            }}
            disabled={createMutation.isPending}
            className="rounded-lg bg-emerald-600 px-4 py-2 text-sm font-semibold text-white hover:bg-emerald-700 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {createMutation.isPending ? 'Salvando...' : 'Cadastrar estrutura'}
          </button>
        </div>
      </div>
    </section>
  )
}
