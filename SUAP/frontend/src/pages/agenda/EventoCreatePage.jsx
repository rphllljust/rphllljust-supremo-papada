import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { ArrowLeft } from 'lucide-react'
import toast from 'react-hot-toast'
import { Link, useNavigate } from 'react-router-dom'

import { eventosApi, turmasApi } from '@/api/endpoints'
import EntityFormPanel from '@/components/ui/EntityFormPanel'
import SearchableRemoteSelect from '@/components/ui/SearchableRemoteSelect'

const DEFAULT_FORM = {
  titulo: '',
  descricao: '',
  turma: '',
  inicio: '',
  fim: '',
}

function getErrorMessage(error, fallback) {
  const data = error?.response?.data
  if (!data) return fallback
  if (typeof data.detail === 'string') return data.detail
  const firstValue = Object.values(data)[0]
  return Array.isArray(firstValue) ? firstValue[0] : (firstValue || fallback)
}

export default function EventoCreatePage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [formData, setFormData] = useState(DEFAULT_FORM)
  const [turmaSearch, setTurmaSearch] = useState('')

  const { data: turmasData } = useQuery({
    queryKey: ['turmas', 'agenda-options', turmaSearch],
    queryFn: () => turmasApi.list({ page_size: 10, search: turmaSearch || undefined }).then((response) => response.data),
    staleTime: 60_000,
  })

  const saveMutation = useMutation({
    mutationFn: (payload) => eventosApi.create(payload),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['eventos'] })
      toast.success('Evento criado com sucesso.')
      navigate('/agenda')
    },
    onError: (error) => toast.error(getErrorMessage(error, 'Não foi possível salvar o evento.')),
  })

  const turmas = turmasData?.results || []

  return (
    <div className="page page--wide">
      <nav className="profile-breadcrumb">
        <Link to="/dashboard">Início</Link>
        <span className="profile-breadcrumb__sep">&gt;</span>
        <Link to="/agenda">Agenda</Link>
        <span className="profile-breadcrumb__sep">&gt;</span>
        <span>Novo Evento</span>
      </nav>

      <div className="page-header">
        <div>
          <h1 className="page-title">Novo evento</h1>
          <p className="page-subtitle">A criação de eventos agora acontece em uma tela própria.</p>
        </div>
        <div className="page-header__actions">
          <button type="button" className="btn btn--outline" onClick={() => navigate('/agenda')}>
            <ArrowLeft size={16} /> Voltar para agenda
          </button>
        </div>
      </div>

      <EntityFormPanel
        title="Novo evento"
        subtitle="Associe o evento a uma turma e defina período e descrição."
        onSubmit={(event) => {
          event.preventDefault()

          if (!formData.titulo.trim() || !formData.turma || !formData.inicio || !formData.fim) {
            toast.error('Informe título, turma, início e fim do evento.')
            return
          }

          saveMutation.mutate({
            titulo: formData.titulo.trim(),
            descricao: formData.descricao.trim(),
            turma: Number(formData.turma),
            inicio: new Date(formData.inicio).toISOString(),
            fim: new Date(formData.fim).toISOString(),
          })
        }}
        onCancel={() => navigate('/agenda')}
        submitLabel="Criar evento"
        isSubmitting={saveMutation.isPending}
      >
        <SearchableRemoteSelect
          id="agenda-turma"
          label="Turma"
          searchLabel="Buscar turma"
          searchPlaceholder="Digite nome da turma ou curso"
          searchValue={turmaSearch}
          onSearchChange={setTurmaSearch}
          value={formData.turma}
          onChange={(nextValue) => setFormData((current) => ({ ...current, turma: nextValue }))}
          options={turmas}
          getOptionLabel={(item) => `${item.nome} - ${item.curso_nome}`}
        />

        <div className="form-field form-field--full">
          <label htmlFor="agenda-titulo">Título</label>
          <input id="agenda-titulo" className="form-control" value={formData.titulo} onChange={(event) => setFormData((current) => ({ ...current, titulo: event.target.value }))} />
        </div>

        <div className="form-field">
          <label htmlFor="agenda-inicio">Início</label>
          <input id="agenda-inicio" type="datetime-local" className="form-control" value={formData.inicio} onChange={(event) => setFormData((current) => ({ ...current, inicio: event.target.value }))} />
        </div>

        <div className="form-field">
          <label htmlFor="agenda-fim">Fim</label>
          <input id="agenda-fim" type="datetime-local" className="form-control" value={formData.fim} onChange={(event) => setFormData((current) => ({ ...current, fim: event.target.value }))} />
        </div>

        <div className="form-field form-field--full">
          <label htmlFor="agenda-descricao">Descrição</label>
          <textarea id="agenda-descricao" className="form-control" rows={4} value={formData.descricao} onChange={(event) => setFormData((current) => ({ ...current, descricao: event.target.value }))} />
        </div>
      </EntityFormPanel>
    </div>
  )
}
