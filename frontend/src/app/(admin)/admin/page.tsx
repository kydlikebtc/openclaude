'use client'

import { useEffect, useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { minersApi } from '@/lib/api'
import { Users, Cpu, DollarSign, Activity } from 'lucide-react'

export default function AdminOverviewPage() {
  const [minerCount, setMinerCount] = useState<number | null>(null)
  const [activeMiners, setActiveMiners] = useState<number | null>(null)

  useEffect(() => {
    minersApi.list().then(({ data }) => {
      setMinerCount(data.length)
      setActiveMiners(data.filter((m) => m.status === 'active').length)
    })
  }, [])

  const stats = [
    { title: 'Total Users', value: '—', icon: Users, desc: 'Registered accounts', color: 'text-blue-500' },
    { title: 'Total Miners', value: minerCount !== null ? String(minerCount) : '…', icon: Cpu, desc: `${activeMiners ?? '…'} active`, color: 'text-purple-500' },
    { title: 'Total Revenue', value: '—', icon: DollarSign, desc: 'All-time USDT', color: 'text-green-500' },
    { title: 'API Requests', value: '—', icon: Activity, desc: 'All time', color: 'text-orange-500' },
  ]

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-slate-900">Admin Overview</h1>
        <p className="text-slate-500 mt-1">System health and key metrics at a glance</p>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        {stats.map(({ title, value, icon: Icon, desc, color }) => (
          <Card key={title}>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium text-slate-600">{title}</CardTitle>
              <Icon className={`h-4 w-4 ${color}`} />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{value}</div>
              <p className="text-xs text-slate-500 mt-1">{desc}</p>
            </CardContent>
          </Card>
        ))}
      </div>

      <Card>
        <CardHeader>
          <CardTitle>System Status</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {[
              { name: 'API Gateway', status: 'Operational' },
              { name: 'Database (PostgreSQL)', status: 'Operational' },
              { name: 'Cache (Redis)', status: 'Operational' },
              { name: 'Miner Pool Router', status: 'Operational' },
              { name: 'Bittensor Subnet', status: 'Monitoring' },
            ].map(({ name, status }) => (
              <div key={name} className="flex items-center justify-between py-2 border-b last:border-0">
                <span className="text-sm font-medium">{name}</span>
                <span className={`text-xs px-2 py-1 rounded-full font-medium ${
                  status === 'Operational'
                    ? 'bg-green-100 text-green-800'
                    : 'bg-yellow-100 text-yellow-800'
                }`}>
                  {status}
                </span>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
