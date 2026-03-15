import { MinerSidebar } from '@/components/layout/MinerSidebar'

export default function MinerLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex min-h-screen bg-slate-50">
      <MinerSidebar />
      <main className="flex-1 overflow-auto">{children}</main>
    </div>
  )
}
