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
  const description = state?.description || 'Este item ainda nao foi implementado no frontend do SUAP.'
  const isActivation = state?.status === 'ativacao'

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <h1 className="page-title">{title}</h1>
          <p className="page-subtitle">
            {isActivation ? 'Modulo em ativacao' : 'Item ainda nao integrado'}
          </p>
        </div>
      </div>

      <div className="dashboard-card">
        <p>{description}</p>
        <p style={{ marginTop: '1rem', color: 'var(--color-gray-400)' }}>
          Origem do menu legado: {slug}
        </p>
      </div>
    </div>
  )
}