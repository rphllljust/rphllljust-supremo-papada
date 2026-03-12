import { useEffect, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { ArrowLeft, Eye, Save, Trash2 } from 'lucide-react'
import toast from 'react-hot-toast'
import { Link, useNavigate } from 'react-router-dom'

import { publicacoesApi } from '@/api/endpoints'
import EntityFormPanel from '@/components/ui/EntityFormPanel'

import PublicacaoFormFields from './PublicacaoFormFields'
import ProcessosSeletivosTabs from './ProcessosSeletivosTabs'
import {
  buildPublicacaoFormValues,
  buildPublicacaoPayload,
  DEFAULT_PUBLICACAO_FORM,
  formatDate,
  getErrorMessage,
  getPublicacaoStatusLabel,
  validatePublicacaoForm,
} from './publicacaoShared'

export default function PublicacaoFormView({ publicacaoId = null }) {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const isCreateMode = !publicacaoId
  const [formData, setFormData] = useState(DEFAULT_PUBLICACAO_FORM)

  const {
    data,
    isLoading,
    isError,
  } = useQuery({
    queryKey: ['publicacao', publicacaoId],
    queryFn: () => publicacoesApi.get(publicacaoId).then((response) => response.data),
    enabled: !isCreateMode,
  })

  useEffect(() => {
    if (data) {
      setFormData(buildPublicacaoFormValues(data))
      return
    }

    if (isCreateMode) {
      setFormData(DEFAULT_PUBLICACAO_FORM)
    }
  }, [data, isCreateMode])

  const saveMutation = useMutation({
    mutationFn: async ({ id, payload }) => {
      const response = id ? await publicacoesApi.update(id, payload) : await publicacoesApi.create(payload)
      return response.data
    },
    onSuccess: async (saved) => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ['publicacoes'] }),
        saved?.id ? queryClient.invalidateQueries({ queryKey: ['publicacao', saved.id] }) : Promise.resolve(),
      ])
      return saved
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (id) => publicacoesApi.delete(id),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['publicacoes'] })
    },
  })

  const persistForm = async (mode = 'view') => {
    if (!validatePublicacaoForm(formData)) {
      toast.error('Informe curso, título, início e fim do edital.')
      return
    }

    try {
      const saved = await saveMutation.mutateAsync({
        id: publicacaoId,
        payload: buildPublicacaoPayload(formData),
      })

      toast.success(isCreateMode ? 'Edital criado com sucesso.' : 'Edital atualizado com sucesso.')

      if (mode === 'stay') {
        if (isCreateMode && saved?.id) {
          navigate(`/inscricoes/editais/${saved.id}/editar`, { replace: true })
        }
        return
      }

      navigate(`/inscricoes/editais/${saved.id}`)
    } catch (error) {
      toast.error(getErrorMessage(error, 'Nao foi possivel salvar o edital.'))
    }
  }

  const handleSubmit = async (event) => {
    event.preventDefault()
    await persistForm('view')
  }

  const handleDelete = async () => {
    if (!data?.id) return
    if (!window.confirm(`Excluir o edital ${data.titulo}?`)) return

    try {
      await deleteMutation.mutateAsync(data.id)
      toast.success('Edital removido com sucesso.')
      navigate('/inscricoes/editais')
    } catch (error) {
      toast.error(getErrorMessage(error, 'Nao foi possivel remover o edital.'))
    }
  }

  if (!isCreateMode && isLoading) {
    return (
      <div className="page page--wide">
        <div className="page-loader" role="status" aria-live="polite">
          <div className="spinner" />
          <span>Carregando edital...</span>
        </div>
      </div>
    )
  }

  if (!isCreateMode && (isError || !data)) {
    return (
      <div className="page page--wide">
        <div className="page-error">
          <h1 className="page-error__title">Nao foi possivel carregar o edital</h1>
          <p className="page-error__description">Verifique se o registro existe e tente novamente.</p>
        </div>
      </div>
    )
  }

  const selectedCursoOption = formData.curso && data ? {
    id: data.curso,
    nome: data.curso_nome,
  } : null

  return (
    <div className="page page--wide processos-seletivos-page">
      <nav className="profile-breadcrumb">
        <Link to="/dashboard">Início</Link>
        <span className="profile-breadcrumb__sep">&gt;</span>
        <Link to="/inscricoes/editais">Processos seletivos</Link>
        <span className="profile-breadcrumb__sep">&gt;</span>
        <span>{isCreateMode ? 'Novo edital' : 'Editar edital'}</span>
      </nav>

      <div className="page-header processos-seletivos-page__header">
        <div>
          <h1 className="page-title">{isCreateMode ? 'Novo edital' : `Editar ${data.titulo}`}</h1>
          <p className="page-subtitle">Preencha os dados do processo seletivo usando o mesmo padrão visual do restante do sistema.</p>
        </div>
        <div className="page-header__actions">
          {!isCreateMode ? (
            <button type="button" className="btn btn--outline" onClick={() => navigate(`/inscricoes/editais/${data.id}`)}>
              <Eye size={16} /> Visualizar
            </button>
          ) : null}
          <button type="button" className="btn btn--outline" onClick={() => navigate(isCreateMode ? '/inscricoes/editais' : `/inscricoes/editais/${data.id}`)}>
            <ArrowLeft size={16} /> Voltar
          </button>
        </div>
      </div>

      <ProcessosSeletivosTabs activeTab="editais" />

      {!isCreateMode ? (
        <section className="stats-grid processos-seletivos-stats-grid processos-seletivos-stats-grid--compact">
          <article className="dashboard-card processos-seletivos-metric-card">
            <span className="processos-seletivos-metric-card__label">Curso</span>
            <strong className="processos-seletivos-metric-card__value processos-seletivos-metric-card__value--small">{data.curso_nome || '-'}</strong>
          </article>
          <article className="dashboard-card processos-seletivos-metric-card">
            <span className="processos-seletivos-metric-card__label">Status</span>
            <strong className="processos-seletivos-metric-card__value processos-seletivos-metric-card__value--small">{getPublicacaoStatusLabel(data.status)}</strong>
          </article>
          <article className="dashboard-card processos-seletivos-metric-card">
            <span className="processos-seletivos-metric-card__label">Período</span>
            <strong className="processos-seletivos-metric-card__value processos-seletivos-metric-card__value--small">{formatDate(data.data_inicio)} a {formatDate(data.data_fim)}</strong>
          </article>
          <article className="dashboard-card processos-seletivos-metric-card">
            <span className="processos-seletivos-metric-card__label">Inscrições</span>
            <strong className="processos-seletivos-metric-card__value">{data.inscricoes_count ?? 0}</strong>
          </article>
        </section>
      ) : null}

      <EntityFormPanel
        title="Dados do edital"
        subtitle="Defina curso, período de inscrição, vagas e status do edital."
        onSubmit={handleSubmit}
        onCancel={() => navigate(isCreateMode ? '/inscricoes/editais' : `/inscricoes/editais/${data.id}`)}
        submitLabel="Salvar edital"
        isSubmitting={saveMutation.isPending}
      >
        <PublicacaoFormFields formData={formData} setFormData={setFormData} selectedCursoOption={selectedCursoOption} />
      </EntityFormPanel>

      <div className="processos-seletivos-footer-actions">
        <button type="button" className="btn btn--secondary" onClick={() => persistForm('stay')} disabled={saveMutation.isPending}>
          <Save size={16} /> Salvar e continuar
        </button>
        {!isCreateMode ? (
          <button type="button" className="btn btn--danger" disabled={deleteMutation.isPending} onClick={handleDelete}>
            <Trash2 size={16} /> Remover
          </button>
        ) : null}
      </div>
    </div>
  )
}