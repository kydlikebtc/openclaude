'use client'

import { useEffect, useState } from 'react'
import { toast } from 'sonner'
import { Card, CardContent, CardHeader } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { minersApi, MinerResponse } from '@/lib/api'
import { Search } from 'lucide-react'

export default function AdminMinersPage() {
  const [miners, setMiners] = useState<MinerResponse[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')

  useEffect(() => {
    minersApi.list()
      .then(({ data }) => setMiners(data))
      .catch(() => toast.error('Failed to load miners'))
      .finally(() => setLoading(false))
  }, [])

  const filtered = miners.filter(
    (m) =>
      m.hotkey.toLowerCase().includes(search.toLowerCase()) ||
      (m.name ?? '').toLowerCase().includes(search.toLowerCase()),
  )

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-slate-900">Miners</h1>
        <p className="text-slate-500 mt-1">All registered miners and their performance</p>
      </div>

      <Card>
        <CardHeader>
          <div className="flex items-center gap-3">
            <div className="relative flex-1 max-w-sm">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
              <Input
                placeholder="Search by name or hotkey…"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="pl-9"
              />
            </div>
            <Badge variant="outline">{miners.length} total</Badge>
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
                  <TableHead>Referral Code</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Registered</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filtered.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={7} className="text-center text-slate-500 py-8">
                      No miners found
                    </TableCell>
                  </TableRow>
                ) : (
                  filtered.map((miner) => (
                    <TableRow key={miner.id}>
                      <TableCell className="font-medium">
                        {miner.name ?? <span className="text-slate-400">Unnamed</span>}
                      </TableCell>
                      <TableCell className="font-mono text-xs text-slate-500">
                        {miner.hotkey.slice(0, 16)}…
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          <div className="w-12 h-1.5 bg-slate-200 rounded-full">
                            <div
                              className="h-full bg-orange-500 rounded-full"
                              style={{ width: `${miner.score * 100}%` }}
                            />
                          </div>
                          <span className="text-xs">{(miner.score * 100).toFixed(0)}%</span>
                        </div>
                      </TableCell>
                      <TableCell>{parseFloat(miner.stake_amount).toFixed(2)} TAO</TableCell>
                      <TableCell>
                        <code className="text-xs bg-slate-100 px-1 py-0.5 rounded">
                          {miner.referral_code ?? '—'}
                        </code>
                      </TableCell>
                      <TableCell>
                        <Badge
                          variant={miner.status === 'active' ? 'default' : 'secondary'}
                          className={miner.status === 'active' ? 'bg-green-100 text-green-800 hover:bg-green-100' : ''}
                        >
                          {miner.status}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-slate-500 text-sm">
                        {new Date(miner.created_at).toLocaleDateString()}
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
