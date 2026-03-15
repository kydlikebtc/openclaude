'use client'

import { useEffect, useState, useCallback } from 'react'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { billingApi, TransactionRecord, BalanceResponse } from '@/lib/api'
import { DollarSign, Wallet, Plus } from 'lucide-react'

const PRESET_AMOUNTS = ['10', '50', '100', '500']

export default function BillingPage() {
  const [balance, setBalance] = useState<BalanceResponse | null>(null)
  const [transactions, setTransactions] = useState<TransactionRecord[]>([])
  const [loading, setLoading] = useState(true)
  const [rechargeAmount, setRechargeAmount] = useState('50')
  const [isRecharging, setIsRecharging] = useState(false)

  const fetchData = useCallback(async () => {
    try {
      const [balRes, txRes] = await Promise.all([
        billingApi.balance(),
        billingApi.transactions(20),
      ])
      setBalance(balRes.data)
      setTransactions(txRes.data)
    } catch {
      toast.error('Failed to load billing data')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchData()
  }, [fetchData])

  const handleRecharge = async (e: React.FormEvent) => {
    e.preventDefault()
    const amount = parseFloat(rechargeAmount)
    if (isNaN(amount) || amount <= 0) {
      toast.error('Please enter a valid amount')
      return
    }
    setIsRecharging(true)
    try {
      await billingApi.recharge(rechargeAmount)
      toast.success(`$${amount.toFixed(2)} added to your balance`)
      await fetchData()
    } catch {
      toast.error('Recharge failed. Please try again.')
    } finally {
      setIsRecharging(false)
    }
  }

  const txTypeBadge = (type: string) => {
    switch (type) {
      case 'recharge': return <Badge className="bg-green-100 text-green-800 hover:bg-green-100">Recharge</Badge>
      case 'api_call': return <Badge variant="secondary">API Call</Badge>
      default: return <Badge variant="outline">{type}</Badge>
    }
  }

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-slate-900">Billing</h1>
        <p className="text-slate-500 mt-1">Manage your balance and view transaction history</p>
      </div>

      <div className="grid md:grid-cols-2 gap-6 mb-8">
        {/* Balance card */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-slate-600">Current Balance</CardTitle>
            <Wallet className="h-4 w-4 text-green-500" />
          </CardHeader>
          <CardContent>
            <div className="text-4xl font-bold text-green-600">
              {loading ? '—' : `$${parseFloat(balance?.balance ?? '0').toFixed(2)}`}
            </div>
            <p className="text-xs text-slate-500 mt-1">Available USDT balance</p>
          </CardContent>
        </Card>

        {/* Recharge card */}
        <Card className="border-orange-200">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-slate-600">Add Funds</CardTitle>
            <DollarSign className="h-4 w-4 text-orange-500" />
          </CardHeader>
          <CardContent>
            <form onSubmit={handleRecharge}>
              <div className="flex gap-2 mb-3 flex-wrap">
                {PRESET_AMOUNTS.map((amount) => (
                  <Button
                    key={amount}
                    type="button"
                    size="sm"
                    variant={rechargeAmount === amount ? 'default' : 'outline'}
                    className={rechargeAmount === amount ? 'bg-orange-500 hover:bg-orange-600' : ''}
                    onClick={() => setRechargeAmount(amount)}
                  >
                    ${amount}
                  </Button>
                ))}
              </div>
              <div className="flex gap-2">
                <div className="flex-1">
                  <Label htmlFor="amount" className="sr-only">Amount</Label>
                  <Input
                    id="amount"
                    type="number"
                    min="1"
                    step="0.01"
                    placeholder="Custom amount"
                    value={rechargeAmount}
                    onChange={(e) => setRechargeAmount(e.target.value)}
                  />
                </div>
                <Button
                  type="submit"
                  className="bg-orange-500 hover:bg-orange-600"
                  disabled={isRecharging}
                >
                  <Plus size={16} className="mr-1" />
                  {isRecharging ? 'Processing…' : 'Add Funds'}
                </Button>
              </div>
              <p className="text-xs text-slate-400 mt-2">
                Accepts USDT, USDC, TAO · Demo mode: funds credited instantly
              </p>
            </form>
          </CardContent>
        </Card>
      </div>

      {/* Transaction history */}
      <Card>
        <CardHeader>
          <CardTitle>Transaction History</CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <p className="text-slate-500 py-8 text-center">Loading transactions…</p>
          ) : transactions.length === 0 ? (
            <p className="text-slate-500 py-8 text-center">No transactions yet.</p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Type</TableHead>
                  <TableHead>Amount</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Date</TableHead>
                  <TableHead>Description</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {transactions.map((tx) => (
                  <TableRow key={tx.id}>
                    <TableCell>{txTypeBadge(tx.type)}</TableCell>
                    <TableCell className={parseFloat(tx.amount) >= 0 ? 'text-green-600 font-medium' : 'text-red-600 font-medium'}>
                      {parseFloat(tx.amount) >= 0 ? '+' : ''}${Math.abs(parseFloat(tx.amount)).toFixed(4)}
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline" className="text-slate-600">
                        {tx.status}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-slate-500">
                      {new Date(tx.created_at).toLocaleDateString()}
                    </TableCell>
                    <TableCell className="text-slate-500 text-sm">
                      {tx.description ?? '—'}
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
