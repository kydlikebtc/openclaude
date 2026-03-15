import axios from 'axios'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export const api = axios.create({
  baseURL: `${API_BASE_URL}/api/v1`,
  headers: { 'Content-Type': 'application/json' },
  withCredentials: true, // Send httpOnly cookies automatically
})

// Redirect to login on 401
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401 && typeof window !== 'undefined') {
      window.location.href = '/login'
    }
    return Promise.reject(error)
  },
)

// ─── Auth ────────────────────────────────────────────────────────────────────
export interface TokenResponse {
  access_token: string
  token_type: string
}

export interface UserResponse {
  id: string
  email: string
  status: string
}

export const authApi = {
  register: (email: string, password: string) =>
    api.post<TokenResponse>('/auth/register', { email, password }),

  login: (email: string, password: string) =>
    api.post<TokenResponse>('/auth/login', { email, password }),

  logout: () => api.post('/auth/logout'),

  me: () => api.get<UserResponse>('/auth/me'),
}

// ─── API Keys ─────────────────────────────────────────────────────────────────
export interface ApiKeyResponse {
  id: string
  name: string
  key_prefix: string
  rate_limit: number
  is_active: boolean
  created_at: string
}

export interface ApiKeyCreatedResponse extends ApiKeyResponse {
  key: string
}

export const apiKeysApi = {
  list: () => api.get<ApiKeyResponse[]>('/api-keys'),

  create: (name: string, rate_limit: number = 60) =>
    api.post<ApiKeyCreatedResponse>('/api-keys', { name, rate_limit }),

  revoke: (keyId: string) => api.delete(`/api-keys/${keyId}`),
}

// ─── Billing ──────────────────────────────────────────────────────────────────
export interface BalanceResponse {
  balance: string
}

export interface TransactionRecord {
  id: string
  type: string
  amount: string
  status: string
  created_at: string
  description: string | null
}

export interface UsageSummary {
  total_tokens: number
  total_cost: string
  request_count: number
  period: string
}

export const billingApi = {
  balance: () => api.get<BalanceResponse>('/billing/balance'),

  recharge: (amount: string) =>
    api.post('/billing/recharge', { amount }),

  transactions: (limit = 50) =>
    api.get<TransactionRecord[]>(`/billing/transactions?limit=${limit}`),

  usage: (period: 'today' | 'week' | 'month' = 'month') =>
    api.get<UsageSummary>(`/billing/usage?period=${period}`),
}

// ─── Miners ───────────────────────────────────────────────────────────────────
export interface MinerResponse {
  id: string
  hotkey: string
  name: string | null
  status: string
  stake_amount: string
  referral_code: string | null
  score: number
  created_at: string
}

export interface MinerEarningsRecord {
  date: string
  requests: number
  tokens_in: number
  tokens_out: number
  gross_revenue: string
  earnings: string
}

export interface MinerEarningsResponse {
  miner_id: string
  hotkey: string
  stake_amount: string
  revenue_share_pct: number
  total_gross_revenue: string
  total_earnings: string
  daily: MinerEarningsRecord[]
  start: string
  end: string
}

export const minersApi = {
  list: (status?: string) =>
    api.get<MinerResponse[]>(`/miners${status ? `?status_filter=${status}` : ''}`),

  register: (data: {
    hotkey: string
    coldkey: string
    name?: string
    api_key: string
    supported_models: string[]
  }) => api.post<MinerResponse>('/miners/register', data),

  poolStatus: () => api.get('/miners/pool'),

  earnings: (minerId: string, days = 30) =>
    api.get<MinerEarningsResponse>(`/miners/${minerId}/earnings?days=${days}`),
}
