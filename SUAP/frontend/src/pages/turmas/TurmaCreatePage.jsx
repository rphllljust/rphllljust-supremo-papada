import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { ArrowLeft, Save } from 'lucide-react'
import toast from 'react-hot-toast'
import { Link, useNavigate } from 'react-router-dom'

import { cursosApi, turmasApi, usuariosApi } from '@/api/endpoints'
import EntityFormPanel from '@/components/ui/EntityFormPanel'
import SearchableRemoteSelect from '@/components/ui/SearchableRemoteSelect'

const STATUS_OPTIONS = [
  { value: 'PLANEJADA', label: 'Planejada' },
  { value: 'ATIVA', label: 'Ativa' },
  { value: 'ENCERRADA', label: 'Encerrada' },
  { value: 'CANCELADA', label: 'Cancelada' },
]

const DEFAULT_FORM = {
  curso: '',
  nome: '',
  ano_letivo: String(new Date().getFullYear()),
  status: 'PLANEJADA',
  professor_responsavel: '',
}

function getErrorMessage(error, fallback) {
  const data = error?.response?.data

  if (!data) return fallback
  if (typeof data.detail === 'string') return data.detail

  const firstValue = Object.values(data)[0]
  return Array.isArray(firstValue) ? firstValue[0] : (firstValue || fallback)
}

export default function TurmaCreatePage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [cursoSearch, setCursoSearch] = useState('')
  const [professorSearch, setProfessorSearch] = useState('')
  const [formData, setFormData] = useState(DEFAULT_FORM)

  const { data: cursosData } = useQuery({
    queryKey: ['cursos', 'turmas-options', cursoSearch],
    queryFn: () => cursosApi.list({ page_size: 10, search: cursoSearch || undefined }).then((response) => response.data),
    staleTime: 60_000,
  })

  const { data: professoresData } = useQuery({
    queryKey: ['usuarios', 'turmas-professores', professorSearch],
    queryFn: () => usuariosApi.list({ tipo: 'PROFESSOR', page_size: 10, search: professorSearch || undefined }).then((response) => response.data),
    staleTime: 60_000,
  })

  const saveMutation = useMutation({
    mutationFn: (payload) => turmasApi.create(payload),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['turmas'] })
      toast.success('Turma criada com sucesso.')
      navigate('/turmas')
    },
    onError: (error) => toast.error(getErrorMessage(error, 'Nao foi possivel salvar a turma.')),
  })

  const cursos = cursosData?.results || []
  const professores = professoresData?.results || []

  return (
    <div className="page page--wide">
      <nav className="profile-breadcrumb">
        <Link to="/dashboard">Início</Link>
        <span className="profile-breadcrumb__sep">&gt;</span>
        <Link to="/turmas">Turmas</Link>
        <span className="profile-breadcrumb__sep">&gt;</span>
        <span>Nova Turma</span>
      </nav>

      <div className="page-header">
        <div>
          <h1 className="page-title">Nova turma</h1>
          <p className="page-subtitle">Cadastre a turma em uma página dedicada, sem abrir o formulário na listagem.</p>
        </div>
        <div className="page-header__actions">
          <button type="button" className="btn btn--outline" onClick={() => navigate('/turmas')}>
            <ArrowLeft size={16} /> Voltar para listagem
          </button>
        </div>
      </div>

      <EntityFormPanel
        title="Nova turma"
        subtitle="Informe curso, identificação da turma, ano letivo e professor responsável."
        onSubmit={(event) => {
          event.preventDefault()

          if (!formData.curso || !formData.nome.trim() || !formData.ano_letivo) {
            toast.error('Informe curso, nome da turma e ano letivo.')
            return
          }

          saveMutation.mutate({
            curso: Number(formData.curso),
            nome: formData.nome.trim(),
            ano_letivo: Number(formData.ano_letivo),
            status: formData.status,
            professor_responsavel: formData.professor_responsavel ? Number(formData.professor_responsavel) : null,
          })
        }}
        onCancel={() => navigate('/turmas')}
        submitLabel="Criar turma"
        isSubmitting={saveMutation.isPending}
      >
        <SearchableRemoteSelect
          id="turma-curso"
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
          <label htmlFor="turma-nome">Turma</label>
          <input
            id="turma-nome"
            className="form-control"
            value={formData.nome}
            onChange={(event) => setFormData((current) => ({ ...current, nome: event.target.value }))}
            placeholder="Ex.: 1A, 2026.1, ADS-N1"
          />
        </div>

        <div className="form-field">
          <label htmlFor="turma-ano-letivo">Ano letivo</label>
          <input
            id="turma-ano-letivo"
            type="number"
            min="2000"
            max="2100"
            className="form-control"
            value={formData.ano_letivo}
            onChange={(event) => setFormData((current) => ({ ...current, ano_letivo: event.target.value }))}
          />
        </div>

        <div className="form-field">
          <label htmlFor="turma-status">Status</label>
          <select
            id="turma-status"
            className="select"
            value={formData.status}
            onChange={(event) => setFormData((current) => ({ ...current, status: event.target.value }))}
          >
            {STATUS_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>{option.label}</option>
            ))}
          </select>
        </div>

        <SearchableRemoteSelect
          id="turma-professor"
          label="Professor responsável"
          searchLabel="Buscar professor"
          searchPlaceholder="Digite nome, CPF ou usuario"
          searchValue={professorSearch}
          onSearchChange={setProfessorSearch}
          value={formData.professor_responsavel}
          onChange={(nextValue) => setFormData((current) => ({ ...current, professor_responsavel: nextValue }))}
          options={professores}
          getOptionLabel={(item) => item.username ? `${item.nome_completo} - ${item.username}` : item.nome_completo}
          emptyOptionLabel="Nao informado"
        />
      </EntityFormPanel>
    </div>
  )
}
