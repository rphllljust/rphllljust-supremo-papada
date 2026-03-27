import { useEffect, useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Eye, Pencil, Plus, Trash2 } from 'lucide-react'
import toast from 'react-hot-toast'

import { certificadosApi, cursosApi, unidadesApi } from '@/api/endpoints'
import ModeloCertificadoForm from '@/components/certificados/ModeloCertificadoForm'
import DataTable from '@/components/ui/DataTable'
import EntityDetailsPanel from '@/components/ui/EntityDetailsPanel'

const COLUMNS = [
  { key: 'nome', label: 'Modelo' },
  { key: 'tipo', label: 'Tipo' },
  { key: 'curso_nome', label: 'Curso' },
  { key: 'unidade_nome', label: 'Unidade' },
  {
    key: 'ativo',
    label: 'Ativo',
    render: (row) => (row.ativo ? 'Sim' : 'Nao'),
  },
]

function buildDefaultForm() {
  return {
    nome: '',
    descricao: '',
    tipo: 'CERTIFICADO',
    curso: null,
    unidade: null,
    template_html: '',
    stylesheet_css: '',
    texto_certificado: '',
    ativo: true,
    assinaturas: [
      { nome: '', cargo: '', ordem: 1, ativo: true },
      { nome: '', cargo: '', ordem: 2, ativo: true },
    ],
    configuracao_visual: {
      nome_da_instituicao: 'Instituto Estadual de Desenvolvimento da Educacao Profissional de Rondonia',
      sigla_instituicao: 'IDEP',
      brasao_instituicao: '',
      logo_instituicao: '',
      logos_rodape: [],
      marca_dagua: '',
      cidade_padrao: 'Porto Velho',
      estado_padrao: 'RO',
    },
  }
}

function getErrorMessage(error, fallback) {
  const data = error?.response?.data
  if (!data) return fallback
  if (typeof data.detail === 'string') return data.detail
  const firstValue = Object.values(data)[0]
  return Array.isArray(firstValue) ? firstValue[0] : (firstValue || fallback)
}

function normalizeUrls(urls) {
  if (!Array.isArray(urls)) return []
  return urls
    .map((item) => String(item || '').trim())
    .filter(Boolean)
}

function normalizeAssinaturas(assinaturas) {
  if (!Array.isArray(assinaturas)) return []

  return assinaturas
    .map((assinatura, index) => ({
      id: assinatura.id || undefined,
      nome: String(assinatura.nome || '').trim(),
      cargo: String(assinatura.cargo || '').trim(),
      ordem: Number(assinatura.ordem || index + 1),
      ativo: assinatura.ativo !== false,
    }))
    .filter((assinatura) => assinatura.nome && assinatura.cargo)
}

function mapModeloToForm(modelo) {
  const defaultForm = buildDefaultForm()

  const assinaturas = normalizeAssinaturas(modelo.assinaturas || [])
  return {
    nome: modelo.nome || '',
    descricao: modelo.descricao || '',
    tipo: modelo.tipo || 'CERTIFICADO',
    curso: modelo.curso || null,
    unidade: modelo.unidade || null,
    template_html: modelo.template_html || '',
    stylesheet_css: modelo.stylesheet_css || '',
    texto_certificado: modelo.texto_certificado || '',
    ativo: Boolean(modelo.ativo),
    assinaturas: assinaturas.length > 0 ? assinaturas : defaultForm.assinaturas,
    configuracao_visual: {
      nome_da_instituicao: modelo.configuracao_visual?.nome_da_instituicao || defaultForm.configuracao_visual.nome_da_instituicao,
      sigla_instituicao: modelo.configuracao_visual?.sigla_instituicao || defaultForm.configuracao_visual.sigla_instituicao,
      brasao_instituicao: modelo.configuracao_visual?.brasao_instituicao || '',
      logo_instituicao: modelo.configuracao_visual?.logo_instituicao || '',
      logos_rodape: normalizeUrls(modelo.configuracao_visual?.logos_rodape || []),
      marca_dagua: modelo.configuracao_visual?.marca_dagua || '',
      cidade_padrao: modelo.configuracao_visual?.cidade_padrao || 'Porto Velho',
      estado_padrao: modelo.configuracao_visual?.estado_padrao || 'RO',
    },
  }
}

export default function ModelosCertificadosPage() {
  const queryClient = useQueryClient()
  const [search, setSearch] = useState('')
  const [page, setPage] = useState(1)
  const [selectedId, setSelectedId] = useState(null)
  const [editingId, setEditingId] = useState(null)
  const [isCreating, setIsCreating] = useState(false)
  const [formData, setFormData] = useState(buildDefaultForm)

  const { data, isLoading, isError } = useQuery({
    queryKey: ['certificados-modelos', { search, page }],
    queryFn: () => certificadosApi.modelos.list({ search, page }).then((response) => response.data),
    staleTime: 30_000,
  })

  const { data: selectedItem } = useQuery({
    queryKey: ['certificados-modelo', selectedId],
    queryFn: () => certificadosApi.modelos.get(selectedId).then((response) => response.data),
    enabled: Boolean(selectedId),
    staleTime: 30_000,
  })

  const { data: editingItem } = useQuery({
    queryKey: ['certificados-modelo-edit', editingId],
    queryFn: () => certificadosApi.modelos.get(editingId).then((response) => response.data),
    enabled: Boolean(editingId),
    staleTime: 0,
  })

  const { data: cursosData } = useQuery({
    queryKey: ['cursos-modelo-certificado'],
    queryFn: () => cursosApi.list({ page_size: 200 }).then((response) => response.data),
    staleTime: 60_000,
  })

  const { data: unidadesData } = useQuery({
    queryKey: ['unidades-modelo-certificado'],
    queryFn: () => unidadesApi.list({ page_size: 200 }).then((response) => response.data),
    staleTime: 60_000,
  })

  const cursos = useMemo(() => cursosData?.results || [], [cursosData])
  const unidades = useMemo(() => unidadesData?.results || [], [unidadesData])

  const saveMutation = useMutation({
    mutationFn: ({ id, payload }) => (id
      ? certificadosApi.modelos.update(id, payload)
      : certificadosApi.modelos.create(payload)),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['certificados-modelos'] })
      toast.success(editingId ? 'Modelo atualizado com sucesso.' : 'Modelo criado com sucesso.')
      setEditingId(null)
      setIsCreating(false)
      setFormData(buildDefaultForm())
    },
    onError: (error) => toast.error(getErrorMessage(error, 'Nao foi possivel salvar o modelo.')),
  })

  const deleteMutation = useMutation({
    mutationFn: (id) => certificadosApi.modelos.remove(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['certificados-modelos'] })
      toast.success('Modelo removido com sucesso.')
      if (selectedId) setSelectedId(null)
    },
    onError: (error) => toast.error(getErrorMessage(error, 'Nao foi possivel remover o modelo.')),
  })

  useEffect(() => {
    if (editingItem && editingId && !isCreating) {
      setFormData(mapModeloToForm(editingItem))
    }
  }, [editingItem, editingId, isCreating])

  const rows = data?.results || []

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <h1 className="page-title">Modelos de Certificado</h1>
          <p className="page-subtitle">Gestao de layouts, texto oficial, assinaturas e identidade institucional.</p>
        </div>
        <div className="page-header__actions">
          <button
            type="button"
            className="btn btn--primary"
            onClick={() => {
              setIsCreating(true)
              setEditingId(null)
              setFormData(buildDefaultForm())
            }}
          >
            <Plus size={16} /> Novo modelo
          </button>
        </div>
      </div>

      {isError ? <div className="alert alert--error">Nao foi possivel carregar os modelos de certificado.</div> : null}

      <DataTable
        columns={COLUMNS}
        data={{ ...data, results: rows }}
        isLoading={isLoading}
        onSearch={(value) => {
          setSearch(value)
          setPage(1)
        }}
        searchPlaceholder="Buscar por nome, descricao ou slug..."
        emptyMessage="Nenhum modelo encontrado."
        rowActions={(row) => (
          <div className="table-actions">
            <button type="button" className="btn btn--outline btn--sm" onClick={() => setSelectedId(row.id)}>
              <Eye size={14} /> Visualizar
            </button>
            <button
              type="button"
              className="btn btn--secondary btn--sm"
              onClick={() => {
                setIsCreating(false)
                setEditingId(row.id)
                setSelectedId(null)
              }}
            >
              <Pencil size={14} /> Editar
            </button>
            <button
              type="button"
              className="btn btn--danger btn--sm"
              onClick={() => window.confirm(`Remover o modelo "${row.nome}"?`) && deleteMutation.mutate(row.id)}
            >
              <Trash2 size={14} /> Excluir
            </button>
          </div>
        )}
      />

      {data ? (
        <div className="pagination">
          <button className="btn btn--secondary" disabled={!data.previous} onClick={() => setPage((current) => current - 1)}>
            Anterior
          </button>
          <span className="pagination__info">Pagina {page} - {data.count || 0} registros</span>
          <button className="btn btn--secondary" disabled={!data.next} onClick={() => setPage((current) => current + 1)}>
            Proxima
          </button>
        </div>
      ) : null}

      {selectedId && selectedItem ? (
        <EntityDetailsPanel
          title={selectedItem.nome}
          subtitle={selectedItem.descricao || 'Detalhes do modelo de certificado'}
          fields={[
            { label: 'Tipo', value: selectedItem.tipo },
            { label: 'Curso', value: selectedItem.curso_nome || 'Todos' },
            { label: 'Unidade', value: selectedItem.unidade_nome || 'Todas' },
            { label: 'Ativo', value: selectedItem.ativo ? 'Sim' : 'Nao' },
            { label: 'Sigla institucional', value: selectedItem.configuracao_visual?.sigla_instituicao || '-' },
            { label: 'Instituicao', value: selectedItem.configuracao_visual?.nome_da_instituicao || '-' },
            { label: 'Assinaturas ativas', value: String((selectedItem.assinaturas || []).filter((item) => item.ativo).length) },
          ]}
          onClose={() => setSelectedId(null)}
        />
      ) : null}

      {(isCreating || editingId) ? (
        <ModeloCertificadoForm
          formData={formData}
          setFormData={setFormData}
          cursos={cursos}
          unidades={unidades}
          onCancel={() => {
            setIsCreating(false)
            setEditingId(null)
            setFormData(buildDefaultForm())
          }}
          onSubmit={(event) => {
            event.preventDefault()

            const assinaturasNormalizadas = normalizeAssinaturas(formData.assinaturas)
            if (assinaturasNormalizadas.length < 2) {
              toast.error('Informe pelo menos duas assinaturas validas (nome e cargo).')
              return
            }

            saveMutation.mutate({
              id: editingId || null,
              payload: {
                ...formData,
                curso: formData.curso || null,
                unidade: formData.unidade || null,
                assinaturas: assinaturasNormalizadas,
                configuracao_visual: {
                  ...formData.configuracao_visual,
                  logos_rodape: normalizeUrls(formData.configuracao_visual.logos_rodape),
                },
              },
            })
          }}
          isSubmitting={saveMutation.isPending}
          submitLabel={editingId ? 'Salvar alteracoes' : 'Criar modelo'}
        />
      ) : null}
    </div>
  )
}
