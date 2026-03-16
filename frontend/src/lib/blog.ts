import fs from 'fs'
import path from 'path'
import { marked } from 'marked'
import sanitizeHtml from 'sanitize-html'

const SANITIZE_OPTIONS: sanitizeHtml.IOptions = {
  allowedTags: sanitizeHtml.defaults.allowedTags.concat([
    'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
    'details', 'summary', 'img',
  ]),
  allowedAttributes: {
    ...sanitizeHtml.defaults.allowedAttributes,
    a: ['href', 'name', 'target', 'rel'],
    img: ['src', 'alt', 'title', 'width', 'height'],
    code: ['class'],
    pre: ['class'],
  },
  allowedSchemes: ['http', 'https', 'mailto'],
}

export interface BlogPost {
  slug: string
  title: string
  date: string
  excerpt: string
  content: string
  keywords: string[]
  metaDescription: string
  category: 'blog' | 'guide'
}

const CONTENT_DIR = path.join(process.cwd(), 'src/content/blog')

/** Extract the H1 title from the first line */
function extractTitle(raw: string): string {
  const match = raw.match(/^#\s+(.+)$/m)
  return match ? match[1].trim() : 'Untitled'
}

/** Extract a metadata field like **Date:** 2026-03 */
function extractMeta(raw: string, ...keys: string[]): string {
  for (const key of keys) {
    const pattern = new RegExp(`\\*\\*${key}:\\*\\*\\s*(.+)`, 'i')
    const match = raw.match(pattern)
    if (match) return match[1].trim()
  }
  return ''
}

/** Extract the TL;DR paragraph as the post excerpt */
function extractExcerpt(raw: string): string {
  const tldr = raw.match(/##\s+TL;DR\s*\n+([^#\n][^\n]+)/i)
  if (tldr) return tldr[1].trim()
  // Fall back to first real paragraph after the metadata block
  const afterDivider = raw.split(/^---$/m)[1] ?? raw
  const firstPara = afterDivider.match(/\n\n([^#\n][^\n]{20,})/)?.[1]
  return firstPara?.trim() ?? ''
}

/** Strip the metadata preamble (bold key:value lines) before rendering */
function stripPreamble(raw: string): string {
  // Remove lines that are purely **Key:** value metadata
  return raw
    .split('\n')
    .filter((line) => !line.match(/^\*\*(Publication target|Word count|Author|Date|SEO keywords|Target Keywords|Publish To|SEO Title|Meta Description|URL Slug):\*\*/i))
    .join('\n')
}

/** Derive a URL-safe slug from filename */
function filenameToSlug(filename: string): string {
  return filename
    .replace(/\.md$/, '')
    .replace(/^\d+_/, '') // remove numeric prefix
    .replace(/_/g, '-')
    .toLowerCase()
}

/** Load and parse a single blog post by slug */
export function getPostBySlug(slug: string): BlogPost | null {
  const files = fs.readdirSync(CONTENT_DIR).filter((f) => f.endsWith('.md'))
  const file = files.find((f) => filenameToSlug(f) === slug)
  if (!file) return null

  const raw = fs.readFileSync(path.join(CONTENT_DIR, file), 'utf-8')
  const keywords = extractMeta(raw, 'SEO keywords', 'Target Keywords')
    .split(',')
    .map((k) => k.trim())
    .filter(Boolean)

  const stripped = stripPreamble(raw)
  const rawHtml = marked(stripped) as string
  const htmlContent = sanitizeHtml(rawHtml, SANITIZE_OPTIONS)

  return {
    slug,
    title: extractTitle(raw),
    date: extractMeta(raw, 'Date') || '2026-03',
    excerpt: extractExcerpt(raw),
    content: htmlContent,
    keywords,
    metaDescription: extractMeta(raw, 'Meta Description') || extractExcerpt(raw).slice(0, 160),
    category: file.includes('pricing') || file.includes('reduce') || file.includes('openai_sdk') || file.includes('vs_gpt4')
      ? 'guide'
      : 'blog',
  }
}

/** List all posts as lightweight metadata (no full content) */
export function getAllPosts(): Omit<BlogPost, 'content'>[] {
  const files = fs.readdirSync(CONTENT_DIR).filter((f) => f.endsWith('.md'))

  return files
    .map((file) => {
      const raw = fs.readFileSync(path.join(CONTENT_DIR, file), 'utf-8')
      const slug = filenameToSlug(file)
      const keywords = extractMeta(raw, 'SEO keywords', 'Target Keywords')
        .split(',')
        .map((k) => k.trim())
        .filter(Boolean)

      return {
        slug,
        title: extractTitle(raw),
        date: extractMeta(raw, 'Date') || '2026-03',
        excerpt: extractExcerpt(raw),
        keywords,
        metaDescription: extractMeta(raw, 'Meta Description') || extractExcerpt(raw).slice(0, 160),
        category: (file.includes('pricing') || file.includes('reduce') || file.includes('openai_sdk') || file.includes('vs_gpt4')
          ? 'guide'
          : 'blog') as 'blog' | 'guide',
      }
    })
    .sort((a, b) => a.title.localeCompare(b.title))
}

/** All slugs for static path generation */
export function getAllSlugs(): string[] {
  return fs
    .readdirSync(CONTENT_DIR)
    .filter((f) => f.endsWith('.md'))
    .map(filenameToSlug)
}
