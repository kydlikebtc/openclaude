import Link from 'next/link'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

export default function Home() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 text-white">
      {/* Header */}
      <header className="border-b border-white/10 px-6 py-4">
        <div className="max-w-6xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-xl font-bold">OpenClade</span>
            <Badge variant="outline" className="text-xs border-orange-400/50 text-orange-400">
              Beta
            </Badge>
          </div>
          <nav className="flex items-center gap-4">
            <Link href="/docs" className="text-sm text-slate-400 hover:text-white transition-colors">
              Docs
            </Link>
            <Link href="/login">
              <Button variant="ghost" size="sm">Log in</Button>
            </Link>
            <Link href="/register">
              <Button size="sm" className="bg-orange-500 hover:bg-orange-600">
                Get Started
              </Button>
            </Link>
          </nav>
        </div>
      </header>

      {/* Hero */}
      <main className="max-w-6xl mx-auto px-6 py-24 text-center">
        <Badge className="mb-6 bg-orange-500/20 text-orange-400 border-orange-400/30">
          Powered by Bittensor TAO Subnet
        </Badge>
        <h1 className="text-5xl md:text-6xl font-bold mb-6 leading-tight">
          Decentralized Claude API
          <br />
          <span className="text-orange-400">for Everyone</span>
        </h1>
        <p className="text-xl text-slate-400 mb-10 max-w-2xl mx-auto">
          Access Anthropic&apos;s Claude models through a decentralized network of miners.
          Pay-as-you-go, no subscriptions, competitive pricing.
        </p>
        <div className="flex gap-4 justify-center flex-wrap">
          <Link href="/register">
            <Button size="lg" className="bg-orange-500 hover:bg-orange-600 text-white px-8">
              Start Building Free
            </Button>
          </Link>
          <Link href="/docs">
            <Button size="lg" variant="outline" className="border-white/20 text-white hover:bg-white/10 px-8">
              View Docs
            </Button>
          </Link>
        </div>

        {/* Feature cards */}
        <div className="grid md:grid-cols-3 gap-6 mt-24">
          <Card className="bg-white/5 border-white/10 text-white">
            <CardHeader>
              <CardTitle className="text-lg">OpenAI-Compatible</CardTitle>
            </CardHeader>
            <CardContent className="text-slate-400 text-sm">
              Drop-in replacement for Anthropic&apos;s API. Just change the base URL and API key.
            </CardContent>
          </Card>
          <Card className="bg-white/5 border-white/10 text-white">
            <CardHeader>
              <CardTitle className="text-lg">Decentralized</CardTitle>
            </CardHeader>
            <CardContent className="text-slate-400 text-sm">
              Powered by a network of miners on Bittensor&apos;s TAO subnet. No single point of failure.
            </CardContent>
          </Card>
          <Card className="bg-white/5 border-white/10 text-white">
            <CardHeader>
              <CardTitle className="text-lg">Earn as a Miner</CardTitle>
            </CardHeader>
            <CardContent className="text-slate-400 text-sm">
              Contribute your Claude API keys to the network and earn TAO rewards based on performance.
            </CardContent>
          </Card>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-white/10 py-8 text-center text-slate-500 text-sm">
        <div className="max-w-6xl mx-auto px-6 flex justify-between items-center flex-wrap gap-4">
          <span>© 2024 OpenClade. All rights reserved.</span>
          <div className="flex gap-6">
            <Link href="/miner/register" className="hover:text-white transition-colors">
              Become a Miner
            </Link>
            <Link href="/admin" className="hover:text-white transition-colors">
              Admin
            </Link>
          </div>
        </div>
      </footer>
    </div>
  )
}
