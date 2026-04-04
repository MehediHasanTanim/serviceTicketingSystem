import React, { createContext, useContext, useMemo, useState } from 'react'
import { apiRequest } from '../../shared/api/client'

const AuthContext = createContext(null as AuthContextValue | null)

type AuthState = {
  accessToken: string
  refreshToken: string
  expiresAt: string
  refreshExpiresAt: string
  userName: string
  user?: {
    id: number
    org_id: number
    email: string
    display_name: string
    roles?: string[]
    is_admin?: boolean
  }
}

type LoginInput = {
  org_id: number
  email: string
  password: string
}

type AuthContextValue = {
  auth: AuthState | null
  login: (input: LoginInput) => Promise<AuthState>
  logout: () => Promise<void>
  fetchMe: (accessToken?: string) => Promise<AuthState['user'] | null>
}

const STORAGE_KEY = 'ticketing.auth'

function loadAuth(): AuthState | null {
  const raw = localStorage.getItem(STORAGE_KEY)
  if (!raw) return null
  try {
    return JSON.parse(raw)
  } catch {
    return null
  }
}

function saveAuth(auth: AuthState | null) {
  if (!auth) {
    localStorage.removeItem(STORAGE_KEY)
    return
  }
  localStorage.setItem(STORAGE_KEY, JSON.stringify(auth))
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [auth, setAuth] = useState<AuthState | null>(() => loadAuth())

  const value = useMemo(() => ({
    auth,
    async fetchMe(accessToken?: string) {
      const token = accessToken || auth?.accessToken
      if (!token) return null
      return apiRequest('/me', {
        method: 'GET',
        headers: {
          Authorization: `Bearer ${token}`,
        },
      })
    },
    async login({ org_id, email, password }: LoginInput) {
      const data = await apiRequest('/auth/login', {
        method: 'POST',
        body: JSON.stringify({ org_id, email, password }),
      })
      const me = await apiRequest('/me', {
        method: 'GET',
        headers: {
          Authorization: `Bearer ${data.token}`,
        },
      })
      const next = {
        accessToken: data.token,
        refreshToken: data.refresh_token,
        expiresAt: data.expires_at,
        refreshExpiresAt: data.refresh_expires_at,
        userName: me.display_name,
        user: me,
      }
      setAuth(next)
      saveAuth(next)
      return next
    },
    async logout() {
      if (auth?.accessToken) {
        await apiRequest('/auth/logout', {
          method: 'POST',
          headers: {
            Authorization: `Bearer ${auth.accessToken}`,
          },
        })
      }
      setAuth(null)
      saveAuth(null)
    },
  }), [auth])

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) {
    throw new Error('useAuth must be used within AuthProvider')
  }
  return ctx
}
