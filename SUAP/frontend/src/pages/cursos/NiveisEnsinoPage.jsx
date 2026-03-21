import CatalogoCrudPage from '@/pages/cursos/CatalogoCrudPage'
import { niveisEnsinoApi } from '@/api/endpoints'

export default function NiveisEnsinoPage() {
  return (
    <CatalogoCrudPage
      title="Níveis de Ensino"
      singular="Nível de Ensino"
      plural="Níveis de Ensino"
      api={niveisEnsinoApi}
      queryKey="niveis-ensino"
      helpSlug="ajuda-niveis-de-ensino"
      helpTitle="Ajuda de Níveis de Ensino"
      helpDescription="A ajuda detalhada desta funcionalidade ainda será portada para o frontend React."
      exportFileName="niveis-de-ensino.xls"
    />
  )
}