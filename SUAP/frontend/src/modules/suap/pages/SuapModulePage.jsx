import { useMemo } from 'react'
import { useLocation } from 'react-router-dom'
import { suapService } from '../services/suapService'
import { resolveExternalUrlDecision } from '@/utils/externalAllowlist'

export default function SuapModulePage() {
  const location = useLocation()
  const resolved = useMemo(() => suapService.abrirServicoPublico(location.pathname), [location.pathname])

  if (!resolved) {
    return (
      <section className="page page--wide">
        <header className="page-header">
          <h1 className="page-title">Módulo SUAP</h1>
          <p className="page-subtitle">pendente de confirmação no treinamento</p>
        </header>
        <article className="dashboard-card">
          <p>Não foi possível identificar esta página no catálogo SUAP local.</p>
        </article>
      </section>
    )
  }

  const { module, page } = resolved
  const externalDecision = resolveExternalUrlDecision(page.externalUrl)

  return (
    <section className="page page--wide">
      <header className="page-header">
        <div>
          <h1 className="page-title">{page.title}</h1>
          <p className="page-subtitle">{module.title} • {page.status}</p>
        </div>
      </header>

      <article className="dashboard-card" role="status" aria-live="polite">
        <h2 className="dashboard-card__title">Resumo</h2>
        <p className="dashboard-card__subtitle">
          Funcionalidade preparada para integração incremental com SUAP.
        </p>
        <p style={{ marginTop: 12 }}>
          Dados ainda não integrados. Status atual: <strong>{page.status}</strong>.
        </p>
      </article>

      <article className="dashboard-card" style={{ marginTop: 16 }}>
        <h2 className="dashboard-card__title">Filtros e resultado</h2>
        <p className="dashboard-card__subtitle">
          Estrutura base de busca/listagem disponível para evolução.
        </p>
        <div style={{ marginTop: 12, display: 'grid', gap: 12 }}>
          <input className="form-control" placeholder="Buscar (pendente de confirmação no treinamento)" disabled />
          <div className="dashboard-empty">Nenhum dado carregado para este módulo no momento.</div>
        </div>
      </article>

      {externalDecision.status !== 'blocked' ? (
        <div style={{ marginTop: 16 }}>
          <a className="btn btn--outline" href={externalDecision.url} target="_blank" rel="noreferrer">Abrir no SUAP</a>
          {externalDecision.status === 'manual_review' ? (
            <p className="dashboard-card__subtitle" style={{ marginTop: 8 }}>
              Link externo fora da lista confiável automática. Valide manualmente antes de prosseguir.
            </p>
          ) : null}
        </div>
      ) : (
        <div className="dashboard-empty" style={{ marginTop: 16 }}>
          Link externo bloqueado por política de segurança (URL inválida ou protocolo não permitido).
        </div>
      )}
    </section>
  )
}
