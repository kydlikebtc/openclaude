'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { cn } from '@/lib/utils'
import { LayoutDashboard, Key, Users, Info } from 'lucide-react'

const navItems = [
  { href: '/miner/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { href: '/miner/api-keys', label: 'Claude API Keys', icon: Key },
  { href: '/miner/referral', label: 'Referral Program', icon: Users },
]

export function MinerSidebar() {
  const pathname = usePathname()

  return (
    <aside className="w-64 min-h-screen bg-slate-900 text-white flex flex-col">
      <div className="p-6 border-b border-white/10">
        <Link href="/" className="text-xl font-bold text-orange-400">
          OpenClade
        </Link>
        <p className="text-xs text-slate-500 mt-1">Miner Portal</p>
      </div>

      <nav className="flex-1 p-4 space-y-1">
        {navItems.map(({ href, label, icon: Icon }) => (
          <Link
            key={href}
            href={href}
            className={cn(
              'flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors',
              pathname.startsWith(href)
                ? 'bg-orange-500/20 text-orange-400'
                : 'text-slate-400 hover:text-white hover:bg-white/5',
            )}
          >
            <Icon size={16} />
            {label}
          </Link>
        ))}
      </nav>

      <div className="p-4 border-t border-white/10">
        <Link
          href="/login"
          className="flex items-center gap-2 text-xs text-slate-500 hover:text-white transition-colors"
        >
          <Info size={12} />
          Switch to User Portal
        </Link>
      </div>
    </aside>
  )
}
