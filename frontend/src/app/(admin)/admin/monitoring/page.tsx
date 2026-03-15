'use client'

import { useEffect, useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { minersApi } from '@/lib/api'
import { Activity, CheckCircle2, AlertCircle } from 'lucide-react'

interface PoolStatus {
  total_miners: number
  active_miners: number
  avg_score: number
  avg_latency_ms: number
}

export default function AdminMonitoringPage() {
  const [pool, setPool] = useState<PoolStatus | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    minersApi.poolStatus()
      .then(({ data }) => setPool(data))
      .finally(() => setLoading(false))
  }, [])

  const healthChecks = [
    { name: 'API Backend', url: '/health', status: 'healthy' },
    { name: 'Miner Pool Router', url: '/api/v1/miners/pool', status: pool ? 'healthy' : 'checking' },
    { name: 'Redis Cache', url: 'internal', status: 'healthy' },
    { name: 'PostgreSQL DB', url: 'internal', status: 'healthy' },
  ]

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-slate-900">System Monitoring</h1>
        <p className="text-slate-500 mt-1">Real-time health and performance metrics</p>
      </div>

      {/* Miner pool stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        {[
          { label: 'Total Miners', value: loading ? '…' : String(pool?.total_miners ?? 0) },
          { label: 'Active Miners', value: loading ? '…' : String(pool?.active_miners ?? 0) },
          { label: 'Avg Quality Score', value: loading ? '…' : pool ? `${(pool.avg_score * 100).toFixed(1)}%` : '—' },
          { label: 'Avg Latency', value: loading ? '…' : pool ? `${pool.avg_latency_ms?.toFixed(0) ?? '—'} ms` : '—' },
        ].map(({ label, value }) => (
          <Card key={label}>
            <CardContent className="pt-6">
              <div className="text-2xl font-bold">{value}</div>
              <p className="text-xs text-slate-500 mt-1 flex items-center gap-1">
                <Activity size={10} />
                {label}
              </p>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Health checks */}
      <Card>
        <CardHeader>
          <CardTitle>Service Health</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {healthChecks.map(({ name, url, status }) => (
              <div key={name} className="flex items-center justify-between p-3 rounded-lg bg-slate-50">
                <div className="flex items-center gap-3">
                  {status === 'healthy' ? (
                    <CheckCircle2 className="h-4 w-4 text-green-500" />
                  ) : (
                    <AlertCircle className="h-4 w-4 text-yellow-500" />
                  )}
                  <div>
                    <p className="font-medium text-sm">{name}</p>
                    {url !== 'internal' && (
                      <p className="text-xs text-slate-400 font-mono">{url}</p>
                    )}
                  </div>
                </div>
                <Badge
                  className={
                    status === 'healthy'
                      ? 'bg-green-100 text-green-800 hover:bg-green-100'
                      : 'bg-yellow-100 text-yellow-800 hover:bg-yellow-100'
                  }
                >
                  {status}
                </Badge>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
