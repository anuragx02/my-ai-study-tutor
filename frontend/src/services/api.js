import axios from 'axios'

const baseURL = import.meta.env.VITE_API_BASE_URL || '/api'

const api = axios.create({
  baseURL,
  withCredentials: true,
})

const refreshClient = axios.create({
  baseURL,
  withCredentials: true,
})

export function storeSession({ access, refresh, user }) {
  if (access) {
    window.localStorage.setItem('authToken', access)
  }
  if (refresh) {
    window.localStorage.setItem('refreshToken', refresh)
  }
  if (user?.name) {
    window.localStorage.setItem('username', user.name)
  }
  if (user?.email) {
    window.localStorage.setItem('userEmail', user.email)
  }
}

export function clearSession() {
  window.localStorage.removeItem('authToken')
  window.localStorage.removeItem('refreshToken')
  window.localStorage.removeItem('username')
  window.localStorage.removeItem('userEmail')
}

api.interceptors.request.use((config) => {
  const token = window.localStorage.getItem('authToken')
  if (token) {
    config.headers = config.headers || {}
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config
    const refreshToken = window.localStorage.getItem('refreshToken')

    if (
      error.response?.status === 401 &&
      refreshToken &&
      originalRequest &&
      !originalRequest._retry &&
      !originalRequest.url?.includes('/auth/login') &&
      !originalRequest.url?.includes('/auth/register') &&
      !originalRequest.url?.includes('/auth/refresh')
    ) {
      originalRequest._retry = true

      try {
        const refreshResponse = await refreshClient.post('/auth/refresh', { refresh: refreshToken })
        const nextAccess = refreshResponse.data.access
        const nextRefresh = refreshResponse.data.refresh || refreshToken
        window.localStorage.setItem('authToken', nextAccess)
        window.localStorage.setItem('refreshToken', nextRefresh)
        originalRequest.headers = originalRequest.headers || {}
        originalRequest.headers.Authorization = `Bearer ${nextAccess}`
        return api(originalRequest)
      } catch (refreshError) {
        clearSession()
        return Promise.reject(refreshError)
      }
    }

    return Promise.reject(error)
  },
)

export default api
