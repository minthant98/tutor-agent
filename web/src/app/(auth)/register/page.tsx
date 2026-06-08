'use client'
import { useState } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { register, login, getMe } from '@/lib/api'
import { setToken } from '@/lib/auth'
import { ApiError } from '@/lib/api'
import { identifyUser, track } from '@/lib/posthog'

export default function RegisterPage() {
  const router = useRouter()
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError('')
    if (password.length < 8) { setError('Password must be at least 8 characters.'); return }
    setLoading(true)
    try {
      await register(email, name, password)
      const { access_token } = await login(email, password)
      setToken(access_token)
      try {
        const student = await getMe()
        identifyUser(student.id, { email: student.email, subscription_tier: student.subscription_tier })
      } catch { /* empty */ }
      track('signup_completed')
      router.push('/onboarding')
    } catch (err) {
      if (err instanceof ApiError && err.status === 400) {
        setError('An account with this email already exists.')
      } else {
        setError('Something went wrong. Please try again.')
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex flex-col items-center justify-center px-4" style={{ background: 'var(--bg)' }}>
      <Link href="/" className="text-2xl font-bold mb-10" style={{ color: 'var(--navy)' }}>Stride</Link>

      <div className="w-full max-w-sm bg-white rounded-2xl shadow-sm border border-slate-100 p-8">
        <h1 className="text-2xl font-bold mb-1" style={{ color: 'var(--navy)' }}>Create your account</h1>
        <p className="text-slate-500 text-sm mb-8">Free to start · No credit card needed</p>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-600 mb-1.5 uppercase tracking-wide">Your name</label>
            <input
              type="text" required value={name} onChange={e => setName(e.target.value)}
              className="w-full border border-slate-200 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:border-transparent transition-all"
              placeholder="Alex Smith"
            />
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-600 mb-1.5 uppercase tracking-wide">Email</label>
            <input
              type="email" required value={email} onChange={e => setEmail(e.target.value)}
              className="w-full border border-slate-200 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:border-transparent transition-all"
              placeholder="you@example.com"
            />
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-600 mb-1.5 uppercase tracking-wide">Password</label>
            <input
              type="password" required value={password} onChange={e => setPassword(e.target.value)}
              className="w-full border border-slate-200 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:border-transparent transition-all"
              placeholder="At least 8 characters"
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
            {loading ? 'Creating account…' : 'Create account'}
          </button>
        </form>

        <p className="text-sm text-center text-slate-400 mt-6">
          Already have an account?{' '}
          <Link href="/login" className="font-semibold hover:underline" style={{ color: 'var(--blue)' }}>Sign in</Link>
        </p>
      </div>
    </div>
  )
}
