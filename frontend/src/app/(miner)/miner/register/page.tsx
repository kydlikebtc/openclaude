'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { minersApi } from '@/lib/api'

const SUPPORTED_MODELS = [
  'claude-opus-4-6',
  'claude-sonnet-4-6',
  'claude-haiku-4-5',
]

export default function MinerRegisterPage() {
  const router = useRouter()
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [form, setForm] = useState({
    hotkey: '',
    coldkey: '',
    name: '',
    api_key: '',
  })
  const [selectedModels, setSelectedModels] = useState<string[]>(['claude-sonnet-4-6'])

  const toggleModel = (model: string) => {
    setSelectedModels((prev) =>
      prev.includes(model) ? prev.filter((m) => m !== model) : [...prev, model],
    )
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (selectedModels.length === 0) {
      toast.error('Select at least one supported model')
      return
    }
    setIsSubmitting(true)
    try {
      await minersApi.register({ ...form, supported_models: selectedModels })
      toast.success('Miner registered successfully!')
      router.push('/miner/dashboard')
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
        'Registration failed. Check your details and try again.'
      toast.error(msg)
    } finally {
      setIsSubmitting(false)
    }
  }

  const update = (field: keyof typeof form) => (e: React.ChangeEvent<HTMLInputElement>) =>
    setForm((prev) => ({ ...prev, [field]: e.target.value }))

  return (
    <div className="min-h-screen bg-slate-50 flex items-center justify-center px-4 py-12">
      <Card className="w-full max-w-lg">
        <CardHeader className="text-center">
          <Link href="/" className="text-2xl font-bold text-orange-500 mb-2 block">
            OpenClade
          </Link>
          <CardTitle>Register as a Miner</CardTitle>
          <CardDescription>
            Contribute your Claude API keys and earn TAO rewards based on performance
          </CardDescription>
        </CardHeader>
        <form onSubmit={handleSubmit}>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="hotkey">Hotkey (SS58 address)</Label>
              <Input
                id="hotkey"
                placeholder="5GrwvaEF5zXb26Fz9rcQpDWS57CtERHpNehXCPcNoHGKutQY"
                value={form.hotkey}
                onChange={update('hotkey')}
                required
                className="font-mono text-sm"
              />
              <p className="text-xs text-slate-500">Your Bittensor wallet hotkey SS58 address</p>
            </div>
            <div className="space-y-2">
              <Label htmlFor="coldkey">Coldkey (SS58 address)</Label>
              <Input
                id="coldkey"
                placeholder="5FHneW46xGXgs5mUiveU4sbTyGBzmstUspZC92UhjJM694ty"
                value={form.coldkey}
                onChange={update('coldkey')}
                required
                className="font-mono text-sm"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="name">Miner Name (optional)</Label>
              <Input
                id="name"
                placeholder="My Mining Node"
                value={form.name}
                onChange={update('name')}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="api_key">Anthropic API Key</Label>
              <Input
                id="api_key"
                type="password"
                placeholder="sk-ant-api03-..."
                value={form.api_key}
                onChange={update('api_key')}
                required
                className="font-mono text-sm"
              />
              <p className="text-xs text-slate-500">
                Your Anthropic API key will be encrypted and stored securely.
              </p>
            </div>
            <div className="space-y-2">
              <Label>Supported Models</Label>
              <div className="flex flex-wrap gap-2">
                {SUPPORTED_MODELS.map((model) => (
                  <Badge
                    key={model}
                    variant={selectedModels.includes(model) ? 'default' : 'outline'}
                    className={`cursor-pointer ${selectedModels.includes(model) ? 'bg-orange-500 hover:bg-orange-600' : ''}`}
                    onClick={() => toggleModel(model)}
                  >
                    {model}
                  </Badge>
                ))}
              </div>
            </div>
            <Button
              type="submit"
              className="w-full bg-orange-500 hover:bg-orange-600"
              disabled={isSubmitting}
            >
              {isSubmitting ? 'Registering…' : 'Register Miner'}
            </Button>
            <p className="text-xs text-center text-slate-400">
              Already registered?{' '}
              <Link href="/miner/dashboard" className="text-orange-500 hover:underline">
                Go to dashboard
              </Link>
            </p>
          </CardContent>
        </form>
      </Card>
    </div>
  )
}
