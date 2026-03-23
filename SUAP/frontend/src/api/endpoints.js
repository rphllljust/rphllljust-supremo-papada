/**
 * Funções de API para cada recurso — usadas com React Query.
 */
import client from './client'
import { instrumentAxiosClient } from '@/utils/debug'

// ── Portal Público (sem JWT) ───────────────────────────────────────────────────
import axios from 'axios'
const BASE_URL = import.meta.env.VITE_API_URL || '/api/v1'
const publicClient = axios.create({ baseURL: BASE_URL })

instrumentAxiosClient(publicClient, 'api.public')

export const portalApi = {
  cursos:     (params) => publicClient.get('/portal/cursos/',      { params }),
  unidades:   ()       => publicClient.get('/portal/unidades/'),
  publicacoes:()       => publicClient.get('/portal/publicacoes/'),
}

// ── Auth ───────────────────────────────────────────────────────────────────────
export const authApi = {
  login: (credentials) => client.post('/auth/token/', credentials),
  refresh: (refresh) => client.post('/auth/token/refresh/', { refresh }),
  logout: (refresh) => client.post('/auth/logout/', { refresh }, { withCredentials: true }),
  changePassword: (payload) => client.post('/auth/change-password/', payload),
  me: () => client.get('/auth/me/'),
}

export const accessApi = {
  avaExportPreview: () => client.get('/access/ava-export/preview/'),
}

export const dashboardApi = {
  overview: () => client.get('/dashboard/overview/'),
}

// ── Fábrica genérica de endpoints CRUD ────────────────────────────────────────
const crud = (resource) => ({
  list: (params) => client.get(`/${resource}/`, { params }),
  get: (id) => client.get(`/${resource}/${id}/`),
  create: (data) => client.post(`/${resource}/`, data),
  update: (id, data) => client.put(`/${resource}/${id}/`, data),
  patch: (id, data) => client.patch(`/${resource}/${id}/`, data),
  remove: (id) => client.delete(`/${resource}/${id}/`),
})

export const usuariosApi = {
  ...crud('usuarios'),
}
export const alunosApi = crud('alunos')
export const servidoresApi = {
  ...crud('servidores'),
  myProfile: () => client.get('/servidores/me/perfil/'),
  profile: (id) => client.get(`/servidores/${id}/perfil/`),
  profileByMatricula: (matricula) => client.get(`/servidores/matricula/${matricula}/perfil/`),
}
export const setoresApi = crud('setores')
export const declaracoesApi = crud('declaracoes')
export const historicosApi = crud('historicos')
export const historicosDigitaisApi = {
  list: (params) => client.get('/historicos-digitais/', { params }),
  get: (id) => client.get(`/historicos-digitais/${id}/`),
  emitir: (historicoId, data) => client.post(`/historicos-digitais/emitir/${historicoId}/`, data),
  revogar: (id, data) => client.post(`/historicos-digitais/${id}/revogar/`, data),
  validarPublico: (chave) => client.get('/historicos-digitais/validar-publico/', { params: { chave } }),
}
export const guiasTransferenciaApi = crud('guias-transferencia')
export const transferenciasApi = {
  list: (params) => client.get('/transferencias/', { params }),
}

export const unidadesApi = crud('unidades')
export const cursosApi = {
  ...crud('cursos'),
  componentes: (id) => client.get(`/cursos/${id}/componentes/`),
  calendarios: (id) => client.get(`/cursos/${id}/calendarios/`),
}
export const moodleIntegrationApi = {
  listCursos: (params) => client.get('/integracoes/moodle/espelho/cursos/', { params }),
  importCursos: (data) => client.post('/integracoes/moodle/sincronizar/cursos/', data),
  getCursosByField: (field, value, params = {}) => client.get('/integracoes/moodle/cursos/', {
    params: { ...params, action: 'core_course_get_courses_by_field', field, value },
  }),
  getRecentCursos: (userid, params = {}) => client.get('/integracoes/moodle/cursos/', {
    params: { ...params, action: 'core_course_get_recent_courses', userid, source: 'live' },
  }),
  searchCursos: (criteriavalue, params = {}) => client.get('/integracoes/moodle/cursos/', {
    params: { ...params, action: 'core_course_search_courses', criterianame: 'search', criteriavalue },
  }),
  createCursos: (data) => client.post('/integracoes/moodle/cursos/', { ...data, action: 'core_course_create_courses' }),
  updateCursos: (data) => client.post('/integracoes/moodle/cursos/', { ...data, action: 'core_course_update_courses' }),
  deleteCursos: (data) => client.post('/integracoes/moodle/cursos/', { ...data, action: 'core_course_delete_courses' }),
  viewCurso: (data) => client.post('/integracoes/moodle/cursos/', { ...data, action: 'core_course_view_course' }),
  syncCategorias: (data) => client.post('/integracoes/moodle/sincronizar/categorias/', data),
  getCategorias: (params = {}) => client.get('/integracoes/moodle/espelho/categorias/', { params }),
  createCategorias: (data) => client.post('/integracoes/moodle/categorias/', { ...data, action: 'core_course_create_categories' }),
  updateCategorias: (data) => client.post('/integracoes/moodle/categorias/', { ...data, action: 'core_course_update_categories' }),
  deleteCategorias: (data) => client.post('/integracoes/moodle/categorias/', { ...data, action: 'core_course_delete_categories' }),
  // Alternative using HTTP DELETE (sends categoryids as query params)
  deleteCategoriasDelete: (params) => client.delete('/integracoes/moodle/categorias/', { params }),
}
export const areasCursoApi = {
  list: (params) => client.get('/cursos/areas/', { params }),
  get: (id) => client.get(`/cursos/areas/${id}/`),
  create: (data) => client.post('/cursos/areas/', data),
  update: (id, data) => client.put(`/cursos/areas/${id}/`, data),
  patch: (id, data) => client.patch(`/cursos/areas/${id}/`, data),
  remove: (id) => client.delete(`/cursos/areas/${id}/`),
}
export const eixosTecnologicosApi = {
  list: (params) => client.get('/cursos/eixos-tecnologicos/', { params }),
  get: (id) => client.get(`/cursos/eixos-tecnologicos/${id}/`),
  create: (data) => client.post('/cursos/eixos-tecnologicos/', data),
  update: (id, data) => client.put(`/cursos/eixos-tecnologicos/${id}/`, data),
  patch: (id, data) => client.patch(`/cursos/eixos-tecnologicos/${id}/`, data),
  remove: (id) => client.delete(`/cursos/eixos-tecnologicos/${id}/`),
}
export const tiposComponentesApi = {
  list: (params) => client.get('/cursos/tipos-componentes/', { params }),
  get: (id) => client.get(`/cursos/tipos-componentes/${id}/`),
  create: (data) => client.post('/cursos/tipos-componentes/', data),
  update: (id, data) => client.put(`/cursos/tipos-componentes/${id}/`, data),
  patch: (id, data) => client.patch(`/cursos/tipos-componentes/${id}/`, data),
  remove: (id) => client.delete(`/cursos/tipos-componentes/${id}/`),
}
export const niveisEnsinoApi = {
  list: (params) => client.get('/cursos/niveis-ensino/', { params }),
  get: (id) => client.get(`/cursos/niveis-ensino/${id}/`),
  create: (data) => client.post('/cursos/niveis-ensino/', data),
  update: (id, data) => client.put(`/cursos/niveis-ensino/${id}/`, data),
  patch: (id, data) => client.patch(`/cursos/niveis-ensino/${id}/`, data),
  remove: (id) => client.delete(`/cursos/niveis-ensino/${id}/`),
}
export const componentesApi = {
  list: (params) => client.get('/cursos/componentes/', { params }),
  get: (id) => client.get(`/cursos/componentes/${id}/`),
  create: (data) => client.post('/cursos/componentes/', data),
  update: (id, data) => client.put(`/cursos/componentes/${id}/`, data),
  patch: (id, data) => client.patch(`/cursos/componentes/${id}/`, data),
  remove: (id) => client.delete(`/cursos/componentes/${id}/`),
}
export const matrizesCurricularesApi = {
  list: (params) => client.get('/cursos/matrizes-curriculares/', { params }),
  get: (id) => client.get(`/cursos/matrizes-curriculares/${id}/`),
  create: (data) => client.post('/cursos/matrizes-curriculares/', data),
  update: (id, data) => client.put(`/cursos/matrizes-curriculares/${id}/`, data),
  patch: (id, data) => client.patch(`/cursos/matrizes-curriculares/${id}/`, data),
  remove: (id) => client.delete(`/cursos/matrizes-curriculares/${id}/`),
  componentes: (id, params) => client.get(`/cursos/matrizes-curriculares/${id}/componentes/`, { params }),
  createComponente: (id, data) => client.post(`/cursos/matrizes-curriculares/${id}/componentes/`, data),
  logs: (id) => client.get(`/cursos/matrizes-curriculares/${id}/logs/`),
  templateStatus: (id) => client.get(`/cursos/matrizes-curriculares/${id}/template-status/`),
  clonar: (id, data = {}) => client.post(`/cursos/matrizes-curriculares/${id}/clonar/`, data),
  publicar: (id) => client.post(`/cursos/matrizes-curriculares/${id}/publicar/`),
  encerrar: (id) => client.post(`/cursos/matrizes-curriculares/${id}/encerrar/`),
  definirVigente: (id) => client.post(`/cursos/matrizes-curriculares/${id}/definir-vigente/`),
  syncTemplate: (id, data = {}) => client.post(`/cursos/matrizes-curriculares/${id}/sincronizar-template-moodle/`, data),
  gerarOferta: (id, data = {}) => client.post(`/cursos/matrizes-curriculares/${id}/gerar-oferta/`, data),
}
export const ofertasApi = {
  ...crud('ofertas'),
  logs: (id) => client.get(`/ofertas/${id}/logs/`),
  syncMoodle: (id, data = {}) => client.post(`/ofertas/${id}/sincronizar-moodle/`, data),
}
export const turmasApi = {
  ...crud('turmas'),
  matriculas: (id) => client.get(`/turmas/${id}/matriculas/`),
}
export const diarioApi = {
  ...crud('diarios'),
  fechar: (id) => client.post(`/diarios/${id}/fechar/`),
  reabrir: (id) => client.post(`/diarios/${id}/reabrir/`),
  documento: (id) => client.get(`/diarios/${id}/documento/`),
  criarMaterial: (id, data) => client.post(`/diarios/${id}/materiais/`, data),
  criarOcorrencia: (id, data) => client.post(`/diarios/${id}/ocorrencias/`, data),
}
export const matriculasApi = {
  ...crud('matriculas'),
  notas: (id) => client.get(`/matriculas/${id}/notas/`),
  frequencias: (id) => client.get(`/matriculas/${id}/frequencias/`),
}
export const notasApi = crud('notas')
export const frequenciasApi = crud('frequencias')
export const atasProfessoresApi = crud('atas-professores')
export const notificacoesApi = {
  list: (params) => client.get('/notificacoes/', { params }),
  get: (id) => client.get(`/notificacoes/${id}/`),
  markRead: (id, lida = true) => client.post(`/notificacoes/${id}/marcar-lida/`, { lida }),
  markAllRead: (params) => client.post('/notificacoes/marcar-todas-lidas/', null, { params }),
  hide: (id) => client.post(`/notificacoes/${id}/ocultar/`),
  preferences: (params) => client.get('/notificacoes/preferencias/', { params }),
  updatePreference: (id, data) => client.patch(`/notificacoes/preferencias/${id}/`, data),
  bulkUpdatePreferences: (data) => client.post('/notificacoes/preferencias/atualizar-em-lote/', data),
}
export const eventosApi = crud('eventos')
export const processosApi = {
  ...crud('processos'),
  tramitar: (id, data) => client.post(`/processos/${id}/tramitar/`, data),
}
export const guardaApi = crud('guarda-documental')
export const publicacoesApi = crud('publicacoes')
export const inscricoesApi = crud('inscricoes')
export const conveniosApi = crud('convenios')
export const estagiosApi = crud('estagios')
export const moodleCategoriesApi = {
  resetAndSync: () => client.post('/integracoes/moodle/reset-sync-categorias/'),
  resetLocalAndSync: () => client.post('/integracoes/moodle/reset-local-and-sync/'),
  diffAndSync: {
    diff: () => client.get('/integracoes/moodle/diff-sync-categorias/'),
    sync: () => client.post('/integracoes/moodle/diff-sync-categorias/'),
  },
}
