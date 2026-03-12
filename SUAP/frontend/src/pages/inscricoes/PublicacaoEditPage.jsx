import { useParams } from 'react-router-dom'

import PublicacaoFormView from './PublicacaoFormView'

export default function PublicacaoEditPage() {
  const { publicacaoId } = useParams()
  return <PublicacaoFormView publicacaoId={publicacaoId} />
}