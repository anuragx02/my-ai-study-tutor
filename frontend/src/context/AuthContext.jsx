import { createContext, useContext, useEffect, useMemo, useState } from 'react'
import api, { clearSession, storeSession } from '../services/api'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [authReady, setAuthReady] = useState(false)

  useEffect(() => {
    let active = true

    async function bootstrap() {
      const token = window.localStorage.getItem('authToken')
      if (!token) {
        setAuthReady(true)
        return
      }

      try {
        const { data } = await api.get('/auth/profile')
        if (active) {
          setUser(data)
        }
      } catch {
        clearSession()
        if (active) {
          setUser(null)
        }
      } finally {
        if (active) {
          setAuthReady(true)
        }
      }
    }

    bootstrap()

    return () => {
      active = false
    }
  }, [])

  async function login(values) {
    const { data } = await api.post('/auth/login', values)
    storeSession(data)
    setUser(data.user)
    return data.user
  }

  async function register(values) {
    const { data } = await api.post('/auth/register', values)
    storeSession(data)
    setUser(data.user)
    return data.user
  }

  async function logout() {
    const refreshToken = window.localStorage.getItem('refreshToken')
    try {
      if (refreshToken) {
        await api.post('/auth/logout', { refresh: refreshToken })
      }
    } catch {
      // Ignore logout failures and clear local state.
    } finally {
      clearSession()
      setUser(null)
    }
  }

  const value = useMemo(
    () => ({
      user,
      setUser,
      login,
      register,
      logout,
      authReady,
      isAuthenticated: Boolean(user),
    }),
    [user, authReady],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider')
  }
  return context
}
