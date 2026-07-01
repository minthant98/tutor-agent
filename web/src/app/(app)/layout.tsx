'use client'
import { useEffect } from 'react'
import { usePathname, useRouter } from 'next/navigation'
import { isAuthenticated, useStudent } from '@/lib/auth'
import { TopBar } from '@/components/shell/top-bar'

export default function AppLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter()
  const pathname = usePathname()
  const student = useStudent()

  useEffect(() => {
    if (!isAuthenticated()) router.push('/login')
  }, [router])

  const inSession = pathname?.startsWith('/session/')

  return (
    <div className="min-h-screen bg-[var(--bg)]">
      {!inSession && student && <TopBar studentName={student.name} />}
      <main className={inSession ? '' : 'mx-auto max-w-3xl px-4 py-6'}>
        {children}
      </main>
    </div>
  )
}
