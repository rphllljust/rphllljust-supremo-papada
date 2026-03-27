import { useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'

import AlertMessage from '@/modules/configurar-curso/components/AlertMessage'
import FormField from '@/modules/configurar-curso/components/FormField'
import SearchSelect from '@/modules/configurar-curso/components/SearchSelect'
import { CURSO_MODALIDADE_OPTIONS, CURSO_SITUACAO_OPTIONS } from '@/modules/configurar-curso/constants'
import { configurarCursoApi, extractErrorMessage, extractResults } from '@/modules/configurar-curso/services/configurarCursoApi'

const EMPTY_FORM = {
  codigo: '',
  nome: '',
  nome_curto: '',
  modalidade: 'PRESENCIAL',
  carga_horaria_total: '',
  situacao: 'EM_CONFIGURACAO',
}

export default function EtapaCurso({
  selectedEstruturaId,
  selectedMatrizId,
  selectedCursoId,
  onSelectCurso,
}) {
  const queryClient = useQueryClient()
  const [search, setSearch] = useState('')
  const [formData, setFormData] = useState(EMPTY_FORM)

  const cursosQuery = useQuery({
    queryKey: ['configurar-curso', 'cursos', search],
    queryFn: () => configurarCursoApi.listCursos({ search, page_size: 100 }).then((response) => response.data),
    staleTime: 20_000,
  })

  const createMutation = useMutation({
    mutationFn: (payload) => configurarCursoApi.createCurso(payload),
    onSuccess: (response) => {
      const curso = response.data
      queryClient.invalidateQueries({ queryKey: ['configurar-curso', 'cursos'] })
      onSelectCurso(curso.id, curso)
      setFormData(EMPTY_FORM)
      toast.success('Curso cadastrado e vinculado a matriz curricular.')
    },
    onError: (error) => toast.error(extractErrorMessage(error, 'Nao foi possivel cadastrar o curso.')),
  })

  const cursos = useMemo(() => extractResults(cursosQuery.data) || [], [cursosQuery.data])

  if (!selectedMatrizId) {
    return (
      <AlertMessage
        type="warning"
        title="Dependencia da etapa"
        message="Selecione uma matriz curricular antes de cadastrar o curso."
      />
    )
  }

  return (
    <section className="grid gap-6">
      <AlertMessage
        type="info"
        title="Etapa 5"
        message="Cadastre o curso e vincule a matriz curricular definida no fluxo."
      />

      <div className="grid gap-4 rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
        <SearchSelect
          id="wizard-curso-select"
          label="Curso existente"
          searchLabel="Buscar curso"
          searchValue={search}
          onSearchChange={setSearch}
          value={selectedCursoId || ''}
          onChange={(value) => onSelectCurso(value ? Number(value) : null, null)}
          options={cursos}
          getOptionValue={(item) => item.id}
          getOptionLabel={(item) => `${item.codigo} - ${item.nome}`}
          emptyOptionLabel="Selecione um curso"
        />
      </div>

      <div className="grid gap-4 rounded-2xl border border-emerald-200 bg-emerald-50 p-4 shadow-sm">
        <h3 className="text-base font-semibold text-slate-900">Cadastro rapido de curso</h3>

        <div className="grid gap-4 md:grid-cols-2">
          <FormField id="curso-codigo" label="Codigo" required>
            <input
              id="curso-codigo"
              value={formData.codigo}
              onChange={(event) => setFormData((current) => ({ ...current, codigo: event.target.value }))}
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-emerald-500 focus:ring-2 focus:ring-emerald-100"
            />
          </FormField>

          <FormField id="curso-nome" label="Nome" required>
            <input
              id="curso-nome"
              value={formData.nome}
              onChange={(event) => setFormData((current) => ({ ...current, nome: event.target.value }))}
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-emerald-500 focus:ring-2 focus:ring-emerald-100"
            />
          </FormField>

          <FormField id="curso-nome-curto" label="Nome curto" required>
            <input
              id="curso-nome-curto"
              value={formData.nome_curto}
              onChange={(event) => setFormData((current) => ({ ...current, nome_curto: event.target.value }))}
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-emerald-500 focus:ring-2 focus:ring-emerald-100"
            />
          </FormField>

          <FormField id="curso-carga" label="Carga horaria total" required>
            <input
              id="curso-carga"
              type="number"
              min="1"
              value={formData.carga_horaria_total}
              onChange={(event) => setFormData((current) => ({ ...current, carga_horaria_total: event.target.value }))}
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-emerald-500 focus:ring-2 focus:ring-emerald-100"
            />
          </FormField>

          <FormField id="curso-modalidade" label="Modalidade" required>
            <select
              id="curso-modalidade"
              value={formData.modalidade}
              onChange={(event) => setFormData((current) => ({ ...current, modalidade: event.target.value }))}
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-emerald-500 focus:ring-2 focus:ring-emerald-100"
            >
              {CURSO_MODALIDADE_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>{option.label}</option>
              ))}
            </select>
          </FormField>

          <FormField id="curso-situacao" label="Situacao" required>
            <select
              id="curso-situacao"
              value={formData.situacao}
              onChange={(event) => setFormData((current) => ({ ...current, situacao: event.target.value }))}
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-emerald-500 focus:ring-2 focus:ring-emerald-100"
            >
              {CURSO_SITUACAO_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>{option.label}</option>
              ))}
            </select>
          </FormField>
        </div>

        <div>
          <button
            type="button"
            onClick={() => {
              if (!formData.codigo.trim() || !formData.nome.trim() || !formData.nome_curto.trim() || !formData.carga_horaria_total) {
                toast.error('Preencha codigo, nome, nome curto e carga horaria do curso.')
                return
              }

              createMutation.mutate({
                codigo: formData.codigo.trim(),
                nome: formData.nome.trim(),
                nome_curto: formData.nome_curto.trim(),
                modalidade: formData.modalidade,
                carga_horaria_total: Number(formData.carga_horaria_total),
                situacao: formData.situacao,
                matriz_curricular: selectedMatrizId,
                estrutura_curso: selectedEstruturaId || null,
                ativo: true,
              })
            }}
            disabled={createMutation.isPending}
            className="rounded-lg bg-emerald-600 px-4 py-2 text-sm font-semibold text-white hover:bg-emerald-700 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {createMutation.isPending ? 'Salvando...' : 'Cadastrar curso'}
          </button>
        </div>
      </div>
    </section>
  )
}
