export const WIZARD_STEPS = [
  { key: 'estrutura', title: 'Estrutura', description: 'Selecionar ou cadastrar estrutura de curso' },
  { key: 'matriz', title: 'Matriz', description: 'Cadastrar matriz curricular' },
  { key: 'componentes', title: 'Componentes', description: 'Selecionar e vincular componentes' },
  { key: 'requisitos', title: 'Requisitos', description: 'Definir pre e co-requisitos' },
  { key: 'curso', title: 'Curso', description: 'Cadastrar curso e vincular matriz' },
  { key: 'coordenadores', title: 'Coordenadores', description: 'Definir coordenacao do curso' },
  { key: 'resumo', title: 'Resumo', description: 'Revisar e concluir configuracao' },
]

export const COMPONENTE_TIPO_OPTIONS = [
  { value: 'OBRIGATORIO', label: 'Obrigatorio' },
  { value: 'OPTATIVO', label: 'Optativo' },
  { value: 'PRATICO', label: 'Pratico' },
]

export const CURSO_MODALIDADE_OPTIONS = [
  { value: 'PRESENCIAL', label: 'Presencial' },
  { value: 'EAD', label: 'EAD' },
  { value: 'HIBRIDO', label: 'Hibrido' },
]

export const CURSO_SITUACAO_OPTIONS = [
  { value: 'EM_CONFIGURACAO', label: 'Em configuracao' },
  { value: 'ATIVO', label: 'Ativo' },
  { value: 'INATIVO', label: 'Inativo' },
]

export const WIZARD_STATUS_META = {
  rascunho: { label: 'Rascunho', tone: 'warning' },
  em_andamento: { label: 'Em andamento', tone: 'info' },
  concluido: { label: 'Concluido', tone: 'success' },
}

export function getStepIndex(stepKey) {
  return WIZARD_STEPS.findIndex((step) => step.key === stepKey)
}

export function getStepByIndex(index) {
  return WIZARD_STEPS[index] || WIZARD_STEPS[0]
}
