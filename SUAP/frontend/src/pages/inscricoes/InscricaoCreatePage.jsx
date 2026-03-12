import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { ArrowLeft } from 'lucide-react'
import toast from 'react-hot-toast'
import { Link, useNavigate } from 'react-router-dom'

import { inscricoesApi, publicacoesApi } from '@/api/endpoints'
import EntityFormPanel from '@/components/ui/EntityFormPanel'
import SearchableRemoteSelect from '@/components/ui/SearchableRemoteSelect'

const INSCRICAO_STATUS_OPTIONS = [
  { value: 'PENDENTE', label: 'Pendente de validação' },
  { value: 'VALIDADA', label: 'Validada' },
  { value: 'INDEFERIDA', label: 'Indeferida' },
]

const DEFAULT_INSCRICAO_FORM = {
  publicacao: '',
  nome_candidato: '',
  cpf: '',
  email: '',
  telefone: '',
  data_nascimento: '',
  status: 'PENDENTE',
  observacao: '',
}

function getErrorMessage(error, fallback) {
  const data = error?.response?.data

  if (!data) return fallback
  if (typeof data.detail === 'string') return data.detail

  const firstValue = Object.values(data)[0]
  return Array.isArray(firstValue) ? firstValue[0] : (firstValue || fallback)
}

export default function InscricaoCreatePage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [editalSearch, setEditalSearch] = useState('')
  const [formData, setFormData] = useState(DEFAULT_INSCRICAO_FORM)

  const { data: editaisData } = useQuery({
    queryKey: ['publicacoes', 'inscricoes-options', editalSearch],
    queryFn: () => publicacoesApi.list({ page_size: 10, search: editalSearch || undefined }).then((response) => response.data),
    staleTime: 60_000,
  })

  const saveMutation = useMutation({
    mutationFn: (payload) => inscricoesApi.create(payload),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['inscricoes'] })
      toast.success('Inscricao criada com sucesso.')
      navigate('/inscricoes?aba=inscricoes')
    },
    onError: (error) => toast.error(getErrorMessage(error, 'Nao foi possivel salvar a inscricao.')),
  })

  const editais = editaisData?.results || []

  return (
    <div className="page page--wide">
      <nav className="profile-breadcrumb">
        <Link to="/dashboard">Início</Link>
        <span className="profile-breadcrumb__sep">&gt;</span>
        <Link to="/inscricoes?aba=inscricoes">Inscrições / Editais</Link>
        <span className="profile-breadcrumb__sep">&gt;</span>
        <span>Nova Inscrição</span>
      </nav>

      <div className="page-header">
        <div>
          <h1 className="page-title">Nova inscrição</h1>
          <p className="page-subtitle">O cadastro do candidato agora usa uma página separada da listagem.</p>
        </div>
        <div className="page-header__actions">
          <button type="button" className="btn btn--outline" onClick={() => navigate('/inscricoes?aba=inscricoes')}>
            <ArrowLeft size={16} /> Voltar para inscrições
          </button>
        </div>
      </div>

      <EntityFormPanel
        title="Nova inscrição"
        subtitle="Associe o candidato a um edital e registre os dados básicos da inscrição."
        onSubmit={(event) => {
          event.preventDefault()

          if (!formData.publicacao || !formData.nome_candidato.trim() || !formData.cpf.trim() || !formData.email.trim()) {
            toast.error('Informe edital, candidato, CPF e e-mail.')
            return
          }

          saveMutation.mutate({
            publicacao: Number(formData.publicacao),
            nome_candidato: formData.nome_candidato.trim(),
            cpf: formData.cpf.trim(),
            email: formData.email.trim(),
            telefone: formData.telefone.trim(),
            data_nascimento: formData.data_nascimento || null,
            status: formData.status,
            observacao: formData.observacao.trim(),
          })
        }}
        onCancel={() => navigate('/inscricoes?aba=inscricoes')}
        submitLabel="Criar inscrição"
        isSubmitting={saveMutation.isPending}
      >
        <SearchableRemoteSelect
          id="inscricao-edital"
          label="Edital"
          searchLabel="Buscar edital"
          searchPlaceholder="Digite título do edital"
          searchValue={editalSearch}
          onSearchChange={setEditalSearch}
          value={formData.publicacao}
          onChange={(nextValue) => setFormData((current) => ({ ...current, publicacao: nextValue }))}
          options={editais}
          getOptionLabel={(item) => `${item.titulo} - ${item.curso_nome}`}
        />

        <div className="form-field form-field--full">
          <label htmlFor="inscricao-candidato">Nome do candidato</label>
          <input id="inscricao-candidato" className="form-control" value={formData.nome_candidato} onChange={(event) => setFormData((current) => ({ ...current, nome_candidato: event.target.value }))} />
        </div>

        <div className="form-field">
          <label htmlFor="inscricao-cpf">CPF</label>
          <input id="inscricao-cpf" className="form-control" value={formData.cpf} onChange={(event) => setFormData((current) => ({ ...current, cpf: event.target.value }))} />
        </div>

        <div className="form-field">
          <label htmlFor="inscricao-email">E-mail</label>
          <input id="inscricao-email" type="email" className="form-control" value={formData.email} onChange={(event) => setFormData((current) => ({ ...current, email: event.target.value }))} />
        </div>

        <div className="form-field">
          <label htmlFor="inscricao-telefone">Telefone</label>
          <input id="inscricao-telefone" className="form-control" value={formData.telefone} onChange={(event) => setFormData((current) => ({ ...current, telefone: event.target.value }))} />
        </div>

        <div className="form-field">
          <label htmlFor="inscricao-data-nascimento">Data de nascimento</label>
          <input id="inscricao-data-nascimento" type="date" className="form-control" value={formData.data_nascimento} onChange={(event) => setFormData((current) => ({ ...current, data_nascimento: event.target.value }))} />
        </div>

        <div className="form-field">
          <label htmlFor="inscricao-status">Status</label>
          <select id="inscricao-status" className="select" value={formData.status} onChange={(event) => setFormData((current) => ({ ...current, status: event.target.value }))}>
            {INSCRICAO_STATUS_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>{option.label}</option>
            ))}
          </select>
        </div>

        <div className="form-field form-field--full">
          <label htmlFor="inscricao-observacao">Observação</label>
          <textarea id="inscricao-observacao" className="form-control" rows={4} value={formData.observacao} onChange={(event) => setFormData((current) => ({ ...current, observacao: event.target.value }))} />
        </div>
      </EntityFormPanel>
    </div>
  )
}