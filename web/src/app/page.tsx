'use client'
import Link from 'next/link'
import { useState, useEffect } from 'react'

const DEMO_MESSAGES = [
  { role: 'student', content: 'Differentiate x²sin(x)', delay: 0 },
  { role: 'tutor', content: 'Good question. When two functions are multiplied together, which differentiation rule do we need?', delay: 1400 },
  { role: 'student', content: 'The product rule?', delay: 3000 },
  { role: 'tutor', content: 'Exactly. If y = uv, then dy/dx = u\'v + uv\'. So what would you set as u and v here?', delay: 4400 },
  { role: 'student', content: 'u = x² and v = sin(x)?', delay: 6000 },
  { role: 'tutor', content: 'Perfect. Now differentiate each — what\'s du/dx and dv/dx?', delay: 7400 },
]

function DemoChat() {
  const [visible, setVisible] = useState(0)
  const [typing, setTyping] = useState(false)

  useEffect(() => {
    if (visible >= DEMO_MESSAGES.length) return
    const msg = DEMO_MESSAGES[visible]
    const t = setTimeout(() => {
      if (msg.role === 'tutor') setTyping(true)
      const t2 = setTimeout(() => {
        setTyping(false)
        setVisible(v => v + 1)
      }, msg.role === 'tutor' ? 900 : 0)
      return () => clearTimeout(t2)
    }, msg.delay)
    return () => clearTimeout(t)
  }, [visible])

  return (
    <div className="space-y-3">
      {DEMO_MESSAGES.slice(0, visible).map((m, i) => (
        <div key={i} className={`flex ${m.role === 'tutor' ? 'justify-start' : 'justify-end'}`}>
          {m.role === 'tutor' && (
            <div className="w-7 h-7 rounded-full text-white text-xs font-bold flex items-center justify-center mr-2 mt-1 shrink-0" style={{ background: 'var(--navy)' }}>A</div>
          )}
          <div className={`max-w-[80%] rounded-2xl px-3.5 py-2.5 text-sm leading-relaxed ${
            m.role === 'tutor'
              ? 'bg-slate-50 text-slate-800 border border-slate-100'
              : 'text-white'
          }`} style={m.role === 'student' ? { background: 'var(--blue)' } : {}}>
            {m.content}
          </div>
        </div>
      ))}
      {typing && (
        <div className="flex justify-start">
          <div className="w-7 h-7 rounded-full text-white text-xs font-bold flex items-center justify-center mr-2 shrink-0" style={{ background: 'var(--navy)' }}>A</div>
          <div className="bg-slate-50 border border-slate-100 rounded-2xl px-4 py-3">
            <div className="flex gap-1 items-center h-4">
              {[0, 150, 300].map(d => (
                <span key={d} className="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: `${d}ms` }} />
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

const PROBLEMS = [
  { icon: '😓', title: 'Stuck on a problem at 11pm', body: "Your tutor is asleep. Your exam is in 6 weeks. Alex is always available." },
  { icon: '💸', title: 'Private tutors cost £50+/hr', body: 'Alex costs less than a single session — for an entire month of unlimited tutoring.' },
  { icon: '📋', title: 'Not enough past paper practice', body: 'Alex draws from thousands of real Edexcel past paper questions and mark schemes.' },
]

const HOW = [
  { step: '01', title: 'Ask anything', body: "Type a question, a problem, or just say you're stuck." },
  { step: '02', title: 'Get guided hints', body: 'Alex asks the right questions to help you reach the answer yourself.' },
  { step: '03', title: 'Master the concept', body: 'Build genuine understanding, not just memorised steps.' },
  { step: '04', title: 'Track progress', body: 'See your mastery grow topic by topic as you practice.' },
]

export default function LandingPage() {
  return (
    <div className="min-h-screen" style={{ background: 'var(--bg)' }}>

      {/* Nav */}
      <nav className="sticky top-0 z-50 border-b border-slate-200 bg-white/80 backdrop-blur-md">
        <div className="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
          <span className="text-xl font-bold" style={{ color: 'var(--navy)' }}>Ascend</span>
          <div className="flex items-center gap-3">
            <Link href="/login" className="text-sm font-medium text-slate-600 hover:text-slate-900 px-3 py-2">Sign in</Link>
            <Link href="/register" className="text-sm font-semibold text-white px-4 py-2 rounded-xl hover:opacity-90 transition-opacity" style={{ background: 'var(--navy)' }}>
              Get started free
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section className="max-w-6xl mx-auto px-6 py-20 lg:py-28 grid lg:grid-cols-2 gap-16 items-center">
        <div>
          <div className="inline-flex items-center gap-2 text-xs font-semibold px-3 py-1.5 rounded-full mb-8 border" style={{ color: 'var(--blue)', borderColor: '#BFDBFE', background: '#EFF6FF' }}>
            <span className="w-1.5 h-1.5 rounded-full bg-blue-500 inline-block" />
            Built for Edexcel A-Level · Maths
          </div>
          <h1 className="text-5xl lg:text-6xl font-bold leading-tight tracking-tight mb-6" style={{ color: 'var(--navy)' }}>
            Your personal<br />A-Level tutor.<br />
            <span style={{ color: 'var(--blue)' }}>Available 24/7.</span>
          </h1>
          <p className="text-lg text-slate-500 leading-relaxed mb-10 max-w-lg">
            Alex guides you to answers — never just gives them. Grounded in real Edexcel past papers. Remembers your weak topics.
          </p>
          <div className="flex flex-wrap gap-3">
            <Link href="/register" className="inline-flex items-center gap-2 text-sm font-semibold text-white px-6 py-3 rounded-xl shadow-sm hover:opacity-90 transition-opacity" style={{ background: 'var(--navy)' }}>
              Start free →
            </Link>
            <a href="#how" className="inline-flex items-center gap-2 text-sm font-semibold px-6 py-3 rounded-xl border border-slate-200 text-slate-700 hover:border-slate-300 bg-white transition-colors">
              See how Alex teaches
            </a>
          </div>
          <p className="text-xs text-slate-400 mt-4">Free to start · No credit card needed</p>
        </div>

        {/* Animated demo */}
        <div className="relative">
          <div className="bg-white rounded-2xl shadow-xl border border-slate-100 overflow-hidden">
            <div className="border-b border-slate-100 px-5 py-4 flex items-center gap-3">
              <div className="w-9 h-9 rounded-full flex items-center justify-center text-white text-sm font-bold" style={{ background: 'var(--navy)' }}>A</div>
              <div>
                <p className="text-sm font-semibold" style={{ color: 'var(--navy)' }}>Alex</p>
                <p className="text-xs text-slate-400">A-Level Maths Tutor · Edexcel</p>
              </div>
              <span className="ml-auto flex items-center gap-1.5 text-xs text-emerald-600 font-medium">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 inline-block animate-pulse" />Online
              </span>
            </div>
            <div className="p-5 min-h-56">
              <DemoChat />
            </div>
            <div className="border-t border-slate-100 px-4 py-3">
              <div className="flex items-center gap-2 px-3 py-2 rounded-xl bg-slate-50 text-sm text-slate-400">
                <span>Type your question…</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Problems */}
      <section className="border-y border-slate-100 bg-white py-20">
        <div className="max-w-6xl mx-auto px-6">
          <p className="text-center text-xs font-bold text-slate-400 uppercase tracking-widest mb-12">Sound familiar?</p>
          <div className="grid md:grid-cols-3 gap-6">
            {PROBLEMS.map(p => (
              <div key={p.title} className="rounded-2xl p-7 border border-slate-100" style={{ background: 'var(--bg)' }}>
                <span className="text-3xl mb-4 block">{p.icon}</span>
                <h3 className="font-semibold text-base mb-2" style={{ color: 'var(--navy)' }}>{p.title}</h3>
                <p className="text-sm text-slate-500 leading-relaxed">{p.body}</p>
              </div>
            ))}
          </div>
          <p className="text-center mt-12 font-semibold text-base" style={{ color: 'var(--navy)' }}>
            Alex helps you think like an examiner.
          </p>
        </div>
      </section>

      {/* How it works */}
      <section id="how" className="py-24 max-w-6xl mx-auto px-6">
        <p className="text-xs font-bold text-slate-400 uppercase tracking-widest text-center mb-3">How it works</p>
        <h2 className="text-3xl font-bold text-center mb-16" style={{ color: 'var(--navy)' }}>Tutoring that builds real understanding</h2>
        <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-10">
          {HOW.map(h => (
            <div key={h.step} className="text-center">
              <span className="text-5xl font-bold block mb-4" style={{ color: '#E2E8F0' }}>{h.step}</span>
              <h3 className="font-semibold text-sm mb-2" style={{ color: 'var(--navy)' }}>{h.title}</h3>
              <p className="text-xs text-slate-500 leading-relaxed">{h.body}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Exam countdown CTA */}
      <section className="max-w-6xl mx-auto px-6 pb-8">
        <div className="rounded-2xl px-8 py-8 flex items-center justify-between gap-6 flex-wrap" style={{ background: 'var(--navy)' }}>
          <div>
            <p className="text-white font-bold text-xl">A-Level exams are coming.</p>
            <p className="text-slate-400 text-sm mt-1">Every session with Alex builds toward your target grade.</p>
          </div>
          <Link href="/register" className="shrink-0 text-sm font-semibold px-6 py-3 rounded-xl hover:opacity-90 transition-opacity" style={{ background: 'var(--blue)', color: 'white' }}>
            Start preparing →
          </Link>
        </div>
      </section>

      {/* Pricing */}
      <section className="py-24 max-w-4xl mx-auto px-6">
        <p className="text-xs font-bold text-slate-400 uppercase tracking-widest text-center mb-3">Pricing</p>
        <h2 className="text-3xl font-bold text-center mb-16" style={{ color: 'var(--navy)' }}>Less than the cost of one tutoring hour</h2>
        <div className="grid sm:grid-cols-2 gap-6">
          <div className="rounded-2xl p-8 border-2 border-slate-100 bg-white">
            <p className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-5">Free</p>
            <p className="text-5xl font-bold mb-1" style={{ color: 'var(--navy)' }}>£0</p>
            <p className="text-sm text-slate-400 mb-8">forever</p>
            <ul className="space-y-3 text-sm text-slate-600 mb-8">
              {['20 messages per day', 'Mathematics only', 'Socratic tutoring', 'Explain & Guide modes'].map(f => (
                <li key={f} className="flex items-center gap-2.5"><span className="text-emerald-500 font-bold">✓</span>{f}</li>
              ))}
            </ul>
            <Link href="/register" className="block text-center text-sm font-semibold py-3 rounded-xl border-2 border-slate-200 text-slate-700 hover:border-slate-300 transition-colors">
              Get started free
            </Link>
          </div>

          <div className="rounded-2xl p-8 border-2 text-white relative overflow-hidden" style={{ background: 'var(--navy)', borderColor: 'var(--navy)' }}>
            <div className="absolute top-5 right-5 text-xs font-bold px-2.5 py-1 rounded-full" style={{ background: 'var(--blue)' }}>7-day trial</div>
            <p className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-5">Pro</p>
            <p className="text-5xl font-bold mb-1">£9.99</p>
            <p className="text-sm text-slate-400 mb-8">per month</p>
            <ul className="space-y-3 text-sm text-slate-300 mb-8">
              {['Unlimited messages', 'All subjects (Maths, Physics, Chemistry)', 'Cross-session memory', 'Exam readiness score', 'Weekly progress emails'].map(f => (
                <li key={f} className="flex items-center gap-2.5"><span className="text-emerald-400 font-bold">✓</span>{f}</li>
              ))}
            </ul>
            <Link href="/register" className="block text-center text-sm font-semibold py-3 rounded-xl hover:opacity-90 transition-opacity" style={{ background: 'var(--blue)' }}>
              Start free trial →
            </Link>
          </div>
        </div>
        <p className="text-center text-xs text-slate-400 mt-6">Cancel anytime. No questions asked.</p>
      </section>

      {/* Footer */}
      <footer className="border-t border-slate-100 bg-white py-10">
        <div className="max-w-6xl mx-auto px-6 flex flex-col sm:flex-row items-center justify-between gap-4">
          <span className="font-bold text-sm" style={{ color: 'var(--navy)' }}>Ascend</span>
          <p className="text-xs text-slate-400">Built for A-Level students. Powered by AI. © 2026 Ascend.</p>
          <div className="flex gap-6 text-xs text-slate-400">
            <a href="#" className="hover:text-slate-600">Privacy</a>
            <a href="#" className="hover:text-slate-600">Terms</a>
          </div>
        </div>
      </footer>
    </div>
  )
}
