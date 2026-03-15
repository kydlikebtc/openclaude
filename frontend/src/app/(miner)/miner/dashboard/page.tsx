'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { toast } from 'sonner'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { minersApi, MinerResponse } from '@/lib/api'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar } from 'recharts'
import { Award, Cpu, Users, TrendingUp, Wifi, WifiOff } from 'lucide-react'

interface PoolStats {
  total_miners: number
  active_miners: number
  avg_score: number
}

export default function MinerDashboardPage() {
  const [miners, setMiners] = useState<MinerResponse[]>([])
  const [poolStats, setPoolStats] = useState<PoolStats | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([minersApi.list(), minersApi.poolStatus()])
      .then(([minerRes, poolRes]) => {
        setMiners(minerRes.data)
        setPoolStats(poolRes.data)
      })
      .catch(() => toast.error('Failed to load miner data'))
      .finally(() => setLoading(false))
  }, [])

  const statusColor = (status: string) => {
    switch (status) {
      case 'active': return 'bg-green-100 text-green-800'
      case 'inactive': return 'bg-slate-100 text-slate-600'
      default: return 'bg-yellow-100 text-yellow-800'
    }
  }

  // Build score distribution chart from live miner data
  const scoreDistribution = loading ? [] : (() => {
    const buckets: Record<string, number> = {
      '0–20%': 0, '20–40%': 0, '40–60%': 0, '60–80%': 0, '80–100%': 0,
    }
    miners.forEach((m) => {
      const pct = m.score * 100
      if (pct < 20) buckets['0–20%']++
      else if (pct < 40) buckets['20–40%']++
      else if (pct < 60) buckets['40–60%']++
      else if (pct < 80) buckets['60–80%']++
      else buckets['80–100%']++
    })
    return Object.entries(buckets).map(([range, count]) => ({ range, count }))
  })()

  const activeMinersList = miners.filter((m) => m.status === 'active')

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-slate-900">Miner Dashboard</h1>
        <p className="text-slate-500 mt-1">Monitor the mining network performance and earnings</p>
      </div>

      {/* Pool stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-slate-600">Total Miners</CardTitle>
            <Users className="h-4 w-4 text-blue-500" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">
              {loading ? '—' : poolStats?.total_miners ?? 0}
            </div>
            <p className="text-xs text-slate-500 mt-1">Registered in network</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-slate-600">Active Miners</CardTitle>
            <Wifi className="h-4 w-4 text-green-500" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-green-600">
              {loading ? '—' : poolStats?.active_miners ?? 0}
            </div>
            <p className="text-xs text-slate-500 mt-1">
              {poolStats && poolStats.total_miners > 0
                ? `${((poolStats.active_miners / poolStats.total_miners) * 100).toFixed(0)}% online rate`
                : 'Currently online'}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-slate-600">Avg Score</CardTitle>
            <Award className="h-4 w-4 text-purple-500" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">
              {loading ? '—' : poolStats ? (poolStats.avg_score * 100).toFixed(1) + '%' : '—'}
            </div>
            <p className="text-xs text-slate-500 mt-1">Network quality average</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-slate-600">Top Score</CardTitle>
            <TrendingUp className="h-4 w-4 text-orange-500" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">
              {loading || miners.length === 0
                ? '—'
                : (Math.max(...miners.map((m) => m.score)) * 100).toFixed(1) + '%'}
            </div>
            <p className="text-xs text-slate-500 mt-1">Best miner in network</p>
          </CardContent>
        </Card>
      </div>

      {/* Score distribution chart from real data */}
      {!loading && miners.length > 0 && (
        <Card className="mb-8">
          <CardHeader>
            <CardTitle>Score Distribution</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={scoreDistribution}>
                <CartesianGrid strokeDasharray="3 3" className="opacity-30" />
                <XAxis dataKey="range" tick={{ fontSize: 12 }} />
                <YAxis allowDecimals={false} tick={{ fontSize: 12 }} />
                <Tooltip formatter={(v) => [v, 'Miners']} />
                <Bar dataKey="count" fill="#f97316" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      )}

      {/* Active miner score snapshot */}
      {!loading && activeMinersList.length > 0 && (
        <Card className="mb-8">
          <CardHeader>
            <CardTitle>Active Miner Score Snapshot</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={220}>
              <LineChart
                data={activeMinersList.map((m, i) => ({
                  name: m.name ?? m.hotkey.slice(0, 8),
                  score: +(m.score * 100).toFixed(1),
                  index: i + 1,
                }))}
              >
                <CartesianGrid strokeDasharray="3 3" className="opacity-30" />
                <XAxis dataKey="index" tick={{ fontSize: 12 }} />
                <YAxis domain={[0, 100]} tick={{ fontSize: 12 }} unit="%" />
                <Tooltip
                  formatter={(v) => [`${v}%`, 'Score']}
                  labelFormatter={(i) => `Miner #${i}`}
                />
                <Line
                  type="monotone"
                  dataKey="score"
                  stroke="#f97316"
                  strokeWidth={2}
                  dot={{ fill: '#f97316', r: 3 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      )}

      {/* Register CTA if no miners */}
      {!loading && miners.length === 0 && (
        <Card className="mb-8 border-dashed border-orange-200 bg-orange-50/50">
          <CardContent className="py-8 text-center">
            <Cpu className="h-10 w-10 text-orange-400 mx-auto mb-3" />
            <h3 className="font-semibold text-slate-900 mb-1">No miners yet — be the first!</h3>
            <p className="text-sm text-slate-500 mb-4">
              Register your Bittensor hotkey and start earning TAO for serving Claude API requests.
            </p>
            <Link
              href="/miner/register"
              className="inline-flex items-center px-4 py-2 bg-orange-500 text-white rounded-lg text-sm font-medium hover:bg-orange-600 transition-colors"
            >
              Register Miner
            </Link>
          </CardContent>
        </Card>
      )}

      {/* Miners table */}
      {miners.length > 0 && (
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>All Miners in Network</CardTitle>
              <Cpu className="h-4 w-4 text-slate-400" />
            </div>
          </CardHeader>
          <CardContent>
            {loading ? (
              <p className="text-center text-slate-500 py-8">Loading miners…</p>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Name</TableHead>
                    <TableHead>Hotkey</TableHead>
                    <TableHead>Score</TableHead>
                    <TableHead>Stake</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Online</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {miners.map((miner) => (
                    <TableRow key={miner.id}>
                      <TableCell className="font-medium">
                        {miner.name ?? 'Unnamed Miner'}
                      </TableCell>
                      <TableCell className="font-mono text-xs text-slate-500">
                        {miner.hotkey.slice(0, 12)}…
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          <div className="w-16 h-1.5 bg-slate-200 rounded-full">
                            <div
                              className="h-full bg-orange-500 rounded-full"
                              style={{ width: `${miner.score * 100}%` }}
                            />
                          </div>
                          <span className="text-sm">{(miner.score * 100).toFixed(0)}%</span>
                        </div>
                      </TableCell>
                      <TableCell>
                        {parseFloat(miner.stake_amount).toFixed(2)} TAO
                      </TableCell>
                      <TableCell>
                        <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${statusColor(miner.status)}`}>
                          {miner.status}
                        </span>
                      </TableCell>
                      <TableCell>
                        {miner.status === 'active'
                          ? <Wifi className="h-4 w-4 text-green-500" />
                          : <WifiOff className="h-4 w-4 text-slate-300" />}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  )
}
