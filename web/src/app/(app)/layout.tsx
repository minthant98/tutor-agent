'use client'
import { useEffect } from 'react'
import { usePathname, useRouter } from 'next/navigation'
import { isAuthenticated, useStudent } from '@/lib/auth'
import { TopBar } from '@/components/shell/top-bar'
import { useFeatureFlag } from '@/lib/feature-flags'

export default function AppLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter()
  const pathname = usePathname()
  const student = useStudent()
  const shellV3 = useFeatureFlag('shell_v3', false)

  useEffect(() => {
    if (!isAuthenticated()) router.push('/login')
  }, [router])

  const inSession = pathname?.startsWith('/session/')

  return (
    <div className="min-h-screen bg-[var(--bg)]">
      {!inSession && !shellV3 && student && <TopBar />}
      <main className={inSession ? '' : 'mx-auto max-w-3xl px-4 py-6'}>
        {children}
      </main>
    </div>
  )
}
