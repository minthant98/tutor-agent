'use client'
import { useState } from 'react'
import Link from 'next/link'
import { forgotPassword } from '@/lib/api'
import Logo from '@/components/Logo'

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState('')
  const [submitted, setSubmitted] = useState(false)
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setLoading(true)
    try {
      await forgotPassword(email)
    } catch {
      // swallow — we show the same "check your email" message either way
      // so attackers can't enumerate registered emails
    } finally {
      setLoading(false)
      setSubmitted(true)
    }
  }

  return (
    <div className="min-h-screen flex flex-col items-center justify-center px-4" style={{ background: 'var(--bg)' }}>
      <Logo size="lg" href="/" className="mb-10" />

      <div className="w-full max-w-sm bg-white rounded-2xl shadow-sm border border-slate-100 p-8">
        {!submitted ? (
          <>
            <h1 className="text-2xl font-bold mb-1" style={{ color: 'var(--navy)' }}>Forgot password?</h1>
            <p className="text-slate-500 text-sm mb-8">Enter your email and we&apos;ll send you a reset link.</p>

            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-600 mb-1.5 uppercase tracking-wide">Email</label>
                <input
                  type="email" required value={email} onChange={e => setEmail(e.target.value)}
                  className="w-full border border-slate-200 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:border-transparent transition-all"
                  placeholder="you@example.com"
                  autoFocus
                />
              </div>
              <button
                type="submit" disabled={loading}
                className="w-full text-white py-3 rounded-xl font-semibold text-sm hover:opacity-90 disabled:opacity-50 transition-opacity mt-2"
                style={{ background: 'var(--navy)' }}
              >
                {loading ? 'Sending…' : 'Send reset link'}
              </button>
            </form>
          </>
        ) : (
          <div className="text-center">
            <div
              className="w-12 h-12 rounded-full mx-auto mb-4 flex items-center justify-center text-white text-xl"
              style={{ background: 'var(--blue)' }}
            >
              ✓
            </div>
            <h1 className="text-2xl font-bold mb-2" style={{ color: 'var(--navy)' }}>Check your email</h1>
            <p className="text-slate-500 text-sm leading-relaxed">
              If an account exists for <span className="font-semibold text-slate-700">{email}</span>, we&apos;ve sent a password reset link.
              <br /><br />
              The link expires in 1 hour. Don&apos;t forget to check your spam folder.
            </p>
          </div>
        )}

        <p className="text-sm text-center text-slate-400 mt-6">
          <Link href="/login" className="font-semibold hover:underline" style={{ color: 'var(--blue)' }}>← Back to sign in</Link>
        </p>
      </div>
    </div>
  )
}
