export const PUBLICACAO_STATUS_BADGE = {
  RASCUNHO: 'badge--secondary',
  PUBLICADO: 'badge--success',
  ENCERRADO: 'badge--danger',
}

export const PUBLICACAO_STATUS_OPTIONS = [
  { value: 'RASCUNHO', label: 'Rascunho' },
  { value: 'PUBLICADO', label: 'Publicado' },
  { value: 'ENCERRADO', label: 'Encerrado' },
]

export const DEFAULT_PUBLICACAO_FORM = {
  curso: '',
  titulo: '',
  descricao: '',
  vagas: '0',
  data_inicio: '',
  data_fim: '',
  status: 'RASCUNHO',
}

export function formatDate(value) {
  if (!value) return '-'
  return new Date(`${value}T00:00:00`).toLocaleDateString('pt-BR')
}

export function formatDateTime(value) {
  if (!value) return '-'
  return new Date(value).toLocaleString('pt-BR')
}

export function getErrorMessage(error, fallback) {
  const data = error?.response?.data

  if (!data) return fallback
  if (typeof data.detail === 'string') return data.detail

  const firstValue = Object.values(data)[0]
  return Array.isArray(firstValue) ? firstValue[0] : (firstValue || fallback)
}

export function buildPublicacaoFormValues(publicacao) {
  return {
    curso: publicacao?.curso ? String(publicacao.curso) : '',
    titulo: publicacao?.titulo || '',
    descricao: publicacao?.descricao || '',
    vagas: String(publicacao?.vagas ?? 0),
    data_inicio: publicacao?.data_inicio || '',
    data_fim: publicacao?.data_fim || '',
    status: publicacao?.status || 'RASCUNHO',
  }
}

export function buildPublicacaoPayload(formData) {
  return {
    curso: Number(formData.curso),
    titulo: formData.titulo.trim(),
    descricao: formData.descricao.trim(),
    vagas: Number(formData.vagas || 0),
    data_inicio: formData.data_inicio,
    data_fim: formData.data_fim,
    status: formData.status,
  }
}

export function validatePublicacaoForm(formData) {
  return Boolean(formData.curso && formData.titulo.trim() && formData.data_inicio && formData.data_fim)
}

export function getPublicacaoStatusLabel(status) {
  return PUBLICACAO_STATUS_OPTIONS.find((option) => option.value === status)?.label || status || '-'
}