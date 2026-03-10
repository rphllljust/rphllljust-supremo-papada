import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import DataTable from '@/components/ui/DataTable'

export default function EstagiosPage() {
  const [search, setSearch] = useState('')
  const [page, setPage] = useState(1)

  return (
    <div className="page">
      <div className="page-header">
        <h1 className="page-title">Estagios</h1>
      </div>
      <p style={{color:'#9AA1B9', marginTop:40, textAlign:'center'}}>
        Página em construção — conecte à API /api/v1/estagios/
      </p>
    </div>
  )
}
