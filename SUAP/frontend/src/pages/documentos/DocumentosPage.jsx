import { Link } from 'react-router-dom'
import { FileText, GraduationCap, ScrollText, Waypoints } from 'lucide-react'

const ITEMS = [
  {
    to: '/documentos/declaracoes',
    title: 'Declaracoes',
    description: 'Emissao e consulta de declaracoes de matricula, frequencia e conclusao.',
    icon: FileText,
  },
  {
    to: '/documentos/historicos',
    title: 'Historicos Escolares',
    description: 'Gerencie historicos escolares completos e parciais.',
    icon: GraduationCap,
  },
  {
    to: '/documentos/guias',
    title: 'Guias de Transferencia',
    description: 'Emita e acompanhe guias vinculadas a transferencias.',
    icon: Waypoints,
  },
  {
    to: '/ata-professores',
    title: 'Atas dos Professores',
    description: 'Acesse o assistente de atas escolares digitais e seus rascunhos.',
    icon: ScrollText,
  },
]

export default function DocumentosPage() {
  return (
    <div className="page">
      <div className="page-header">
        <div>
          <h1 className="page-title">Documentos</h1>
          <p className="page-subtitle">Modulo portado para o frontend React</p>
        </div>
      </div>

      <div className="document-grid">
        {ITEMS.map((item) => (
          <Link key={item.to} to={item.to} className="document-card">
            <div className="document-card__icon">
              <item.icon size={22} />
            </div>
            <h2 className="document-card__title">{item.title}</h2>
            <p className="document-card__description">{item.description}</p>
          </Link>
        ))}
      </div>
    </div>
  )
}