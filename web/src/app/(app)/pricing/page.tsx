'use client'
import { useRouter } from 'next/navigation'
import { createCheckout } from '@/lib/api'

const features = {
  free: [
    '20 messages per day',
    'Mathematics only',
    'Socratic tutoring',
    'Explain & Guide modes',
    'KaTeX math rendering',
  ],
  pro: [
    'Unlimited messages',
    'All subjects (Maths, Physics, Chemistry, Biology)',
    'Cross-session memory',
    'Exam readiness score',
    'Weekly progress emails',
    'Priority support',
  ],
}

export default function PricingPage() {
  const router = useRouter()

  async function handleUpgrade() {
    try {
      const { url } = await createCheckout()
      window.location.href = url
    } catch { /* empty */ }
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b border-gray-100 px-6 py-4 flex items-center gap-4">
        <button onClick={() => router.back()} className="text-gray-400 hover:text-gray-600">←</button>
        <span className="text-xl font-bold text-indigo-600">Ascend</span>
      </header>

      <main className="max-w-3xl mx-auto px-4 py-12">
        <div className="text-center mb-10">
          <h1 className="text-3xl font-bold text-gray-900">Simple pricing</h1>
          <p className="text-gray-500 mt-2">Less than the cost of one tutoring hour per month.</p>
        </div>

        <div className="grid sm:grid-cols-2 gap-6">
          {/* Free */}
          <div className="bg-white rounded-2xl border-2 border-gray-100 p-6">
            <p className="text-sm font-semibold text-gray-500 uppercase tracking-wide">Free</p>
            <p className="mt-2 text-4xl font-bold text-gray-900">£0</p>
            <p className="text-sm text-gray-400 mt-1">forever</p>
            <ul className="mt-6 space-y-3">
              {features.free.map(f => (
                <li key={f} className="flex items-start gap-2 text-sm text-gray-700">
                  <span className="text-green-500 mt-0.5">✓</span>{f}
                </li>
              ))}
            </ul>
            <button
              onClick={() => router.push('/dashboard')}
              className="mt-8 w-full py-2.5 rounded-xl border-2 border-gray-200 text-sm font-semibold text-gray-700 hover:border-indigo-300 transition-colors"
            >
              Continue with Free
            </button>
          </div>

          {/* Pro */}
          <div className="bg-indigo-600 rounded-2xl border-2 border-indigo-600 p-6 text-white relative overflow-hidden">
            <div className="absolute top-4 right-4 bg-white text-indigo-600 text-xs font-bold px-2 py-0.5 rounded-full">7-day trial</div>
            <p className="text-sm font-semibold text-indigo-200 uppercase tracking-wide">Pro</p>
            <p className="mt-2 text-4xl font-bold">£9.99</p>
            <p className="text-sm text-indigo-300 mt-1">per month</p>
            <ul className="mt-6 space-y-3">
              {features.pro.map(f => (
                <li key={f} className="flex items-start gap-2 text-sm text-indigo-100">
                  <span className="text-white mt-0.5">✓</span>{f}
                </li>
              ))}
            </ul>
            <button
              onClick={handleUpgrade}
              className="mt-8 w-full py-2.5 rounded-xl bg-white text-indigo-600 text-sm font-bold hover:bg-indigo-50 transition-colors"
            >
              Start free trial →
            </button>
          </div>
        </div>

        <p className="text-center text-xs text-gray-400 mt-8">
          Cancel anytime. No questions asked. Prices exclude VAT.
        </p>
      </main>
    </div>
  )
}
