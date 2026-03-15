'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { UserSidebar } from '@/components/layout/UserSidebar'
import { useAuthStore } from '@/store/auth'

export default function UserLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter()
  const { token, fetchMe, user } = useAuthStore()

  useEffect(() => {
    if (!token) {
      router.push('/login')
      return
    }
    if (!user) {
      fetchMe().catch(() => router.push('/login'))
    }
  }, [token, user, router, fetchMe])

  if (!token) return null

  return (
    <div className="flex min-h-screen bg-slate-50">
      <UserSidebar />
      <main className="flex-1 overflow-auto">
        {children}
      </main>
    </div>
  )
}
