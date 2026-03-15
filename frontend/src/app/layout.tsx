import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import { Toaster } from 'sonner'
import './globals.css'

const inter = Inter({
  subsets: ['latin'],
  display: 'swap',
  variable: '--font-inter',
  preload: true,
})

export const metadata: Metadata = {
  title: 'OpenClade — Decentralized Claude API',
  description:
    'Access Claude AI at 65-75% less cost through a decentralized miner network powered by Bittensor TAO subnet.',
  metadataBase: new URL('https://openclaude.io'),
  openGraph: {
    title: 'OpenClade — Decentralized Claude API',
    description: 'Save 65-75% on Claude API costs. Pay-as-you-go, no subscriptions.',
    type: 'website',
    url: 'https://openclaude.io',
    siteName: 'OpenClade',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'OpenClade — Decentralized Claude API',
    description: 'Save 65-75% on Claude API costs. Powered by Bittensor.',
  },
  robots: {
    index: true,
    follow: true,
  },
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={inter.variable} suppressHydrationWarning>
      <body className={inter.className}>
        {children}
        <Toaster position="top-right" richColors />
      </body>
    </html>
  )
}
