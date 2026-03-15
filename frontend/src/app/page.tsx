import Link from 'next/link'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

const PRICING = {
  official: { input: 3.0, output: 15.0 },
  openclade: { input: 0.9, output: 4.5 },
  founding: { input: 0.81, output: 4.05 },
}

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
            Claude API at{' '}
            <span className="text-orange-400">25–35%</span>
            <br />
            of Official Price
          </h1>
          <p className="text-lg md:text-xl text-slate-400 mb-10 max-w-2xl mx-auto">
            Access Anthropic&apos;s latest Claude models through a decentralized miner network.
            Pay only for what you use — no subscriptions, no commitments.
          </p>
          <div className="flex gap-4 justify-center flex-wrap mb-16">
            <Link href="/register">
              <Button size="lg" className="bg-orange-500 hover:bg-orange-600 text-white px-8">
                Get Started Free
              </Button>
            </Link>
            <a href="#pricing">
              <Button size="lg" variant="outline" className="border-white/20 text-white hover:bg-white/10 px-8">
                View Pricing
              </Button>
            </a>
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

        {/* ── Value Props ── */}
        <section className="bg-white/3 border-y border-white/10 py-20">
          <div className="max-w-6xl mx-auto px-6">
            <h2 className="text-3xl font-bold text-center mb-12">Who benefits from OpenClade?</h2>
            <div className="grid md:grid-cols-3 gap-8">
              <Card className="bg-white/5 border-white/10 text-white">
                <CardHeader>
                  <div className="text-3xl mb-2">👨‍💻</div>
                  <CardTitle className="text-lg">Developers & Teams</CardTitle>
                </CardHeader>
                <CardContent className="text-slate-400 text-sm space-y-2">
                  <p>Save <span className="text-orange-400 font-semibold">65–75%</span> on Claude API costs.</p>
                  <p>OpenAI-compatible SDK — change just one line of code.</p>
                  <p>Pay-as-you-go, no upfront commitment.</p>
                  <p>Founding members get an extra <span className="text-orange-400 font-semibold">10% off</span>.</p>
                </CardContent>
              </Card>
              <Card className="bg-white/5 border-orange-400/20 text-white border-2">
                <CardHeader>
                  <div className="text-3xl mb-2">⛏️</div>
                  <CardTitle className="text-lg flex items-center gap-2">
                    Miners
                    <Badge className="text-xs bg-orange-500/20 text-orange-400 border-orange-400/30">Earn TAO</Badge>
                  </CardTitle>
                </CardHeader>
                <CardContent className="text-slate-400 text-sm space-y-2">
                  <p>Contribute your Claude API keys to the network.</p>
                  <p>Earn <span className="text-orange-400 font-semibold">41% of TAO subnet emissions</span>.</p>
                  <p>Rewards scale with your uptime and response quality.</p>
                  <p>TAO rewards cover API costs <span className="text-orange-400 font-semibold">+ profit</span>.</p>
                </CardContent>
              </Card>
              <Card className="bg-white/5 border-white/10 text-white">
                <CardHeader>
                  <div className="text-3xl mb-2">🌐</div>
                  <CardTitle className="text-lg">The Ecosystem</CardTitle>
                </CardHeader>
                <CardContent className="text-slate-400 text-sm space-y-2">
                  <p>Decentralized AI infrastructure — no single point of failure.</p>
                  <p>More miners → better stability and latency.</p>
                  <p>Built on Bittensor, the leading decentralized AI network.</p>
                  <p>Open participation, transparent scoring.</p>
                </CardContent>
              </Card>
            </div>
          </div>
        </section>

        {/* ── Pricing ── */}
        <section id="pricing" className="max-w-6xl mx-auto px-6 py-20">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold mb-3">Transparent Pricing</h2>
            <p className="text-slate-400">Pay-as-you-go per million tokens. No surprises.</p>
          </div>
          <div className="grid md:grid-cols-3 gap-6">
            {/* Official */}
            <Card className="bg-white/5 border-white/10 text-white opacity-70">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="text-base">Official Anthropic</CardTitle>
                  <Badge variant="outline" className="text-xs border-slate-500 text-slate-400">Reference</Badge>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                <PricingRow label="Input (per 1M tokens)" value={`$${PRICING.official.input.toFixed(2)}`} />
                <PricingRow label="Output (per 1M tokens)" value={`$${PRICING.official.output.toFixed(2)}`} />
                <div className="pt-2 border-t border-white/10">
                  <p className="text-xs text-slate-500">claude-sonnet-4-6 pricing</p>
                </div>
                <Link href="https://www.anthropic.com/pricing" target="_blank">
                  <Button variant="outline" size="sm" className="w-full border-white/20 text-slate-400">
                    Official site
                  </Button>
                </Link>
              </CardContent>
            </Card>

            {/* OpenClade Standard */}
            <Card className="bg-white/5 border-white/10 text-white">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="text-base">OpenClade</CardTitle>
                  <Badge className="text-xs bg-green-500/20 text-green-400 border-green-400/30">Save 70%</Badge>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                <PricingRow
                  label="Input (per 1M tokens)"
                  value={`$${PRICING.openclade.input.toFixed(2)}`}
                  compare={`vs $${PRICING.official.input.toFixed(2)}`}
                />
                <PricingRow
                  label="Output (per 1M tokens)"
                  value={`$${PRICING.openclade.output.toFixed(2)}`}
                  compare={`vs $${PRICING.official.output.toFixed(2)}`}
                />
                <div className="pt-2 border-t border-white/10">
                  <p className="text-xs text-slate-500">All Claude models supported</p>
                </div>
                <Link href="/register">
                  <Button size="sm" className="w-full bg-orange-500 hover:bg-orange-600">
                    Get Started
                  </Button>
                </Link>
              </CardContent>
            </Card>

            {/* Founding Member */}
            <Card className="bg-gradient-to-b from-orange-500/10 to-orange-900/5 border-orange-400/40 text-white">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="text-base">Founding Member</CardTitle>
                  <Badge className="text-xs bg-orange-500/30 text-orange-300 border-orange-400/30">Limited</Badge>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                <PricingRow
                  label="Input (per 1M tokens)"
                  value={`$${PRICING.founding.input.toFixed(2)}`}
                  compare="Extra 10% off"
                  highlight
                />
                <PricingRow
                  label="Output (per 1M tokens)"
                  value={`$${PRICING.founding.output.toFixed(2)}`}
                  compare="Extra 10% off"
                  highlight
                />
                <div className="pt-2 border-t border-orange-400/20">
                  <p className="text-xs text-orange-400/70">Lock in this rate forever</p>
                </div>
                <Link href="/register">
                  <Button size="sm" className="w-full bg-orange-500 hover:bg-orange-600">
                    Join as Founding Member
                  </Button>
                </Link>
              </CardContent>
            </Card>
          </div>
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
          {/* Earnings table */}
          <Card className="bg-white/5 border-white/10 text-white max-w-2xl mx-auto mb-8">
            <CardHeader>
              <CardTitle className="text-base text-center">Estimated Monthly Miner Earnings</CardTitle>
            </CardHeader>
            <CardContent>
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-slate-500 text-xs uppercase border-b border-white/10">
                    <th className="text-left py-2">Network size</th>
                    <th className="text-right py-2">TAO / month</th>
                    <th className="text-right py-2">USD equiv.</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/5">
                  {[
                    { size: '10 miners (early)', tao: '41 TAO', usd: '~$12,300' },
                    { size: '50 miners', tao: '8 TAO', usd: '~$2,460' },
                    { size: '100 miners', tao: '4 TAO', usd: '~$1,230' },
                  ].map(({ size, tao, usd }) => (
                    <tr key={size}>
                      <td className="py-3 text-slate-300">{size}</td>
                      <td className="py-3 text-right text-orange-400">{tao}</td>
                      <td className="py-3 text-right text-slate-400">{usd}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
              <p className="text-xs text-slate-500 mt-3 text-center">
                * Based on 41% of subnet emissions at ~$300/TAO. Actual rewards vary with TAO price and network size.
              </p>
            </CardContent>
          </Card>
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
              <Link href="/register" className="text-slate-400 hover:text-white transition-colors">Sign Up</Link>
              <Link href="/miner/register" className="text-slate-400 hover:text-white transition-colors">Become a Miner</Link>
              <Link href="/login" className="text-slate-400 hover:text-white transition-colors">Log In</Link>
              <Link href="/admin" className="text-slate-400 hover:text-white transition-colors">Admin</Link>
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

function PricingRow({
  label,
  value,
  compare,
  highlight,
}: {
  label: string
  value: string
  compare?: string
  highlight?: boolean
}) {
  return (
    <div className="flex items-center justify-between">
      <span className="text-sm text-slate-400">{label}</span>
      <div className="text-right">
        <span className={`font-semibold ${highlight ? 'text-orange-400' : 'text-white'}`}>{value}</span>
        {compare && (
          <div className={`text-xs mt-0.5 ${highlight ? 'text-orange-400/70' : 'text-slate-500'}`}>{compare}</div>
        )}
      </div>
    </div>
  )
}
