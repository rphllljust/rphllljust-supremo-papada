import { Link } from 'react-router-dom'
import { internalSuapModules, publicSuapServices, SUAP_PENDING } from '@/modules/suap/config/suapModules'

export default function SuapModulosPage() {
  return (
    <section className="page page--wide">
      <header className="page-header">
        <div>
          <h1 className="page-title">Módulos SUAP</h1>
          <p className="page-subtitle">Estrutura inicial da Fase 1 para navegação de módulos.</p>
        </div>
      </header>

      <div className="dashboard-card" role="status" aria-live="polite">
        <p>
          Mapeamento fino de telas, campos e fluxos autenticados: <strong>{SUAP_PENDING}</strong>.
        </p>
      </div>

      <div style={{ marginTop: 16 }}>
        <h2 className="page-title" style={{ fontSize: 24 }}>Serviços públicos confirmados</h2>
      </div>

      <div className="dashboard-admin__quick-grid" style={{ marginTop: 16 }}>
        {publicSuapServices.map((modulo) => (
          <article key={modulo.group} className="dashboard-card">
            <h2 className="dashboard-card__title">{modulo.group}</h2>
            <p className="dashboard-card__subtitle">status: confirmado_publico • origem: {modulo.source}</p>
            <div style={{ marginTop: 12 }}>
              <strong>Serviços</strong>
              <ul style={{ marginTop: 8, paddingLeft: 18 }}>
                {modulo.items.map((submodulo) => (
                  <li key={submodulo.path} style={{ marginBottom: 6 }}>
                    <span>{submodulo.title}</span> - <span>{submodulo.status}</span>{' '}
                    <Link to={submodulo.path} className="btn btn--outline btn--sm" style={{ marginLeft: 8 }}>
                      Abrir página interna
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
            <div style={{ marginTop: 12 }}>
              <a className="btn btn--outline btn--sm" href="https://treinamento.suapdevs.ifrn.edu.br/" target="_blank" rel="noreferrer">
                Abrir no SUAP
              </a>
            </div>
          </article>
        ))}
      </div>

      <div style={{ marginTop: 24 }}>
        <h2 className="page-title" style={{ fontSize: 24 }}>Módulos internos pendentes de confirmação autenticada</h2>
      </div>

      <div className="dashboard-admin__quick-grid" style={{ marginTop: 16 }}>
        {internalSuapModules.map((modulo) => (
          <article key={modulo.name} className="dashboard-card">
            <h2 className="dashboard-card__title">{modulo.name}</h2>
            <p className="dashboard-card__subtitle">{modulo.status} • origem: {modulo.source}</p>
            <ul style={{ marginTop: 8, paddingLeft: 18 }}>
              {modulo.submodules.map((submodulo, index) => (
                <li key={`${modulo.name}-${index}`}>
                  {submodulo.name} - {submodulo.status}
                </li>
              ))}
            </ul>
            <button type="button" className="btn btn--outline btn--sm" disabled style={{ marginTop: 12 }}>
              {SUAP_PENDING}
            </button>
          </article>
        ))}
      </div>
    </section>
  )
}
