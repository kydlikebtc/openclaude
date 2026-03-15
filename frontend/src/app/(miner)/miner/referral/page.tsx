'use client'

import { useState } from 'react'
import { toast } from 'sonner'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Copy, Users, Gift, TrendingUp } from 'lucide-react'

// Placeholder data — will be replaced when referral API is available
const DEMO_REFERRAL_CODE = 'MINER-X8K3P'
const DEMO_REFERRALS = [
  { address: '5Grw...QpDW', joinedAt: '2024-01-15', earnings: '0.42 TAO', status: 'active' },
  { address: '5FHn...M694', joinedAt: '2024-01-22', earnings: '0.18 TAO', status: 'active' },
  { address: '5DAn...9kwh', joinedAt: '2024-02-01', earnings: '0.03 TAO', status: 'inactive' },
]

export default function MinerReferralPage() {
  const [copied, setCopied] = useState(false)

  const copyCode = () => {
    navigator.clipboard.writeText(DEMO_REFERRAL_CODE).then(() => {
      setCopied(true)
      toast.success('Referral code copied!')
      setTimeout(() => setCopied(false), 2000)
    })
  }

  return (
    <div className="p-8 max-w-3xl">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-slate-900">Referral Program</h1>
        <p className="text-slate-500 mt-1">Invite other miners and earn bonus rewards</p>
      </div>

      {/* Referral code */}
      <Card className="mb-6 border-orange-200 bg-gradient-to-br from-orange-50 to-amber-50">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-orange-800">
            <Gift size={18} />
            Your Referral Code
          </CardTitle>
          <CardDescription className="text-orange-700">
            Share this code with new miners. Earn 5% of their TAO earnings for 90 days.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex gap-2">
            <Input
              value={DEMO_REFERRAL_CODE}
              readOnly
              className="font-mono text-lg font-bold bg-white border-orange-200 text-orange-900"
            />
            <Button
              onClick={copyCode}
              className="bg-orange-500 hover:bg-orange-600 shrink-0"
            >
              <Copy size={16} className="mr-2" />
              {copied ? 'Copied!' : 'Copy'}
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Stats */}
      <div className="grid grid-cols-3 gap-4 mb-6">
        <Card>
          <CardContent className="pt-6">
            <div className="text-2xl font-bold">{DEMO_REFERRALS.length}</div>
            <p className="text-xs text-slate-500 flex items-center gap-1 mt-1">
              <Users size={12} /> Total referrals
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-2xl font-bold text-green-600">0.63</div>
            <p className="text-xs text-slate-500 flex items-center gap-1 mt-1">
              <TrendingUp size={12} /> TAO earned
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-2xl font-bold">
              {DEMO_REFERRALS.filter((r) => r.status === 'active').length}
            </div>
            <p className="text-xs text-slate-500 mt-1">Active referrals</p>
          </CardContent>
        </Card>
      </div>

      {/* Referral list */}
      <Card>
        <CardHeader>
          <CardTitle>Referred Miners</CardTitle>
        </CardHeader>
        <CardContent>
          {DEMO_REFERRALS.length === 0 ? (
            <p className="text-slate-500 text-center py-8">No referrals yet. Share your code to get started!</p>
          ) : (
            <div className="space-y-3">
              {DEMO_REFERRALS.map((ref, i) => (
                <div key={i} className="flex items-center justify-between p-3 rounded-lg bg-slate-50">
                  <div>
                    <code className="text-sm font-mono">{ref.address}</code>
                    <p className="text-xs text-slate-400">Joined {ref.joinedAt}</p>
                  </div>
                  <div className="text-right flex items-center gap-3">
                    <span className="text-sm font-medium text-green-600">+{ref.earnings}</span>
                    <Badge variant={ref.status === 'active' ? 'default' : 'secondary'}>
                      {ref.status}
                    </Badge>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
