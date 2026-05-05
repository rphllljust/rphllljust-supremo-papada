import { useEffect, useMemo, useState } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'
import { useNavigate, useParams } from 'react-router-dom'
import toast from 'react-hot-toast'
import { Minus, Paperclip, Plus } from 'lucide-react'

import { atasProfessoresApi, processosApi, unidadesApi } from '@/api/endpoints'
import SearchableRemoteSelect from '@/components/ui/SearchableRemoteSelect'

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

const SECTION_ITEMS = [
  { id: 'identificacao', label: '1. Identificacao' },
  { id: 'reuniao', label: '2. Dados da reuniao' },
  { id: 'participantes', label: '3. Participantes' },
  { id: 'pauta', label: '4. Pauta' },
  { id: 'deliberacoes', label: '5. Relato e deliberacoes' },
  { id: 'encaminhamentos', label: '6. Encaminhamentos' },
  { id: 'anexos', label: '7. Anexos' },
  { id: 'encerramento', label: '8. Encerramento e assinaturas' },
  { id: 'previa', label: '9. Previa da ata' },
]

function createParticipant() {
  return { nome: '', cargo: '', presente: true, justificativa: '' }
}

function createPautaItem() {
  return { titulo: '', descricao: '' }
}

function createDeliberacaoItem() {
  return { titulo: '', relato: '', decisao: '', responsavel: '', prazo: '', observacoes: '' }
}

function createEncaminhamentoItem() {
  return { descricao: '', responsavel: '', prazo: '' }
}

function createAssinaturaItem() {
  return { nome: '', cargo: '', tipo_assinatura: 'eletronica' }
}

function createAttachment() {
  return { id: null, tipo: 'OUTROS', descricao: '', file: null, arquivo_nome: '', arquivo_url: '' }
}

function normalizeParticipants(items) {
  if (!Array.isArray(items) || items.length === 0) return [createParticipant()]
  return items.map((item) => {
    if (typeof item === 'string') {
      return { ...createParticipant(), nome: item }
    }
    return {
      nome: item?.nome || '',
      cargo: item?.cargo || '',
      presente: item?.presente !== false,
      justificativa: item?.justificativa || '',
    }
  })
}

function normalizePauta(items) {
  if (!Array.isArray(items) || items.length === 0) return [createPautaItem()]
  return items.map((item) => {
    if (typeof item === 'string') {
      return { titulo: item, descricao: '' }
    }
    return {
      titulo: item?.titulo || item?.texto || '',
      descricao: item?.descricao || '',
    }
  })
}

function normalizeDeliberacoes(items) {
  if (!Array.isArray(items) || items.length === 0) return []
  return items.map((item) => {
    if (typeof item === 'string') {
      return { ...createDeliberacaoItem(), decisao: item }
    }
    return {
      titulo: item?.titulo || '',
      relato: item?.relato || item?.texto || '',
      decisao: item?.decisao || '',
      responsavel: item?.responsavel || '',
      prazo: item?.prazo || '',
      observacoes: item?.observacoes || '',
    }
  })
}

function normalizeEncaminhamentos(items) {
  if (!Array.isArray(items) || items.length === 0) return [createEncaminhamentoItem()]
  return items.map((item) => {
    if (typeof item === 'string') {
      return { ...createEncaminhamentoItem(), descricao: item }
    }
    return {
      descricao: item?.descricao || item?.texto || '',
      responsavel: item?.responsavel || '',
      prazo: item?.prazo || '',
    }
  })
}

function normalizeAssinaturas(items) {
  if (!Array.isArray(items) || items.length === 0) return [createAssinaturaItem()]
  return items.map((item) => {
    if (typeof item === 'string') {
      return { ...createAssinaturaItem(), nome: item }
    }
    return {
      nome: item?.nome || '',
      cargo: item?.cargo || '',
      tipo_assinatura: item?.tipo_assinatura || 'eletronica',
    }
  })
}

function reconcileDeliberacoes(currentDeliberacoes, pautaItems) {
  const next = [...currentDeliberacoes]
  while (next.length < pautaItems.length) {
    next.push(createDeliberacaoItem())
  }
  return next.slice(0, pautaItems.length).map((item, index) => ({
    ...createDeliberacaoItem(),
    ...item,
    titulo: item?.titulo || pautaItems[index]?.titulo || '',
  }))
}

function toBRDate(value) {
  if (!value) return '[dd/mm/aaaa]'
  const [year, month, day] = String(value).split('-')
  return `${day}/${month}/${year}`
}

function monthName(value) {
  if (!value) return '[mes]'
  const months = ['janeiro', 'fevereiro', 'marco', 'abril', 'maio', 'junho', 'julho', 'agosto', 'setembro', 'outubro', 'novembro', 'dezembro']
  return months[Number(String(value).split('-')[1]) - 1] || '[mes]'
}

function formatSchoolCity(unit) {
  if (!unit) return 'Cidade-UF'
  const city = unit.cidade || 'Cidade'
  const state = unit.uf || 'UF'
  return `${city}-${state}`
}

function extractFirstError(data) {
  if (!data || typeof data !== 'object') return null
  const [field, value] = Object.entries(data)[0] || []
  if (!field) return null
  if (Array.isArray(value)) return { field, message: value[0] }
  if (typeof value === 'string') return { field, message: value }
  return null
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

export default function AtaProfessoresAssistantPage() {
  const navigate = useNavigate()
  const { ataId } = useParams()
  const isEditing = Boolean(ataId)
  const [processSearch, setProcessSearch] = useState('')
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
  const [pauta, setPauta] = useState([createPautaItem()])
  const [deliberacoes, setDeliberacoes] = useState([createDeliberacaoItem()])
  const [encaminhamentos, setEncaminhamentos] = useState([createEncaminhamentoItem()])
  const [assinaturas, setAssinaturas] = useState([createAssinaturaItem()])
  const [anexos, setAnexos] = useState([createAttachment()])
  const [validationItems, setValidationItems] = useState([])

  const { data: processosData } = useQuery({
    queryKey: ['processos', 'assistant-options', processSearch],
    queryFn: () => processosApi.list({ page_size: 10, search: processSearch || undefined }).then((response) => response.data),
    staleTime: 60_000,
  })

  const { data: unidadesData } = useQuery({
    queryKey: ['unidades', 'ata-assistant-school'],
    queryFn: () => unidadesApi.list({ page_size: 1 }).then((response) => response.data),
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
    const nextPauta = normalizePauta(ataData.pauta)
    setParticipantes(normalizeParticipants(ataData.participantes))
    setPauta(nextPauta)
    setDeliberacoes(reconcileDeliberacoes(normalizeDeliberacoes(ataData.deliberacoes), nextPauta))
    setEncaminhamentos(normalizeEncaminhamentos(ataData.encaminhamentos))
    setAssinaturas(normalizeAssinaturas(ataData.assinaturas))
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
  const selectedProcessOption = formData.processo && ataData ? {
    id: ataData.processo,
    numero: ataData.processo_numero,
    assunto: ataData.processo_assunto || ataData.assunto,
  } : null
  const school = unidadesData?.results?.[0] || null
  const isReadOnly = Boolean(isEditing && ataData?.situacao === 'EMITIDO')

  const preview = useMemo(() => {
    const tipoReuniao = formData.tipo_reuniao_registro === 'OUTRO' && formData.tipo_reuniao_outro
      ? formData.tipo_reuniao_outro
      : (TIPO_REUNIAO_OPTIONS.find((option) => option.value === formData.tipo_reuniao_registro)?.label || '[TIPO DE REUNIAO/REGISTRO]')
    const presentes = participantes.filter((item) => item.presente)
    const ausentes = participantes.filter((item) => !item.presente)
    const pautaText = pauta.map((item, index) => `${index + 1}. ${item.titulo || '[Item]'}`).join('\n') || '[Sem pauta cadastrada]'
    const deliberacoesText = reconcileDeliberacoes(deliberacoes, pauta).map((item, index) => (
      `4.${index + 1} ${item.titulo || pauta[index]?.titulo || '[Assunto]'}\n` +
      `Foi apresentado(a) ${item.relato || '[resumo]'}. Apos discussoes, deliberou-se:\n\n` +
      `Decisao: ${item.decisao || '[texto]'}\n` +
      `Responsavel: ${item.responsavel || '[nome/cargo]'}\n` +
      `Prazo: ${item.prazo ? toBRDate(item.prazo) : '[data]'}\n` +
      `Observacoes: ${item.observacoes || '[texto]'}\n`
    )).join('\n') || '[Sem deliberacoes]'
    const encaminhamentosText = encaminhamentos
      .filter((item) => item.descricao || item.responsavel || item.prazo)
      .map((item) => `- ${item.descricao || '[Encaminhamento]'} - ${item.responsavel || '[responsavel]'} - ${item.prazo ? toBRDate(item.prazo) : '[prazo]'}`)
      .join('\n') || '[Sem encaminhamentos]'
    const anexosText = anexos
      .filter((item) => item.descricao || item.arquivo_nome || item.file)
      .map((item, index) => `Anexo ${String.fromCharCode(73 + index)} - ${item.descricao || item.arquivo_nome || '[nome]'}`)
      .join('\n') || '[Sem anexos]'
    const assinaturasText = assinaturas
      .filter((item) => item.nome || item.cargo)
      .map((item) => `${item.nome || '[Nome]'} - ${item.cargo || '[Cargo/Funcao]'}`)
      .join('\n') || '[Sem assinaturas]'
    const localLinha = ['ONLINE', 'HIBRIDA'].includes(formData.modalidade)
      ? `${formData.local_reuniao || '[local]'} - ${formData.plataforma || '[plataforma]'}`
      : (formData.local_reuniao || '[local]')

    return `${school?.nome || '[NOME DA ESCOLA]'}
CNPJ: ${school?.cnpj || '00.000.000/0000-00'} - INEP: 00000000
Endereco: ${school?.endereco || 'Rua, n, Bairro'}, ${formatSchoolCity(school)}
E-mail/Telefone: [contato]

ATA N ${formData.numero_ata || '[000]/[ANO]'} - ${tipoReuniao}

Livro: ${formData.livro || '[n]'} - Folha/Pagina: ${formData.folha_pagina || '[n]'}
Data: ${toBRDate(formData.data_reuniao)} - Horario: ${formData.horario_inicio || '[inicio]'} as ${formData.horario_termino || '[termino]'}
Local: ${localLinha}

1. Abertura

Aos ${formData.data_reuniao ? String(formData.data_reuniao).split('-')[2] : '[dia]'} dias do mes de ${monthName(formData.data_reuniao)} de ${formData.ano || '[ANO]'}, as ${formData.horario_inicio || '[inicio]'}, no(a) ${formData.local_reuniao || '[local]'}, reuniu-se ${tipoReuniao}, sob a presidencia/coordenacao de ${formData.presidente_reuniao || '[nome + cargo]'}, para tratar da pauta descrita nesta ata.

2. Participantes

Estiveram presentes:
${presentes.map((item) => `${item.nome || '[Nome]'}, ${item.cargo || '[cargo/funcao]'}`).join('\n') || '[Sem participantes presentes]'}

Ausentes/Justificativas:
${ausentes.map((item) => `${item.nome || '[Nome]'}, ${item.justificativa || '[justificativa]'}`).join('\n') || '[Sem ausencias registradas]'}

3. Pauta

${pautaText}

4. Relato e deliberacoes

${deliberacoesText}

5. Encaminhamentos

${encaminhamentosText}

6. Anexos

${anexosText}

7. Encerramento

${formData.texto_final || DEFAULT_TEXT_FINAL}

${formData.cidade_uf || '[Cidade-UF]'}, ${toBRDate(formData.data_reuniao)}.

Assinaturas:
${assinaturasText}`
  }, [anexos, assinaturas, deliberacoes, encaminhamentos, formData, participantes, pauta, school])

  const saveMutation = useMutation({
    mutationFn: async ({ action }) => {
      const nextDeliberacoes = reconcileDeliberacoes(deliberacoes, pauta)
      const body = new FormData()
      Object.entries(formData).forEach(([key, value]) => {
        body.append(key, value ?? '')
      })
      body.append('acao', action)
      body.append('participantes', JSON.stringify(participantes.filter((item) => item.nome || item.cargo || item.justificativa)))
      body.append('pauta', JSON.stringify(pauta.filter((item) => item.titulo || item.descricao)))
      body.append('deliberacoes', JSON.stringify(nextDeliberacoes.filter((item) => item.titulo || item.relato || item.decisao || item.responsavel || item.prazo || item.observacoes)))
      body.append('encaminhamentos', JSON.stringify(encaminhamentos.filter((item) => item.descricao || item.responsavel || item.prazo)))
      body.append('assinaturas', JSON.stringify(assinaturas.filter((item) => item.nome || item.cargo || item.tipo_assinatura)))

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
      setValidationItems([])
      toast.success(variables.action === 'emitir' ? 'Ata emitida com sucesso.' : 'Rascunho salvo com sucesso.')
      navigate(`/ata-professores?ata=${ata.id}`, { replace: true })
    },
    onError: (error) => {
      const firstError = extractFirstError(error?.response?.data)
      if (firstError) {
        setValidationItems([{ label: firstError.message, targetId: firstError.field }])
      }
      toast.error(getErrorMessage(error, 'Nao foi possivel salvar a ata.'))
    },
  })

  const updateField = (field, value) => {
    setFormData((current) => ({ ...current, [field]: value }))
  }

  const updateCollectionItem = (setter, items, index, field, value) => {
    const nextItems = items.map((item, itemIndex) => (itemIndex === index ? { ...item, [field]: value } : item))
    setter(nextItems)
    if (validationItems.length) {
      setValidationItems([])
    }
  }

  const addCollectionItem = (setter, factory) => setter((current) => [...current, factory()])
  const removeCollectionItem = (setter, index) => setter((current) => current.filter((_, currentIndex) => currentIndex !== index))

  const pageTitle = useMemo(() => (isEditing ? 'Editar Rascunho de Ata Escolar' : 'Assistente de Ata Escolar Digital'), [isEditing])

  const changePautaItem = (index, field, value) => {
    const nextPauta = pauta.map((item, itemIndex) => (itemIndex === index ? { ...item, [field]: value } : item))
    setPauta(nextPauta)
    setDeliberacoes((current) => reconcileDeliberacoes(current, nextPauta))
    if (validationItems.length) {
      setValidationItems([])
    }
  }

  const addPautaItem = () => {
    const nextPauta = [...pauta, createPautaItem()]
    setPauta(nextPauta)
    setDeliberacoes((current) => reconcileDeliberacoes(current, nextPauta))
  }

  const removePautaItem = (index) => {
    const nextPauta = pauta.filter((_, currentIndex) => currentIndex !== index)
    const safePauta = nextPauta.length ? nextPauta : [createPautaItem()]
    setPauta(safePauta)
    setDeliberacoes((current) => reconcileDeliberacoes(current.filter((_, currentIndex) => currentIndex !== index), safePauta))
  }

  const movePautaItem = (index, direction) => {
    const targetIndex = direction === 'up' ? index - 1 : index + 1
    if (targetIndex < 0 || targetIndex >= pauta.length) return
    const nextPauta = [...pauta]
    const nextDeliberacoes = reconcileDeliberacoes(deliberacoes, pauta)
    ;[nextPauta[index], nextPauta[targetIndex]] = [nextPauta[targetIndex], nextPauta[index]]
    ;[nextDeliberacoes[index], nextDeliberacoes[targetIndex]] = [nextDeliberacoes[targetIndex], nextDeliberacoes[index]]
    setPauta(nextPauta)
    setDeliberacoes(reconcileDeliberacoes(nextDeliberacoes, nextPauta))
  }

  const validationTargets = useMemo(() => {
    const items = []
    const requiredFields = [
      ['numero_ata', 'id_numero_ata', 'Numero da Ata'],
      ['ano', 'id_ano', 'Ano'],
      ['tipo_reuniao_registro', 'id_tipo_reuniao_registro', 'Tipo de Reuniao/Registro'],
      ['data_reuniao', 'id_data_reuniao', 'Data'],
      ['horario_inicio', 'id_horario_inicio', 'Horario de Inicio'],
      ['local_reuniao', 'id_local_reuniao', 'Local'],
      ['modalidade', 'id_modalidade', 'Modalidade'],
      ['cidade_uf', 'id_cidade_uf', 'Cidade/UF'],
      ['presidente_reuniao', 'id_presidente_reuniao', 'Presidente/Coordenador(a)'],
      ['responsavel_lavratura', 'id_responsavel_lavratura', 'Responsavel pela Lavratura'],
    ]

    requiredFields.forEach(([field, targetId, label]) => {
      if (!String(formData[field] || '').trim()) {
        items.push({ label, targetId })
      }
    })

    if (['ONLINE', 'HIBRIDA'].includes(formData.modalidade) && !String(formData.plataforma || '').trim()) {
      items.push({ label: 'Plataforma', targetId: 'id_plataforma' })
    }

    if (formData.tipo_reuniao_registro === 'OUTRO' && !String(formData.tipo_reuniao_outro || '').trim()) {
      items.push({ label: 'Outro Tipo de Reuniao', targetId: 'id_tipo_reuniao_outro' })
    }

    if (!participantes.some((item) => item.nome && item.cargo)) {
      items.push({ label: 'Ao menos um participante com nome e cargo', targetId: 'participantes' })
    }
    if (!pauta.some((item) => item.titulo)) {
      items.push({ label: 'Ao menos um item de pauta', targetId: 'pauta' })
    }
    if (!reconcileDeliberacoes(deliberacoes, pauta).some((item) => item.titulo && item.decisao)) {
      items.push({ label: 'Ao menos uma deliberacao com titulo e decisao', targetId: 'deliberacoes' })
    }
    if (!assinaturas.some((item) => item.nome && item.cargo)) {
      items.push({ label: 'Ao menos uma assinatura com nome e cargo', targetId: 'encerramento' })
    }

    return items
  }, [assinaturas, deliberacoes, formData, participantes, pauta])

  const goToTarget = (targetId) => {
    const target = document.getElementById(targetId)
    if (!target) return
    target.scrollIntoView({ behavior: 'smooth', block: 'center' })
    if (['INPUT', 'SELECT', 'TEXTAREA'].includes(target.tagName)) {
      target.focus()
      return
    }
    const focusable = target.querySelector?.('input, select, textarea, button')
    if (focusable) {
      focusable.focus()
    }
  }

  const scrollToSection = (sectionId) => {
    const section = document.getElementById(sectionId)
    section?.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }

  const triggerSave = (action) => {
    if (isReadOnly || saveMutation.isPending) {
      return
    }

    if (action === 'emitir') {
      if (validationTargets.length > 0) {
        setValidationItems(validationTargets)
        return
      }

      if (!window.confirm(
        `Confirma a emissao definitiva da ATA ${formData.numero_ata || '[sem numero]'}?\nData da reuniao: ${formData.data_reuniao || '[sem data]'}\n\nApos emitir, a ata ficara bloqueada para edicao.`
      )) {
        return
      }
    }

    setValidationItems([])
    saveMutation.mutate({ action })
  }

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
      <section className="ata-banner-card">
        <h1 className="ata-banner-card__title">{pageTitle}</h1>
        <p className="ata-banner-card__subtitle">Preencha as secoes e acompanhe a previa da ATA em tempo real antes da emissao.</p>
      </section>

      {isReadOnly ? (
        <div className="alert alert--error">
          Esta ata ja foi emitida e esta em modo somente leitura. Volte para a listagem para consultá-la.
        </div>
      ) : null}

      {validationItems.length ? (
        <section className="ata-validation-box-react">
          <strong>Campos obrigatorios pendentes para emissao:</strong>
          <ul>
            {validationItems.map((item, index) => (
              <li key={`${item.targetId}-${index}`}>
                <button type="button" className="ata-missing-link-react" onClick={() => goToTarget(item.targetId)}>
                  {item.label}
                </button>
              </li>
            ))}
          </ul>
        </section>
      ) : null}

      <div className="ata-shell-react">
        <aside className="ata-nav-react dashboard-card">
          {SECTION_ITEMS.map((section) => (
            <button key={section.id} type="button" className="ata-step-btn-react" onClick={() => scrollToSection(section.id)}>
              {section.label}
            </button>
          ))}
        </aside>

        <div className="ata-main-react">
          <section className="dashboard-card" id="identificacao">
            <h2 className="dashboard-card__title">1. Identificacao</h2>
            <div className="ata-grid-react ata-grid-react--4">
              <div className="form-field">
                <label htmlFor="id_tipo">Tipo do Documento</label>
                <input id="id_tipo" type="text" value="ATA" disabled />
              </div>
              <div className="form-field">
                <label htmlFor="id_numero_ata">Numero da Ata</label>
                <input id="id_numero_ata" type="text" value={formData.numero_ata} onChange={(event) => updateField('numero_ata', event.target.value)} disabled={isReadOnly} />
              </div>
              <div className="form-field">
                <label htmlFor="id_ano">Ano</label>
                <input id="id_ano" type="number" value={formData.ano} onChange={(event) => updateField('ano', event.target.value)} disabled={isReadOnly} />
              </div>
              <div className="form-field">
                <label htmlFor="id_tipo_reuniao_registro">Tipo de Reuniao/Registro</label>
                <select id="id_tipo_reuniao_registro" className="select" value={formData.tipo_reuniao_registro} onChange={(event) => updateField('tipo_reuniao_registro', event.target.value)} disabled={isReadOnly}>
                  <option value="">Selecione</option>
                  {TIPO_REUNIAO_OPTIONS.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}
                </select>
              </div>
            </div>
            <div className="ata-grid-react ata-grid-react--3">
              {formData.tipo_reuniao_registro === 'OUTRO' ? (
                <div className="form-field" id="box-tipo-outro">
                  <label htmlFor="id_tipo_reuniao_outro">Outro Tipo de Reuniao</label>
                  <input id="id_tipo_reuniao_outro" type="text" value={formData.tipo_reuniao_outro} onChange={(event) => updateField('tipo_reuniao_outro', event.target.value)} disabled={isReadOnly} />
                </div>
              ) : null}
              <div className="form-field">
                <label htmlFor="id_livro">Livro</label>
                <input id="id_livro" type="text" value={formData.livro} onChange={(event) => updateField('livro', event.target.value)} disabled={isReadOnly} />
              </div>
              <div className="form-field">
                <label htmlFor="id_folha_pagina">Folha/Pagina</label>
                <input id="id_folha_pagina" type="text" value={formData.folha_pagina} onChange={(event) => updateField('folha_pagina', event.target.value)} disabled={isReadOnly} />
              </div>
              <SearchableRemoteSelect
                id="id_processo"
                label="Processo Vinculado"
                searchLabel="Buscar processo"
                searchPlaceholder="Digite numero, assunto ou requerente"
                searchValue={processSearch}
                onSearchChange={setProcessSearch}
                value={formData.processo}
                onChange={(nextValue) => updateField('processo', nextValue)}
                options={processOptions}
                selectedOption={selectedProcessOption}
                emptyOptionLabel="Sem processo"
                getOptionLabel={(processo) => `${processo.numero} - ${processo.assunto}`}
                disabled={isReadOnly}
              />
            </div>
          </section>

          <section className="dashboard-card" id="reuniao">
            <h2 className="dashboard-card__title">2. Dados da reuniao</h2>
            <div className="ata-grid-react ata-grid-react--4">
              <div className="form-field">
                <label htmlFor="id_data_reuniao">Data</label>
                <input id="id_data_reuniao" type="date" value={formData.data_reuniao} onChange={(event) => updateField('data_reuniao', event.target.value)} disabled={isReadOnly} />
              </div>
              <div className="form-field">
                <label htmlFor="id_horario_inicio">Horario de Inicio</label>
                <input id="id_horario_inicio" type="time" value={formData.horario_inicio} onChange={(event) => updateField('horario_inicio', event.target.value)} disabled={isReadOnly} />
              </div>
              <div className="form-field">
                <label htmlFor="id_horario_termino">Horario de Termino</label>
                <input id="id_horario_termino" type="time" value={formData.horario_termino} onChange={(event) => updateField('horario_termino', event.target.value)} disabled={isReadOnly} />
              </div>
              <div className="form-field">
                <label htmlFor="id_modalidade">Modalidade</label>
                <select id="id_modalidade" className="select" value={formData.modalidade} onChange={(event) => updateField('modalidade', event.target.value)} disabled={isReadOnly}>
                  <option value="">Selecione</option>
                  {MODALIDADE_OPTIONS.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}
                </select>
              </div>
            </div>
            <div className="ata-grid-react ata-grid-react--3">
              <div className="form-field">
                <label htmlFor="id_local_reuniao">Local</label>
                <input id="id_local_reuniao" type="text" value={formData.local_reuniao} onChange={(event) => updateField('local_reuniao', event.target.value)} disabled={isReadOnly} />
              </div>
              {['ONLINE', 'HIBRIDA'].includes(formData.modalidade) ? (
                <div className="form-field" id="box-plataforma">
                  <label htmlFor="id_plataforma">Plataforma</label>
                  <input id="id_plataforma" type="text" value={formData.plataforma} onChange={(event) => updateField('plataforma', event.target.value)} disabled={isReadOnly} />
                </div>
              ) : null}
              {['ONLINE', 'HIBRIDA'].includes(formData.modalidade) ? (
                <div className="form-field" id="box-link">
                  <label htmlFor="id_link_reuniao">Link da Reuniao</label>
                  <input id="id_link_reuniao" type="url" value={formData.link_reuniao} onChange={(event) => updateField('link_reuniao', event.target.value)} disabled={isReadOnly} />
                </div>
              ) : null}
              <div className="form-field">
                <label htmlFor="id_cidade_uf">Cidade/UF</label>
                <input id="id_cidade_uf" type="text" value={formData.cidade_uf} onChange={(event) => updateField('cidade_uf', event.target.value)} disabled={isReadOnly} />
              </div>
            </div>
          </section>

          <section className="dashboard-card" id="participantes">
            <h2 className="dashboard-card__title">3. Participantes</h2>
            <div className="ata-grid-react ata-grid-react--2">
              <div className="form-field">
                <label htmlFor="id_presidente_reuniao">Presidente/Coordenador(a)</label>
                <input id="id_presidente_reuniao" type="text" value={formData.presidente_reuniao} onChange={(event) => updateField('presidente_reuniao', event.target.value)} disabled={isReadOnly} />
              </div>
              <div className="form-field">
                <label htmlFor="id_responsavel_lavratura">Responsavel pela Lavratura</label>
                <input id="id_responsavel_lavratura" type="text" value={formData.responsavel_lavratura} onChange={(event) => updateField('responsavel_lavratura', event.target.value)} disabled={isReadOnly} />
              </div>
            </div>
            <div className="ata-dynamic-list-react">
              {participantes.map((item, index) => (
                <div key={`participante-${index}`} className="ata-dynamic-item-react">
                  <div className="ata-dynamic-head-react">
                    <strong>Participante {index + 1}</strong>
                    {participantes.length > 1 ? <button type="button" className="btn btn--danger btn--sm" onClick={() => removeCollectionItem(setParticipantes, index)} disabled={isReadOnly}><Minus size={14} /> Remover</button> : null}
                  </div>
                  <div className="ata-grid-react ata-grid-react--4">
                    <div className="form-field">
                      <label>Nome</label>
                      <input type="text" value={item.nome} onChange={(event) => updateCollectionItem(setParticipantes, participantes, index, 'nome', event.target.value)} disabled={isReadOnly} />
                    </div>
                    <div className="form-field">
                      <label>Cargo/Funcao</label>
                      <input type="text" value={item.cargo} onChange={(event) => updateCollectionItem(setParticipantes, participantes, index, 'cargo', event.target.value)} disabled={isReadOnly} />
                    </div>
                    <div className="form-field">
                      <label>Presente?</label>
                      <select className="select" value={item.presente ? 'sim' : 'nao'} onChange={(event) => updateCollectionItem(setParticipantes, participantes, index, 'presente', event.target.value === 'sim')} disabled={isReadOnly}>
                        <option value="sim">Sim</option>
                        <option value="nao">Nao</option>
                      </select>
                    </div>
                    {!item.presente ? (
                      <div className="form-field">
                        <label>Justificativa de ausencia</label>
                        <input type="text" value={item.justificativa} onChange={(event) => updateCollectionItem(setParticipantes, participantes, index, 'justificativa', event.target.value)} disabled={isReadOnly} />
                      </div>
                    ) : null}
                  </div>
                </div>
              ))}
            </div>
            <button type="button" className="btn btn--secondary" onClick={() => addCollectionItem(setParticipantes, createParticipant)} disabled={isReadOnly}><Plus size={14} /> Adicionar participante</button>
          </section>

          <section className="dashboard-card" id="pauta">
            <h2 className="dashboard-card__title">4. Pauta</h2>
            <div className="ata-dynamic-list-react">
              {pauta.map((item, index) => (
                <div key={`pauta-${index}`} className="ata-dynamic-item-react">
                  <div className="ata-dynamic-head-react">
                    <strong>Item {index + 1}</strong>
                    <div className="table-actions">
                      <button type="button" className="btn btn--secondary btn--sm" onClick={() => movePautaItem(index, 'up')} disabled={isReadOnly || index === 0}>Subir</button>
                      <button type="button" className="btn btn--secondary btn--sm" onClick={() => movePautaItem(index, 'down')} disabled={isReadOnly || index === pauta.length - 1}>Descer</button>
                      {pauta.length > 1 ? <button type="button" className="btn btn--danger btn--sm" onClick={() => removePautaItem(index)} disabled={isReadOnly}><Minus size={14} /> Remover</button> : null}
                    </div>
                  </div>
                  <div className="ata-grid-react ata-grid-react--2">
                    <div className="form-field">
                      <label>Titulo do item</label>
                      <input type="text" value={item.titulo} onChange={(event) => changePautaItem(index, 'titulo', event.target.value)} disabled={isReadOnly} />
                    </div>
                    <div className="form-field">
                      <label>Descricao curta</label>
                      <input type="text" value={item.descricao} onChange={(event) => changePautaItem(index, 'descricao', event.target.value)} disabled={isReadOnly} />
                    </div>
                  </div>
                </div>
              ))}
            </div>
            <button type="button" className="btn btn--secondary" onClick={addPautaItem} disabled={isReadOnly}><Plus size={14} /> Adicionar item de pauta</button>
          </section>

          <section className="dashboard-card" id="deliberacoes">
            <h2 className="dashboard-card__title">5. Relato e deliberacoes</h2>
            <p className="ata-help-react">Blocos gerados automaticamente com base na pauta. Numeracao automatica 4.1, 4.2, 4.3...</p>
            <div className="ata-dynamic-list-react">
              {reconcileDeliberacoes(deliberacoes, pauta).map((item, index) => (
                <div key={`deliberacao-${index}`} className="ata-dynamic-item-react">
                  <div className="ata-dynamic-head-react">
                    <strong>4.{index + 1} {item.titulo || pauta[index]?.titulo || 'Item sem titulo'}</strong>
                  </div>
                  <div className="ata-grid-react ata-grid-react--2">
                    <div className="form-field">
                      <label>Titulo/Assunto</label>
                      <input type="text" value={item.titulo} onChange={(event) => updateCollectionItem(setDeliberacoes, reconcileDeliberacoes(deliberacoes, pauta), index, 'titulo', event.target.value)} disabled={isReadOnly} />
                    </div>
                    <div className="form-field">
                      <label>Responsavel</label>
                      <input type="text" value={item.responsavel} onChange={(event) => updateCollectionItem(setDeliberacoes, reconcileDeliberacoes(deliberacoes, pauta), index, 'responsavel', event.target.value)} disabled={isReadOnly} />
                    </div>
                    <div className="form-field">
                      <label>Relato/Resumo</label>
                      <textarea rows="3" value={item.relato} onChange={(event) => updateCollectionItem(setDeliberacoes, reconcileDeliberacoes(deliberacoes, pauta), index, 'relato', event.target.value)} disabled={isReadOnly} />
                    </div>
                    <div className="form-field">
                      <label>Decisao</label>
                      <textarea rows="3" value={item.decisao} onChange={(event) => updateCollectionItem(setDeliberacoes, reconcileDeliberacoes(deliberacoes, pauta), index, 'decisao', event.target.value)} disabled={isReadOnly} />
                    </div>
                    <div className="form-field">
                      <label>Prazo</label>
                      <input type="date" value={item.prazo} onChange={(event) => updateCollectionItem(setDeliberacoes, reconcileDeliberacoes(deliberacoes, pauta), index, 'prazo', event.target.value)} disabled={isReadOnly} />
                    </div>
                    <div className="form-field">
                      <label>Observacoes</label>
                      <textarea rows="3" value={item.observacoes} onChange={(event) => updateCollectionItem(setDeliberacoes, reconcileDeliberacoes(deliberacoes, pauta), index, 'observacoes', event.target.value)} disabled={isReadOnly} />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </section>

          <section className="dashboard-card" id="encaminhamentos">
            <h2 className="dashboard-card__title">6. Encaminhamentos</h2>
            <div className="ata-dynamic-list-react">
              {encaminhamentos.map((item, index) => (
                <div key={`encaminhamento-${index}`} className="ata-dynamic-item-react">
                  <div className="ata-dynamic-head-react">
                    <strong>Encaminhamento {index + 1}</strong>
                    {encaminhamentos.length > 1 ? <button type="button" className="btn btn--danger btn--sm" onClick={() => removeCollectionItem(setEncaminhamentos, index)} disabled={isReadOnly}><Minus size={14} /> Remover</button> : null}
                  </div>
                  <div className="ata-grid-react ata-grid-react--3">
                    <div className="form-field">
                      <label>Descricao</label>
                      <input type="text" value={item.descricao} onChange={(event) => updateCollectionItem(setEncaminhamentos, encaminhamentos, index, 'descricao', event.target.value)} disabled={isReadOnly} />
                    </div>
                    <div className="form-field">
                      <label>Responsavel</label>
                      <input type="text" value={item.responsavel} onChange={(event) => updateCollectionItem(setEncaminhamentos, encaminhamentos, index, 'responsavel', event.target.value)} disabled={isReadOnly} />
                    </div>
                    <div className="form-field">
                      <label>Prazo</label>
                      <input type="date" value={item.prazo} onChange={(event) => updateCollectionItem(setEncaminhamentos, encaminhamentos, index, 'prazo', event.target.value)} disabled={isReadOnly} />
                    </div>
                  </div>
                </div>
              ))}
            </div>
            <button type="button" className="btn btn--secondary" onClick={() => addCollectionItem(setEncaminhamentos, createEncaminhamentoItem)} disabled={isReadOnly}><Plus size={14} /> Adicionar encaminhamento</button>
          </section>

          <section className="dashboard-card" id="anexos">
            <h2 className="dashboard-card__title">7. Anexos</h2>
            <div className="ata-dynamic-list-react">
              {anexos.map((item, index) => (
                <div key={`anexo-${index}`} className="ata-dynamic-item-react">
                  <div className="ata-dynamic-head-react">
                    <strong>Anexo {index + 1}</strong>
                    {anexos.length > 1 ? <button type="button" className="btn btn--danger btn--sm" onClick={() => removeCollectionItem(setAnexos, index)} disabled={isReadOnly}><Minus size={14} /> Remover</button> : null}
                  </div>
                  <div className="ata-grid-react ata-grid-react--3">
                    <div className="form-field">
                      <label>Tipo do anexo</label>
                      <select className="select" value={item.tipo} onChange={(event) => updateCollectionItem(setAnexos, anexos, index, 'tipo', event.target.value)} disabled={isReadOnly}>
                        {TIPO_ANEXO_OPTIONS.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}
                      </select>
                    </div>
                    <div className="form-field">
                      <label>Descricao</label>
                      <input type="text" value={item.descricao} onChange={(event) => updateCollectionItem(setAnexos, anexos, index, 'descricao', event.target.value)} disabled={isReadOnly} />
                    </div>
                    <div className="form-field">
                      <label>Arquivo (opcional)</label>
                      <input type="file" accept=".pdf,.jpg,.jpeg,.png" onChange={(event) => {
                        const file = event.target.files?.[0] || null
                        if (file) {
                          import('@/utils/fileValidation').then(({ validateUploadFile }) => {
                            const { valid, error } = validateUploadFile(file)
                            if (!valid) {
                              event.target.value = ''
                              toast.error(error)
                              return
                            }
                            const next = anexos.map((attachment, attachmentIndex) => (
                              attachmentIndex === index
                                ? { ...attachment, file, arquivo_nome: file.name }
                                : attachment
                            ))
                            setAnexos(next)
                          })
                        }
                      }} disabled={isReadOnly} />
                      {item.arquivo_nome ? (
                        <span className="assistant-attachment-name">
                          <Paperclip size={14} />
                          {item.arquivo_url ? <a href={item.arquivo_url} target="_blank" rel="noreferrer">{item.arquivo_nome}</a> : item.arquivo_nome}
                        </span>
                      ) : null}
                    </div>
                  </div>
                </div>
              ))}
            </div>
            <button type="button" className="btn btn--secondary" onClick={() => addCollectionItem(setAnexos, createAttachment)} disabled={isReadOnly}><Plus size={14} /> Adicionar anexo</button>
          </section>

          <section className="dashboard-card" id="encerramento">
            <h2 className="dashboard-card__title">8. Encerramento e assinaturas</h2>
            <div className="ata-grid-react ata-grid-react--3">
              <div className="form-field">
                <label htmlFor="id_horario_encerramento">Horario de Encerramento</label>
                <input id="id_horario_encerramento" type="time" value={formData.horario_encerramento} onChange={(event) => updateField('horario_encerramento', event.target.value)} disabled={isReadOnly} />
              </div>
              <div className="form-field">
                <label htmlFor="id_forma_assinatura">Forma de assinatura</label>
                <input id="id_forma_assinatura" type="text" value={formData.forma_assinatura} onChange={(event) => updateField('forma_assinatura', event.target.value)} disabled={isReadOnly} />
              </div>
              <div className="form-field">
                <label htmlFor="id_assunto">Assunto/Titulo</label>
                <input id="id_assunto" type="text" value={formData.assunto} onChange={(event) => updateField('assunto', event.target.value)} disabled={isReadOnly} />
              </div>
            </div>
            <div className="form-field">
              <label htmlFor="id_texto_final">Texto final padrao da ata</label>
              <textarea id="id_texto_final" rows="4" value={formData.texto_final} onChange={(event) => updateField('texto_final', event.target.value)} disabled={isReadOnly} />
            </div>
            <div className="form-field">
              <label htmlFor="id_observacao">Observacoes internas</label>
              <textarea id="id_observacao" rows="3" value={formData.observacao} onChange={(event) => updateField('observacao', event.target.value)} disabled={isReadOnly} />
            </div>
            <h3 className="dashboard-card__title">Assinaturas</h3>
            <div className="ata-dynamic-list-react">
              {assinaturas.map((item, index) => (
                <div key={`assinatura-${index}`} className="ata-dynamic-item-react">
                  <div className="ata-dynamic-head-react">
                    <strong>Assinatura {index + 1}</strong>
                    {assinaturas.length > 1 ? <button type="button" className="btn btn--danger btn--sm" onClick={() => removeCollectionItem(setAssinaturas, index)} disabled={isReadOnly}><Minus size={14} /> Remover</button> : null}
                  </div>
                  <div className="ata-grid-react ata-grid-react--3">
                    <div className="form-field">
                      <label>Nome</label>
                      <input type="text" value={item.nome} onChange={(event) => updateCollectionItem(setAssinaturas, assinaturas, index, 'nome', event.target.value)} disabled={isReadOnly} />
                    </div>
                    <div className="form-field">
                      <label>Cargo/Funcao</label>
                      <input type="text" value={item.cargo} onChange={(event) => updateCollectionItem(setAssinaturas, assinaturas, index, 'cargo', event.target.value)} disabled={isReadOnly} />
                    </div>
                    <div className="form-field">
                      <label>Tipo de assinatura</label>
                      <input type="text" value={item.tipo_assinatura} onChange={(event) => updateCollectionItem(setAssinaturas, assinaturas, index, 'tipo_assinatura', event.target.value)} disabled={isReadOnly} />
                    </div>
                  </div>
                </div>
              ))}
            </div>
            <button type="button" className="btn btn--secondary" onClick={() => addCollectionItem(setAssinaturas, createAssinaturaItem)} disabled={isReadOnly}><Plus size={14} /> Adicionar assinatura</button>
          </section>

          <section className="dashboard-card" id="previa">
            <h2 className="dashboard-card__title">9. Previa da ata</h2>
            <pre className="ata-preview-react">{preview}</pre>
          </section>

          <section className="dashboard-card">
            <div className="ata-actions-react">
              <button type="button" className="btn btn--secondary" onClick={() => triggerSave('rascunho')} disabled={saveMutation.isPending || isReadOnly}>
                {saveMutation.isPending ? 'Salvando...' : 'Salvar como rascunho'}
              </button>
              <button type="button" className="btn btn--primary" onClick={() => scrollToSection('previa')}>
                Gerar previa
              </button>
              <button type="button" className="btn btn--primary" onClick={() => triggerSave('emitir')} disabled={saveMutation.isPending || isReadOnly}>
                {saveMutation.isPending ? 'Emitindo...' : 'Emitir ata'}
              </button>
              <button type="button" className="btn btn--outline" onClick={() => navigate('/ata-professores')} disabled={saveMutation.isPending}>
                Cancelar
              </button>
            </div>
            <p className="ata-help-react">Apos emissao a ata ficara bloqueada para edicao.</p>
          </section>
        </div>
      </div>
    </div>
  )
}