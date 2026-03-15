import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import Link from 'next/link'
import { Shield, Key, CheckCircle2 } from 'lucide-react'

export default function MinerApiKeysPage() {
  return (
    <div className="p-8 max-w-3xl">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-slate-900">Claude API Key Management</h1>
        <p className="text-slate-500 mt-1">
          Your Anthropic API keys are registered at the time of miner registration. Contact support to update or rotate keys.
        </p>
      </div>

      <Card className="mb-6 border-green-200">
        <CardHeader className="flex flex-row items-start gap-4">
          <Shield className="h-5 w-5 text-green-500 mt-0.5 shrink-0" />
          <div>
            <CardTitle className="text-base">Key Security</CardTitle>
            <CardDescription>
              Your Anthropic API keys are encrypted at rest using AES-256. Only your miner node
              has access to the decrypted key during request processing.
            </CardDescription>
          </div>
        </CardHeader>
      </Card>

      <Card className="mb-6">
        <CardHeader>
          <CardTitle>Key Requirements</CardTitle>
        </CardHeader>
        <CardContent>
          <ul className="space-y-3">
            {[
              'Valid Anthropic API key (sk-ant-api03-...)',
              'Sufficient balance to handle incoming requests',
              'Access to Claude models enabled on your Anthropic account',
              'Rate limits compatible with network request volume',
            ].map((req) => (
              <li key={req} className="flex items-start gap-3">
                <CheckCircle2 className="h-4 w-4 text-green-500 mt-0.5 shrink-0" />
                <span className="text-sm text-slate-700">{req}</span>
              </li>
            ))}
          </ul>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Key size={18} />
            Registered Key
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-3 p-3 bg-slate-50 rounded-lg">
            <code className="text-sm font-mono text-slate-600">sk-ant-api03-••••••••••••••••</code>
            <Badge className="bg-green-100 text-green-800 hover:bg-green-100">Active</Badge>
          </div>
          <p className="text-xs text-slate-400 mt-3">
            To rotate your key, create a new miner registration with the updated key and deactivate the old one.
          </p>
          <div className="mt-4">
            <Link href="/miner/register">
              <Button variant="outline" size="sm">
                Register New Key
              </Button>
            </Link>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
