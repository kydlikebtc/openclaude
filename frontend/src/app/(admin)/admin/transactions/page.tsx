import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Info } from 'lucide-react'

export default function AdminTransactionsPage() {
  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-slate-900">Transactions</h1>
        <p className="text-slate-500 mt-1">Financial records and billing history</p>
      </div>

      <Card className="border-blue-200 bg-blue-50">
        <CardHeader className="flex flex-row items-start gap-3">
          <Info className="h-5 w-5 text-blue-500 mt-0.5 shrink-0" />
          <div>
            <CardTitle className="text-base text-blue-800">Admin Transaction API Pending</CardTitle>
            <p className="text-sm text-blue-700 mt-1">
              Cross-user transaction history requires{' '}
              <code className="bg-blue-100 px-1 rounded">GET /api/v1/admin/transactions</code>{' '}
              with admin scope. Individual user billing is available via the billing API.
            </p>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            <p className="text-sm text-blue-700 font-medium">Planned Features:</p>
            <ul className="space-y-1 text-sm text-blue-600">
              {[
                'All transactions across all users',
                'Revenue analytics and reports',
                'Export to CSV/Excel',
                'Refund processing',
                'Miner payout tracking',
              ].map((f) => (
                <li key={f} className="flex items-center gap-2">
                  <Badge variant="outline" className="text-blue-600 border-blue-300 text-xs">Planned</Badge>
                  {f}
                </li>
              ))}
            </ul>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
