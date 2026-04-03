import React, { createContext, useContext, useMemo, useState } from 'react'
import { apiRequest } from '../../shared/api/client.js'

const AuthContext = createContext(null)

const STORAGE_KEY = 'ticketing.auth'

function loadAuth() {
  const raw = localStorage.getItem(STORAGE_KEY)
  if (!raw) return null
  try {
    return JSON.parse(raw)
  } catch {
    return null
  }
}

function saveAuth(auth) {
  if (!auth) {
    localStorage.removeItem(STORAGE_KEY)
    return
  }
  localStorage.setItem(STORAGE_KEY, JSON.stringify(auth))
}

export function AuthProvider({ children }) {
  const [auth, setAuth] = useState(() => loadAuth())

  const value = useMemo(() => ({
    auth,
    async fetchMe(accessToken) {
      const token = accessToken || auth?.accessToken
      if (!token) return null
      return apiRequest('/me', {
        method: 'GET',
        headers: {
          Authorization: `Bearer ${token}`,
        },
      })
    },
    async login({ org_id, email, password }) {
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
