import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { ArrowLeft } from 'lucide-react'
import toast from 'react-hot-toast'
import { Link, useNavigate } from 'react-router-dom'

import { processosApi, usuariosApi } from '@/api/endpoints'
import EntityFormPanel from '@/components/ui/EntityFormPanel'
import SearchableRemoteSelect from '@/components/ui/SearchableRemoteSelect'

const STATUS_OPTIONS = [
  { value: 'ABERTO', label: 'Aberto' },
  { value: 'EM_TRAMITACAO', label: 'Em Tramitação' },
  { value: 'CONCLUIDO', label: 'Concluído' },
  { value: 'ARQUIVADO', label: 'Arquivado' },
]

const TIPO_OPTIONS = [
  { value: 'REQUERIMENTO', label: 'Requerimento' },
  { value: 'RECURSO', label: 'Recurso' },
  { value: 'TRANSFERENCIA', label: 'Transferência' },
  { value: 'SOLICITACAO', label: 'Solicitação Geral' },
  { value: 'OUTROS', label: 'Outros' },
]

const DEFAULT_FORM = {
  tipo: 'REQUERIMENTO',
  requerente: '',
  assunto: '',
  descricao: '',
  status: 'ABERTO',
  data_conclusao: '',
}

function getErrorMessage(error, fallback) {
  const data = error?.response?.data
  if (!data) return fallback
  if (typeof data.detail === 'string') return data.detail
  const firstValue = Object.values(data)[0]
  return Array.isArray(firstValue) ? firstValue[0] : (firstValue || fallback)
}

export default function ProcessoCreatePage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [formData, setFormData] = useState(DEFAULT_FORM)
  const [requerenteSearch, setRequerenteSearch] = useState('')

  const { data: requerentesData } = useQuery({
    queryKey: ['usuarios', 'processos-options', requerenteSearch],
    queryFn: () => usuariosApi.list({ page_size: 10, search: requerenteSearch || undefined }).then((response) => response.data),
    staleTime: 60_000,
  })

  const saveMutation = useMutation({
    mutationFn: (payload) => processosApi.create(payload),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['processos'] })
      toast.success('Processo aberto com sucesso.')
      navigate('/processos')
    },
    onError: (error) => toast.error(getErrorMessage(error, 'Não foi possível salvar o processo.')),
  })

  const requerentes = requerentesData?.results || []

  return (
    <div className="page page--wide">
      <nav className="profile-breadcrumb">
        <Link to="/dashboard">Início</Link>
        <span className="profile-breadcrumb__sep">&gt;</span>
        <Link to="/processos">Processos</Link>
        <span className="profile-breadcrumb__sep">&gt;</span>
        <span>Abrir Processo</span>
      </nav>

      <div className="page-header">
        <div>
          <h1 className="page-title">Abrir processo</h1>
          <p className="page-subtitle">O cadastro inicial do processo foi movido para uma página dedicada.</p>
        </div>
        <div className="page-header__actions">
          <button type="button" className="btn btn--outline" onClick={() => navigate('/processos')}>
            <ArrowLeft size={16} /> Voltar para processos
          </button>
        </div>
      </div>

      <EntityFormPanel
        title="Abrir processo"
        subtitle="Preencha o tipo, o requerente e os dados principais do processo."
        onSubmit={(event) => {
          event.preventDefault()

          if (!formData.tipo || !formData.assunto.trim()) {
            toast.error('Informe o tipo e o assunto do processo.')
            return
          }

          saveMutation.mutate({
            tipo: formData.tipo,
            requerente: formData.requerente ? Number(formData.requerente) : null,
            assunto: formData.assunto.trim(),
            descricao: formData.descricao.trim(),
            status: formData.status,
            data_conclusao: formData.data_conclusao || null,
          })
        }}
        onCancel={() => navigate('/processos')}
        submitLabel="Criar processo"
        isSubmitting={saveMutation.isPending}
      >
        <div className="form-field">
          <label htmlFor="processo-tipo">Tipo</label>
          <select id="processo-tipo" className="select" value={formData.tipo} onChange={(event) => setFormData((current) => ({ ...current, tipo: event.target.value }))}>
            {TIPO_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>{option.label}</option>
            ))}
          </select>
        </div>

        <div className="form-field">
          <label htmlFor="processo-status">Status</label>
          <select id="processo-status" className="select" value={formData.status} onChange={(event) => setFormData((current) => ({ ...current, status: event.target.value }))}>
            {STATUS_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>{option.label}</option>
            ))}
          </select>
        </div>

        <SearchableRemoteSelect
          id="processo-requerente"
          label="Requerente"
          searchLabel="Buscar requerente"
          searchPlaceholder="Digite nome, CPF ou usuário"
          searchValue={requerenteSearch}
          onSearchChange={setRequerenteSearch}
          value={formData.requerente}
          onChange={(nextValue) => setFormData((current) => ({ ...current, requerente: nextValue }))}
          options={requerentes}
          getOptionLabel={(item) => item.username ? `${item.nome_completo} - ${item.username}` : item.nome_completo}
          emptyOptionLabel="Sem requerente"
        />

        <div className="form-field form-field--full">
          <label htmlFor="processo-assunto">Assunto</label>
          <input id="processo-assunto" className="form-control" value={formData.assunto} onChange={(event) => setFormData((current) => ({ ...current, assunto: event.target.value }))} />
        </div>

        <div className="form-field">
          <label htmlFor="processo-data-conclusao">Data de conclusão</label>
          <input id="processo-data-conclusao" type="date" className="form-control" value={formData.data_conclusao} onChange={(event) => setFormData((current) => ({ ...current, data_conclusao: event.target.value }))} />
        </div>

        <div className="form-field form-field--full">
          <label htmlFor="processo-descricao">Descrição</label>
          <textarea id="processo-descricao" className="form-control" rows={4} value={formData.descricao} onChange={(event) => setFormData((current) => ({ ...current, descricao: event.target.value }))} />
        </div>
      </EntityFormPanel>
    </div>
  )
}
