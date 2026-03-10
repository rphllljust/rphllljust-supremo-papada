import { useEffect, useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useForm } from 'react-hook-form'
import toast from 'react-hot-toast'
import { Eye, Pencil, Plus, Trash2 } from 'lucide-react'

import { setoresApi } from '@/api/endpoints'
import DataTable from '@/components/ui/DataTable'
import EntityDetailsPanel from '@/components/ui/EntityDetailsPanel'
import EntityFormPanel from '@/components/ui/EntityFormPanel'

const COLUMNS = [
  { key: 'codigo', label: 'Codigo' },
  { key: 'sigla', label: 'Sigla' },
  { key: 'nome', label: 'Setor' },
  { key: 'setor_superior_nome', label: 'Setor superior' },
  {
    key: 'ativo',
    label: 'Ativo',
    render: (row) => (row.ativo ? 'Sim' : 'Nao'),
  },
]

const DEFAULT_VALUES = {
  nome: '',
  sigla: '',
  codigo: '',
  setor_superior: '',
  ativo: true,
}

function getErrorMessage(error, fallback) {
  const data = error?.response?.data
  if (!data) {
    return fallback
  }

  if (typeof data.detail === 'string') {
    return data.detail
  }

  const firstValue = Object.values(data)[0]
  if (Array.isArray(firstValue)) {
    return firstValue[0]
  }

  return firstValue || fallback
}

export default function SetoresPage() {
  const queryClient = useQueryClient()
  const [search, setSearch] = useState('')
  const [page, setPage] = useState(1)
  const [ativoFiltro, setAtivoFiltro] = useState('')
  const [selectedSetorId, setSelectedSetorId] = useState(null)
  const [editingSetorId, setEditingSetorId] = useState(null)
  const [isCreating, setIsCreating] = useState(false)

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm({ defaultValues: DEFAULT_VALUES })

  const listParams = useMemo(() => ({
    search,
    page,
    ativo: ativoFiltro || undefined,
  }), [ativoFiltro, page, search])

  const { data, isLoading, isError } = useQuery({
    queryKey: ['setores', listParams],
    queryFn: () => setoresApi.list(listParams).then((response) => response.data),
    staleTime: 30_000,
  })

  const { data: setoresOptionsData } = useQuery({
    queryKey: ['setores', 'hierarquia-options'],
    queryFn: () => setoresApi.list({ page_size: 100 }).then((response) => response.data),
    staleTime: 60_000,
  })

  const setorOptions = setoresOptionsData?.results || []

  const { data: selectedSetor, isLoading: isLoadingDetails, isError: isErrorDetails } = useQuery({
    queryKey: ['setor', selectedSetorId],
    queryFn: () => setoresApi.get(selectedSetorId).then((response) => response.data),
    enabled: Boolean(selectedSetorId),
    staleTime: 30_000,
  })

  const { data: editingSetor, isLoading: isLoadingEditing } = useQuery({
    queryKey: ['setor-edit', editingSetorId],
    queryFn: () => setoresApi.get(editingSetorId).then((response) => response.data),
    enabled: Boolean(editingSetorId),
    staleTime: 0,
  })

  useEffect(() => {
    if (!editingSetor) {
      return
    }

    reset({
      nome: editingSetor.nome || '',
      sigla: editingSetor.sigla || '',
      codigo: editingSetor.codigo || '',
      setor_superior: editingSetor.setor_superior ? String(editingSetor.setor_superior) : '',
      ativo: Boolean(editingSetor.ativo),
    })
  }, [editingSetor, reset])

  const saveMutation = useMutation({
    mutationFn: ({ id, payload }) => (id ? setoresApi.update(id, payload) : setoresApi.create(payload)),
    onSuccess: (_response, variables) => {
      queryClient.invalidateQueries({ queryKey: ['setores'] })
      if (variables.id) {
        queryClient.invalidateQueries({ queryKey: ['setor', variables.id] })
        toast.success('Setor atualizado com sucesso.')
      } else {
        toast.success('Setor criado com sucesso.')
      }
      setEditingSetorId(null)
      setIsCreating(false)
      reset(DEFAULT_VALUES)
    },
    onError: (error) => {
      toast.error(getErrorMessage(error, 'Nao foi possivel salvar o setor.'))
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (id) => setoresApi.remove(id),
    onSuccess: (_response, id) => {
      queryClient.invalidateQueries({ queryKey: ['setores'] })
      queryClient.invalidateQueries({ queryKey: ['setor', id] })
      if (selectedSetorId === id) {
        setSelectedSetorId(null)
      }
      if (editingSetorId === id) {
        setEditingSetorId(null)
        setIsCreating(false)
        reset(DEFAULT_VALUES)
      }
      toast.success('Setor excluido com sucesso.')
    },
    onError: (error) => {
      toast.error(getErrorMessage(error, 'Nao foi possivel excluir o setor.'))
    },
  })

  const detailsFields = selectedSetor
    ? [
        { label: 'ID', value: selectedSetor.id },
        { label: 'Codigo', value: selectedSetor.codigo },
        { label: 'Sigla', value: selectedSetor.sigla || '-' },
        { label: 'Setor', value: selectedSetor.nome },
        { label: 'Setor superior', value: selectedSetor.setor_superior_nome || '-' },
        { label: 'Ativo', value: selectedSetor.ativo },
      ]
    : []

  const openCreateForm = () => {
    setEditingSetorId(null)
    setIsCreating(true)
    reset(DEFAULT_VALUES)
  }

  const openEditForm = (id) => {
    setSelectedSetorId(null)
    setIsCreating(false)
    setEditingSetorId(id)
  }

  const closeForm = () => {
    setEditingSetorId(null)
    setIsCreating(false)
    reset(DEFAULT_VALUES)
  }

  const onSubmit = handleSubmit(async (formData) => {
    const payload = {
      nome: formData.nome.trim(),
      sigla: formData.sigla.trim(),
      codigo: formData.codigo.trim(),
      setor_superior: formData.setor_superior ? Number(formData.setor_superior) : null,
      ativo: Boolean(formData.ativo),
    }

    await saveMutation.mutateAsync({
      id: editingSetorId,
      payload,
    })
  })

  const handleDelete = (row) => {
    if (!window.confirm(`Deseja realmente excluir o setor ${row.nome}?`)) {
      return
    }

    deleteMutation.mutate(row.id)
  }

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <h1 className="page-title">Setores</h1>
          <p className="page-subtitle">Gestao de Pessoas</p>
        </div>
        <div className="page-header__actions">
          <select className="select" value={ativoFiltro} onChange={(event) => { setAtivoFiltro(event.target.value); setPage(1) }}>
            <option value="">Todos os status</option>
            <option value="true">Ativos</option>
            <option value="false">Inativos</option>
          </select>
          <button type="button" className="btn btn--primary" onClick={openCreateForm}>
            <Plus size={16} /> Novo Setor
          </button>
        </div>
      </div>

      {isError ? (
        <div className="alert alert--error">
          Nao foi possivel carregar os setores com as permissoes atuais.
        </div>
      ) : null}

      <DataTable
        columns={COLUMNS}
        data={data}
        isLoading={isLoading}
        onSearch={(value) => {
          setSearch(value)
          setPage(1)
        }}
        searchPlaceholder="Buscar por nome, sigla, codigo ou setor superior..."
        emptyMessage="Nenhum setor encontrado."
        rowActions={(row) => (
          <div className="table-actions">
            <button type="button" className="btn btn--outline btn--sm" onClick={() => setSelectedSetorId(row.id)}>
              <Eye size={14} /> Visualizar
            </button>
            <button type="button" className="btn btn--secondary btn--sm" onClick={() => openEditForm(row.id)}>
              <Pencil size={14} /> Editar
            </button>
            <button type="button" className="btn btn--danger btn--sm" onClick={() => handleDelete(row)}>
              <Trash2 size={14} /> Excluir
            </button>
          </div>
        )}
      />

      {selectedSetorId ? (
        <EntityDetailsPanel
          title="Detalhes do setor"
          subtitle={selectedSetor?.nome || 'Consultando setor selecionado'}
          fields={detailsFields}
          isLoading={isLoadingDetails}
          errorMessage={isErrorDetails ? 'Nao foi possivel carregar os detalhes deste setor.' : ''}
          onClose={() => setSelectedSetorId(null)}
        />
      ) : null}

      {(isCreating || editingSetorId) ? (
        <EntityFormPanel
          title={editingSetorId ? 'Editar setor' : 'Novo setor'}
          subtitle={editingSetorId ? 'Atualize os dados do setor selecionado.' : 'Cadastre um novo setor para organizacao de servidores.'}
          onSubmit={onSubmit}
          onCancel={closeForm}
          submitLabel={editingSetorId ? 'Salvar alteracoes' : 'Criar setor'}
          isSubmitting={isSubmitting || saveMutation.isPending || isLoadingEditing}
        >
          <div className="form-field">
            <label htmlFor="setor-nome">Nome</label>
            <input id="setor-nome" type="text" {...register('nome', { required: 'Informe o nome do setor' })} />
            {errors.nome ? <span className="field-error">{errors.nome.message}</span> : null}
          </div>

          <div className="form-field">
            <label htmlFor="setor-sigla">Sigla</label>
            <input id="setor-sigla" type="text" {...register('sigla')} />
          </div>

          <div className="form-field">
            <label htmlFor="setor-codigo">Codigo</label>
            <input id="setor-codigo" type="text" {...register('codigo', { required: 'Informe o codigo do setor' })} />
            {errors.codigo ? <span className="field-error">{errors.codigo.message}</span> : null}
          </div>

          <div className="form-field">
            <label htmlFor="setor-superior">Setor superior</label>
            <select id="setor-superior" className="select" {...register('setor_superior')}>
              <option value="">Sem setor superior</option>
              {setorOptions
                .filter((setor) => String(setor.id) !== String(editingSetorId || ''))
                .map((setor) => (
                  <option key={setor.id} value={setor.id}>{setor.nome}</option>
                ))}
            </select>
          </div>

          <div className="form-field form-field--checkbox">
            <label className="checkbox-field">
              <input type="checkbox" {...register('ativo')} />
              <span>Setor ativo</span>
            </label>
          </div>
        </EntityFormPanel>
      ) : null}

      {data ? (
        <div className="pagination">
          <button className="btn btn--secondary" disabled={!data.previous} onClick={() => setPage((current) => current - 1)}>Anterior</button>
          <span className="pagination__info">Pagina {page} — {data.count} registros</span>
          <button className="btn btn--secondary" disabled={!data.next} onClick={() => setPage((current) => current + 1)}>Proxima</button>
        </div>
      ) : null}
    </div>
  )
}