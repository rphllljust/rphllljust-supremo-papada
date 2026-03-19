import React from 'react'
import { useQuery } from '@tanstack/react-query'
import { useParams, Link } from 'react-router-dom'
import { cursosApi } from '@/api/endpoints'

export default function CursoDetailPage() {
  const { cursoId } = useParams()
  const { data, isLoading, isError } = useQuery({
    queryKey: ['curso', 'detail', cursoId],
    queryFn: () => cursosApi.get(cursoId).then((r) => r.data),
    enabled: !!cursoId,
  })

  if (isLoading) {
    return (
      <div className="page page--wide">
        <div className="page-loader" role="status" aria-live="polite">
          <div className="spinner" />
          <span>Carregando detalhes do curso...</span>
        </div>
      </div>
    )
  }

  if (isError || !data) {
    return (
      <div className="page page--wide">
        <div className="page-error">
          <h1 className="page-error__title">Não foi possível carregar o curso</h1>
          <p className="page-error__description">Verifique se o registro existe e tente novamente.</p>
        </div>
      </div>
    )
  }

  return (
    <div className="page page--wide curso-detail-page">
      <nav className="profile-breadcrumb">
        <Link to="/dashboard">Início</Link>
        <span className="profile-breadcrumb__sep">&gt;</span>
        <Link to="/ensino/cursoinicial/">Cursos iniciais</Link>
        <span className="profile-breadcrumb__sep">&gt;</span>
        <span>{data.nome}</span>
      </nav>

      <div className="page-header">
        <h1 className="page-title">{data.nome}</h1>
      </div>

      <div className="dashboard-card">
        <dl>
          <dt>Sigla</dt>
          <dd>{data.sigla || '—'}</dd>
          <dt>Unidade</dt>
          <dd>{data.unidade_display || data.unidade || '—'}</dd>
          <dt>Área do curso</dt>
          <dd>{data.area_curso_display || data.area_curso || '—'}</dd>
          <dt>Eixo tecnológico</dt>
          <dd>{data.eixo_tecnologico || '—'}</dd>
          <dt>Carga horária (h)</dt>
          <dd>{data.carga_horaria || '—'}</dd>
        </dl>

        <div style={{ marginTop: 16 }}>
          <Link className="btn btn--outline" to="/ensino/cursoinicial/">Voltar</Link>
          <Link className="btn btn--primary" to={`/ensino/cursoinicial/${data.id}/editar`} style={{ marginLeft: 8 }}>Editar</Link>
        </div>
      </div>
    </div>
  )
}
