import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'

export default function DocsPage() {
  return (
    <div className="p-8 max-w-4xl">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-slate-900">API Documentation</h1>
        <p className="text-slate-500 mt-1">
          OpenClade is compatible with the Anthropic API. Just swap the base URL and API key.
        </p>
      </div>

      <Card className="mb-6">
        <CardHeader>
          <CardTitle>Quick Start</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <p className="text-sm font-medium text-slate-700 mb-2">Base URL</p>
            <code className="block bg-slate-100 rounded-lg px-4 py-3 text-sm">
              https://api.openclade.io
            </code>
          </div>
          <div>
            <p className="text-sm font-medium text-slate-700 mb-2">Python (anthropic SDK)</p>
            <pre className="bg-slate-900 text-slate-100 rounded-lg p-4 text-sm overflow-x-auto">{`import anthropic

client = anthropic.Anthropic(
    base_url="https://api.openclade.io",
    api_key="YOUR_OPENCLADE_API_KEY",
)

message = client.messages.create(
    model="claude-opus-4-6",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Hello!"}]
)
print(message.content)`}</pre>
          </div>
          <div>
            <p className="text-sm font-medium text-slate-700 mb-2">JavaScript / Node.js</p>
            <pre className="bg-slate-900 text-slate-100 rounded-lg p-4 text-sm overflow-x-auto">{`import Anthropic from "@anthropic-ai/sdk";

const client = new Anthropic({
  baseURL: "https://api.openclade.io",
  apiKey: "YOUR_OPENCLADE_API_KEY",
});

const message = await client.messages.create({
  model: "claude-opus-4-6",
  max_tokens: 1024,
  messages: [{ role: "user", content: "Hello!" }],
});
console.log(message.content);`}</pre>
          </div>
          <div>
            <p className="text-sm font-medium text-slate-700 mb-2">cURL</p>
            <pre className="bg-slate-900 text-slate-100 rounded-lg p-4 text-sm overflow-x-auto">{`curl https://api.openclade.io/v1/messages \\
  -H "x-api-key: YOUR_OPENCLADE_API_KEY" \\
  -H "anthropic-version: 2023-06-01" \\
  -H "content-type: application/json" \\
  -d '{
    "model": "claude-opus-4-6",
    "max_tokens": 1024,
    "messages": [{"role": "user", "content": "Hello!"}]
  }'`}</pre>
          </div>
        </CardContent>
      </Card>

      <Card className="mb-6">
        <CardHeader>
          <CardTitle>Supported Models</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {[
              { id: 'claude-opus-4-6', label: 'Claude Opus 4.6', desc: 'Most capable model for complex tasks' },
              { id: 'claude-sonnet-4-6', label: 'Claude Sonnet 4.6', desc: 'Balanced speed and intelligence' },
              { id: 'claude-haiku-4-5', label: 'Claude Haiku 4.5', desc: 'Fastest and most compact model' },
            ].map(({ id, label, desc }) => (
              <div key={id} className="flex items-start gap-3 p-3 rounded-lg bg-slate-50">
                <Badge variant="outline" className="font-mono text-xs shrink-0">{id}</Badge>
                <div>
                  <p className="font-medium text-sm">{label}</p>
                  <p className="text-xs text-slate-500">{desc}</p>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Rate Limits & Pricing</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3 text-sm text-slate-600">
          <p>Rate limits are set per API key (default: 60 requests/min). Pricing is based on token usage:</p>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b">
                  <th className="text-left py-2 font-medium">Model</th>
                  <th className="text-right py-2 font-medium">Input (per 1M tokens)</th>
                  <th className="text-right py-2 font-medium">Output (per 1M tokens)</th>
                </tr>
              </thead>
              <tbody className="divide-y">
                <tr>
                  <td className="py-2">Claude Opus 4.6</td>
                  <td className="py-2 text-right">$15.00</td>
                  <td className="py-2 text-right">$75.00</td>
                </tr>
                <tr>
                  <td className="py-2">Claude Sonnet 4.6</td>
                  <td className="py-2 text-right">$3.00</td>
                  <td className="py-2 text-right">$15.00</td>
                </tr>
                <tr>
                  <td className="py-2">Claude Haiku 4.5</td>
                  <td className="py-2 text-right">$0.25</td>
                  <td className="py-2 text-right">$1.25</td>
                </tr>
              </tbody>
            </table>
          </div>
          <p className="text-xs text-slate-400">
            * OpenClade pricing may vary from Anthropic&apos;s official prices. Always check the dashboard for current rates.
          </p>
        </CardContent>
      </Card>
    </div>
  )
}
