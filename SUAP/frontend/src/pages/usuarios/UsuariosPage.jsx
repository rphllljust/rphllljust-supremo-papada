import { useEffect, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useSearchParams } from 'react-router-dom'
import { usuariosApi } from '@/api/endpoints'
import DataTable from '@/components/ui/DataTable'

const TIPO_LABELS = {
  ALUNO: 'Aluno',
  PROFESSOR: 'Professor',
  SECRETARIA: 'Secretaria',
  COORDENACAO: 'Coordenador de Curso',
  ADMIN: 'Administrador',
}

const COLUMNS = [
  { key: 'nome_completo', label: 'Nome' },
  { key: 'username', label: 'Usuário' },
  { key: 'cpf', label: 'CPF' },
  { key: 'email', label: 'E-mail' },
  {
    key: 'tipo',
    label: 'Perfil',
    render: (row) => row.tipo_display || TIPO_LABELS[row.tipo] || row.tipo,
  },
  {
    key: 'is_active',
    label: 'Ativo',
    render: (row) => (row.is_active ? 'Sim' : 'Não'),
  },
]

export default function UsuariosPage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const [search, setSearch] = useState('')
  const [tipo, setTipo] = useState(searchParams.get('tipo') || '')
  const [page, setPage] = useState(1)

  useEffect(() => {
    setTipo(searchParams.get('tipo') || '')
  }, [searchParams])

  const { data, isLoading, isError } = useQuery({
    queryKey: ['usuarios', { search, tipo, page }],
    queryFn: () => usuariosApi.list({ search, tipo: tipo || undefined, page }).then((response) => response.data),
    staleTime: 30_000,
  })

  return (
    <div className="page">
      <div className="page-header">
        <h1 className="page-title">Usuários</h1>
        <div className="page-header__actions">
          <select
            className="select"
            value={tipo}
            onChange={(event) => {
              const nextType = event.target.value
              setTipo(nextType)
              setSearchParams(nextType ? { tipo: nextType } : {})
              setPage(1)
            }}
          >
            <option value="">Todos os perfis</option>
            <option value="ALUNO">Aluno</option>
            <option value="PROFESSOR">Professor</option>
            <option value="SECRETARIA">Secretaria</option>
            <option value="COORDENACAO">Coordenador de Curso</option>
            <option value="ADMIN">Administrador</option>
          </select>
        </div>
      </div>

      {isError && (
        <div className="alert alert--error">
          Não foi possível carregar os usuários com as permissões atuais.
        </div>
      )}

      <DataTable
        columns={COLUMNS}
        data={data}
        isLoading={isLoading}
        onSearch={(value) => {
          setSearch(value)
          setPage(1)
        }}
        searchPlaceholder="Buscar por nome, CPF, e-mail ou usuário..."
        emptyMessage="Nenhum usuário encontrado."
      />

      {data && (
        <div className="pagination">
          <button className="btn btn--secondary" disabled={!data.previous} onClick={() => setPage((current) => current - 1)}>
            Anterior
          </button>
          <span className="pagination__info">Página {page} — {data.count} registros</span>
          <button className="btn btn--secondary" disabled={!data.next} onClick={() => setPage((current) => current + 1)}>
            Próxima
          </button>
        </div>
      )}
    </div>
  )
}