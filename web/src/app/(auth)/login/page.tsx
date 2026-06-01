'use client'
import { useState } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { login, getMe } from '@/lib/api'
import { setToken } from '@/lib/auth'
import { identifyUser, track } from '@/lib/posthog'

export default function LoginPage() {
  const router = useRouter()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const { access_token } = await login(email, password)
      setToken(access_token)
      const student = await getMe()
      identifyUser(student.id, {
        email: student.email,
        subscription_tier: student.subscription_tier,
        exam_board: student.exam_board,
      })
      track('login_completed')
      router.push(student.onboarding_complete ? '/dashboard' : '/onboarding')
    } catch {
      setError('Incorrect email or password.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex flex-col items-center justify-center px-4" style={{ background: 'var(--bg)' }}>
      <Link href="/" className="text-2xl font-bold mb-10" style={{ color: 'var(--navy)' }}>Ascend</Link>

      <div className="w-full max-w-sm bg-white rounded-2xl shadow-sm border border-slate-100 p-8">
        <h1 className="text-2xl font-bold mb-1" style={{ color: 'var(--navy)' }}>Welcome back</h1>
        <p className="text-slate-500 text-sm mb-8">Sign in to your account</p>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-600 mb-1.5 uppercase tracking-wide">Email</label>
            <input
              type="email" required value={email} onChange={e => setEmail(e.target.value)}
              className="w-full border border-slate-200 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:border-transparent transition-all"
              style={{ '--tw-ring-color': 'var(--blue)' } as React.CSSProperties}
              placeholder="you@example.com"
            />
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-600 mb-1.5 uppercase tracking-wide">Password</label>
            <input
              type="password" required value={password} onChange={e => setPassword(e.target.value)}
              className="w-full border border-slate-200 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:border-transparent transition-all"
              placeholder="••••••••"
            />
          </div>

          {error && (
            <div className="text-sm text-red-700 bg-red-50 border border-red-100 px-4 py-3 rounded-xl">
              {error}
            </div>
          )}

          <button
            type="submit" disabled={loading}
            className="w-full text-white py-3 rounded-xl font-semibold text-sm hover:opacity-90 disabled:opacity-50 transition-opacity mt-2"
            style={{ background: 'var(--navy)' }}
          >
            {loading ? 'Signing in…' : 'Sign in'}
          </button>
        </form>

        <p className="text-sm text-center text-slate-400 mt-6">
          No account?{' '}
          <Link href="/register" className="font-semibold hover:underline" style={{ color: 'var(--blue)' }}>Sign up free</Link>
        </p>
      </div>
    </div>
  )
}
