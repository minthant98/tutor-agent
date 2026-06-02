'use client'
import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { updateProfile } from '@/lib/api'

const SUBJECTS = [
  { id: 'pure_mathematics', label: 'Pure Mathematics', desc: 'Algebra, calculus, trigonometry & more' },
  { id: 'mechanics_statistics', label: 'Mechanics & Statistics', desc: 'Coming soon', soon: true },
  { id: 'physics', label: 'Physics', desc: 'Coming soon', soon: true },
  { id: 'chemistry', label: 'Chemistry', desc: 'Coming soon', soon: true },
]

const EXAM_BOARDS = [
  { id: 'edexcel', label: 'Edexcel', desc: 'A-Level' },
  { id: 'cambridge', label: 'Cambridge (CIE)', desc: 'A-Level / IGCSE' },
  { id: 'ib', label: 'IB', desc: 'International Baccalaureate', soon: true },
]

export default function OnboardingPage() {
  const router = useRouter()
  const [step, setStep] = useState(1)
  const [subjects, setSubjects] = useState<string[]>([])
  const [examBoard, setExamBoard] = useState('edexcel')
  const [examDate, setExamDate] = useState('')
  const [loading, setLoading] = useState(false)

  function toggleSubject(id: string) {
    setSubjects(prev => prev.includes(id) ? prev.filter(s => s !== id) : [...prev, id])
  }

  async function finish() {
    setLoading(true)
    try {
      await updateProfile({
        subjects: subjects.length ? subjects : ['pure_mathematics'],
        exam_board: examBoard,
        exam_date: examDate || undefined,
      })
      router.push('/dashboard')
    } catch {
      router.push('/dashboard')
    }
  }

  return (
    <div className="min-h-screen flex flex-col items-center justify-center px-4 py-10" style={{ background: 'var(--bg)' }}>
      <span className="text-2xl font-bold mb-8" style={{ color: 'var(--navy)' }}>Ascend</span>

      <div className="w-full max-w-md bg-white rounded-2xl shadow-sm border border-slate-100 p-8">
        {/* Progress */}
        <div className="flex gap-2 mb-8">
          {[1, 2, 3].map(s => (
            <div
              key={s}
              className="h-1 flex-1 rounded-full transition-colors"
              style={{ background: s <= step ? 'var(--blue)' : '#E2E8F0' }}
            />
          ))}
        </div>

        {step === 1 && (
          <div>
            <h1 className="text-2xl font-bold mb-1" style={{ color: 'var(--navy)' }}>Which subjects are you taking?</h1>
            <p className="text-slate-500 text-sm mb-6">Select all that apply</p>
            <div className="space-y-3">
              {SUBJECTS.map(s => {
                const selected = subjects.includes(s.id)
                return (
                  <button
                    key={s.id}
                    onClick={() => !s.soon && toggleSubject(s.id)}
                    disabled={s.soon}
                    className={`w-full flex items-center justify-between px-4 py-3 rounded-xl border-2 text-left transition-all ${
                      selected
                        ? 'bg-blue-50'
                        : s.soon
                        ? 'border-slate-100 bg-slate-50 cursor-not-allowed opacity-60'
                        : 'border-slate-200 hover:border-slate-300'
                    }`}
                    style={selected ? { borderColor: 'var(--blue)' } : {}}
                  >
                    <div>
                      <p className="font-semibold text-sm" style={{ color: selected ? 'var(--navy)' : s.soon ? '#94A3B8' : 'var(--navy)' }}>{s.label}</p>
                      {s.desc && <p className="text-xs text-slate-400 mt-0.5">{s.desc}</p>}
                    </div>
                    {s.soon && <span className="text-xs font-medium text-slate-500 bg-slate-100 px-2 py-0.5 rounded-full">Soon</span>}
                    {!s.soon && selected && <span className="font-bold" style={{ color: 'var(--blue)' }}>✓</span>}
                  </button>
                )
              })}
            </div>
            <button
              onClick={() => setStep(2)}
              disabled={subjects.length === 0}
              className="w-full mt-6 text-white py-3 rounded-xl text-sm font-semibold hover:opacity-90 disabled:opacity-40 transition-opacity"
              style={{ background: 'var(--navy)' }}
            >
              Continue →
            </button>
          </div>
        )}

        {step === 2 && (
          <div>
            <h1 className="text-2xl font-bold mb-1" style={{ color: 'var(--navy)' }}>Which exam board?</h1>
            <p className="text-slate-500 text-sm mb-6">We&apos;ll use the right syllabus and mark schemes</p>
            <div className="space-y-3">
              {EXAM_BOARDS.map(b => {
                const selected = examBoard === b.id
                return (
                  <button
                    key={b.id}
                    onClick={() => !b.soon && setExamBoard(b.id)}
                    disabled={b.soon}
                    className={`w-full flex items-center justify-between px-4 py-3 rounded-xl border-2 text-left transition-all ${
                      selected
                        ? 'bg-blue-50'
                        : b.soon
                        ? 'border-slate-100 bg-slate-50 cursor-not-allowed opacity-60'
                        : 'border-slate-200 hover:border-slate-300'
                    }`}
                    style={selected ? { borderColor: 'var(--blue)' } : {}}
                  >
                    <div>
                      <p className="font-semibold text-sm" style={{ color: selected ? 'var(--navy)' : b.soon ? '#94A3B8' : 'var(--navy)' }}>{b.label}</p>
                      <p className="text-xs text-slate-400 mt-0.5">{b.desc}</p>
                    </div>
                    {b.soon && <span className="text-xs font-medium text-slate-500 bg-slate-100 px-2 py-0.5 rounded-full">Soon</span>}
                    {!b.soon && selected && <span className="font-bold" style={{ color: 'var(--blue)' }}>✓</span>}
                  </button>
                )
              })}
            </div>
            <div className="flex gap-3 mt-6">
              <button
                onClick={() => setStep(1)}
                className="text-sm font-medium text-slate-500 px-4 py-3 rounded-xl border-2 border-slate-200 hover:border-slate-300 transition-colors"
              >
                ← Back
              </button>
              <button
                onClick={() => setStep(3)}
                className="flex-1 text-white py-3 rounded-xl text-sm font-semibold hover:opacity-90 transition-opacity"
                style={{ background: 'var(--navy)' }}
              >
                Continue →
              </button>
            </div>
          </div>
        )}

        {step === 3 && (
          <div>
            <h1 className="text-2xl font-bold mb-1" style={{ color: 'var(--navy)' }}>When&apos;s your first exam?</h1>
            <p className="text-slate-500 text-sm mb-6">We&apos;ll count down and help you prepare in time</p>
            <input
              type="date"
              value={examDate}
              onChange={e => setExamDate(e.target.value)}
              min={new Date().toISOString().split('T')[0]}
              className="w-full border-2 border-slate-200 rounded-xl px-4 py-3 text-sm focus:outline-none focus:border-slate-400 transition-colors"
            />
            <div className="flex gap-3 mt-6">
              <button
                onClick={() => setStep(2)}
                className="text-sm font-medium text-slate-500 px-4 py-3 rounded-xl border-2 border-slate-200 hover:border-slate-300 transition-colors"
              >
                ← Back
              </button>
              <button
                onClick={finish}
                disabled={loading}
                className="flex-1 text-white py-3 rounded-xl text-sm font-semibold hover:opacity-90 disabled:opacity-50 transition-opacity"
                style={{ background: 'var(--navy)' }}
              >
                {loading ? 'Setting up…' : "Let's go →"}
              </button>
            </div>
            <button
              onClick={finish}
              className="w-full mt-3 text-xs text-slate-400 py-2 hover:text-slate-600 transition-colors"
            >
              Skip for now
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
