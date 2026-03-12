import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { ArrowLeft } from 'lucide-react'
import toast from 'react-hot-toast'
import { Link, useNavigate } from 'react-router-dom'

import { guardaApi, matriculasApi, processosApi } from '@/api/endpoints'
import EntityFormPanel from '@/components/ui/EntityFormPanel'
import SearchableRemoteSelect from '@/components/ui/SearchableRemoteSelect'

const STATUS_OPTIONS = [
  { value: 'ATIVO', label: 'Ativo' },
  { value: 'EMPRESTADO', label: 'Emprestado' },
  { value: 'ELIMINADO', label: 'Eliminado' },
]

const TIPO_OPTIONS = [
  { value: 'PASTA_ALUNO', label: 'Pasta do Aluno' },
  { value: 'PROCESSO', label: 'Processo Administrativo' },
  { value: 'CONTRATO', label: 'Contrato' },
  { value: 'ATA', label: 'Ata' },
  { value: 'DECLARACAO', label: 'Declaração' },
  { value: 'HISTORICO', label: 'Histórico Escolar' },
  { value: 'OUTROS', label: 'Outros' },
]

const DEFAULT_FORM = {
  tipo_documento: 'PASTA_ALUNO',
  descricao: '',
  numero_caixa: '',
  localizacao: '',
  data_eliminacao_prevista: '',
  status: 'ATIVO',
  matricula: '',
  processo: '',
}

function getErrorMessage(error, fallback) {
  const data = error?.response?.data
  if (!data) return fallback
  if (typeof data.detail === 'string') return data.detail
  const firstValue = Object.values(data)[0]
  return Array.isArray(firstValue) ? firstValue[0] : (firstValue || fallback)
}

export default function GuardaCreatePage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [formData, setFormData] = useState(DEFAULT_FORM)
  const [matriculaSearch, setMatriculaSearch] = useState('')
  const [processoSearch, setProcessoSearch] = useState('')

  const { data: matriculasData } = useQuery({
    queryKey: ['matriculas', 'guarda-options', matriculaSearch],
    queryFn: () => matriculasApi.list({ page_size: 10, search: matriculaSearch || undefined }).then((response) => response.data),
    staleTime: 60_000,
  })

  const { data: processosData } = useQuery({
    queryKey: ['processos', 'guarda-options', processoSearch],
    queryFn: () => processosApi.list({ page_size: 10, search: processoSearch || undefined }).then((response) => response.data),
    staleTime: 60_000,
  })

  const saveMutation = useMutation({
    mutationFn: (payload) => guardaApi.create(payload),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['guarda'] })
      toast.success('Registro arquivado com sucesso.')
      navigate('/arquivo')
    },
    onError: (error) => toast.error(getErrorMessage(error, 'Não foi possível salvar o registro documental.')),
  })

  const matriculas = matriculasData?.results || []
  const processos = processosData?.results || []

  return (
    <div className="page page--wide">
      <nav className="profile-breadcrumb">
        <Link to="/dashboard">Início</Link>
        <span className="profile-breadcrumb__sep">&gt;</span>
        <Link to="/arquivo">Arquivo / Guarda Documental</Link>
        <span className="profile-breadcrumb__sep">&gt;</span>
        <span>Arquivar Documento</span>
      </nav>

      <div className="page-header">
        <div>
          <h1 className="page-title">Arquivar documento</h1>
          <p className="page-subtitle">A abertura do registro documental agora fica em uma página própria.</p>
        </div>
        <div className="page-header__actions">
          <button type="button" className="btn btn--outline" onClick={() => navigate('/arquivo')}>
            <ArrowLeft size={16} /> Voltar para arquivo
          </button>
        </div>
      </div>

      <EntityFormPanel
        title="Arquivar documento"
        subtitle="Defina o tipo, a identificação física e os vínculos opcionais do registro documental."
        onSubmit={(event) => {
          event.preventDefault()

          if (!formData.tipo_documento || !formData.descricao.trim()) {
            toast.error('Informe o tipo e a descrição do documento.')
            return
          }

          saveMutation.mutate({
            tipo_documento: formData.tipo_documento,
            descricao: formData.descricao.trim(),
            numero_caixa: formData.numero_caixa.trim(),
            localizacao: formData.localizacao.trim(),
            data_eliminacao_prevista: formData.data_eliminacao_prevista || null,
            status: formData.status,
            matricula: formData.matricula ? Number(formData.matricula) : null,
            processo: formData.processo ? Number(formData.processo) : null,
          })
        }}
        onCancel={() => navigate('/arquivo')}
        submitLabel="Arquivar"
        isSubmitting={saveMutation.isPending}
      >
        <div className="form-field">
          <label htmlFor="guarda-tipo">Tipo de documento</label>
          <select id="guarda-tipo" className="select" value={formData.tipo_documento} onChange={(event) => setFormData((current) => ({ ...current, tipo_documento: event.target.value }))}>
            {TIPO_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>{option.label}</option>
            ))}
          </select>
        </div>

        <div className="form-field">
          <label htmlFor="guarda-status">Status</label>
          <select id="guarda-status" className="select" value={formData.status} onChange={(event) => setFormData((current) => ({ ...current, status: event.target.value }))}>
            {STATUS_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>{option.label}</option>
            ))}
          </select>
        </div>

        <div className="form-field form-field--full">
          <label htmlFor="guarda-descricao">Descrição</label>
          <input id="guarda-descricao" className="form-control" value={formData.descricao} onChange={(event) => setFormData((current) => ({ ...current, descricao: event.target.value }))} />
        </div>

        <div className="form-field">
          <label htmlFor="guarda-numero-caixa">Número da caixa</label>
          <input id="guarda-numero-caixa" className="form-control" value={formData.numero_caixa} onChange={(event) => setFormData((current) => ({ ...current, numero_caixa: event.target.value }))} />
        </div>

        <div className="form-field">
          <label htmlFor="guarda-localizacao">Localização</label>
          <input id="guarda-localizacao" className="form-control" value={formData.localizacao} onChange={(event) => setFormData((current) => ({ ...current, localizacao: event.target.value }))} />
        </div>

        <div className="form-field">
          <label htmlFor="guarda-data-eliminacao">Data de eliminação prevista</label>
          <input id="guarda-data-eliminacao" type="date" className="form-control" value={formData.data_eliminacao_prevista} onChange={(event) => setFormData((current) => ({ ...current, data_eliminacao_prevista: event.target.value }))} />
        </div>

        <SearchableRemoteSelect
          id="guarda-matricula"
          label="Matrícula vinculada"
          searchLabel="Buscar matrícula"
          searchPlaceholder="Digite número, aluno ou curso"
          searchValue={matriculaSearch}
          onSearchChange={setMatriculaSearch}
          value={formData.matricula}
          onChange={(nextValue) => setFormData((current) => ({ ...current, matricula: nextValue }))}
          options={matriculas}
          getOptionLabel={(item) => `${item.numero_matricula} - ${item.aluno_nome || ''}`.trim()}
          emptyOptionLabel="Não vincular"
        />

        <SearchableRemoteSelect
          id="guarda-processo"
          label="Processo vinculado"
          searchLabel="Buscar processo"
          searchPlaceholder="Digite número ou assunto"
          searchValue={processoSearch}
          onSearchChange={setProcessoSearch}
          value={formData.processo}
          onChange={(nextValue) => setFormData((current) => ({ ...current, processo: nextValue }))}
          options={processos}
          getOptionLabel={(item) => `${item.numero} - ${item.assunto || ''}`.trim()}
          emptyOptionLabel="Não vincular"
        />
      </EntityFormPanel>
    </div>
  )
}
