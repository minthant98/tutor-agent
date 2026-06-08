'use client'
import { useState } from 'react'
import Link from 'next/link'
import { useParams, useRouter } from 'next/navigation'
import { resetPassword } from '@/lib/api'
import Logo from '@/components/Logo'

export default function ResetPasswordPage() {
  const router = useRouter()
  const { token } = useParams<{ token: string }>()
  const [password, setPassword] = useState('')
  const [confirm, setConfirm] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [done, setDone] = useState(false)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError('')
    if (password.length < 8) {
      setError('Password must be at least 8 characters.')
      return
    }
    if (password !== confirm) {
      setError('Passwords do not match.')
      return
    }
    setLoading(true)
    try {
      await resetPassword(token, password)
      setDone(true)
      setTimeout(() => router.push('/login'), 2000)
    } catch (err) {
      const msg = err instanceof Error ? err.message : ''
      setError(
        msg.includes('expired') || msg.includes('Invalid')
          ? 'This reset link is invalid or expired. Request a new one.'
          : 'Something went wrong. Please try again.'
      )
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex flex-col items-center justify-center px-4" style={{ background: 'var(--bg)' }}>
      <Logo size="lg" href="/" className="mb-10" />

      <div className="w-full max-w-sm bg-white rounded-2xl shadow-sm border border-slate-100 p-8">
        {!done ? (
          <>
            <h1 className="text-2xl font-bold mb-1" style={{ color: 'var(--navy)' }}>Set a new password</h1>
            <p className="text-slate-500 text-sm mb-8">Choose something at least 8 characters long.</p>

            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-600 mb-1.5 uppercase tracking-wide">New password</label>
                <input
                  type="password" required value={password} onChange={e => setPassword(e.target.value)}
                  className="w-full border border-slate-200 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:border-transparent transition-all"
                  placeholder="••••••••"
                  autoFocus
                  minLength={8}
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-600 mb-1.5 uppercase tracking-wide">Confirm password</label>
                <input
                  type="password" required value={confirm} onChange={e => setConfirm(e.target.value)}
                  className="w-full border border-slate-200 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:border-transparent transition-all"
                  placeholder="••••••••"
                  minLength={8}
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
                {loading ? 'Updating…' : 'Update password'}
              </button>
            </form>
          </>
        ) : (
          <div className="text-center">
            <div
              className="w-12 h-12 rounded-full mx-auto mb-4 flex items-center justify-center text-white text-xl"
              style={{ background: '#10B981' }}
            >
              ✓
            </div>
            <h1 className="text-2xl font-bold mb-2" style={{ color: 'var(--navy)' }}>Password updated</h1>
            <p className="text-slate-500 text-sm">Redirecting you to sign in…</p>
          </div>
        )}

        <p className="text-sm text-center text-slate-400 mt-6">
          <Link href="/login" className="font-semibold hover:underline" style={{ color: 'var(--blue)' }}>← Back to sign in</Link>
        </p>
      </div>
    </div>
  )
}
