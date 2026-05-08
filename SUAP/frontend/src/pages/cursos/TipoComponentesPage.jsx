import CatalogoCrudPage from '@/pages/cursos/CatalogoCrudPage'
import { tiposComponentesApi } from '@/api/endpoints'

export default function TipoComponentesPage() {
  return (
    <CatalogoCrudPage
      title="Tipos do Componente"
      singular="Tipo do Componente"
      plural="Tipos do Componente"
      api={tiposComponentesApi}
      queryKey="tipos-componentes"
      helpSlug="ajuda-tipos-do-componente"
      helpTitle="Ajuda de Tipos do Componente"
      helpDescription="A ajuda detalhada desta funcionalidade ainda será portada para o frontend React."
      exportFileName="tipos-do-componente.xls"
      pageClassName="tipo-componentes-page"
    />
  )
}
