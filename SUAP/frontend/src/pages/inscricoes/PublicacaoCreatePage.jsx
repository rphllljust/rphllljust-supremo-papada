import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { ArrowLeft } from 'lucide-react'
import toast from 'react-hot-toast'
import { Link, useNavigate } from 'react-router-dom'

import { cursosApi, publicacoesApi } from '@/api/endpoints'
import EntityFormPanel from '@/components/ui/EntityFormPanel'
import SearchableRemoteSelect from '@/components/ui/SearchableRemoteSelect'

const PUBLICACAO_STATUS_OPTIONS = [
  { value: 'RASCUNHO', label: 'Rascunho' },
  { value: 'PUBLICADO', label: 'Publicado' },
  { value: 'ENCERRADO', label: 'Encerrado' },
]

const DEFAULT_PUBLICACAO_FORM = {
  curso: '',
  titulo: '',
  descricao: '',
  vagas: '0',
  data_inicio: '',
  data_fim: '',
  status: 'RASCUNHO',
}

function getErrorMessage(error, fallback) {
  const data = error?.response?.data

  if (!data) return fallback
  if (typeof data.detail === 'string') return data.detail

  const firstValue = Object.values(data)[0]
  return Array.isArray(firstValue) ? firstValue[0] : (firstValue || fallback)
}

export default function PublicacaoCreatePage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [cursoSearch, setCursoSearch] = useState('')
  const [formData, setFormData] = useState(DEFAULT_PUBLICACAO_FORM)

  const { data: cursosData } = useQuery({
    queryKey: ['cursos', 'publicacoes-options', cursoSearch],
    queryFn: () => cursosApi.list({ page_size: 10, search: cursoSearch || undefined }).then((response) => response.data),
    staleTime: 60_000,
  })

  const saveMutation = useMutation({
    mutationFn: (payload) => publicacoesApi.create(payload),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['publicacoes'] })
      toast.success('Edital criado com sucesso.')
      navigate('/inscricoes?aba=publicacoes')
    },
    onError: (error) => toast.error(getErrorMessage(error, 'Nao foi possivel salvar o edital.')),
  })

  const cursos = cursosData?.results || []

  return (
    <div className="page page--wide">
      <nav className="profile-breadcrumb">
        <Link to="/dashboard">Início</Link>
        <span className="profile-breadcrumb__sep">&gt;</span>
        <Link to="/inscricoes?aba=publicacoes">Inscrições / Editais</Link>
        <span className="profile-breadcrumb__sep">&gt;</span>
        <span>Novo Edital</span>
      </nav>

      <div className="page-header">
        <div>
          <h1 className="page-title">Novo edital</h1>
          <p className="page-subtitle">A criação de editais agora abre em uma tela exclusiva.</p>
        </div>
        <div className="page-header__actions">
          <button type="button" className="btn btn--outline" onClick={() => navigate('/inscricoes?aba=publicacoes')}>
            <ArrowLeft size={16} /> Voltar para editais
          </button>
        </div>
      </div>

      <EntityFormPanel
        title="Novo edital"
        subtitle="Defina curso, período de inscrição, vagas e status de publicação."
        onSubmit={(event) => {
          event.preventDefault()

          if (!formData.curso || !formData.titulo.trim() || !formData.data_inicio || !formData.data_fim) {
            toast.error('Informe curso, título, início e fim do edital.')
            return
          }

          saveMutation.mutate({
            curso: Number(formData.curso),
            titulo: formData.titulo.trim(),
            descricao: formData.descricao.trim(),
            vagas: Number(formData.vagas || 0),
            data_inicio: formData.data_inicio,
            data_fim: formData.data_fim,
            status: formData.status,
          })
        }}
        onCancel={() => navigate('/inscricoes?aba=publicacoes')}
        submitLabel="Criar edital"
        isSubmitting={saveMutation.isPending}
      >
        <SearchableRemoteSelect
          id="publicacao-curso"
          label="Curso"
          searchLabel="Buscar curso"
          searchPlaceholder="Digite nome ou sigla do curso"
          searchValue={cursoSearch}
          onSearchChange={setCursoSearch}
          value={formData.curso}
          onChange={(nextValue) => setFormData((current) => ({ ...current, curso: nextValue }))}
          options={cursos}
          getOptionLabel={(item) => `${item.nome}${item.sigla ? ` - ${item.sigla}` : ''}`}
        />

        <div className="form-field form-field--full">
          <label htmlFor="publicacao-titulo">Título do edital</label>
          <input id="publicacao-titulo" className="form-control" value={formData.titulo} onChange={(event) => setFormData((current) => ({ ...current, titulo: event.target.value }))} />
        </div>

        <div className="form-field">
          <label htmlFor="publicacao-vagas">Vagas</label>
          <input id="publicacao-vagas" type="number" min="0" className="form-control" value={formData.vagas} onChange={(event) => setFormData((current) => ({ ...current, vagas: event.target.value }))} />
        </div>

        <div className="form-field">
          <label htmlFor="publicacao-status">Status</label>
          <select id="publicacao-status" className="select" value={formData.status} onChange={(event) => setFormData((current) => ({ ...current, status: event.target.value }))}>
            {PUBLICACAO_STATUS_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>{option.label}</option>
            ))}
          </select>
        </div>

        <div className="form-field">
          <label htmlFor="publicacao-data-inicio">Início das inscrições</label>
          <input id="publicacao-data-inicio" type="date" className="form-control" value={formData.data_inicio} onChange={(event) => setFormData((current) => ({ ...current, data_inicio: event.target.value }))} />
        </div>

        <div className="form-field">
          <label htmlFor="publicacao-data-fim">Fim das inscrições</label>
          <input id="publicacao-data-fim" type="date" className="form-control" value={formData.data_fim} onChange={(event) => setFormData((current) => ({ ...current, data_fim: event.target.value }))} />
        </div>

        <div className="form-field form-field--full">
          <label htmlFor="publicacao-descricao">Descrição / requisitos</label>
          <textarea id="publicacao-descricao" className="form-control" rows={4} value={formData.descricao} onChange={(event) => setFormData((current) => ({ ...current, descricao: event.target.value }))} />
        </div>
      </EntityFormPanel>
    </div>
  )
}
