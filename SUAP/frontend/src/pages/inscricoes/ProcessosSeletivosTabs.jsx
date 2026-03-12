import { Link } from 'react-router-dom'

const TAB_CONFIG = {
  editais: {
    label: 'Editais',
    to: '/inscricoes/editais',
  },
  inscricoes: {
    label: 'Inscrições',
    to: '/inscricoes?aba=inscricoes',
  },
}

export default function ProcessosSeletivosTabs({ activeTab }) {
  return (
    <div className="profile-tabs processos-seletivos-tabs" role="tablist" aria-label="Navegação de processos seletivos">
      {Object.entries(TAB_CONFIG).map(([key, tab]) => (
        <Link
          key={key}
          to={tab.to}
          className={`profile-tabs__item ${activeTab === key ? 'profile-tabs__item--active' : ''}`}
          role="tab"
          aria-selected={activeTab === key}
        >
          {tab.label}
        </Link>
      ))}
    </div>
  )
}