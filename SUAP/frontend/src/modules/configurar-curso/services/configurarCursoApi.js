import client from '@/api/client'

const BASE_PATH = '/configurar-curso'

export const configurarCursoApi = {
  listEstruturas: (params) => client.get(`${BASE_PATH}/estruturas/`, { params }),
  getEstrutura: (id) => client.get(`${BASE_PATH}/estruturas/${id}/`),
  createEstrutura: (data) => client.post(`${BASE_PATH}/estruturas/`, data),
  updateEstrutura: (id, data) => client.put(`${BASE_PATH}/estruturas/${id}/`, data),
  deleteEstrutura: (id) => client.delete(`${BASE_PATH}/estruturas/${id}/`),

  listMatrizes: (params) => client.get(`${BASE_PATH}/matrizes/`, { params }),
  getMatriz: (id) => client.get(`${BASE_PATH}/matrizes/${id}/`),
  createMatriz: (data) => client.post(`${BASE_PATH}/matrizes/`, data),
  updateMatriz: (id, data) => client.put(`${BASE_PATH}/matrizes/${id}/`, data),

  listComponentes: (params) => client.get(`${BASE_PATH}/componentes/`, { params }),
  getComponente: (id) => client.get(`${BASE_PATH}/componentes/${id}/`),
  createComponente: (data) => client.post(`${BASE_PATH}/componentes/`, data),
  updateComponente: (id, data) => client.put(`${BASE_PATH}/componentes/${id}/`, data),

  listMatrizComponentes: (matrizId, params) => client.get(`${BASE_PATH}/matrizes/${matrizId}/componentes/`, { params }),
  createMatrizComponente: (matrizId, data) => client.post(`${BASE_PATH}/matrizes/${matrizId}/componentes/`, data),
  updateMatrizComponente: (id, data) => client.put(`${BASE_PATH}/matriz-componentes/${id}/`, data),
  deleteMatrizComponente: (id) => client.delete(`${BASE_PATH}/matriz-componentes/${id}/`),

  listPreRequisitos: (params) => client.get(`${BASE_PATH}/pre-requisitos/`, { params }),
  createPreRequisito: (data) => client.post(`${BASE_PATH}/pre-requisitos/`, data),
  deletePreRequisito: (id) => client.delete(`${BASE_PATH}/pre-requisitos/${id}/`),

  listCoRequisitos: (params) => client.get(`${BASE_PATH}/co-requisitos/`, { params }),
  createCoRequisito: (data) => client.post(`${BASE_PATH}/co-requisitos/`, data),
  deleteCoRequisito: (id) => client.delete(`${BASE_PATH}/co-requisitos/${id}/`),

  listCursos: (params) => client.get(`${BASE_PATH}/cursos/`, { params }),
  getCurso: (id) => client.get(`${BASE_PATH}/cursos/${id}/`),
  createCurso: (data) => client.post(`${BASE_PATH}/cursos/`, data),
  updateCurso: (id, data) => client.put(`${BASE_PATH}/cursos/${id}/`, data),

  listCoordenadores: (params) => client.get(`${BASE_PATH}/coordenadores/`, { params }),
  getCoordenador: (id) => client.get(`${BASE_PATH}/coordenadores/${id}/`),
  createCoordenador: (data) => client.post(`${BASE_PATH}/coordenadores/`, data),

  listCursoCoordenadores: (cursoId) => client.get(`${BASE_PATH}/cursos/${cursoId}/coordenadores/`),
  addCursoCoordenador: (cursoId, data) => client.post(`${BASE_PATH}/cursos/${cursoId}/coordenadores/`, data),
  deleteCursoCoordenador: (id) => client.delete(`${BASE_PATH}/curso-coordenadores/${id}/`),

  createWizard: (data) => client.post(`${BASE_PATH}/wizard/`, data),
  getWizard: (id) => client.get(`${BASE_PATH}/wizard/${id}/`),
  saveWizardStep: (id, data) => client.patch(`${BASE_PATH}/wizard/${id}/salvar-etapa/`, data),
  advanceWizard: (id) => client.post(`${BASE_PATH}/wizard/${id}/avancar/`),
  backWizard: (id) => client.post(`${BASE_PATH}/wizard/${id}/voltar/`),
  getWizardSummary: (id) => client.post(`${BASE_PATH}/wizard/${id}/resumo/`),
  concludeWizard: (id) => client.post(`${BASE_PATH}/wizard/${id}/concluir/`),
}

export function extractResults(payload) {
  if (!payload) return []
  return Array.isArray(payload.results) ? payload.results : payload
}

export function extractErrorMessage(error, fallbackMessage = 'Nao foi possivel concluir a operacao.') {
  const data = error?.response?.data
  if (!data) return fallbackMessage

  if (typeof data.detail === 'string') {
    return data.detail
  }

  const [firstKey] = Object.keys(data)
  const firstValue = firstKey ? data[firstKey] : null

  if (Array.isArray(firstValue) && firstValue.length) {
    return firstValue[0]
  }

  if (typeof firstValue === 'string') {
    return firstValue
  }

  return fallbackMessage
}
