import { useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'

import AlertMessage from '@/modules/configurar-curso/components/AlertMessage'
import FormField from '@/modules/configurar-curso/components/FormField'
import SearchSelect from '@/modules/configurar-curso/components/SearchSelect'
import { configurarCursoApi, extractErrorMessage, extractResults } from '@/modules/configurar-curso/services/configurarCursoApi'

const EMPTY_FORM = {
  nome: '',
  codigo: '',
  versao: '1.0',
  carga_horaria_total: '',
}

export default function EtapaMatrizCurricular({
  selectedEstruturaId,
  selectedMatrizId,
  onSelectMatriz,
}) {
  const queryClient = useQueryClient()
  const [search, setSearch] = useState('')
  const [formData, setFormData] = useState(EMPTY_FORM)

  const matrizesQuery = useQuery({
    queryKey: ['configurar-curso', 'matrizes', { search, estrutura: selectedEstruturaId }],
    queryFn: () => configurarCursoApi.listMatrizes({ search, estrutura_curso: selectedEstruturaId, page_size: 100 }).then((response) => response.data),
    staleTime: 20_000,
    enabled: Boolean(selectedEstruturaId),
  })

  const createMutation = useMutation({
    mutationFn: (payload) => configurarCursoApi.createMatriz(payload),
    onSuccess: (response) => {
      const matriz = response.data
      queryClient.invalidateQueries({ queryKey: ['configurar-curso', 'matrizes'] })
      onSelectMatriz(matriz.id, matriz)
      setFormData(EMPTY_FORM)
      toast.success('Matriz curricular cadastrada e selecionada.')
    },
    onError: (error) => toast.error(extractErrorMessage(error, 'Nao foi possivel cadastrar a matriz curricular.')),
  })

  const matrizes = useMemo(() => extractResults(matrizesQuery.data) || [], [matrizesQuery.data])

  if (!selectedEstruturaId) {
    return (
      <AlertMessage
        type="warning"
        title="Dependencia da etapa"
        message="Selecione uma estrutura de curso na etapa anterior para habilitar o cadastro de matriz curricular."
      />
    )
  }

  return (
    <section className="grid gap-6">
      <AlertMessage
        type="info"
        title="Etapa 2"
        message="A matriz curricular depende de uma estrutura de curso. Voce pode selecionar uma matriz existente ou cadastrar uma nova versao."
      />

      <div className="grid gap-4 rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
        <SearchSelect
          id="wizard-matriz-select"
          label="Matriz curricular existente"
          searchLabel="Buscar matriz"
          searchValue={search}
          onSearchChange={setSearch}
          value={selectedMatrizId || ''}
          onChange={(value) => onSelectMatriz(value ? Number(value) : null, null)}
          options={matrizes}
          getOptionValue={(item) => item.id}
          getOptionLabel={(item) => `${item.codigo} - ${item.nome} (v${item.versao})`}
          emptyOptionLabel="Selecione uma matriz"
          required
        />
      </div>

      <div className="grid gap-4 rounded-2xl border border-emerald-200 bg-emerald-50 p-4 shadow-sm">
        <h3 className="text-base font-semibold text-slate-900">Cadastro rapido de matriz curricular</h3>

        <div className="grid gap-4 md:grid-cols-2">
          <FormField id="wizard-matriz-nome" label="Nome" required>
            <input
              id="wizard-matriz-nome"
              value={formData.nome}
              onChange={(event) => setFormData((current) => ({ ...current, nome: event.target.value }))}
              className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm outline-none focus:border-emerald-500 focus:ring-2 focus:ring-emerald-100"
            />
          </FormField>

          <FormField id="wizard-matriz-codigo" label="Codigo" required>
            <input
              id="wizard-matriz-codigo"
              value={formData.codigo}
              onChange={(event) => setFormData((current) => ({ ...current, codigo: event.target.value }))}
              className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm outline-none focus:border-emerald-500 focus:ring-2 focus:ring-emerald-100"
            />
          </FormField>

          <FormField id="wizard-matriz-versao" label="Versao" required>
            <input
              id="wizard-matriz-versao"
              value={formData.versao}
              onChange={(event) => setFormData((current) => ({ ...current, versao: event.target.value }))}
              className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm outline-none focus:border-emerald-500 focus:ring-2 focus:ring-emerald-100"
            />
          </FormField>

          <FormField id="wizard-matriz-ch" label="Carga horaria total" required>
            <input
              id="wizard-matriz-ch"
              type="number"
              min="1"
              value={formData.carga_horaria_total}
              onChange={(event) => setFormData((current) => ({ ...current, carga_horaria_total: event.target.value }))}
              className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm outline-none focus:border-emerald-500 focus:ring-2 focus:ring-emerald-100"
            />
          </FormField>
        </div>

        <div>
          <button
            type="button"
            onClick={() => {
              if (!formData.nome.trim() || !formData.codigo.trim() || !formData.versao.trim() || !formData.carga_horaria_total) {
                toast.error('Preencha nome, codigo, versao e carga horaria total.')
                return
              }

              createMutation.mutate({
                nome: formData.nome.trim(),
                codigo: formData.codigo.trim(),
                versao: formData.versao.trim(),
                carga_horaria_total: Number(formData.carga_horaria_total),
                estrutura_curso: selectedEstruturaId,
                ativo: true,
              })
            }}
            disabled={createMutation.isPending}
            className="rounded-lg bg-emerald-600 px-4 py-2 text-sm font-semibold text-white hover:bg-emerald-700 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {createMutation.isPending ? 'Salvando...' : 'Cadastrar matriz'}
          </button>
        </div>
      </div>
    </section>
  )
}
