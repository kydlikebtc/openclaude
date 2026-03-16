// Force static generation — no dynamic data on landing page
export const dynamic = 'force-static'

import Link from 'next/link'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

const PRICING_TIERS = [
  {
    name: 'Founder',
    badge: 'Month 1–3',
    badgeColor: 'bg-orange-500/30 text-orange-300 border-orange-400/30',
    discount: '10%',
    description: 'of official price',
    highlight: 'Lock in forever',
    cta: 'Join as Founder',
    featured: true,
  },
  {
    name: 'Early',
    badge: 'Month 4–6',
    badgeColor: 'bg-green-500/20 text-green-400 border-green-400/30',
    discount: '15%',
    description: 'of official price',
    highlight: 'Save 85%',
    cta: 'Get Started',
    featured: false,
  },
  {
    name: 'Standard',
    badge: 'Month 7+',
    badgeColor: 'bg-slate-500/20 text-slate-400 border-slate-400/30',
    discount: '20–25%',
    description: 'of official price',
    highlight: 'Save 75–80%',
    cta: 'Get Started',
    featured: false,
  },
]

const CODE_EXAMPLE = `import anthropic

# Just change base_url and api_key
client = anthropic.Anthropic(
    base_url="https://api.openclade.io",
    api_key="YOUR_OPENCLADE_KEY",
)

message = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Hello!"}]
)
print(message.content)`

export default function Home() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 text-white">
      {/* ── Header ── */}
      <header className="sticky top-0 z-50 border-b border-white/10 bg-slate-900/80 backdrop-blur-sm px-6 py-4">
        <div className="max-w-6xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-xl font-bold">OpenClade</span>
            <Badge variant="outline" className="text-xs border-orange-400/50 text-orange-400">
              Beta
            </Badge>
          </div>
          <nav className="hidden md:flex items-center gap-6">
            <a href="#pricing" className="text-sm text-slate-400 hover:text-white transition-colors">
              Pricing
            </a>
            <a href="#miners" className="text-sm text-slate-400 hover:text-white transition-colors">
              Mine & Earn
            </a>
            <Link href="/blog" className="text-sm text-slate-400 hover:text-white transition-colors">
              Blog
            </Link>
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
          {/* Mobile nav */}
          <div className="flex md:hidden gap-2">
            <Link href="/login">
              <Button variant="ghost" size="sm">Log in</Button>
            </Link>
            <Link href="/register">
              <Button size="sm" className="bg-orange-500 hover:bg-orange-600">Get Started</Button>
            </Link>
          </div>
        </div>
      </header>

      <main>
        {/* ── Hero ── */}
        <section className="max-w-6xl mx-auto px-6 py-20 md:py-28 text-center">
          <Badge className="mb-6 bg-orange-500/20 text-orange-400 border-orange-400/30">
            Powered by Bittensor TAO Subnet
          </Badge>
          <h1 className="text-4xl md:text-6xl font-bold mb-6 leading-tight">
            Affordable Claude API Access,
            <br />
            <span className="text-orange-400">Powered by Decentralization</span>
          </h1>
          <p className="text-lg md:text-xl text-slate-400 mb-10 max-w-2xl mx-auto">
            Save 65–75% on Claude API costs through the Bittensor network.
            Pay only for what you use — no subscriptions, no commitments.
          </p>
          <div className="flex gap-4 justify-center flex-wrap mb-16">
            <Link href="/register">
              <Button size="lg" className="bg-orange-500 hover:bg-orange-600 text-white px-8">
                Get Started
              </Button>
            </Link>
            <Link href="/miner/register">
              <Button size="lg" variant="outline" className="border-white/20 text-white hover:bg-white/10 px-8">
                Become a Miner
              </Button>
            </Link>
          </div>
          {/* Stats bar */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 max-w-3xl mx-auto">
            {[
              { value: '65–75%', label: 'Cost savings' },
              { value: '100%', label: 'API compatible' },
              { value: '<100ms', label: 'Added latency' },
              { value: '24/7', label: 'Availability' },
            ].map(({ value, label }) => (
              <div key={label} className="bg-white/5 border border-white/10 rounded-xl p-4">
                <div className="text-2xl font-bold text-orange-400">{value}</div>
                <div className="text-xs text-slate-400 mt-1">{label}</div>
              </div>
            ))}
          </div>
        </section>

        {/* ── Features ── */}
        <section className="bg-white/3 border-y border-white/10 py-20">
          <div className="max-w-6xl mx-auto px-6">
            <h2 className="text-3xl font-bold text-center mb-4">Why OpenClade?</h2>
            <p className="text-slate-400 text-center mb-12 max-w-xl mx-auto">
              The most cost-efficient way to access Claude — without compromising on quality or availability.
            </p>
            <div className="grid md:grid-cols-3 gap-8">
              <Card className="bg-white/5 border-white/10 text-white">
                <CardHeader>
                  <div className="text-4xl mb-3">💸</div>
                  <CardTitle className="text-lg">Save 65–75% on Costs</CardTitle>
                </CardHeader>
                <CardContent className="text-slate-400 text-sm space-y-2">
                  <p>Access Claude Sonnet, Haiku, and Opus at a fraction of official price.</p>
                  <p>Founder members lock in <span className="text-orange-400 font-semibold">10% of official price</span> forever.</p>
                  <p>Pay-as-you-go — no subscriptions, no upfront commitment.</p>
                </CardContent>
              </Card>
              <Card className="bg-white/5 border-orange-400/20 text-white border-2">
                <CardHeader>
                  <div className="text-4xl mb-3">🔌</div>
                  <CardTitle className="text-lg flex items-center gap-2">
                    OpenAI SDK Compatible
                    <Badge className="text-xs bg-orange-500/20 text-orange-400 border-orange-400/30">Drop-in</Badge>
                  </CardTitle>
                </CardHeader>
                <CardContent className="text-slate-400 text-sm space-y-2">
                  <p>100% compatible with the official Anthropic Python and JS SDKs.</p>
                  <p>Works with the <span className="text-orange-400 font-semibold">OpenAI SDK</span> via the /v1 endpoint.</p>
                  <p>Switch in seconds — change just <span className="text-orange-400 font-semibold">one line</span> of code.</p>
                </CardContent>
              </Card>
              <Card className="bg-white/5 border-white/10 text-white">
                <CardHeader>
                  <div className="text-4xl mb-3">🌐</div>
                  <CardTitle className="text-lg">Decentralized & Uncensored</CardTitle>
                </CardHeader>
                <CardContent className="text-slate-400 text-sm space-y-2">
                  <p>Built on Bittensor — no single point of failure or control.</p>
                  <p>Traffic routes across many independent miners worldwide.</p>
                  <p>Open, transparent, censorship-resistant AI infrastructure.</p>
                </CardContent>
              </Card>
            </div>
          </div>
        </section>

        {/* ── Pricing ── */}
        <section id="pricing" className="max-w-6xl mx-auto px-6 py-20">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold mb-3">Simple, Transparent Pricing</h2>
            <p className="text-slate-400">All plans include every Claude model. Pay-as-you-go.</p>
          </div>
          <div className="grid md:grid-cols-3 gap-6">
            {PRICING_TIERS.map((tier) => (
              <Card
                key={tier.name}
                className={
                  tier.featured
                    ? 'bg-gradient-to-b from-orange-500/10 to-orange-900/5 border-orange-400/40 text-white'
                    : 'bg-white/5 border-white/10 text-white'
                }
              >
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-base">{tier.name}</CardTitle>
                    <Badge className={`text-xs ${tier.badgeColor}`}>{tier.badge}</Badge>
                  </div>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="py-4">
                    <div className={`text-5xl font-bold mb-1 ${tier.featured ? 'text-orange-400' : 'text-white'}`}>
                      {tier.discount}
                    </div>
                    <div className="text-sm text-slate-400">{tier.description}</div>
                  </div>
                  <div className={`pt-2 border-t ${tier.featured ? 'border-orange-400/20' : 'border-white/10'}`}>
                    <p className={`text-xs ${tier.featured ? 'text-orange-400/70' : 'text-slate-500'}`}>
                      {tier.highlight}
                    </p>
                  </div>
                  <Link href="/register">
                    <Button size="sm" className="w-full bg-orange-500 hover:bg-orange-600">
                      {tier.cta}
                    </Button>
                  </Link>
                </CardContent>
              </Card>
            ))}
          </div>
          <p className="text-center text-xs text-slate-500 mt-6">
            * Prices are a percentage of official Anthropic pricing. All Claude models (Haiku, Sonnet, Opus) included.
          </p>
        </section>

        {/* ── Code Example ── */}
        <section className="bg-white/3 border-y border-white/10 py-20">
          <div className="max-w-5xl mx-auto px-6">
            <div className="grid md:grid-cols-2 gap-12 items-center">
              <div>
                <h2 className="text-3xl font-bold mb-4">
                  One-line migration
                </h2>
                <p className="text-slate-400 mb-6">
                  OpenClade is 100% compatible with the official Anthropic SDK.
                  Switch in seconds — no refactoring required.
                </p>
                <ul className="space-y-3 text-sm text-slate-300">
                  {[
                    'Works with the official anthropic Python/JS SDK',
                    'OpenAI SDK compatible via /v1 endpoint',
                    'All Claude models: Haiku, Sonnet, Opus',
                    'Streaming, tool use, vision — all supported',
                  ].map((item) => (
                    <li key={item} className="flex items-start gap-2">
                      <span className="text-orange-400 mt-0.5">✓</span>
                      {item}
                    </li>
                  ))}
                </ul>
              </div>
              <div className="bg-slate-950 rounded-xl border border-white/10 overflow-hidden">
                <div className="flex items-center gap-2 px-4 py-2 bg-white/5 border-b border-white/10">
                  <div className="w-3 h-3 rounded-full bg-red-500/60" />
                  <div className="w-3 h-3 rounded-full bg-yellow-500/60" />
                  <div className="w-3 h-3 rounded-full bg-green-500/60" />
                  <span className="ml-2 text-xs text-slate-500">example.py</span>
                </div>
                <pre className="p-4 text-xs text-slate-300 overflow-x-auto leading-relaxed">
                  <code>{CODE_EXAMPLE}</code>
                </pre>
              </div>
            </div>
          </div>
        </section>

        {/* ── How It Works ── */}
        <section className="max-w-6xl mx-auto px-6 py-20">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold mb-3">Get Started in 3 Steps</h2>
            <p className="text-slate-400">From sign-up to your first API call in under 2 minutes.</p>
          </div>
          <div className="grid md:grid-cols-3 gap-8">
            {[
              {
                step: '1',
                title: 'Register',
                desc: 'Create a free account at openclade.io. No credit card required to get started.',
                icon: '📝',
              },
              {
                step: '2',
                title: 'Get API Key',
                desc: 'Generate your API key from the dashboard and top up your balance to begin.',
                icon: '🔑',
              },
              {
                step: '3',
                title: 'Start Calling',
                desc: 'Point your existing SDK to our endpoint. Change one line of code — that\'s it.',
                icon: '🚀',
              },
            ].map(({ step, title, desc, icon }) => (
              <div key={step} className="relative bg-white/5 border border-white/10 rounded-xl p-6 text-center">
                <div className="text-3xl mb-3">{icon}</div>
                <div className="w-8 h-8 rounded-full bg-orange-500 text-white flex items-center justify-center font-bold text-sm mx-auto mb-4">
                  {step}
                </div>
                <h3 className="font-semibold text-lg mb-2">{title}</h3>
                <p className="text-slate-400 text-sm">{desc}</p>
              </div>
            ))}
          </div>
          <div className="text-center mt-10">
            <Link href="/register">
              <Button size="lg" className="bg-orange-500 hover:bg-orange-600 text-white px-10">
                Create Free Account
              </Button>
            </Link>
          </div>
        </section>

        {/* ── Miner CTA ── */}
        <section id="miners" className="max-w-6xl mx-auto px-6 py-20">
          <div className="text-center mb-12">
            <Badge className="mb-4 bg-orange-500/20 text-orange-400 border-orange-400/30">
              Mine & Earn
            </Badge>
            <h2 className="text-3xl font-bold mb-4">Turn your Claude API key into passive income</h2>
            <p className="text-slate-400 max-w-xl mx-auto">
              Join the OpenClade miner network. Provide API capacity, earn TAO rewards.
              The network rewards performance — quality uptime, fast responses.
            </p>
          </div>
          {/* Miner earnings highlight */}
          <div className="grid md:grid-cols-2 gap-6 max-w-2xl mx-auto mb-12">
            <div className="bg-white/5 border border-white/10 rounded-xl p-6 text-center">
              <div className="text-sm text-slate-400 mb-1">Regular Miner</div>
              <div className="text-3xl font-bold text-orange-400 mb-1">$3,300<span className="text-base font-normal text-slate-400">/mo</span></div>
              <div className="text-xs text-slate-500">Net profit after API costs</div>
            </div>
            <div className="bg-gradient-to-b from-orange-500/10 to-transparent border border-orange-400/30 rounded-xl p-6 text-center">
              <div className="text-sm text-slate-400 mb-1">Top-Tier Miner</div>
              <div className="text-3xl font-bold text-orange-400 mb-1">$11,500<span className="text-base font-normal text-slate-400">/mo</span></div>
              <div className="text-xs text-orange-400/60">With referrals & high uptime</div>
            </div>
          </div>
          <div className="grid md:grid-cols-3 gap-6 mb-12">
            {[
              {
                step: '1',
                title: 'Register as Miner',
                desc: 'Create a miner account and get your subnet wallet address.',
              },
              {
                step: '2',
                title: 'Stake & Connect',
                desc: 'Stake a small amount of TAO and connect your Claude API key securely.',
              },
              {
                step: '3',
                title: 'Earn TAO Rewards',
                desc: 'Validators score your responses. High scores = more TAO emissions.',
              },
            ].map(({ step, title, desc }) => (
              <div key={step} className="relative bg-white/5 border border-white/10 rounded-xl p-6">
                <div className="w-10 h-10 rounded-full bg-orange-500/20 text-orange-400 flex items-center justify-center font-bold text-lg mb-4">
                  {step}
                </div>
                <h3 className="font-semibold mb-2">{title}</h3>
                <p className="text-slate-400 text-sm">{desc}</p>
              </div>
            ))}
          </div>
          <div className="text-center">
            <Link href="/miner/register">
              <Button size="lg" className="bg-orange-500 hover:bg-orange-600 px-10">
                Start Mining
              </Button>
            </Link>
          </div>
        </section>

        {/* ── FAQ / Trust ── */}
        <section className="bg-white/3 border-y border-white/10 py-20">
          <div className="max-w-3xl mx-auto px-6">
            <h2 className="text-3xl font-bold text-center mb-12">Frequently Asked Questions</h2>
            <div className="space-y-4">
              {[
                {
                  q: 'How is this legal / sustainable?',
                  a: "Miners contribute their own Claude API keys and are compensated in TAO tokens from Bittensor subnet emissions. The platform operates as a marketplace connecting API supply with demand. Miners agree to Anthropic's terms of service for their own keys.",
                },
                {
                  q: 'Is my data safe?',
                  a: 'API requests are routed directly to Claude through miner keys. We do not store request content. Each miner operates independently and is incentivized by performance, not data collection.',
                },
                {
                  q: 'What if a miner goes offline?',
                  a: 'The validator network continuously scores and routes traffic to the best-performing miners. If a miner degrades, traffic is automatically re-routed, ensuring high availability.',
                },
                {
                  q: 'Do I need to know anything about crypto to use OpenClade?',
                  a: 'No. As a user, you just need a credit card. You pay in USD. The TAO / Bittensor layer is handled entirely by miners and the platform.',
                },
              ].map(({ q, a }) => (
                <details key={q} className="bg-white/5 border border-white/10 rounded-xl p-5 group">
                  <summary className="font-medium cursor-pointer list-none flex items-center justify-between">
                    {q}
                    <span className="text-slate-400 group-open:rotate-180 transition-transform">▼</span>
                  </summary>
                  <p className="text-slate-400 text-sm mt-3">{a}</p>
                </details>
              ))}
            </div>
          </div>
        </section>

        {/* ── Final CTA ── */}
        <section className="max-w-4xl mx-auto px-6 py-24 text-center">
          <h2 className="text-4xl font-bold mb-4">
            Ready to cut your AI costs by <span className="text-orange-400">70%</span>?
          </h2>
          <p className="text-slate-400 mb-10 text-lg">
            Join hundreds of developers already saving on Claude API costs.
            Get started in under 2 minutes.
          </p>
          <div className="flex gap-4 justify-center flex-wrap">
            <Link href="/register">
              <Button size="lg" className="bg-orange-500 hover:bg-orange-600 text-white px-10">
                Start Building Free
              </Button>
            </Link>
            <Link href="/miner/register">
              <Button size="lg" variant="outline" className="border-orange-400/40 text-orange-400 hover:bg-orange-500/10 px-10">
                Become a Miner
              </Button>
            </Link>
          </div>
        </section>
      </main>

      {/* ── Footer ── */}
      <footer className="border-t border-white/10 py-10">
        <div className="max-w-6xl mx-auto px-6">
          <div className="flex flex-col md:flex-row justify-between items-start gap-8 mb-8">
            <div>
              <div className="flex items-center gap-2 mb-2">
                <span className="font-bold">OpenClade</span>
                <Badge variant="outline" className="text-xs border-orange-400/50 text-orange-400">Beta</Badge>
              </div>
              <p className="text-xs text-slate-500 max-w-xs">
                Decentralized Claude API powered by Bittensor TAO subnet.
              </p>
            </div>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-x-12 gap-y-3 text-sm">
              <Link href="/docs" className="text-slate-400 hover:text-white transition-colors">Documentation</Link>
              <Link href="/blog" className="text-slate-400 hover:text-white transition-colors">Blog</Link>
              <Link href="/register" className="text-slate-400 hover:text-white transition-colors">Sign Up</Link>
              <Link href="/miner/register" className="text-slate-400 hover:text-white transition-colors">Become a Miner</Link>
              <Link href="https://github.com/kydlikebtc/openclaude" target="_blank" rel="noopener noreferrer" className="text-slate-400 hover:text-white transition-colors">GitHub</Link>
              <Link href="/login" className="text-slate-400 hover:text-white transition-colors">Log In</Link>
              <Link href="https://discord.gg/openclade" target="_blank" rel="noopener noreferrer" className="text-slate-400 hover:text-white transition-colors">Community</Link>
            </div>
          </div>
          <div className="border-t border-white/10 pt-6 flex flex-col md:flex-row justify-between items-center gap-2 text-xs text-slate-500">
            <span>© {new Date().getFullYear()} OpenClade. All rights reserved.</span>
            <span>Powered by Bittensor TAO Subnet</span>
          </div>
        </div>
      </footer>
    </div>
  )
}
