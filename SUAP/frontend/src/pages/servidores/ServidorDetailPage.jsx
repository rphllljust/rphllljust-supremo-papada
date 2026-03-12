import { useParams } from 'react-router-dom'

import { ServidorProfileView } from '@/pages/servidores/ServidorProfilePage'

export default function ServidorDetailPage() {
  const { servidorId } = useParams()

  return <ServidorProfileView servidorId={servidorId} />
}