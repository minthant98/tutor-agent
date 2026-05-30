'use client'
import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { updateProfile } from '@/lib/api'

const SUBJECTS = [
  { id: 'mathematics', label: 'Mathematics' },
  { id: 'physics', label: 'Physics', soon: true },
  { id: 'chemistry', label: 'Chemistry', soon: true },
  { id: 'biology', label: 'Biology', soon: true },
]

const EXAM_BOARDS = ['Edexcel', 'AQA', 'OCR']

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
        subjects: subjects.length ? subjects : ['mathematics'],
        exam_board: examBoard,
        exam_date: examDate || undefined,
      })
      router.push('/dashboard')
    } catch {
      router.push('/dashboard')
    }
  }

  return (
    <div className="min-h-screen flex flex-col items-center justify-center px-4 bg-gray-50">
      <div className="w-full max-w-md">
        {/* Progress */}
        <div className="flex gap-2 mb-8">
          {[1, 2, 3].map(s => (
            <div key={s} className={`h-1 flex-1 rounded-full transition-colors ${s <= step ? 'bg-indigo-600' : 'bg-gray-200'}`} />
          ))}
        </div>

        {step === 1 && (
          <div>
            <h1 className="text-2xl font-bold text-gray-900 mb-1">Which subjects are you taking?</h1>
            <p className="text-gray-500 text-sm mb-6">Select all that apply</p>
            <div className="space-y-3">
              {SUBJECTS.map(s => (
                <button
                  key={s.id}
                  onClick={() => !s.soon && toggleSubject(s.id)}
                  disabled={s.soon}
                  className={`w-full flex items-center justify-between px-4 py-3 rounded-xl border-2 text-left transition-all ${
                    subjects.includes(s.id)
                      ? 'border-indigo-600 bg-indigo-50 text-indigo-700'
                      : s.soon
                      ? 'border-gray-100 bg-gray-50 text-gray-400 cursor-not-allowed'
                      : 'border-gray-200 hover:border-indigo-300'
                  }`}
                >
                  <span className="font-medium">{s.label}</span>
                  {s.soon && <span className="text-xs bg-gray-200 text-gray-500 px-2 py-0.5 rounded-full">Coming soon</span>}
                  {subjects.includes(s.id) && <span className="text-indigo-600">✓</span>}
                </button>
              ))}
            </div>
            <button
              onClick={() => setStep(2)}
              disabled={subjects.length === 0}
              className="w-full mt-6 bg-indigo-600 text-white py-3 rounded-xl font-semibold hover:bg-indigo-700 disabled:opacity-40"
            >
              Continue →
            </button>
          </div>
        )}

        {step === 2 && (
          <div>
            <h1 className="text-2xl font-bold text-gray-900 mb-1">Which exam board?</h1>
            <p className="text-gray-500 text-sm mb-6">We'll use the right syllabus and mark schemes</p>
            <div className="space-y-3">
              {EXAM_BOARDS.map(b => (
                <button
                  key={b}
                  onClick={() => setExamBoard(b.toLowerCase())}
                  className={`w-full flex items-center justify-between px-4 py-3 rounded-xl border-2 text-left transition-all font-medium ${
                    examBoard === b.toLowerCase()
                      ? 'border-indigo-600 bg-indigo-50 text-indigo-700'
                      : 'border-gray-200 hover:border-indigo-300'
                  }`}
                >
                  {b}
                  {examBoard === b.toLowerCase() && <span className="text-indigo-600">✓</span>}
                </button>
              ))}
            </div>
            <button
              onClick={() => setStep(3)}
              className="w-full mt-6 bg-indigo-600 text-white py-3 rounded-xl font-semibold hover:bg-indigo-700"
            >
              Continue →
            </button>
          </div>
        )}

        {step === 3 && (
          <div>
            <h1 className="text-2xl font-bold text-gray-900 mb-1">When's your first exam?</h1>
            <p className="text-gray-500 text-sm mb-6">We'll count down and help you prepare in time</p>
            <input
              type="date"
              value={examDate}
              onChange={e => setExamDate(e.target.value)}
              min={new Date().toISOString().split('T')[0]}
              className="w-full border-2 border-gray-200 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
            <button
              onClick={finish}
              disabled={loading}
              className="w-full mt-6 bg-indigo-600 text-white py-3 rounded-xl font-semibold hover:bg-indigo-700 disabled:opacity-50"
            >
              {loading ? 'Setting up…' : "Let's go →"}
            </button>
            <button
              onClick={finish}
              className="w-full mt-2 text-sm text-gray-400 py-2 hover:text-gray-600"
            >
              Skip for now
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
