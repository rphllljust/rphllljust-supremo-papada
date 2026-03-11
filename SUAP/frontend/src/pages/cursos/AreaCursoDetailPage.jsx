import { useQuery } from '@tanstack/react-query'
import { Info, Pencil } from 'lucide-react'
import { Link, useNavigate, useParams } from 'react-router-dom'

import { areasCursoApi } from '@/api/endpoints'

function DetailField({ label, value }) {
  return (
    <div className="area-curso-detail-field">
      <span className="area-curso-detail-field__label">{label}:</span>
      <strong className="area-curso-detail-field__value">{value || '-'}</strong>
    </div>
  )
}

export default function AreaCursoDetailPage() {
  const navigate = useNavigate()
  const { areaCursoId } = useParams()

  const { data, isLoading, isError } = useQuery({
    queryKey: ['areas-curso', 'detail', areaCursoId],
    queryFn: () => areasCursoApi.get(areaCursoId).then((response) => response.data),
    enabled: Boolean(areaCursoId),
    staleTime: 30_000,
  })

  if (isLoading) {
    return (
      <div className="page page--wide">
        <div className="page-loader" role="status" aria-live="polite">
          <div className="spinner" />
          <span>Carregando área de curso...</span>
        </div>
      </div>
    )
  }

  if (isError || !data) {
    return (
      <div className="page page--wide">
        <div className="page-error">
          <h1 className="page-error__title">Não foi possível carregar a área de curso</h1>
          <p className="page-error__description">Verifique se o registro existe e tente novamente.</p>
        </div>
      </div>
    )
  }

  const titulo = [data.codigo_cine, data.cine || data.descricao].filter(Boolean).join(' - ')

  return (
    <div className="page page--wide area-curso-detail-page">
      <nav className="profile-breadcrumb">
        <Link to="/dashboard">Início</Link>
        <span className="profile-breadcrumb__sep">&gt;</span>
        <Link to="/ensino/areacurso/">Áreas de cursos de formação superior</Link>
        <span className="profile-breadcrumb__sep">&gt;</span>
        <span>{titulo}</span>
      </nav>

      <div className="page-header area-cursos-page__header">
        <div>
          <h1 className="page-title">{titulo}</h1>
        </div>
        <div className="page-header__actions">
          <button type="button" className="btn btn--outline" onClick={() => navigate(`/ensino/areacurso/${data.id}/editar`)}>
            <Pencil size={16} /> Editar
          </button>
        </div>
      </div>

      <section className="dashboard-card area-curso-detail-card">
        <div className="estagio-detail-section__title">
          <Info size={18} /> Dados gerais
        </div>
        <div className="area-curso-detail-fields">
          <DetailField label="Código CINE" value={data.codigo_cine} />
          <DetailField label="Código da área detalhada" value={data.codigo_area_detalhada} />
          <DetailField label="Código da área específica" value={data.codigo_area_especifica} />
          <DetailField label="Código da área geral" value={data.codigo_area_geral} />
          <DetailField label="CINE" value={data.cine} />
          <DetailField label="Área detalhada" value={data.area_detalhada} />
          <DetailField label="Área específica" value={data.area_especifica} />
          <DetailField label="Área geral" value={data.area_geral} />
        </div>
      </section>
    </div>
  )
}