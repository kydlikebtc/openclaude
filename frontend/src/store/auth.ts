import { create } from 'zustand'
import { authApi, UserResponse } from '@/lib/api'

interface AuthState {
  user: UserResponse | null
  isLoading: boolean
  login: (email: string, password: string) => Promise<void>
  register: (email: string, password: string) => Promise<void>
  logout: () => Promise<void>
  fetchMe: () => Promise<void>
}

export const useAuthStore = create<AuthState>()((set, get) => ({
  user: null,
  isLoading: false,

  login: async (email, password) => {
    set({ isLoading: true })
    try {
      // Server sets httpOnly cookie — no token handling needed here
      await authApi.login(email, password)
      await get().fetchMe()
    } finally {
      set({ isLoading: false })
    }
  },

  register: async (email, password) => {
    set({ isLoading: true })
    try {
      await authApi.register(email, password)
      await get().fetchMe()
    } finally {
      set({ isLoading: false })
    }
  },

  logout: async () => {
    try {
      await authApi.logout()
    } finally {
      set({ user: null })
    }
  },

  fetchMe: async () => {
    const { data } = await authApi.me()
    set({ user: data })
  },
}))
