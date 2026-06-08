'use client'
import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { createCheckout } from '@/lib/api'
import { track } from '@/lib/posthog'

const features = {
  free: [
    '50 messages per day',
    'Pure Mathematics only',
    'Socratic tutoring',
    'Explain & Guide modes',
    'Topic mastery tracking',
  ],
  pro: [
    'Unlimited messages',
    'All subjects (Maths, Physics, Chemistry)',
    'Session memory & continuity',
    'Personalised study plan',
    'Weak topic coaching',
    'Priority support',
  ],
}

export default function PricingPage() {
  const router = useRouter()

  useEffect(() => { track('pricing_viewed') }, [])

  async function handleUpgrade() {
    track('checkout_started', { source: 'pricing_page' })
    try {
      const { url } = await createCheckout()
      window.location.href = url
    } catch { /* empty */ }
  }

  return (
    <div className="min-h-screen" style={{ background: 'var(--bg)' }}>
      <header className="bg-white border-b border-slate-100 px-6 py-4 flex items-center gap-4 sticky top-0 z-10">
        <button onClick={() => router.back()} className="text-slate-400 hover:text-slate-600">←</button>
        <span className="text-xl font-bold" style={{ color: 'var(--navy)' }}>Stride</span>
      </header>

      <main className="max-w-3xl mx-auto px-4 py-12">
        <div className="text-center mb-10">
          <h1 className="text-3xl font-bold mb-2" style={{ color: 'var(--navy)' }}>Simple pricing</h1>
          <p className="text-slate-500">Less than the cost of one tutoring hour per month.</p>
        </div>

        <div className="grid sm:grid-cols-2 gap-6">
          {/* Free */}
          <div className="bg-white rounded-2xl border-2 border-slate-100 p-6">
            <p className="text-xs font-bold text-slate-400 uppercase tracking-widest">Free</p>
            <p className="mt-3 text-4xl font-bold" style={{ color: 'var(--navy)' }}>0 MMK</p>
            <p className="text-sm text-slate-400 mt-1">forever</p>
            <ul className="mt-6 space-y-3">
              {features.free.map(f => (
                <li key={f} className="flex items-start gap-2 text-sm text-slate-700">
                  <span className="text-green-500 mt-0.5 shrink-0">✓</span>{f}
                </li>
              ))}
            </ul>
            <button
              onClick={() => router.push('/dashboard')}
              className="mt-8 w-full py-2.5 rounded-xl border-2 border-slate-200 text-sm font-semibold text-slate-600 hover:border-slate-300 transition-colors"
            >
              Continue with Free
            </button>
          </div>

          {/* Pro */}
          <div className="rounded-2xl p-6 text-white relative overflow-hidden" style={{ background: 'var(--navy)' }}>
            <div
              className="absolute top-4 right-4 text-xs font-bold px-2 py-0.5 rounded-full"
              style={{ background: 'var(--blue)', color: 'white' }}
            >
              7-day trial
            </div>
            <p className="text-xs font-bold text-slate-400 uppercase tracking-widest">Pro</p>
            <p className="mt-3 text-4xl font-bold text-white">50,000 MMK</p>
            <p className="text-sm text-slate-400 mt-1">per month</p>
            <ul className="mt-6 space-y-3">
              {features.pro.map(f => (
                <li key={f} className="flex items-start gap-2 text-sm text-slate-300">
                  <span className="text-white mt-0.5 shrink-0">✓</span>{f}
                </li>
              ))}
            </ul>
            <button
              onClick={handleUpgrade}
              className="mt-8 w-full py-2.5 rounded-xl text-sm font-bold hover:opacity-90 transition-opacity"
              style={{ background: 'var(--blue)', color: 'white' }}
            >
              Start free trial →
            </button>
          </div>
        </div>

        <p className="text-center text-xs text-slate-400 mt-8">
          Cancel anytime. No questions asked.
        </p>
      </main>
    </div>
  )
}
