import { useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { CircleHelp, Pencil, Plus, Search, Trash2, X } from 'lucide-react'
import { Link } from 'react-router-dom'
import toast from 'react-hot-toast'

import { hipotesesLegaisApi } from '@/api/endpoints'

import './hipoteses-legais.css'

const EMPTY_FORM = {
  descricao: '',
  base_legal: '',
  nivel_acesso: 'RESTRITO',
  ativo: true,
}

const NIVEL_OPTIONS = [
  { value: 'PUBLICO', label: 'Publico' },
  { value: 'RESTRITO', label: 'Restrito' },
  { value: 'SIGILOSO', label: 'Sigiloso' },
]

function getErrorMessage(error, fallback) {
  const data = error?.response?.data
  if (!data) return fallback
  if (typeof data.detail === 'string') return data.detail
  if (typeof data === 'string') return data
  const firstValue = Object.values(data)[0]
  return Array.isArray(firstValue) ? firstValue[0] : (firstValue || fallback)
}

function accessClass(nivelAcesso) {
  if (nivelAcesso === 'SIGILOSO') return 'hipoteses-legais__tag hipoteses-legais__tag--sigiloso'
  if (nivelAcesso === 'PUBLICO') return 'hipoteses-legais__tag hipoteses-legais__tag--publico'
  return 'hipoteses-legais__tag hipoteses-legais__tag--restrito'
}

export default function HipotesesLegaisPage() {
  const queryClient = useQueryClient()
  const [page, setPage] = useState(1)
  const [searchDraft, setSearchDraft] = useState('')
  const [searchValue, setSearchValue] = useState('')
  const [editingItem, setEditingItem] = useState(null)
  const [formData, setFormData] = useState(EMPTY_FORM)
  const [isEditorOpen, setIsEditorOpen] = useState(false)

  const { data, isLoading, isError } = useQuery({
    queryKey: ['hipoteses-legais', { page, texto: searchValue }],
    queryFn: () => hipotesesLegaisApi.list({ page, texto: searchValue || undefined }).then((response) => response.data),
    staleTime: 30_000,
  })

  const saveMutation = useMutation({
    mutationFn: (payload) => {
      if (editingItem?.id) {
        return hipotesesLegaisApi.patch(editingItem.id, payload)
      }
      return hipotesesLegaisApi.create(payload)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['hipoteses-legais'] })
      toast.success(editingItem?.id ? 'Hipotese legal atualizada.' : 'Hipotese legal criada.')
      setEditingItem(null)
      setFormData(EMPTY_FORM)
      setIsEditorOpen(false)
    },
    onError: (error) => toast.error(getErrorMessage(error, 'Nao foi possivel salvar.')),
  })

  const deleteMutation = useMutation({
    mutationFn: (id) => hipotesesLegaisApi.remove(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['hipoteses-legais'] })
      toast.success('Hipotese legal removida.')
    },
    onError: (error) => toast.error(getErrorMessage(error, 'Nao foi possivel remover.')),
  })

  const rows = data?.results || []
  const countLabel = useMemo(() => {
    if (isLoading) return 'Carregando hipoteses legais...'
    if (isError) return 'Falha ao carregar hipoteses legais.'
    return `Mostrando ${data?.count || 0} Hipoteses Legais`
  }, [data?.count, isError, isLoading])

  const openCreate = () => {
    setEditingItem(null)
    setFormData(EMPTY_FORM)
    setIsEditorOpen(true)
  }

  const openEdit = (item) => {
    setEditingItem(item)
    setFormData({
      descricao: item.descricao || '',
      base_legal: item.base_legal || '',
      nivel_acesso: item.nivel_acesso || 'RESTRITO',
      ativo: Boolean(item.ativo),
    })
    setIsEditorOpen(true)
  }

  const closeEditor = () => {
    setEditingItem(null)
    setFormData(EMPTY_FORM)
    setIsEditorOpen(false)
  }

  const handleFilter = () => {
    setPage(1)
    setSearchValue(searchDraft.trim())
  }

  return (
    <div className="page page--wide hipoteses-legais-page">
      <nav className="hipoteses-legais__breadcrumb">
        <Link to="/dashboard">Inicio</Link>
        <span>&gt;</span>
        <span>Hipoteses Legais</span>
      </nav>

      <header className="hipoteses-legais__header">
        <h1>Hipoteses Legais</h1>
        <div className="hipoteses-legais__header-actions">
          <button type="button" className="hipoteses-legais__btn hipoteses-legais__btn--add" onClick={openCreate}>
            <Plus size={15} />
            Adicionar Hipotese Legal
          </button>
          <button
            type="button"
            className="hipoteses-legais__btn hipoteses-legais__btn--help"
            onClick={() => toast('Use os filtros para localizar registros e o botao Adicionar para incluir nova hipotese.')}
          >
            <CircleHelp size={15} />
            Ajuda
          </button>
        </div>
      </header>

      <section className="hipoteses-legais__filters-panel">
        <h2>Filtros:</h2>
        <div className="hipoteses-legais__filters-row">
          <label className="hipoteses-legais__field">
            <span>Texto:</span>
            <input
              value={searchDraft}
              onChange={(event) => setSearchDraft(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === 'Enter') {
                  event.preventDefault()
                  handleFilter()
                }
              }}
              placeholder="Descricao ou base legal"
            />
          </label>
          <button type="button" className="hipoteses-legais__btn hipoteses-legais__btn--filter" onClick={handleFilter}>
            <Search size={14} />
            Filtrar
          </button>
        </div>
      </section>

      <p className="hipoteses-legais__summary">{countLabel}</p>

      <section className="hipoteses-legais__table-panel">
        <table className="hipoteses-legais__table">
          <thead>
            <tr>
              <th>
                <div className="hipoteses-legais__th-with-tools">
                  <span>Descricao</span>
                  <div className="hipoteses-legais__th-tools">
                    <button type="button" title="Limpar busca" onClick={() => { setSearchDraft(''); setSearchValue(''); setPage(1) }}>
                      <X size={12} />
                    </button>
                    <button type="button" title="Aplicar filtro" onClick={handleFilter}>
                      <Search size={12} />
                    </button>
                  </div>
                </div>
              </th>
              <th>Base Legal</th>
              <th>Nivel de Acesso</th>
            </tr>
          </thead>
          <tbody>
            {isLoading ? (
              <tr>
                <td colSpan={3} className="hipoteses-legais__empty">Carregando registros...</td>
              </tr>
            ) : null}

            {!isLoading && isError ? (
              <tr>
                <td colSpan={3} className="hipoteses-legais__empty hipoteses-legais__empty--error">
                  Nao foi possivel carregar os dados.
                </td>
              </tr>
            ) : null}

            {!isLoading && !isError && rows.length === 0 ? (
              <tr>
                <td colSpan={3} className="hipoteses-legais__empty">Nenhuma hipotese legal encontrada.</td>
              </tr>
            ) : null}

            {!isLoading && !isError && rows.map((item) => (
              <tr key={item.id}>
                <td>
                  <div className="hipoteses-legais__descricao-cell">
                    <div className="hipoteses-legais__row-actions">
                      <button type="button" title="Editar" onClick={() => openEdit(item)}>
                        <Pencil size={11} />
                      </button>
                      <button
                        type="button"
                        title="Excluir"
                        onClick={() => window.confirm(`Excluir a hipotese "${item.descricao}"?`) && deleteMutation.mutate(item.id)}
                      >
                        <Trash2 size={11} />
                      </button>
                    </div>
                    <span>{item.descricao}</span>
                  </div>
                </td>
                <td>{item.base_legal}</td>
                <td><span className={accessClass(item.nivel_acesso)}>{item.nivel_acesso_display || item.nivel_acesso}</span></td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      {data ? (
        <div className="hipoteses-legais__pagination">
          <button type="button" disabled={!data.previous} onClick={() => setPage((current) => current - 1)}>Anterior</button>
          <span>Pagina {page}</span>
          <button type="button" disabled={!data.next} onClick={() => setPage((current) => current + 1)}>Proxima</button>
        </div>
      ) : null}

      {isEditorOpen ? (
        <div className="hipoteses-legais__modal-backdrop">
          <div className="hipoteses-legais__modal">
            <header className="hipoteses-legais__modal-header">
              <h3>{editingItem?.id ? 'Editar Hipotese Legal' : 'Nova Hipotese Legal'}</h3>
              <button type="button" onClick={closeEditor} aria-label="Fechar"><X size={16} /></button>
            </header>

            <form
              className="hipoteses-legais__modal-form"
              onSubmit={(event) => {
                event.preventDefault()
                if (!formData.descricao.trim() || !formData.base_legal.trim()) {
                  toast.error('Preencha descricao e base legal.')
                  return
                }

                saveMutation.mutate({
                  descricao: formData.descricao.trim(),
                  base_legal: formData.base_legal.trim(),
                  nivel_acesso: formData.nivel_acesso,
                  ativo: formData.ativo,
                })
              }}
            >
              <label>
                <span>Descricao</span>
                <input
                  value={formData.descricao}
                  onChange={(event) => setFormData((current) => ({ ...current, descricao: event.target.value }))}
                />
              </label>

              <label>
                <span>Base legal</span>
                <input
                  value={formData.base_legal}
                  onChange={(event) => setFormData((current) => ({ ...current, base_legal: event.target.value }))}
                />
              </label>

              <label>
                <span>Nivel de acesso</span>
                <select
                  value={formData.nivel_acesso}
                  onChange={(event) => setFormData((current) => ({ ...current, nivel_acesso: event.target.value }))}
                >
                  {NIVEL_OPTIONS.map((option) => (
                    <option key={option.value} value={option.value}>{option.label}</option>
                  ))}
                </select>
              </label>

              <label className="hipoteses-legais__checkbox">
                <input
                  type="checkbox"
                  checked={formData.ativo}
                  onChange={(event) => setFormData((current) => ({ ...current, ativo: event.target.checked }))}
                />
                <span>Registro ativo</span>
              </label>

              <footer className="hipoteses-legais__modal-actions">
                <button type="button" className="hipoteses-legais__btn hipoteses-legais__btn--cancel" onClick={closeEditor}>
                  Cancelar
                </button>
                <button type="submit" className="hipoteses-legais__btn hipoteses-legais__btn--save" disabled={saveMutation.isPending}>
                  {saveMutation.isPending ? 'Salvando...' : 'Salvar'}
                </button>
              </footer>
            </form>
          </div>
        </div>
      ) : null}
    </div>
  )
}
