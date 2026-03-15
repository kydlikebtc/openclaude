'use client'

import { useEffect, useState } from 'react'
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { billingApi, UsageSummary, BalanceResponse } from '@/lib/api'
import { DollarSign, Cpu, Activity, TrendingUp } from 'lucide-react'

// Mock chart data (will be replaced with real API when usage-by-day endpoint is available)
const mockChartData = Array.from({ length: 14 }, (_, i) => ({
  date: new Date(Date.now() - (13 - i) * 86400000).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
  tokens: Math.floor(Math.random() * 50000) + 5000,
  cost: (Math.random() * 2 + 0.1).toFixed(3),
}))

export default function DashboardPage() {
  const [balance, setBalance] = useState<BalanceResponse | null>(null)
  const [usage, setUsage] = useState<UsageSummary | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([billingApi.balance(), billingApi.usage('month')])
      .then(([balRes, usageRes]) => {
        setBalance(balRes.data)
        setUsage(usageRes.data)
      })
      .finally(() => setLoading(false))
  }, [])

  const stats = [
    {
      title: 'Account Balance',
      value: balance ? `$${parseFloat(balance.balance).toFixed(2)}` : '—',
      icon: DollarSign,
      description: 'Current USDT balance',
      color: 'text-green-500',
    },
    {
      title: 'Tokens This Month',
      value: usage ? usage.total_tokens.toLocaleString() : '—',
      icon: Cpu,
      description: 'Input + output tokens',
      color: 'text-blue-500',
    },
    {
      title: 'Requests This Month',
      value: usage ? usage.request_count.toLocaleString() : '—',
      icon: Activity,
      description: 'Total API calls',
      color: 'text-purple-500',
    },
    {
      title: 'Spend This Month',
      value: usage ? `$${parseFloat(usage.total_cost).toFixed(4)}` : '—',
      icon: TrendingUp,
      description: 'Total cost',
      color: 'text-orange-500',
    },
  ]

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-slate-900">Dashboard</h1>
        <p className="text-slate-500 mt-1">Monitor your API usage and account status</p>
      </div>

      {/* Stats grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        {stats.map(({ title, value, icon: Icon, description, color }) => (
          <Card key={title}>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium text-slate-600">{title}</CardTitle>
              <Icon className={cn('h-4 w-4', color)} />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {loading ? <span className="text-slate-300">Loading…</span> : value}
              </div>
              <p className="text-xs text-slate-500 mt-1">{description}</p>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Usage chart */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle>Token Usage (Last 14 Days)</CardTitle>
          <Badge variant="outline">Demo data</Badge>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={260}>
            <AreaChart data={mockChartData}>
              <defs>
                <linearGradient id="tokenGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#f97316" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#f97316" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" className="opacity-30" />
              <XAxis dataKey="date" tick={{ fontSize: 12 }} />
              <YAxis tick={{ fontSize: 12 }} />
              <Tooltip
                formatter={(v) => [Number(v).toLocaleString(), 'Tokens']}
              />
              <Area
                type="monotone"
                dataKey="tokens"
                stroke="#f97316"
                fill="url(#tokenGradient)"
                strokeWidth={2}
              />
            </AreaChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      {/* Quick start */}
      <Card className="mt-6 border-orange-200 bg-orange-50">
        <CardHeader>
          <CardTitle className="text-orange-800">Quick Start</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-orange-700 mb-3">
            Replace your Anthropic API base URL to start using OpenClade:
          </p>
          <pre className="bg-orange-900 text-orange-100 rounded-lg p-4 text-sm overflow-x-auto">
            {`import anthropic

client = anthropic.Anthropic(
    base_url="https://api.openclade.io",
    api_key="YOUR_OPENCLADE_KEY",
)

message = client.messages.create(
    model="claude-opus-4-5",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Hello, Claude!"}]
)`}
          </pre>
        </CardContent>
      </Card>
    </div>
  )
}

function cn(...classes: (string | boolean | undefined)[]) {
  return classes.filter(Boolean).join(' ')
}
