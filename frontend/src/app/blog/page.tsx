export const dynamic = 'force-static'

import Link from 'next/link'
import type { Metadata } from 'next'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { getAllPosts } from '@/lib/blog'

export const metadata: Metadata = {
  title: 'Blog — OpenClade',
  description: 'Technical articles, migration guides, and developer resources for affordable Claude API access via the Bittensor network.',
}

export default function BlogPage() {
  const posts = getAllPosts()
  const blogPosts = posts.filter((p) => p.category === 'blog')
  const guides = posts.filter((p) => p.category === 'guide')

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 text-white">
      {/* Header */}
      <header className="sticky top-0 z-50 border-b border-white/10 bg-slate-900/80 backdrop-blur-sm px-6 py-4">
        <div className="max-w-6xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Link href="/" className="text-xl font-bold hover:text-orange-400 transition-colors">
              OpenClade
            </Link>
            <Badge variant="outline" className="text-xs border-orange-400/50 text-orange-400">
              Beta
            </Badge>
          </div>
          <nav className="hidden md:flex items-center gap-6">
            <Link href="/#pricing" className="text-sm text-slate-400 hover:text-white transition-colors">
              Pricing
            </Link>
            <Link href="/blog" className="text-sm text-white font-medium">
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
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-6 py-16">
        {/* Page heading */}
        <div className="mb-14 text-center">
          <h1 className="text-4xl font-bold mb-4">Blog</h1>
          <p className="text-slate-400 max-w-xl mx-auto">
            Tutorials, migration guides, and deep dives on affordable Claude API access
            powered by the Bittensor network.
          </p>
        </div>

        {/* Blog posts section */}
        {blogPosts.length > 0 && (
          <section className="mb-16">
            <h2 className="text-2xl font-semibold mb-8 flex items-center gap-3">
              <span>Articles</span>
              <Badge className="bg-orange-500/20 text-orange-400 border-orange-400/30">
                {blogPosts.length}
              </Badge>
            </h2>
            <div className="grid md:grid-cols-2 gap-6">
              {blogPosts.map((post) => (
                <Link key={post.slug} href={`/blog/${post.slug}`}>
                  <Card className="bg-white/5 border-white/10 text-white hover:border-orange-400/40 hover:bg-white/8 transition-all h-full cursor-pointer">
                    <CardHeader className="pb-2">
                      <div className="flex items-center gap-2 mb-2">
                        <span className="text-xs text-slate-500">{post.date}</span>
                      </div>
                      <CardTitle className="text-lg leading-snug hover:text-orange-400 transition-colors">
                        {post.title}
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <p className="text-slate-400 text-sm leading-relaxed line-clamp-3">
                        {post.excerpt}
                      </p>
                      <span className="inline-block mt-4 text-xs text-orange-400 hover:underline">
                        Read more →
                      </span>
                    </CardContent>
                  </Card>
                </Link>
              ))}
            </div>
          </section>
        )}

        {/* Guides section */}
        {guides.length > 0 && (
          <section>
            <h2 className="text-2xl font-semibold mb-8 flex items-center gap-3">
              <span>Guides</span>
              <Badge className="bg-slate-500/20 text-slate-400 border-slate-400/30">
                {guides.length}
              </Badge>
            </h2>
            <div className="grid md:grid-cols-2 gap-6">
              {guides.map((post) => (
                <Link key={post.slug} href={`/blog/${post.slug}`}>
                  <Card className="bg-white/5 border-white/10 text-white hover:border-orange-400/40 hover:bg-white/8 transition-all h-full cursor-pointer">
                    <CardHeader className="pb-2">
                      <div className="flex items-center gap-2 mb-2">
                        <span className="text-xs text-slate-500">{post.date}</span>
                        <Badge className="text-xs bg-slate-500/20 text-slate-400 border-slate-400/30">
                          Guide
                        </Badge>
                      </div>
                      <CardTitle className="text-lg leading-snug hover:text-orange-400 transition-colors">
                        {post.title}
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <p className="text-slate-400 text-sm leading-relaxed line-clamp-3">
                        {post.excerpt}
                      </p>
                      <span className="inline-block mt-4 text-xs text-orange-400 hover:underline">
                        Read more →
                      </span>
                    </CardContent>
                  </Card>
                </Link>
              ))}
            </div>
          </section>
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-white/10 py-8 mt-16">
        <div className="max-w-6xl mx-auto px-6 flex flex-col md:flex-row justify-between items-center gap-2 text-xs text-slate-500">
          <span>© {new Date().getFullYear()} OpenClade. All rights reserved.</span>
          <span>Powered by Bittensor TAO Subnet</span>
        </div>
      </footer>
    </div>
  )
}
