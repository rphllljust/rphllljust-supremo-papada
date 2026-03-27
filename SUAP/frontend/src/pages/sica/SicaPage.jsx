import { useEffect, useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Pencil, Plus, Trash2 } from 'lucide-react'
import toast from 'react-hot-toast'

import { cursosApi, sicaApi } from '@/api/endpoints'
import DataTable from '@/components/ui/DataTable'
import EntityFormPanel from '@/components/ui/EntityFormPanel'
import SearchableRemoteSelect from '@/components/ui/SearchableRemoteSelect'

const MATRIZ_STATUS_OPTIONS = [
  { value: 'RASCUNHO', label: 'Rascunho' },
  { value: 'VIGENTE', label: 'Vigente' },
  { value: 'ARQUIVADA', label: 'Arquivada' },
]

const COMPONENTE_TIPO_OPTIONS = [
  { value: 'OBRIGATORIO', label: 'Obrigatorio' },
  { value: 'OPTATIVO', label: 'Optativo' },
  { value: 'PRATICO', label: 'Pratico' },
]

const STATUS_BADGE = {
  RASCUNHO: 'badge--warning',
  VIGENTE: 'badge--success',
  ARQUIVADA: 'badge--secondary',
}

const TIPO_BADGE = {
  OBRIGATORIO: 'badge--info',
  OPTATIVO: 'badge--secondary',
  PRATICO: 'badge--warning',
}

const EMPTY_MATRIZ_FORM = {
  curso: '',
  versao: '',
  status: 'RASCUNHO',
  descricao: '',
}

const EMPTY_COMPONENTE_FORM = {
  periodo: '1',
  componente: '',
  tipo: 'OBRIGATORIO',
  carga_horaria: '',
  ementa: '',
  prerequisitos: [],
  equivalencias: [],
}

const MATRIZ_COLUMNS = [
  { key: 'curso_nome', label: 'Curso' },
  { key: 'versao', label: 'Versao' },
  {
    key: 'status',
    label: 'Status',
    render: (row) => (
      <span className={`badge ${STATUS_BADGE[row.status] || ''}`}>
        {row.status_display || row.status}
      </span>
    ),
  },
  { key: 'total_componentes', label: 'Componentes' },
]

const COMPONENTE_COLUMNS = [
  { key: 'periodo', label: 'Periodo' },
  { key: 'componente', label: 'Componente' },
  {
    key: 'tipo',
    label: 'Tipo',
    render: (row) => (
      <span className={`badge ${TIPO_BADGE[row.tipo] || ''}`}>
        {row.tipo_display || row.tipo}
      </span>
    ),
  },
  { key: 'carga_horaria', label: 'Carga horaria' },
  {
    key: 'prerequisitos_info',
    label: 'Pre-requisito',
    render: (row) => (row.prerequisitos_info?.length ? row.prerequisitos_info.map((item) => item.componente).join(', ') : '-'),
  },
  {
    key: 'equivalencias_info',
    label: 'Equivalencia',
    render: (row) => (row.equivalencias_info?.length ? row.equivalencias_info.map((item) => item.componente).join(', ') : '-'),
  },
]

function getErrorMessage(error, fallback) {
  const data = error?.response?.data
  if (!data) return fallback
  if (typeof data.detail === 'string') return data.detail
  const firstValue = Object.values(data)[0]
  return Array.isArray(firstValue) ? firstValue[0] : (firstValue || fallback)
}

function parseMultiSelect(event) {
  return Array.from(event.target.selectedOptions).map((option) => option.value)
}

function MultiSelectField({
  id,
  label,
  value,
  options,
  onChange,
}) {
  return (
    <div className="form-field form-field--full">
      <label htmlFor={id}>{label}</label>
      <select
        id={id}
        className="select"
        multiple
        value={value}
        onChange={(event) => onChange(parseMultiSelect(event))}
      >
        {options.map((option) => (
          <option key={option.id} value={String(option.id)}>
            {`P${option.periodo} - ${option.componente}`}
          </option>
        ))}
      </select>
    </div>
  )
}

export default function SicaPage() {
  const queryClient = useQueryClient()
  const [matrizSearch, setMatrizSearch] = useState('')
  const [matrizStatusFilter, setMatrizStatusFilter] = useState('')
  const [matrizPage, setMatrizPage] = useState(1)
  const [selectedMatrizId, setSelectedMatrizId] = useState(null)
  const [creatingMatriz, setCreatingMatriz] = useState(false)
  const [editingMatrizId, setEditingMatrizId] = useState(null)
  const [matrizForm, setMatrizForm] = useState(EMPTY_MATRIZ_FORM)
  const [cursoSearch, setCursoSearch] = useState('')
  const [componentSearch, setComponentSearch] = useState('')
  const [componentPage, setComponentPage] = useState(1)
  const [periodoFilter, setPeriodoFilter] = useState('')
  const [tipoFilter, setTipoFilter] = useState('')
  const [creatingComponente, setCreatingComponente] = useState(false)
  const [editingComponenteId, setEditingComponenteId] = useState(null)
  const [componenteForm, setComponenteForm] = useState(EMPTY_COMPONENTE_FORM)

  const { data: matrizData, isLoading: isLoadingMatrizes, isError: isErrorMatrizes } = useQuery({
    queryKey: ['sica', 'matrizes', { search: matrizSearch, status: matrizStatusFilter, page: matrizPage }],
    queryFn: () => sicaApi.listMatrizes({ search: matrizSearch, status: matrizStatusFilter || undefined, page: matrizPage }).then((response) => response.data),
    staleTime: 30_000,
  })

  const { data: cursosData } = useQuery({
    queryKey: ['sica', 'cursos-options', cursoSearch],
    queryFn: () => cursosApi.list({ page_size: 10, search: cursoSearch || undefined }).then((response) => response.data),
    staleTime: 60_000,
  })

  const { data: selectedMatriz } = useQuery({
    queryKey: ['sica', 'matriz', selectedMatrizId],
    queryFn: () => sicaApi.getMatriz(selectedMatrizId).then((response) => response.data),
    enabled: Boolean(selectedMatrizId),
    staleTime: 30_000,
  })

  const { data: editingMatriz } = useQuery({
    queryKey: ['sica', 'matriz-edit', editingMatrizId],
    queryFn: () => sicaApi.getMatriz(editingMatrizId).then((response) => response.data),
    enabled: Boolean(editingMatrizId),
    staleTime: 0,
  })

  const { data: componenteData, isLoading: isLoadingComponentes, isError: isErrorComponentes } = useQuery({
    queryKey: ['sica', 'componentes', { matriz: selectedMatrizId, search: componentSearch, page: componentPage, periodo: periodoFilter, tipo: tipoFilter }],
    queryFn: () => sicaApi.listComponentes({
      matriz: selectedMatrizId,
      search: componentSearch || undefined,
      page: componentPage,
      periodo: periodoFilter || undefined,
      tipo: tipoFilter || undefined,
    }).then((response) => response.data),
    enabled: Boolean(selectedMatrizId),
    staleTime: 30_000,
  })

  const { data: editingComponente } = useQuery({
    queryKey: ['sica', 'componente-edit', editingComponenteId],
    queryFn: () => sicaApi.getComponente(editingComponenteId).then((response) => response.data),
    enabled: Boolean(editingComponenteId),
    staleTime: 0,
  })

  const { data: relacionamentoOptionsData } = useQuery({
    queryKey: ['sica', 'componentes-options', selectedMatrizId],
    queryFn: () => sicaApi.listComponentes({ matriz: selectedMatrizId, page_size: 200 }).then((response) => response.data),
    enabled: Boolean(selectedMatrizId),
    staleTime: 30_000,
  })

  useEffect(() => {
    if (!editingMatriz) return

    setMatrizForm({
      curso: editingMatriz.curso ? String(editingMatriz.curso) : '',
      versao: editingMatriz.versao || '',
      status: editingMatriz.status || 'RASCUNHO',
      descricao: editingMatriz.descricao || '',
    })
  }, [editingMatriz])

  useEffect(() => {
    if (!editingComponente) return

    setComponenteForm({
      periodo: editingComponente.periodo ? String(editingComponente.periodo) : '1',
      componente: editingComponente.componente || '',
      tipo: editingComponente.tipo || 'OBRIGATORIO',
      carga_horaria: editingComponente.carga_horaria ? String(editingComponente.carga_horaria) : '',
      ementa: editingComponente.ementa || '',
      prerequisitos: (editingComponente.prerequisitos || []).map((value) => String(value)),
      equivalencias: (editingComponente.equivalencias || []).map((value) => String(value)),
    })
  }, [editingComponente])

  useEffect(() => {
    setCreatingComponente(false)
    setEditingComponenteId(null)
    setComponenteForm(EMPTY_COMPONENTE_FORM)
    setComponentPage(1)
    setComponentSearch('')
    setPeriodoFilter('')
    setTipoFilter('')
  }, [selectedMatrizId])

  const saveMatrizMutation = useMutation({
    mutationFn: ({ id, payload }) => (id ? sicaApi.patchMatriz(id, payload) : sicaApi.createMatriz(payload)),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['sica', 'matrizes'] })
      await queryClient.invalidateQueries({ queryKey: ['sica', 'matriz'] })
      toast.success('Matriz SICA salva com sucesso.')
      setCreatingMatriz(false)
      setEditingMatrizId(null)
      setMatrizForm(EMPTY_MATRIZ_FORM)
    },
    onError: (error) => toast.error(getErrorMessage(error, 'Nao foi possivel salvar a matriz SICA.')),
  })

  const deleteMatrizMutation = useMutation({
    mutationFn: (id) => sicaApi.removeMatriz(id),
    onSuccess: async (_response, id) => {
      await queryClient.invalidateQueries({ queryKey: ['sica', 'matrizes'] })
      if (selectedMatrizId === id) {
        setSelectedMatrizId(null)
      }
      toast.success('Matriz SICA removida com sucesso.')
    },
    onError: (error) => toast.error(getErrorMessage(error, 'Nao foi possivel remover a matriz SICA.')),
  })

  const saveComponenteMutation = useMutation({
    mutationFn: ({ id, payload }) => (id ? sicaApi.patchComponente(id, payload) : sicaApi.createComponente(payload)),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['sica', 'componentes'] })
      await queryClient.invalidateQueries({ queryKey: ['sica', 'componentes-options'] })
      await queryClient.invalidateQueries({ queryKey: ['sica', 'matrizes'] })
      toast.success('Componente SICA salvo com sucesso.')
      setCreatingComponente(false)
      setEditingComponenteId(null)
      setComponenteForm(EMPTY_COMPONENTE_FORM)
    },
    onError: (error) => toast.error(getErrorMessage(error, 'Nao foi possivel salvar o componente SICA.')),
  })

  const deleteComponenteMutation = useMutation({
    mutationFn: (id) => sicaApi.removeComponente(id),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['sica', 'componentes'] })
      await queryClient.invalidateQueries({ queryKey: ['sica', 'componentes-options'] })
      await queryClient.invalidateQueries({ queryKey: ['sica', 'matrizes'] })
      toast.success('Componente SICA removido com sucesso.')
    },
    onError: (error) => toast.error(getErrorMessage(error, 'Nao foi possivel remover o componente SICA.')),
  })

  const cursos = cursosData?.results || []
  const matrizes = matrizData?.results || []
  const componentes = componenteData?.results || []
  const relacionamentoOptions = useMemo(
    () => (relacionamentoOptionsData?.results || []).filter((item) => String(item.id) !== String(editingComponenteId || '')),
    [relacionamentoOptionsData, editingComponenteId],
  )

  const selectedCursoOption = matrizForm.curso && editingMatriz
    ? { id: editingMatriz.curso, nome: editingMatriz.curso_nome }
    : null

  const matrizFormVisible = creatingMatriz || Boolean(editingMatrizId)
  const componenteFormVisible = creatingComponente || Boolean(editingComponenteId)
  const selectedMatrizName = selectedMatriz ? `${selectedMatriz.curso_nome} - v${selectedMatriz.versao}` : ''

  const openMatrizCreate = () => {
    setCreatingMatriz(true)
    setEditingMatrizId(null)
    setMatrizForm(EMPTY_MATRIZ_FORM)
  }

  const openMatrizEdit = (id) => {
    setCreatingMatriz(false)
    setEditingMatrizId(id)
  }

  const openComponenteCreate = () => {
    setCreatingComponente(true)
    setEditingComponenteId(null)
    setComponenteForm(EMPTY_COMPONENTE_FORM)
  }

  const openComponenteEdit = (id) => {
    setCreatingComponente(false)
    setEditingComponenteId(id)
  }

  return (
    <div className="page">
      <div className="page-header">
        <h1 className="page-title">SICA - Sistema de Informacoes Curriculares</h1>
      </div>

      <section className="dashboard-card">
        <div className="page-header">
          <h2 className="page-title">Matrizes Curriculares Versionadas</h2>
          <div className="page-header__actions">
            <select className="select" value={matrizStatusFilter} onChange={(event) => { setMatrizStatusFilter(event.target.value); setMatrizPage(1) }}>
              <option value="">Todos os status</option>
              {MATRIZ_STATUS_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>{option.label}</option>
              ))}
            </select>
            <button type="button" className="btn btn--primary" onClick={openMatrizCreate}>
              <Plus size={16} /> Nova matriz
            </button>
          </div>
        </div>

        {isErrorMatrizes ? <div className="alert alert--error">Nao foi possivel carregar as matrizes SICA.</div> : null}

        <DataTable
          columns={MATRIZ_COLUMNS}
          data={matrizData}
          isLoading={isLoadingMatrizes}
          onSearch={(value) => {
            setMatrizSearch(value)
            setMatrizPage(1)
          }}
          searchPlaceholder="Buscar por curso, versao ou descricao..."
          emptyMessage="Nenhuma matriz curricular cadastrada no SICA."
          rowActions={(row) => (
            <div className="table-actions">
              <button type="button" className="btn btn--outline btn--sm" onClick={() => setSelectedMatrizId(row.id)}>
                Usar matriz
              </button>
              <button type="button" className="btn btn--secondary btn--sm" onClick={() => openMatrizEdit(row.id)}>
                <Pencil size={14} /> Editar
              </button>
              <button
                type="button"
                className="btn btn--danger btn--sm"
                onClick={() => window.confirm(`Excluir a matriz ${row.curso_nome} v${row.versao}?`) && deleteMatrizMutation.mutate(row.id)}
              >
                <Trash2 size={14} /> Excluir
              </button>
            </div>
          )}
        />

        {matrizData ? (
          <div className="pagination">
            <button className="btn btn--secondary" disabled={!matrizData.previous} onClick={() => setMatrizPage((current) => current - 1)}>Anterior</button>
            <span className="pagination__info">Pagina {matrizPage} - {matrizData.count} registros</span>
            <button className="btn btn--secondary" disabled={!matrizData.next} onClick={() => setMatrizPage((current) => current + 1)}>Proxima</button>
          </div>
        ) : null}

        {matrizFormVisible ? (
          <EntityFormPanel
            title={creatingMatriz ? 'Cadastrar matriz SICA' : 'Editar matriz SICA'}
            subtitle="Versione matrizes curriculares por curso no modulo SICA."
            onSubmit={(event) => {
              event.preventDefault()

              if (!matrizForm.curso || !matrizForm.versao.trim()) {
                toast.error('Informe curso e versao da matriz.')
                return
              }

              saveMatrizMutation.mutate({
                id: editingMatrizId || undefined,
                payload: {
                  curso: Number(matrizForm.curso),
                  versao: matrizForm.versao.trim(),
                  status: matrizForm.status,
                  descricao: matrizForm.descricao.trim(),
                },
              })
            }}
            onCancel={() => {
              setCreatingMatriz(false)
              setEditingMatrizId(null)
              setMatrizForm(EMPTY_MATRIZ_FORM)
            }}
            submitLabel={creatingMatriz ? 'Cadastrar matriz' : 'Salvar matriz'}
            isSubmitting={saveMatrizMutation.isPending}
          >
            <SearchableRemoteSelect
              id="sica-matriz-curso"
              label="Curso"
              searchLabel="Buscar curso"
              searchPlaceholder="Digite o nome do curso"
              searchValue={cursoSearch}
              onSearchChange={setCursoSearch}
              value={matrizForm.curso}
              onChange={(nextValue) => setMatrizForm((current) => ({ ...current, curso: nextValue }))}
              options={cursos}
              selectedOption={selectedCursoOption}
              getOptionLabel={(item) => item.nome}
              emptyOptionLabel="Selecione um curso"
            />

            <div className="form-field">
              <label htmlFor="sica-matriz-versao">Versao</label>
              <input
                id="sica-matriz-versao"
                className="form-control"
                value={matrizForm.versao}
                onChange={(event) => setMatrizForm((current) => ({ ...current, versao: event.target.value }))}
              />
            </div>

            <div className="form-field">
              <label htmlFor="sica-matriz-status">Status</label>
              <select
                id="sica-matriz-status"
                className="select"
                value={matrizForm.status}
                onChange={(event) => setMatrizForm((current) => ({ ...current, status: event.target.value }))}
              >
                {MATRIZ_STATUS_OPTIONS.map((option) => (
                  <option key={option.value} value={option.value}>{option.label}</option>
                ))}
              </select>
            </div>

            <div className="form-field form-field--full">
              <label htmlFor="sica-matriz-descricao">Descricao</label>
              <textarea
                id="sica-matriz-descricao"
                className="form-control"
                rows={3}
                value={matrizForm.descricao}
                onChange={(event) => setMatrizForm((current) => ({ ...current, descricao: event.target.value }))}
              />
            </div>
          </EntityFormPanel>
        ) : null}
      </section>

      <section className="dashboard-card">
        <div className="page-header">
          <h2 className="page-title">Componentes Curriculares</h2>
          <div className="page-header__actions">
            <span className="page-subtitle">
              {selectedMatrizId ? `Matriz ativa: ${selectedMatrizName || `#${selectedMatrizId}`}` : 'Selecione uma matriz para gerenciar componentes'}
            </span>
            <button type="button" className="btn btn--primary" onClick={openComponenteCreate} disabled={!selectedMatrizId}>
              <Plus size={16} /> Novo componente
            </button>
          </div>
        </div>

        {selectedMatrizId ? (
          <>
            <div className="page-section-grid">
              <div className="form-field">
                <label htmlFor="sica-periodo-filtro">Filtrar por periodo</label>
                <input
                  id="sica-periodo-filtro"
                  className="form-control"
                  type="number"
                  min="1"
                  value={periodoFilter}
                  onChange={(event) => {
                    setPeriodoFilter(event.target.value)
                    setComponentPage(1)
                  }}
                />
              </div>
              <div className="form-field">
                <label htmlFor="sica-tipo-filtro">Filtrar por tipo</label>
                <select
                  id="sica-tipo-filtro"
                  className="select"
                  value={tipoFilter}
                  onChange={(event) => {
                    setTipoFilter(event.target.value)
                    setComponentPage(1)
                  }}
                >
                  <option value="">Todos os tipos</option>
                  {COMPONENTE_TIPO_OPTIONS.map((option) => (
                    <option key={option.value} value={option.value}>{option.label}</option>
                  ))}
                </select>
              </div>
            </div>

            {isErrorComponentes ? <div className="alert alert--error">Nao foi possivel carregar os componentes da matriz selecionada.</div> : null}

            <DataTable
              columns={COMPONENTE_COLUMNS}
              data={componenteData}
              isLoading={isLoadingComponentes}
              onSearch={(value) => {
                setComponentSearch(value)
                setComponentPage(1)
              }}
              searchPlaceholder="Buscar por componente ou ementa..."
              emptyMessage="Nenhum componente cadastrado para esta matriz."
              rowActions={(row) => (
                <div className="table-actions">
                  <button type="button" className="btn btn--secondary btn--sm" onClick={() => openComponenteEdit(row.id)}>
                    <Pencil size={14} /> Editar
                  </button>
                  <button
                    type="button"
                    className="btn btn--danger btn--sm"
                    onClick={() => window.confirm(`Excluir o componente ${row.componente}?`) && deleteComponenteMutation.mutate(row.id)}
                  >
                    <Trash2 size={14} /> Excluir
                  </button>
                </div>
              )}
            />

            {componenteData ? (
              <div className="pagination">
                <button className="btn btn--secondary" disabled={!componenteData.previous} onClick={() => setComponentPage((current) => current - 1)}>Anterior</button>
                <span className="pagination__info">Pagina {componentPage} - {componenteData.count} registros</span>
                <button className="btn btn--secondary" disabled={!componenteData.next} onClick={() => setComponentPage((current) => current + 1)}>Proxima</button>
              </div>
            ) : null}
          </>
        ) : (
          <div className="alert alert--info">Selecione uma matriz na tabela acima para cadastrar componentes e controlar pre-requisitos/equivalencias.</div>
        )}

        {componenteFormVisible && selectedMatrizId ? (
          <EntityFormPanel
            title={creatingComponente ? 'Cadastrar componente SICA' : 'Editar componente SICA'}
            subtitle="Defina periodo, carga horaria, ementa, pre-requisitos e equivalencias."
            onSubmit={(event) => {
              event.preventDefault()

              if (!componenteForm.componente.trim() || !componenteForm.periodo || !componenteForm.carga_horaria) {
                toast.error('Informe periodo, componente e carga horaria.')
                return
              }

              saveComponenteMutation.mutate({
                id: editingComponenteId || undefined,
                payload: {
                  matriz: Number(selectedMatrizId),
                  periodo: Number(componenteForm.periodo),
                  componente: componenteForm.componente.trim(),
                  tipo: componenteForm.tipo,
                  carga_horaria: Number(componenteForm.carga_horaria),
                  ementa: componenteForm.ementa.trim(),
                  prerequisitos: componenteForm.prerequisitos.map((value) => Number(value)),
                  equivalencias: componenteForm.equivalencias.map((value) => Number(value)),
                },
              })
            }}
            onCancel={() => {
              setCreatingComponente(false)
              setEditingComponenteId(null)
              setComponenteForm(EMPTY_COMPONENTE_FORM)
            }}
            submitLabel={creatingComponente ? 'Cadastrar componente' : 'Salvar componente'}
            isSubmitting={saveComponenteMutation.isPending}
          >
            <div className="form-field">
              <label htmlFor="sica-componente-periodo">Periodo</label>
              <input
                id="sica-componente-periodo"
                type="number"
                min="1"
                className="form-control"
                value={componenteForm.periodo}
                onChange={(event) => setComponenteForm((current) => ({ ...current, periodo: event.target.value }))}
              />
            </div>

            <div className="form-field">
              <label htmlFor="sica-componente-tipo">Tipo</label>
              <select
                id="sica-componente-tipo"
                className="select"
                value={componenteForm.tipo}
                onChange={(event) => setComponenteForm((current) => ({ ...current, tipo: event.target.value }))}
              >
                {COMPONENTE_TIPO_OPTIONS.map((option) => (
                  <option key={option.value} value={option.value}>{option.label}</option>
                ))}
              </select>
            </div>

            <div className="form-field form-field--full">
              <label htmlFor="sica-componente-nome">Componente</label>
              <input
                id="sica-componente-nome"
                className="form-control"
                value={componenteForm.componente}
                onChange={(event) => setComponenteForm((current) => ({ ...current, componente: event.target.value }))}
              />
            </div>

            <div className="form-field">
              <label htmlFor="sica-componente-carga">Carga horaria</label>
              <input
                id="sica-componente-carga"
                type="number"
                min="1"
                className="form-control"
                value={componenteForm.carga_horaria}
                onChange={(event) => setComponenteForm((current) => ({ ...current, carga_horaria: event.target.value }))}
              />
            </div>

            <div className="form-field form-field--full">
              <label htmlFor="sica-componente-ementa">Ementa</label>
              <textarea
                id="sica-componente-ementa"
                className="form-control"
                rows={4}
                value={componenteForm.ementa}
                onChange={(event) => setComponenteForm((current) => ({ ...current, ementa: event.target.value }))}
              />
            </div>

            <MultiSelectField
              id="sica-componente-prerequisitos"
              label="Pre-requisito"
              value={componenteForm.prerequisitos}
              options={relacionamentoOptions}
              onChange={(value) => setComponenteForm((current) => ({ ...current, prerequisitos: value }))}
            />

            <MultiSelectField
              id="sica-componente-equivalencias"
              label="Equivalencia"
              value={componenteForm.equivalencias}
              options={relacionamentoOptions}
              onChange={(value) => setComponenteForm((current) => ({ ...current, equivalencias: value }))}
            />
          </EntityFormPanel>
        ) : null}
      </section>
    </div>
  )
}
