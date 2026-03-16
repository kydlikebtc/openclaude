import Link from 'next/link'
import { notFound } from 'next/navigation'
import type { Metadata } from 'next'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { getAllSlugs, getPostBySlug } from '@/lib/blog'

export async function generateStaticParams() {
  return getAllSlugs().map((slug) => ({ slug }))
}

export async function generateMetadata({
  params,
}: {
  params: { slug: string }
}): Promise<Metadata> {
  const post = getPostBySlug(params.slug)
  if (!post) return {}
  return {
    title: `${post.title} — OpenClade Blog`,
    description: post.metaDescription,
    keywords: post.keywords,
    openGraph: {
      title: post.title,
      description: post.metaDescription,
      type: 'article',
      publishedTime: post.date,
    },
  }
}

export default function BlogPostPage({ params }: { params: { slug: string } }) {
  const post = getPostBySlug(params.slug)
  if (!post) notFound()

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
        </div>
      </header>

      <main className="max-w-3xl mx-auto px-6 py-16">
        {/* Breadcrumb */}
        <nav className="mb-8 text-sm text-slate-500">
          <Link href="/blog" className="hover:text-slate-300 transition-colors">
            ← Back to Blog
          </Link>
        </nav>

        {/* Post header */}
        <header className="mb-10">
          <div className="flex items-center gap-3 mb-4">
            {post.category === 'guide' && (
              <Badge className="bg-slate-500/20 text-slate-400 border-slate-400/30">
                Guide
              </Badge>
            )}
            <span className="text-sm text-slate-500">{post.date}</span>
          </div>
          <h1 className="text-3xl md:text-4xl font-bold leading-tight mb-4">
            {post.title}
          </h1>
          {post.excerpt && (
            <p className="text-lg text-slate-400 leading-relaxed border-l-2 border-orange-400/50 pl-4">
              {post.excerpt}
            </p>
          )}
        </header>

        {/* Article content — HTML is server-sanitized via sanitize-html before rendering */}
        <article
          className="prose prose-invert prose-slate max-w-none
            prose-headings:font-bold prose-headings:text-white
            prose-h1:text-3xl prose-h2:text-2xl prose-h2:mt-10 prose-h2:mb-4
            prose-h3:text-xl prose-h3:mt-8 prose-h3:mb-3
            prose-p:text-slate-300 prose-p:leading-relaxed
            prose-a:text-orange-400 prose-a:no-underline hover:prose-a:underline
            prose-strong:text-white
            prose-code:text-orange-300 prose-code:bg-white/5 prose-code:px-1 prose-code:rounded
            prose-pre:bg-slate-950 prose-pre:border prose-pre:border-white/10
            prose-blockquote:border-l-orange-400/50 prose-blockquote:text-slate-400
            prose-li:text-slate-300
            prose-table:text-slate-300
            prose-th:text-white prose-th:border-white/20
            prose-td:border-white/10"
          /* Content is our own markdown parsed server-side and sanitized with sanitize-html */
          dangerouslySetInnerHTML={{ __html: post.content }}
        />

        {/* CTA */}
        <div className="mt-16 p-8 bg-orange-500/10 border border-orange-400/20 rounded-2xl text-center">
          <h2 className="text-xl font-bold mb-2">Ready to save on Claude API?</h2>
          <p className="text-slate-400 mb-6 text-sm">
            Join OpenClade and access Claude at 10–25% of official pricing via the Bittensor network.
          </p>
          <div className="flex gap-3 justify-center">
            <Link href="/register">
              <Button className="bg-orange-500 hover:bg-orange-600">
                Get Started Free
              </Button>
            </Link>
            <Link href="/blog">
              <Button variant="outline" className="border-white/20 text-white hover:bg-white/10">
                More Articles
              </Button>
            </Link>
          </div>
        </div>
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
