'use client'

import { useEffect, useState } from 'react'
import { toast } from 'sonner'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { minersApi, MinerResponse } from '@/lib/api'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import { Award, Cpu, Users, TrendingUp } from 'lucide-react'

// Mock score history for chart
const mockScoreHistory = Array.from({ length: 7 }, (_, i) => ({
  day: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'][i],
  score: +(0.3 + Math.random() * 0.6).toFixed(3),
}))

export default function MinerDashboardPage() {
  const [miners, setMiners] = useState<MinerResponse[]>([])
  const [poolStats, setPoolStats] = useState<{
    total_miners: number
    active_miners: number
    avg_score: number
  } | null>(null)
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

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-slate-900">Miner Dashboard</h1>
        <p className="text-slate-500 mt-1">Monitor your mining performance and earnings</p>
      </div>

      {/* Pool stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-slate-600">Network Miners</CardTitle>
            <Users className="h-4 w-4 text-blue-500" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">
              {loading ? '—' : poolStats?.total_miners ?? 0}
            </div>
            <p className="text-xs text-slate-500 mt-1">
              {poolStats?.active_miners ?? 0} active
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-slate-600">Network Avg Score</CardTitle>
            <Award className="h-4 w-4 text-purple-500" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">
              {loading ? '—' : poolStats ? (poolStats.avg_score * 100).toFixed(1) + '%' : '—'}
            </div>
            <p className="text-xs text-slate-500 mt-1">Quality score average</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-slate-600">Your Rank</CardTitle>
            <TrendingUp className="h-4 w-4 text-orange-500" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">—</div>
            <p className="text-xs text-slate-500 mt-1">Register to see your rank</p>
          </CardContent>
        </Card>
      </div>

      {/* Score chart */}
      <Card className="mb-8">
        <CardHeader>
          <CardTitle>Score History (Last 7 Days)</CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={220}>
            <LineChart data={mockScoreHistory}>
              <CartesianGrid strokeDasharray="3 3" className="opacity-30" />
              <XAxis dataKey="day" tick={{ fontSize: 12 }} />
              <YAxis domain={[0, 1]} tick={{ fontSize: 12 }} />
              <Tooltip formatter={(v) => [Number(v).toFixed(3), 'Score']} />
              <Line
                type="monotone"
                dataKey="score"
                stroke="#f97316"
                strokeWidth={2}
                dot={{ fill: '#f97316' }}
              />
            </LineChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      {/* Miners table */}
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
          ) : miners.length === 0 ? (
            <p className="text-center text-slate-500 py-8">
              No miners registered yet. Be the first!
            </p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Name</TableHead>
                  <TableHead>Hotkey</TableHead>
                  <TableHead>Score</TableHead>
                  <TableHead>Stake</TableHead>
                  <TableHead>Status</TableHead>
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
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
