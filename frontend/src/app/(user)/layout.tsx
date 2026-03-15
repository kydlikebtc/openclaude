'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { UserSidebar } from '@/components/layout/UserSidebar'
import { useAuthStore } from '@/store/auth'

export default function UserLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter()
  const { user, fetchMe } = useAuthStore()
  const [checking, setChecking] = useState(!user)

  useEffect(() => {
    if (!user) {
      fetchMe()
        .catch(() => router.push('/login'))
        .finally(() => setChecking(false))
    } else {
      setChecking(false)
    }
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  if (checking) return null

  return (
    <div className="flex min-h-screen bg-slate-50">
      <UserSidebar />
      <main className="flex-1 overflow-auto">
        {children}
      </main>
    </div>
  )
}
