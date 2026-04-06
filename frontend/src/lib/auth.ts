'use client'

import { create } from 'zustand'

const API_URL = process.env.NEXT_PUBLIC_API_URL || ''

export interface UserProfile {
  id: number
  email: string
  full_name: string | null
  subscription_plan: string
  subscription_expires_at: string | null
  has_active_subscription: boolean
  created_at: string
}

interface AuthState {
  user: UserProfile | null
  token: string | null
  isLoading: boolean
  error: string | null
  login: (email: string, password: string) => Promise<boolean>
  register: (email: string, password: string, fullName?: string) => Promise<boolean>
  logout: () => void
  fetchMe: () => Promise<void>
  clearError: () => void
}

export const useAuth = create<AuthState>((set, get) => ({
  user: null,
  token: typeof window !== 'undefined' ? localStorage.getItem('sp_token') : null,
  isLoading: false,
  error: null,

  login: async (email, password) => {
    set({ isLoading: true, error: null })
    try {
      const res = await fetch(`${API_URL}/api/v1/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      })
      if (!res.ok) {
        const err = await res.json().catch(() => ({}))
        set({ error: err.detail || 'Ошибка входа', isLoading: false })
        return false
      }
      const data = await res.json()
      localStorage.setItem('sp_token', data.access_token)
      localStorage.setItem('sp_refresh', data.refresh_token)
      set({ token: data.access_token, isLoading: false })
      await get().fetchMe()
      return true
    } catch {
      set({ error: 'Ошибка сети', isLoading: false })
      return false
    }
  },

  register: async (email, password, fullName) => {
    set({ isLoading: true, error: null })
    try {
      const res = await fetch(`${API_URL}/api/v1/auth/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password, full_name: fullName || null }),
      })
      if (!res.ok) {
        const err = await res.json().catch(() => ({}))
        set({ error: err.detail || 'Ошибка регистрации', isLoading: false })
        return false
      }
      const data = await res.json()
      localStorage.setItem('sp_token', data.access_token)
      localStorage.setItem('sp_refresh', data.refresh_token)
      set({ token: data.access_token, isLoading: false })
      await get().fetchMe()
      return true
    } catch {
      set({ error: 'Ошибка сети', isLoading: false })
      return false
    }
  },

  logout: () => {
    localStorage.removeItem('sp_token')
    localStorage.removeItem('sp_refresh')
    set({ user: null, token: null })
  },

  fetchMe: async () => {
    const token = get().token || localStorage.getItem('sp_token')
    if (!token) return
    try {
      const res = await fetch(`${API_URL}/api/v1/auth/me`, {
        headers: { Authorization: `Bearer ${token}` },
      })
      if (res.ok) {
        const user = await res.json()
        set({ user, token })
      } else {
        localStorage.removeItem('sp_token')
        set({ user: null, token: null })
      }
    } catch {
      // silent fail
    }
  },

  clearError: () => set({ error: null }),
}))

// Auth-aware fetch helper
export async function authFetch(path: string, options: RequestInit = {}) {
  const token = localStorage.getItem('sp_token')
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string> || {}),
  }
  if (token) headers.Authorization = `Bearer ${token}`
  return fetch(`${API_URL}${path}`, { ...options, headers })
}
