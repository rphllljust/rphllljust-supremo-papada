import { useLocation, useParams } from 'react-router-dom'

function humanizeSlug(slug) {
  return slug
    .split('-')
    .filter(Boolean)
    .map((chunk) => chunk.charAt(0).toUpperCase() + chunk.slice(1))
    .join(' ')
}

export default function PlaceholderPage() {
  const { slug } = useParams()
  const { state } = useLocation()

  const title = state?.title || humanizeSlug(slug || 'modulo')

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <h1 className="page-title">{title}</h1>
          <p className="page-subtitle">Funcionalidade nao implementada</p>
        </div>
      </div>

      <div className="dashboard-card">
        <p>Esta funcionalidade ainda nao foi implementada no frontend.</p>
      </div>
    </div>
  )
}