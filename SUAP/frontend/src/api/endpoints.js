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
export const componentesApi = {
  list: (params) => client.get('/cursos/componentes/', { params }),
  get: (id) => client.get(`/cursos/componentes/${id}/`),
  create: (data) => client.post('/cursos/componentes/', data),
  update: (id, data) => client.put(`/cursos/componentes/${id}/`, data),
  patch: (id, data) => client.patch(`/cursos/componentes/${id}/`, data),
  remove: (id) => client.delete(`/cursos/componentes/${id}/`),
}
export const turmasApi = {
  ...crud('turmas'),
  matriculas: (id) => client.get(`/turmas/${id}/matriculas/`),
}
export const diarioApi = crud('diarios')
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
