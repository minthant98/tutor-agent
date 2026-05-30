'use client'
import { useEffect, useState } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { getMe, startSession, createCheckout } from '@/lib/api'
import { clearToken } from '@/lib/auth'
import type { Student } from '@/lib/types'

const SUBJECT_META: Record<string, { label: string; desc: string; available: boolean }> = {
  mathematics: { label: 'Mathematics', desc: 'Pure, Mechanics & Statistics', available: true },
  physics:     { label: 'Physics',     desc: 'Coming soon',                  available: false },
  chemistry:   { label: 'Chemistry',   desc: 'Coming soon',                  available: false },
  biology:     { label: 'Biology',     desc: 'Coming soon',                  available: false },
}

function daysUntil(dateStr: string | null): number | null {
  if (!dateStr) return null
  const diff = Math.ceil((new Date(dateStr).getTime() - Date.now()) / 86400000)
  return diff > 0 ? diff : null
}

export default function DashboardPage() {
  const router = useRouter()
  const [student, setStudent] = useState<Student | null>(null)
  const [starting, setStarting] = useState<string | null>(null)

  useEffect(() => {
    getMe().then(setStudent).catch(() => router.push('/login'))
  }, [router])

  async function handleStartSession(subject: string) {
    if (!student) return
    setStarting(subject)
    try {
      const session = await startSession(subject, student.exam_date ?? undefined)
      router.push(`/session/${session.session_id}?opening=${encodeURIComponent(session.message)}`)
    } catch {
      setStarting(null)
    }
  }

  async function handleUpgrade() {
    try {
      const { url } = await createCheckout()
      window.location.href = url
    } catch { /* empty */ }
  }

  if (!student) {
    return (
      <div className="flex items-center justify-center min-h-screen" style={{ background: 'var(--bg)' }}>
        <div className="w-6 h-6 border-2 border-t-transparent rounded-full animate-spin" style={{ borderColor: 'var(--navy)' }} />
      </div>
    )
  }

  const days = daysUntil(student.exam_date)
  const subjects = student.subjects.length ? student.subjects : ['mathematics']
  const firstName = student.name.split(' ')[0]

  return (
    <div className="min-h-screen" style={{ background: 'var(--bg)' }}>
      {/* Header */}
      <header className="bg-white border-b border-slate-100 px-6 py-4 flex items-center justify-between sticky top-0 z-10">
        <span className="text-xl font-bold" style={{ color: 'var(--navy)' }}>Ascend</span>
        <div className="flex items-center gap-3">
          {student.subscription_tier === 'free' && (
            <button
              onClick={handleUpgrade}
              className="text-sm font-semibold text-white px-4 py-2 rounded-xl hover:opacity-90 transition-opacity"
              style={{ background: 'var(--blue)' }}
            >
              Upgrade to Pro
            </button>
          )}
          <button onClick={() => { clearToken(); router.push('/') }} className="text-sm text-slate-500 hover:text-slate-700">
            Sign out
          </button>
        </div>
      </header>

      <main className="max-w-2xl mx-auto px-4 py-10">

        {/* Welcome */}
        <div className="mb-10">
          <h1 className="text-3xl font-bold mb-1" style={{ color: 'var(--navy)' }}>
            Hey {firstName} 👋
          </h1>
          {days ? (
            <p className="text-slate-500">
              <span className="font-bold" style={{ color: 'var(--blue)' }}>{days} days</span> until your exam. Let's get to work.
            </p>
          ) : (
            <p className="text-slate-500">What would you like to work on today?</p>
          )}
        </div>

        {/* Exam countdown */}
        {days && (
          <div className="rounded-2xl p-6 mb-6 flex items-center justify-between" style={{ background: 'var(--navy)' }}>
            <div>
              <p className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-1">A-Level Exam Countdown</p>
              <p className="text-4xl font-bold text-white">{days} <span className="text-xl font-medium text-slate-400">days</span></p>
            </div>
            <div className="text-right">
              <p className="text-xs text-slate-400 mb-1">Stay consistent.</p>
              <p className="text-xs text-slate-400">Every session counts.</p>
            </div>
          </div>
        )}

        {/* Free tier banner */}
        {student.subscription_tier === 'free' && (
          <div className="rounded-2xl p-5 mb-6 flex items-center justify-between gap-4 border border-blue-100" style={{ background: '#EFF6FF' }}>
            <div>
              <p className="text-sm font-semibold" style={{ color: 'var(--navy)' }}>You're on the free plan</p>
              <p className="text-xs text-blue-600 mt-0.5">20 messages/day · Maths only · No session memory</p>
            </div>
            <button
              onClick={handleUpgrade}
              className="shrink-0 text-sm font-semibold text-white px-4 py-2 rounded-xl hover:opacity-90 transition-opacity"
              style={{ background: 'var(--blue)' }}
            >
              Go Pro →
            </button>
          </div>
        )}

        {/* Start a session */}
        <p className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-4">Start a session</p>
        <div className="grid gap-3 mb-8">
          {subjects.map(subject => {
            const meta = SUBJECT_META[subject] ?? { label: subject, desc: '', available: true }
            return (
              <button
                key={subject}
                onClick={() => meta.available && handleStartSession(subject)}
                disabled={!meta.available || starting === subject}
                className={`flex items-center justify-between w-full px-6 py-5 rounded-2xl border-2 bg-white text-left transition-all ${
                  meta.available
                    ? 'border-slate-100 hover:border-blue-200 hover:shadow-sm cursor-pointer'
                    : 'border-slate-100 opacity-50 cursor-not-allowed'
                }`}
              >
                <div>
                  <p className="font-bold text-sm" style={{ color: 'var(--navy)' }}>{meta.label}</p>
                  <p className="text-xs text-slate-400 mt-0.5">{meta.desc}</p>
                </div>
                {starting === subject
                  ? <div className="w-5 h-5 border-2 border-t-transparent rounded-full animate-spin" style={{ borderColor: 'var(--navy)' }} />
                  : meta.available
                  ? <span className="text-slate-400 font-medium">→</span>
                  : null
                }
              </button>
            )
          })}
        </div>

        {/* Nav cards */}
        <div className="grid grid-cols-2 gap-3">
          <Link href="/progress" className="bg-white rounded-2xl border border-slate-100 p-5 hover:border-slate-200 hover:shadow-sm transition-all">
            <p className="text-2xl mb-3">📊</p>
            <p className="text-sm font-bold" style={{ color: 'var(--navy)' }}>My Progress</p>
            <p className="text-xs text-slate-400 mt-1">Topic mastery & history</p>
          </Link>
          <Link href="/pricing" className="bg-white rounded-2xl border border-slate-100 p-5 hover:border-slate-200 hover:shadow-sm transition-all">
            <p className="text-2xl mb-3">⭐</p>
            <p className="text-sm font-bold" style={{ color: 'var(--navy)' }}>
              {student.subscription_tier === 'pro' ? 'Pro Plan' : 'Upgrade'}
            </p>
            <p className="text-xs text-slate-400 mt-1">
              {student.subscription_tier === 'pro' ? 'Unlimited access' : 'Unlock all subjects'}
            </p>
          </Link>
        </div>
      </main>
    </div>
  )
}
