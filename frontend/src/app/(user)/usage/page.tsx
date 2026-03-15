'use client'

import { useEffect, useState } from 'react'
import { toast } from 'sonner'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { billingApi, UsageSummary } from '@/lib/api'

type Period = 'today' | 'week' | 'month'

// Simulated model-breakdown data (real endpoint breakdown coming in future)
const mockModelData = [
  { model: 'claude-opus-4-6', tokens: 42000, cost: 0.84 },
  { model: 'claude-sonnet-4-6', tokens: 180000, cost: 1.26 },
  { model: 'claude-haiku-4-5', tokens: 320000, cost: 0.64 },
]

export default function UsagePage() {
  const [period, setPeriod] = useState<Period>('month')
  const [summary, setSummary] = useState<UsageSummary | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setLoading(true)
    billingApi.usage(period)
      .then(({ data }) => setSummary(data))
      .catch(() => toast.error('Failed to load usage data'))
      .finally(() => setLoading(false))
  }, [period])

  return (
    <div className="p-8">
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Usage Statistics</h1>
          <p className="text-slate-500 mt-1">Track your API usage and costs</p>
        </div>
        <Tabs value={period} onValueChange={(v) => setPeriod(v as Period)}>
          <TabsList>
            <TabsTrigger value="today">Today</TabsTrigger>
            <TabsTrigger value="week">This Week</TabsTrigger>
            <TabsTrigger value="month">This Month</TabsTrigger>
          </TabsList>
        </Tabs>
      </div>

      {/* Summary cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-slate-500">Total Tokens</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">
              {loading ? '—' : summary?.total_tokens.toLocaleString() ?? '0'}
            </div>
            <p className="text-xs text-slate-400 mt-1">Input + output</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-slate-500">Requests</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">
              {loading ? '—' : summary?.request_count.toLocaleString() ?? '0'}
            </div>
            <p className="text-xs text-slate-400 mt-1">API calls made</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-slate-500">Total Cost</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-orange-600">
              {loading ? '—' : `$${parseFloat(summary?.total_cost ?? '0').toFixed(4)}`}
            </div>
            <p className="text-xs text-slate-400 mt-1">USD equivalent</p>
          </CardContent>
        </Card>
      </div>

      {/* Model breakdown chart */}
      <Card>
        <CardHeader>
          <CardTitle>Usage by Model</CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={mockModelData}>
              <CartesianGrid strokeDasharray="3 3" className="opacity-30" />
              <XAxis dataKey="model" tick={{ fontSize: 11 }} />
              <YAxis tick={{ fontSize: 11 }} />
              <Tooltip
                formatter={(v: number, name: string) =>
                  name === 'tokens' ? [v.toLocaleString(), 'Tokens'] : [`$${v.toFixed(4)}`, 'Cost']
                }
              />
              <Legend />
              <Bar dataKey="tokens" fill="#f97316" name="tokens" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>
    </div>
  )
}
