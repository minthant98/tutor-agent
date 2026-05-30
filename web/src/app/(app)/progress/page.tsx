'use client'
import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { getProgress } from '@/lib/api'
import type { ProgressResponse, TopicMastery } from '@/lib/types'

function MasteryBar({ topic, score }: { topic: string; score: number }) {
  const pct = Math.round(Math.min(score, 1) * 100)
  const color = pct >= 70 ? 'var(--green)' : pct >= 40 ? '#F59E0B' : '#EF4444'
  const bg = pct >= 70 ? '#F0FDF4' : pct >= 40 ? '#FFFBEB' : '#FEF2F2'
  const label = pct >= 70 ? 'Strong' : pct >= 40 ? 'Developing' : 'Needs work'

  return (
    <div className="flex items-center gap-4 py-3 border-b border-slate-50 last:border-0">
      <div className="flex-1 min-w-0">
        <div className="flex items-center justify-between mb-1.5">
          <span className="text-sm font-medium capitalize" style={{ color: 'var(--navy)' }}>
            {topic.replace(/_/g, ' ')}
          </span>
          <span className="text-xs font-semibold px-2 py-0.5 rounded-full" style={{ color, background: bg }}>{label}</span>
        </div>
        <div className="w-full bg-slate-100 rounded-full h-2">
          <div
            className="h-2 rounded-full transition-all duration-700"
            style={{ width: `${pct}%`, background: color }}
          />
        </div>
      </div>
      <span className="text-sm font-bold w-10 text-right shrink-0" style={{ color: 'var(--navy)' }}>{pct}%</span>
    </div>
  )
}

export default function ProgressPage() {
  const router = useRouter()
  const [data, setData] = useState<ProgressResponse | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    getProgress('mathematics').then(setData).catch(() => {}).finally(() => setLoading(false))
  }, [])

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen" style={{ background: 'var(--bg)' }}>
        <div className="w-6 h-6 border-2 border-t-transparent rounded-full animate-spin" style={{ borderColor: 'var(--navy)' }} />
      </div>
    )
  }

  const allTopics: TopicMastery[] = [...(data?.weak_topics ?? []), ...(data?.strong_topics ?? [])]
  const overallPct = Math.round((data?.overall_mastery ?? 0) * 100)

  return (
    <div className="min-h-screen" style={{ background: 'var(--bg)' }}>
      <header className="bg-white border-b border-slate-100 px-6 py-4 flex items-center gap-4 sticky top-0 z-10">
        <button onClick={() => router.push('/dashboard')} className="text-slate-400 hover:text-slate-700 font-medium text-sm flex items-center gap-2">
          ← Dashboard
        </button>
        <span className="font-bold" style={{ color: 'var(--navy)' }}>Ascend</span>
      </header>

      <main className="max-w-2xl mx-auto px-4 py-10">
        <h1 className="text-3xl font-bold mb-1" style={{ color: 'var(--navy)' }}>Your Progress</h1>
        <p className="text-slate-500 text-sm mb-10">Mathematics · Edexcel A-Level</p>

        {/* Exam readiness */}
        <div className="rounded-2xl p-7 mb-6" style={{ background: 'var(--navy)' }}>
          <p className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-4">Exam Readiness</p>
          <div className="flex items-end gap-3 mb-4">
            <span className="text-6xl font-bold text-white">{overallPct}%</span>
            <span className="text-slate-400 text-sm mb-2">overall mastery</span>
          </div>
          <div className="w-full bg-white/10 rounded-full h-2">
            <div
              className="h-2 rounded-full transition-all duration-700"
              style={{ width: `${overallPct}%`, background: 'var(--green)' }}
            />
          </div>
        </div>

        {/* Stats row */}
        <div className="grid grid-cols-3 gap-4 mb-8">
          <div className="bg-white rounded-2xl border border-slate-100 p-5 text-center">
            <p className="text-3xl font-bold mb-1" style={{ color: 'var(--navy)' }}>{data?.total_sessions ?? 0}</p>
            <p className="text-xs text-slate-400">Sessions</p>
          </div>
          <div className="bg-white rounded-2xl border border-slate-100 p-5 text-center">
            <p className="text-3xl font-bold mb-1" style={{ color: 'var(--green)' }}>{data?.strong_topics?.length ?? 0}</p>
            <p className="text-xs text-slate-400">Strong topics</p>
          </div>
          <div className="bg-white rounded-2xl border border-slate-100 p-5 text-center">
            <p className="text-3xl font-bold mb-1" style={{ color: '#F59E0B' }}>{data?.weak_topics?.length ?? 0}</p>
            <p className="text-xs text-slate-400">Need work</p>
          </div>
        </div>

        {/* Topic mastery */}
        {allTopics.length > 0 ? (
          <div className="bg-white rounded-2xl border border-slate-100 p-6">
            <h2 className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-2">Topic Mastery</h2>
            <div>
              {allTopics
                .sort((a, b) => b.mastery_score - a.mastery_score)
                .map(t => <MasteryBar key={t.topic} topic={t.topic} score={t.mastery_score} />)
              }
            </div>
          </div>
        ) : (
          <div className="bg-white rounded-2xl border border-slate-100 p-12 text-center">
            <p className="text-4xl mb-4">📚</p>
            <p className="font-semibold mb-1" style={{ color: 'var(--navy)' }}>No data yet</p>
            <p className="text-slate-400 text-sm mb-6">Complete a session to see your topic mastery here.</p>
            <button
              onClick={() => router.push('/dashboard')}
              className="text-sm font-semibold text-white px-5 py-2.5 rounded-xl hover:opacity-90 transition-opacity"
              style={{ background: 'var(--navy)' }}
            >
              Start a session →
            </button>
          </div>
        )}
      </main>
    </div>
  )
}
