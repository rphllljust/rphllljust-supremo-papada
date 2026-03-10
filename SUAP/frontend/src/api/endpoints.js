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
  logout: (refresh) => client.post('/auth/logout/', { refresh }),
  me: () => client.get('/auth/me/'),
}

export const accessApi = {
  avaExportPreview: () => client.get('/access/ava-export/preview/'),
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

export const unidadesApi = crud('unidades')
export const cursosApi = {
  ...crud('cursos'),
  componentes: (id) => client.get(`/cursos/${id}/componentes/`),
  calendarios: (id) => client.get(`/cursos/${id}/calendarios/`),
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
