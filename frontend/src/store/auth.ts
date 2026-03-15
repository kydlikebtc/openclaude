import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { authApi, UserResponse } from '@/lib/api'

interface AuthState {
  token: string | null
  user: UserResponse | null
  isLoading: boolean
  login: (email: string, password: string) => Promise<void>
  register: (email: string, password: string) => Promise<void>
  logout: () => void
  fetchMe: () => Promise<void>
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      token: null,
      user: null,
      isLoading: false,

      login: async (email, password) => {
        set({ isLoading: true })
        try {
          const { data } = await authApi.login(email, password)
          localStorage.setItem('access_token', data.access_token)
          set({ token: data.access_token })
          await get().fetchMe()
        } finally {
          set({ isLoading: false })
        }
      },

      register: async (email, password) => {
        set({ isLoading: true })
        try {
          const { data } = await authApi.register(email, password)
          localStorage.setItem('access_token', data.access_token)
          set({ token: data.access_token })
          await get().fetchMe()
        } finally {
          set({ isLoading: false })
        }
      },

      logout: () => {
        localStorage.removeItem('access_token')
        set({ token: null, user: null })
      },

      fetchMe: async () => {
        const { data } = await authApi.me()
        set({ user: data })
      },
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({ token: state.token }),
    },
  ),
)
