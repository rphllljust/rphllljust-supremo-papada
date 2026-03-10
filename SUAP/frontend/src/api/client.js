/**
 * Axios client configurado para o Django DRF.
 * - Injeta o Bearer token JWT em cada request
 * - Faz refresh automático do token quando expira (401)
 * - Intercepta erros globais
 */
import axios from 'axios'
import { debugLog, instrumentAxiosClient, normalizeError } from '@/utils/debug'

const BASE_URL = import.meta.env.VITE_API_URL || '/api/v1'

const client = axios.create({
  baseURL: BASE_URL,
  headers: { 'Content-Type': 'application/json' },
})

instrumentAxiosClient(client, 'api.private')

// Injeta o access token em todas as requests
client.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  debugLog('info', 'auth.token.attach', {
    hasToken: Boolean(token),
    url: `${config.baseURL || ''}${config.url || ''}`,
  })
  return config
})

// Refresh automático quando 401
let isRefreshing = false
let failedQueue = []

const processQueue = (error, token = null) => {
  debugLog(error ? 'warn' : 'info', 'auth.refresh.queue.process', {
    pending: failedQueue.length,
    hasToken: Boolean(token),
    error: normalizeError(error),
  })
  failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error)
    } else {
      prom.resolve(token)
    }
  })
  failedQueue = []
}

client.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config

    debugLog('warn', 'api.private.response.intercepted_error', {
      status: error.response?.status,
      url: `${originalRequest?.baseURL || ''}${originalRequest?.url || ''}`,
      error: normalizeError(error),
    })

    if (error.response?.status === 401 && !originalRequest._retry) {
      if (isRefreshing) {
        debugLog('info', 'auth.refresh.wait_existing_request', {
          url: `${originalRequest?.baseURL || ''}${originalRequest?.url || ''}`,
        })
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject })
        })
          .then((token) => {
            originalRequest.headers.Authorization = `Bearer ${token}`
            return client(originalRequest)
          })
          .catch((err) => Promise.reject(err))
      }

      originalRequest._retry = true
      isRefreshing = true
      debugLog('warn', 'auth.refresh.start', {
        url: `${originalRequest?.baseURL || ''}${originalRequest?.url || ''}`,
      })

      const refreshToken = localStorage.getItem('refresh_token')
      if (!refreshToken) {
        // Sem refresh token — desloga
        debugLog('error', 'auth.refresh.missing_token')
        localStorage.clear()
        window.location.href = '/accounts/login'
        return Promise.reject(error)
      }

      try {
        const { data } = await axios.post(`${BASE_URL}/auth/token/refresh/`, {
          refresh: refreshToken,
        })
        localStorage.setItem('access_token', data.access)
        debugLog('info', 'auth.refresh.success')
        processQueue(null, data.access)
        originalRequest.headers.Authorization = `Bearer ${data.access}`
        return client(originalRequest)
      } catch (refreshError) {
        debugLog('error', 'auth.refresh.failed', {
          error: normalizeError(refreshError),
        })
        processQueue(refreshError, null)
        localStorage.clear()
        window.location.href = '/accounts/login'
        return Promise.reject(refreshError)
      } finally {
        isRefreshing = false
      }
    }

    return Promise.reject(error)
  }
)

export default client
