import { useEffect, useMemo, useState } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'
import { useNavigate, useParams } from 'react-router-dom'
import toast from 'react-hot-toast'
import { Minus, Paperclip, Plus } from 'lucide-react'

import { atasProfessoresApi, processosApi } from '@/api/endpoints'
import EntityFormPanel from '@/components/ui/EntityFormPanel'

const TIPO_REUNIAO_OPTIONS = [
  { value: 'CONSELHO_ESCOLAR', label: 'Conselho Escolar' },
  { value: 'CONSELHO_CLASSE', label: 'Conselho de Classe' },
  { value: 'REUNIAO_PEDAGOGICA', label: 'Reuniao Pedagogica' },
  { value: 'REUNIAO_ADMINISTRATIVA', label: 'Reuniao Administrativa' },
  { value: 'OUTRO', label: 'Outro' },
]

const MODALIDADE_OPTIONS = [
  { value: 'PRESENCIAL', label: 'Presencial' },
  { value: 'ONLINE', label: 'Online' },
  { value: 'HIBRIDA', label: 'Hibrida' },
]

const TIPO_ANEXO_OPTIONS = [
  { value: 'LISTA_PRESENCA', label: 'Lista de presenca' },
  { value: 'RELATORIO', label: 'Relatorio' },
  { value: 'FOTOS', label: 'Fotos' },
  { value: 'PRINTS', label: 'Prints' },
  { value: 'OUTROS', label: 'Outros' },
]

const DEFAULT_TEXT_FINAL = 'Nada mais havendo a tratar, deu-se por encerrada a reuniao. Eu, [responsavel], lavrei a presente ata, que apos lida e aprovada, segue assinada eletronicamente pelos participantes.'

function createParticipant() {
  return { nome: '', cargo: '' }
}

function createTextItem() {
  return { texto: '' }
}

function createAttachment() {
  return { id: null, tipo: 'OUTROS', descricao: '', file: null, arquivo_nome: '', arquivo_url: '' }
}

function getErrorMessage(error, fallback) {
  const data = error?.response?.data
  if (!data) {
    return fallback
  }

  if (typeof data.detail === 'string') {
    return data.detail
  }

  const firstEntry = Object.values(data)[0]
  if (Array.isArray(firstEntry)) {
    return firstEntry[0]
  }

  return firstEntry || fallback
}

function DynamicSection({ title, description, items, onAdd, onRemove, renderItem }) {
  return (
    <section className="assistant-section">
      <div className="assistant-section__header">
        <div>
          <h3 className="assistant-section__title">{title}</h3>
          {description ? <p className="assistant-section__description">{description}</p> : null}
        </div>
        <button type="button" className="btn btn--outline btn--sm" onClick={onAdd}>
          <Plus size={14} /> Adicionar
        </button>
      </div>

      <div className="assistant-section__list">
        {items.map((item, index) => (
          <div key={index} className="assistant-item-card">
            <div className="assistant-item-card__content">
              {renderItem(item, index)}
            </div>
            {items.length > 1 ? (
              <button type="button" className="btn btn--danger btn--sm" onClick={() => onRemove(index)}>
                <Minus size={14} /> Remover
              </button>
            ) : null}
          </div>
        ))}
      </div>
    </section>
  )
}

export default function AtaProfessoresAssistantPage() {
  const navigate = useNavigate()
  const { ataId } = useParams()
  const isEditing = Boolean(ataId)
  const [formData, setFormData] = useState({
    numero_ata: '',
    ano: String(new Date().getFullYear()),
    tipo_reuniao_registro: '',
    tipo_reuniao_outro: '',
    livro: '',
    folha_pagina: '',
    processo: '',
    data_reuniao: '',
    horario_inicio: '',
    horario_termino: '',
    local_reuniao: '',
    modalidade: '',
    plataforma: '',
    link_reuniao: '',
    cidade_uf: '',
    presidente_reuniao: '',
    responsavel_lavratura: '',
    horario_encerramento: '',
    texto_final: DEFAULT_TEXT_FINAL,
    forma_assinatura: '',
    assunto: '',
    observacao: '',
  })
  const [participantes, setParticipantes] = useState([createParticipant()])
  const [pauta, setPauta] = useState([createTextItem()])
  const [deliberacoes, setDeliberacoes] = useState([createTextItem()])
  const [encaminhamentos, setEncaminhamentos] = useState([createTextItem()])
  const [assinaturas, setAssinaturas] = useState([createParticipant()])
  const [anexos, setAnexos] = useState([createAttachment()])

  const { data: processosData } = useQuery({
    queryKey: ['processos', 'assistant-options'],
    queryFn: () => processosApi.list({ page_size: 100 }).then((response) => response.data),
    staleTime: 60_000,
  })

  const { data: ataData, isLoading: isLoadingAta } = useQuery({
    queryKey: ['ata-professores-edit', ataId],
    queryFn: () => atasProfessoresApi.get(ataId).then((response) => response.data),
    enabled: isEditing,
    staleTime: 0,
  })

  useEffect(() => {
    if (!ataData) {
      return
    }

    setFormData({
      numero_ata: ataData.numero_ata || '',
      ano: String(ataData.ano || new Date().getFullYear()),
      tipo_reuniao_registro: ataData.tipo_reuniao_registro || '',
      tipo_reuniao_outro: ataData.tipo_reuniao_outro || '',
      livro: ataData.livro || '',
      folha_pagina: ataData.folha_pagina || '',
      processo: ataData.processo ? String(ataData.processo) : '',
      data_reuniao: ataData.data_reuniao || '',
      horario_inicio: ataData.horario_inicio || '',
      horario_termino: ataData.horario_termino || '',
      local_reuniao: ataData.local_reuniao || '',
      modalidade: ataData.modalidade || '',
      plataforma: ataData.plataforma || '',
      link_reuniao: ataData.link_reuniao || '',
      cidade_uf: ataData.cidade_uf || '',
      presidente_reuniao: ataData.presidente_reuniao || '',
      responsavel_lavratura: ataData.responsavel_lavratura || '',
      horario_encerramento: ataData.horario_encerramento || '',
      texto_final: ataData.texto_final || DEFAULT_TEXT_FINAL,
      forma_assinatura: ataData.forma_assinatura || '',
      assunto: ataData.assunto || '',
      observacao: ataData.observacao || '',
    })
    setParticipantes(ataData.participantes?.length ? ataData.participantes : [createParticipant()])
    setPauta(ataData.pauta?.length ? ataData.pauta : [createTextItem()])
    setDeliberacoes(ataData.deliberacoes?.length ? ataData.deliberacoes : [createTextItem()])
    setEncaminhamentos(ataData.encaminhamentos?.length ? ataData.encaminhamentos : [createTextItem()])
    setAssinaturas(ataData.assinaturas?.length ? ataData.assinaturas : [createParticipant()])
    setAnexos(
      ataData.anexos?.length
        ? ataData.anexos.map((anexo) => ({
            id: anexo.id,
            tipo: anexo.tipo_anexo,
            descricao: anexo.descricao || '',
            file: null,
            arquivo_nome: anexo.arquivo_nome || '',
            arquivo_url: anexo.arquivo_url || '',
          }))
        : [createAttachment()]
    )
  }, [ataData])

  const processOptions = processosData?.results || []
  const isReadOnly = Boolean(isEditing && ataData?.situacao === 'EMITIDO')

  const saveMutation = useMutation({
    mutationFn: async ({ action }) => {
      const body = new FormData()
      Object.entries(formData).forEach(([key, value]) => {
        body.append(key, value ?? '')
      })
      body.append('acao', action)
      body.append('participantes', JSON.stringify(participantes.filter((item) => Object.values(item).some(Boolean))))
      body.append('pauta', JSON.stringify(pauta.filter((item) => item.texto?.trim()).map((item) => item.texto.trim())))
      body.append('deliberacoes', JSON.stringify(deliberacoes.filter((item) => item.texto?.trim()).map((item) => item.texto.trim())))
      body.append('encaminhamentos', JSON.stringify(encaminhamentos.filter((item) => item.texto?.trim()).map((item) => item.texto.trim())))
      body.append('assinaturas', JSON.stringify(assinaturas.filter((item) => Object.values(item).some(Boolean))))

      const anexosMetadata = anexos
        .filter((item) => item.id || item.file || item.descricao?.trim())
        .map((item, index) => {
          if (item.file) {
            body.append(`anexo_arquivo_${index}`, item.file)
          }
          return {
            id: item.id,
            tipo: item.tipo,
            descricao: item.descricao,
          }
        })

      body.append('anexos_metadata', JSON.stringify(anexosMetadata))

      if (isEditing) {
        return atasProfessoresApi.update(ataId, body)
      }

      return atasProfessoresApi.create(body)
    },
    onSuccess: (response, variables) => {
      const ata = response.data
      toast.success(variables.action === 'emitir' ? 'Ata emitida com sucesso.' : 'Rascunho salvo com sucesso.')
      navigate(`/ata-professores?ata=${ata.id}`, { replace: true })
    },
    onError: (error) => {
      toast.error(getErrorMessage(error, 'Nao foi possivel salvar a ata.'))
    },
  })

  const updateField = (field, value) => {
    setFormData((current) => ({ ...current, [field]: value }))
  }

  const updateCollectionItem = (setter, items, index, field, value) => {
    const nextItems = items.map((item, itemIndex) => (itemIndex === index ? { ...item, [field]: value } : item))
    setter(nextItems)
  }

  const addCollectionItem = (setter, factory) => setter((current) => [...current, factory()])
  const removeCollectionItem = (setter, index) => setter((current) => current.filter((_, currentIndex) => currentIndex !== index))

  const pageTitle = useMemo(() => (isEditing ? 'Editar Ata dos Professores' : 'Assistente de Emissao de Ata'), [isEditing])

  if (isEditing && isLoadingAta) {
    return (
      <div className="page-loader" role="status" aria-live="polite">
        <div className="spinner" />
        <span>Carregando assistente...</span>
      </div>
    )
  }

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <h1 className="page-title">{pageTitle}</h1>
          <p className="page-subtitle">Fluxo portado do assistente legado de atas</p>
        </div>
      </div>

      {isReadOnly ? (
        <div className="alert alert--error">
          Esta ata ja foi emitida e esta em modo somente leitura. Volte para a listagem para consultá-la.
        </div>
      ) : null}

      <EntityFormPanel
        title={isEditing ? 'Dados principais da ata' : 'Nova ata escolar'}
        subtitle="Preencha os dados basicos e use os blocos abaixo para participantes, pauta, deliberacoes, encaminhamentos, assinaturas e anexos."
        onSubmit={(event) => {
          event.preventDefault()
          saveMutation.mutate({ action: 'rascunho' })
        }}
        onCancel={() => navigate('/ata-professores')}
        submitLabel="Salvar rascunho"
        isSubmitting={saveMutation.isPending || isReadOnly}
      >
        <div className="form-field">
          <label htmlFor="ata-numero">Numero da ata</label>
          <input id="ata-numero" type="text" value={formData.numero_ata} onChange={(event) => updateField('numero_ata', event.target.value)} disabled={isReadOnly} />
        </div>
        <div className="form-field">
          <label htmlFor="ata-ano">Ano</label>
          <input id="ata-ano" type="number" value={formData.ano} onChange={(event) => updateField('ano', event.target.value)} disabled={isReadOnly} />
        </div>
        <div className="form-field">
          <label htmlFor="ata-assunto">Assunto</label>
          <input id="ata-assunto" type="text" value={formData.assunto} onChange={(event) => updateField('assunto', event.target.value)} disabled={isReadOnly} />
        </div>
        <div className="form-field">
          <label htmlFor="ata-processo">Processo vinculado</label>
          <select id="ata-processo" className="select" value={formData.processo} onChange={(event) => updateField('processo', event.target.value)} disabled={isReadOnly}>
            <option value="">Sem processo</option>
            {processOptions.map((processo) => (
              <option key={processo.id} value={processo.id}>{processo.numero} - {processo.assunto}</option>
            ))}
          </select>
        </div>
        <div className="form-field">
          <label htmlFor="ata-tipo-reuniao">Tipo de reuniao</label>
          <select id="ata-tipo-reuniao" className="select" value={formData.tipo_reuniao_registro} onChange={(event) => updateField('tipo_reuniao_registro', event.target.value)} disabled={isReadOnly}>
            <option value="">Selecione</option>
            {TIPO_REUNIAO_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>{option.label}</option>
            ))}
          </select>
        </div>
        {formData.tipo_reuniao_registro === 'OUTRO' ? (
          <div className="form-field">
            <label htmlFor="ata-tipo-outro">Outro tipo de reuniao</label>
            <input id="ata-tipo-outro" type="text" value={formData.tipo_reuniao_outro} onChange={(event) => updateField('tipo_reuniao_outro', event.target.value)} disabled={isReadOnly} />
          </div>
        ) : null}
        <div className="form-field">
          <label htmlFor="ata-data">Data da reuniao</label>
          <input id="ata-data" type="date" value={formData.data_reuniao} onChange={(event) => updateField('data_reuniao', event.target.value)} disabled={isReadOnly} />
        </div>
        <div className="form-field">
          <label htmlFor="ata-hora-inicio">Horario de inicio</label>
          <input id="ata-hora-inicio" type="time" value={formData.horario_inicio} onChange={(event) => updateField('horario_inicio', event.target.value)} disabled={isReadOnly} />
        </div>
        <div className="form-field">
          <label htmlFor="ata-hora-fim">Horario de termino</label>
          <input id="ata-hora-fim" type="time" value={formData.horario_termino} onChange={(event) => updateField('horario_termino', event.target.value)} disabled={isReadOnly} />
        </div>
        <div className="form-field">
          <label htmlFor="ata-hora-encerramento">Horario de encerramento</label>
          <input id="ata-hora-encerramento" type="time" value={formData.horario_encerramento} onChange={(event) => updateField('horario_encerramento', event.target.value)} disabled={isReadOnly} />
        </div>
        <div className="form-field">
          <label htmlFor="ata-local">Local</label>
          <input id="ata-local" type="text" value={formData.local_reuniao} onChange={(event) => updateField('local_reuniao', event.target.value)} disabled={isReadOnly} />
        </div>
        <div className="form-field">
          <label htmlFor="ata-modalidade">Modalidade</label>
          <select id="ata-modalidade" className="select" value={formData.modalidade} onChange={(event) => updateField('modalidade', event.target.value)} disabled={isReadOnly}>
            <option value="">Selecione</option>
            {MODALIDADE_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>{option.label}</option>
            ))}
          </select>
        </div>
        <div className="form-field">
          <label htmlFor="ata-plataforma">Plataforma</label>
          <input id="ata-plataforma" type="text" value={formData.plataforma} onChange={(event) => updateField('plataforma', event.target.value)} disabled={isReadOnly} />
        </div>
        <div className="form-field">
          <label htmlFor="ata-link">Link da reuniao</label>
          <input id="ata-link" type="url" value={formData.link_reuniao} onChange={(event) => updateField('link_reuniao', event.target.value)} disabled={isReadOnly} />
        </div>
        <div className="form-field">
          <label htmlFor="ata-cidade-uf">Cidade/UF</label>
          <input id="ata-cidade-uf" type="text" value={formData.cidade_uf} onChange={(event) => updateField('cidade_uf', event.target.value)} disabled={isReadOnly} />
        </div>
        <div className="form-field">
          <label htmlFor="ata-livro">Livro</label>
          <input id="ata-livro" type="text" value={formData.livro} onChange={(event) => updateField('livro', event.target.value)} disabled={isReadOnly} />
        </div>
        <div className="form-field">
          <label htmlFor="ata-folha">Folha/Pagina</label>
          <input id="ata-folha" type="text" value={formData.folha_pagina} onChange={(event) => updateField('folha_pagina', event.target.value)} disabled={isReadOnly} />
        </div>
        <div className="form-field">
          <label htmlFor="ata-presidente">Presidente/Coordenador(a)</label>
          <input id="ata-presidente" type="text" value={formData.presidente_reuniao} onChange={(event) => updateField('presidente_reuniao', event.target.value)} disabled={isReadOnly} />
        </div>
        <div className="form-field">
          <label htmlFor="ata-lavratura">Responsavel pela lavratura</label>
          <input id="ata-lavratura" type="text" value={formData.responsavel_lavratura} onChange={(event) => updateField('responsavel_lavratura', event.target.value)} disabled={isReadOnly} />
        </div>
        <div className="form-field">
          <label htmlFor="ata-forma-assinatura">Forma de assinatura</label>
          <input id="ata-forma-assinatura" type="text" value={formData.forma_assinatura} onChange={(event) => updateField('forma_assinatura', event.target.value)} disabled={isReadOnly} />
        </div>
        <div className="form-field form-field--full">
          <label htmlFor="ata-texto-final">Texto final</label>
          <textarea id="ata-texto-final" rows="4" value={formData.texto_final} onChange={(event) => updateField('texto_final', event.target.value)} disabled={isReadOnly} />
        </div>
        <div className="form-field form-field--full">
          <label htmlFor="ata-observacao">Observacoes internas</label>
          <textarea id="ata-observacao" rows="3" value={formData.observacao} onChange={(event) => updateField('observacao', event.target.value)} disabled={isReadOnly} />
        </div>
      </EntityFormPanel>

      <DynamicSection
        title="Participantes"
        description="Informe quem participou da reuniao."
        items={participantes}
        onAdd={() => addCollectionItem(setParticipantes, createParticipant)}
        onRemove={(index) => removeCollectionItem(setParticipantes, index)}
        renderItem={(item, index) => (
          <div className="assistant-grid assistant-grid--two">
            <div className="form-field">
              <label>Nome</label>
              <input type="text" value={item.nome || ''} onChange={(event) => updateCollectionItem(setParticipantes, participantes, index, 'nome', event.target.value)} disabled={isReadOnly} />
            </div>
            <div className="form-field">
              <label>Cargo/Funcao</label>
              <input type="text" value={item.cargo || ''} onChange={(event) => updateCollectionItem(setParticipantes, participantes, index, 'cargo', event.target.value)} disabled={isReadOnly} />
            </div>
          </div>
        )}
      />

      <DynamicSection
        title="Pauta"
        description="Liste os itens de pauta da reuniao."
        items={pauta}
        onAdd={() => addCollectionItem(setPauta, createTextItem)}
        onRemove={(index) => removeCollectionItem(setPauta, index)}
        renderItem={(item, index) => (
          <div className="form-field form-field--full">
            <label>Item de pauta</label>
            <textarea rows="3" value={item.texto || ''} onChange={(event) => updateCollectionItem(setPauta, pauta, index, 'texto', event.target.value)} disabled={isReadOnly} />
          </div>
        )}
      />

      <DynamicSection
        title="Deliberacoes"
        description="Registre as deliberacoes da reuniao."
        items={deliberacoes}
        onAdd={() => addCollectionItem(setDeliberacoes, createTextItem)}
        onRemove={(index) => removeCollectionItem(setDeliberacoes, index)}
        renderItem={(item, index) => (
          <div className="form-field form-field--full">
            <label>Deliberacao</label>
            <textarea rows="3" value={item.texto || ''} onChange={(event) => updateCollectionItem(setDeliberacoes, deliberacoes, index, 'texto', event.target.value)} disabled={isReadOnly} />
          </div>
        )}
      />

      <DynamicSection
        title="Encaminhamentos"
        description="Descreva os encaminhamentos definidos."
        items={encaminhamentos}
        onAdd={() => addCollectionItem(setEncaminhamentos, createTextItem)}
        onRemove={(index) => removeCollectionItem(setEncaminhamentos, index)}
        renderItem={(item, index) => (
          <div className="form-field form-field--full">
            <label>Encaminhamento</label>
            <textarea rows="3" value={item.texto || ''} onChange={(event) => updateCollectionItem(setEncaminhamentos, encaminhamentos, index, 'texto', event.target.value)} disabled={isReadOnly} />
          </div>
        )}
      />

      <DynamicSection
        title="Assinaturas"
        description="Informe os responsaveis que assinam a ata."
        items={assinaturas}
        onAdd={() => addCollectionItem(setAssinaturas, createParticipant)}
        onRemove={(index) => removeCollectionItem(setAssinaturas, index)}
        renderItem={(item, index) => (
          <div className="assistant-grid assistant-grid--two">
            <div className="form-field">
              <label>Nome</label>
              <input type="text" value={item.nome || ''} onChange={(event) => updateCollectionItem(setAssinaturas, assinaturas, index, 'nome', event.target.value)} disabled={isReadOnly} />
            </div>
            <div className="form-field">
              <label>Cargo/Funcao</label>
              <input type="text" value={item.cargo || ''} onChange={(event) => updateCollectionItem(setAssinaturas, assinaturas, index, 'cargo', event.target.value)} disabled={isReadOnly} />
            </div>
          </div>
        )}
      />

      <DynamicSection
        title="Anexos"
        description="Inclua anexos opcionais para a ata."
        items={anexos}
        onAdd={() => addCollectionItem(setAnexos, createAttachment)}
        onRemove={(index) => removeCollectionItem(setAnexos, index)}
        renderItem={(item, index) => (
          <div className="assistant-grid assistant-grid--attachment">
            <div className="form-field">
              <label>Tipo do anexo</label>
              <select className="select" value={item.tipo} onChange={(event) => updateCollectionItem(setAnexos, anexos, index, 'tipo', event.target.value)} disabled={isReadOnly}>
                {TIPO_ANEXO_OPTIONS.map((option) => (
                  <option key={option.value} value={option.value}>{option.label}</option>
                ))}
              </select>
            </div>
            <div className="form-field">
              <label>Descricao</label>
              <input type="text" value={item.descricao || ''} onChange={(event) => updateCollectionItem(setAnexos, anexos, index, 'descricao', event.target.value)} disabled={isReadOnly} />
            </div>
            <div className="form-field">
              <label>Arquivo</label>
              <input
                type="file"
                onChange={(event) => updateCollectionItem(setAnexos, anexos, index, 'file', event.target.files?.[0] || null)}
                disabled={isReadOnly}
              />
              {item.arquivo_nome ? (
                <span className="assistant-attachment-name">
                  <Paperclip size={14} />
                  {item.arquivo_url ? <a href={item.arquivo_url} target="_blank" rel="noreferrer">{item.arquivo_nome}</a> : item.arquivo_nome}
                </span>
              ) : null}
            </div>
          </div>
        )}
      />

      <div className="assistant-submit-bar">
        <button type="button" className="btn btn--secondary" onClick={() => navigate('/ata-professores')} disabled={saveMutation.isPending}>
          Voltar para listagem
        </button>
        <button type="button" className="btn btn--primary" onClick={() => saveMutation.mutate({ action: 'rascunho' })} disabled={saveMutation.isPending || isReadOnly}>
          {saveMutation.isPending ? 'Salvando...' : 'Salvar rascunho'}
        </button>
        <button type="button" className="btn btn--primary" onClick={() => saveMutation.mutate({ action: 'emitir' })} disabled={saveMutation.isPending || isReadOnly}>
          {saveMutation.isPending ? 'Emitindo...' : 'Emitir ata'}
        </button>
      </div>
    </div>
  )
}