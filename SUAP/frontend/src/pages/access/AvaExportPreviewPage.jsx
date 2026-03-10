import { useQuery } from '@tanstack/react-query'
import { ShieldCheck, TriangleAlert } from 'lucide-react'
import { accessApi } from '@/api/endpoints'

export default function AvaExportPreviewPage() {
  const { data, isLoading, isError, error, refetch, isFetching } = useQuery({
    queryKey: ['access', 'ava-export-preview'],
    queryFn: () => accessApi.avaExportPreview().then((response) => response.data),
    retry: false,
  })

  return (
    <div className="page">
      <div className="page-header">
        <h1 className="page-title">Validação de Integração AVA</h1>
        <button className="btn btn--secondary" onClick={() => refetch()} disabled={isFetching}>
          {isFetching ? 'Validando...' : 'Validar acesso'}
        </button>
      </div>

      <div className="dashboard-card">
        <p style={{ marginBottom: '1rem' }}>
          Esta tela pertence ao frontend do SUAP e apenas valida a permissão de integração com o AVA.
        </p>

        {isLoading ? (
          <p>Validando permissão de exportação...</p>
        ) : null}

        {!isLoading && !isError && data ? (
          <div className="empty-state" style={{ display: 'grid', gap: '1rem', justifyItems: 'start' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
              <ShieldCheck size={20} />
              <strong>{data.status === 'ok' ? 'Acesso liberado' : 'Resposta recebida'}</strong>
            </div>
            <p>{data.detail}</p>
            <p>Usuario validado: <strong>{data.usuario}</strong></p>
          </div>
        ) : null}

        {!isLoading && isError ? (
          <div className="alert alert--error" style={{ display: 'grid', gap: '0.75rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
              <TriangleAlert size={18} />
              <strong>Permissão não validada</strong>
            </div>
            <span>
              {error?.response?.data?.detail || 'A API recusou a validação de exportação para o AVA.'}
            </span>
          </div>
        ) : null}
      </div>
    </div>
  )
}