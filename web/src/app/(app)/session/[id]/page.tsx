'use client'
import { useEffect, useRef, useState, useCallback } from 'react'
import { useParams, useRouter, useSearchParams } from 'next/navigation'
import { streamMessage, endSession } from '@/lib/api'
import type { EvaluationCard, QuestionCard, Signal } from '@/lib/types'
import { renderMath } from '@/lib/math'
import { track } from '@/lib/posthog'
import { ExitConfirmation } from '@/components/session/exit-confirmation'
import { SegmentProgress } from '@/components/session/segment-progress'
import { useFeatureFlag } from '@/lib/feature-flags'
import { SessionShell } from '@/components/session/session-shell'
import { SegmentBand } from '@/components/session/segment-band'
import type { SegmentDisplay } from '@/components/session/segment-band'
import { SessionContent, type Segment } from '@/components/session/session-content'
import { ActionBar } from '@/components/session/action-bar'
import { SegmentTransition } from '@/components/session/segment-transition'
import { SessionComplete } from '@/components/session/session-complete'
import { useAutosave } from '@/hooks/use-autosave'

type ChatItem =
  | { kind: 'msg'; id: string; role: 'student' | 'tutor'; content: string; streaming?: boolean }
  | { kind: 'question'; id: string; data: QuestionCard; answered: boolean }
  | { kind: 'evaluation'; id: string; data: EvaluationCard }

const PHASE_LABEL: Record<string, string> = {
  intro: 'Getting started',
  diagnostic: 'Calibrating',
  warmup: 'Warm-up',
  main: 'Practice',
  consolidation: 'Wrapping up',
}

const PHASE_COLOR: Record<string, string> = {
  intro: '#94A3B8',
  diagnostic: '#94A3B8',
  warmup: '#F59E0B',
  main: '#3B82F6',
  consolidation: '#22C55E',
}

const DIFFICULTY_COLOR: Record<string, string> = {
  easy: '#22C55E',
  medium: '#F59E0B',
  hard: '#EF4444',
}

function MessageBubble({ item }: { item: Extract<ChatItem, { kind: 'msg' }> }) {
  const isAlex = item.role === 'tutor'
  return (
    <div className={`flex ${isAlex ? 'justify-start' : 'justify-end'} mb-5`}>
      {isAlex && (
        <div className="w-8 h-8 rounded-full text-white text-xs font-bold flex items-center justify-center mr-3 mt-1 shrink-0" style={{ background: 'var(--navy)' }}>
          A
        </div>
      )}
      <div
        className={`max-w-[75%] rounded-2xl px-4 py-3 text-sm leading-relaxed ${
          isAlex
            ? 'bg-white border border-slate-100 shadow-sm text-slate-800'
            : 'text-white'
        } ${item.streaming ? 'after:content-["▋"] after:animate-pulse after:ml-0.5 after:text-slate-400' : ''}`}
        style={!isAlex ? { background: 'var(--navy)' } : {}}
        dangerouslySetInnerHTML={{ __html: renderMath(item.content) }}
      />
    </div>
  )
}

function QuestionCardView({
  item,
  onSubmit,
  disabled,
}: {
  item: Extract<ChatItem, { kind: 'question' }>
  onSubmit: (answer: string) => void
  disabled: boolean
}) {
  const [answer, setAnswer] = useState('')
  const [showScheme, setShowScheme] = useState(false)
  const { data, answered } = item
  const diffColor = DIFFICULTY_COLOR[data.difficulty] ?? '#94A3B8'
  // Auto-reveal mark scheme after the student submits their answer
  const schemeOpen = answered || showScheme

  return (
    <div className="mb-6 rounded-2xl border-2 border-slate-200 bg-white overflow-hidden">
      <div className="px-5 py-3 border-b border-slate-100 flex items-center justify-between" style={{ background: 'var(--bg)' }}>
        <div className="flex items-center gap-3">
          <p className="text-xs font-bold text-slate-500 uppercase tracking-widest">Practice question</p>
          <span
            className="text-[10px] font-bold uppercase tracking-widest px-2 py-0.5 rounded-full text-white"
            style={{ background: diffColor }}
          >
            {data.difficulty}
          </span>
        </div>
        <p className="text-xs font-semibold text-slate-500">{data.marks_available} {data.marks_available === 1 ? 'mark' : 'marks'}</p>
      </div>
      <div
        className="px-5 py-4 text-sm leading-relaxed text-slate-800"
        dangerouslySetInnerHTML={{ __html: renderMath(data.question) }}
      />
      {!answered && (
        <div className="px-5 pb-5">
          <textarea
            value={answer}
            onChange={e => setAnswer(e.target.value)}
            placeholder="Show your working here..."
            rows={4}
            disabled={disabled}
            className="w-full resize-none border border-slate-200 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 disabled:opacity-50 mb-3"
          />
          <button
            onClick={() => { if (answer.trim()) onSubmit(answer.trim()) }}
            disabled={!answer.trim() || disabled}
            className="w-full text-sm font-semibold text-white py-2.5 rounded-xl hover:opacity-90 transition-opacity disabled:opacity-40"
            style={{ background: 'var(--navy)' }}
          >
            Submit answer →
          </button>
        </div>
      )}
      {answered && (
        <div className="px-5 pb-3 text-xs text-slate-400 italic">Answer submitted — see results below.</div>
      )}

      {/* Mark scheme — expandable before submit, auto-open after */}
      {data.mark_scheme && (
        <div className="border-t border-slate-100">
          <button
            onClick={() => setShowScheme(s => !s)}
            disabled={answered}
            className="w-full px-5 py-3 flex items-center justify-between hover:bg-slate-50 transition-colors disabled:cursor-default disabled:hover:bg-transparent"
          >
            <span className="text-xs font-bold text-slate-500 uppercase tracking-widest">Mark scheme</span>
            <span className="text-xs text-slate-400">{schemeOpen ? '▾' : '▸'}</span>
          </button>
          {schemeOpen && (
            <div
              className="px-5 pb-5 text-sm leading-relaxed text-slate-700 whitespace-pre-line"
              dangerouslySetInnerHTML={{ __html: renderMath(data.mark_scheme) }}
            />
          )}
        </div>
      )}
    </div>
  )
}

function EvaluationCardView({ data }: { data: EvaluationCard }) {
  const pct = data.marks_available > 0 ? Math.round((data.marks_awarded / data.marks_available) * 100) : 0
  const color = pct >= 70 ? 'var(--green)' : pct >= 40 ? '#F59E0B' : '#EF4444'
  const label = pct >= 70 ? 'Strong' : pct >= 40 ? 'Partial' : 'Needs work'

  return (
    <div className="mb-6 rounded-2xl border-2 overflow-hidden" style={{ borderColor: color, background: 'white' }}>
      <div className="px-5 py-4 flex items-center justify-between" style={{ background: 'var(--bg)' }}>
        <div>
          <p className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-1">Result</p>
          <p className="text-xs text-slate-500 capitalize">{data.topic.replace(/_/g, ' ')}</p>
        </div>
        <div className="text-right">
          <p className="text-3xl font-bold" style={{ color }}>
            {data.marks_awarded}<span className="text-slate-300 text-xl"> / {data.marks_available}</span>
          </p>
          <p className="text-xs font-semibold" style={{ color }}>{label}</p>
        </div>
      </div>
      <div className="w-full bg-slate-100 h-1.5">
        <div className="h-1.5 transition-all duration-500" style={{ width: `${pct}%`, background: color }} />
      </div>
      <div className="px-5 py-4 space-y-4">
        {data.correct_steps.length > 0 && (
          <div>
            <p className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-2">What you got right</p>
            <ul className="space-y-1.5">
              {data.correct_steps.map((step, i) => (
                <li key={i} className="flex items-start gap-2 text-sm text-slate-700">
                  <span className="text-green-500 mt-0.5 shrink-0">✓</span>
                  <span dangerouslySetInnerHTML={{ __html: renderMath(step) }} />
                </li>
              ))}
            </ul>
          </div>
        )}
        {data.errors.length > 0 && (
          <div>
            <p className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-2">Where marks were lost</p>
            <ul className="space-y-1.5">
              {data.errors.map((err, i) => (
                <li key={i} className="flex items-start gap-2 text-sm text-slate-700">
                  <span className="text-red-500 mt-0.5 shrink-0">✗</span>
                  <span dangerouslySetInnerHTML={{ __html: renderMath(err) }} />
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  )
}

const QUICK_ACTIONS = [
  { label: 'Explain simpler', signal: 'explain' as Signal },
  { label: 'Give a hint', signal: 'guide' as Signal },
  { label: 'Show an example', signal: null, preset: "Can you show me a worked example?" },
  { label: 'Exam-style question', signal: null, preset: "Can you give me an exam-style question on this?" },
]

export default function SessionPage() {
  const { id } = useParams<{ id: string }>()
  const searchParams = useSearchParams()
  const router = useRouter()
  const opening = searchParams.get('opening')
  const sessionV3 = useFeatureFlag('session_v3', false)

  const [items, setItems] = useState<ChatItem[]>([])
  const [input, setInput] = useState('')
  const [streaming, setStreaming] = useState(false)
  const [phase, setPhase] = useState('diagnostic')
  const [weakTopics, setWeakTopics] = useState<string[]>([])
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [rateLimited, setRateLimited] = useState(false)
  const [planReady, setPlanReady] = useState(false)
  const [showExit, setShowExit] = useState(false)
  const [segmentPlan, setSegmentPlan] = useState<{ idx: number; intent: string; status: string }[]>([])
  const [currentSegmentIdx, setCurrentSegmentIdx] = useState(0)
  const bottomRef = useRef<HTMLDivElement>(null)
  const abortRef = useRef<(() => void) | null>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  useEffect(() => {
    if (opening) {
      setItems([{ kind: 'msg', id: 'opening', role: 'tutor', content: opening }])
    }
  }, [opening])

  useEffect(() => {
    // Load segment plan from the active session record
    import('@/lib/api').then(({ apiFetch }) => {
      apiFetch<{ segment_plan: { idx: number; intent: string; status: string }[]; current_segment_idx: number }>('/sessions/active')
        .then((data) => {
          if (data && data.segment_plan?.length > 0) {
            setSegmentPlan(data.segment_plan)
            setCurrentSegmentIdx(data.current_segment_idx ?? 0)
          }
        })
        .catch(() => {/* non-critical — strip stays hidden */})
    })
  }, [id])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [items])

  const send = useCallback((signalOverride?: Signal, presetText?: string) => {
    const text = (presetText ?? input).trim()
    if (!text || streaming) return

    const userItem: ChatItem = { kind: 'msg', id: Date.now().toString(), role: 'student', content: text }
    const alexId = (Date.now() + 1).toString()
    const alexItem: ChatItem = { kind: 'msg', id: alexId, role: 'tutor', content: '', streaming: true }

    // Mark the most recent question as answered (if the message looks like an answer)
    setItems(prev => {
      const next = [...prev]
      for (let i = next.length - 1; i >= 0; i--) {
        const it = next[i]
        if (it.kind === 'question' && !it.answered) {
          next[i] = { ...it, answered: true }
          break
        }
      }
      return [...next, userItem, alexItem]
    })
    setInput('')
    setStreaming(true)

    if (signalOverride) track('signal_clicked', { signal: signalOverride })
    abortRef.current = streamMessage(
      id, text, signalOverride ?? null,
      (token) => {
        setItems(prev => prev.map(it => (it.kind === 'msg' && it.id === alexId) ? { ...it, content: it.content + token } : it))
      },
      (meta) => {
        setItems(prev => prev.map(it => (it.kind === 'msg' && it.id === alexId) ? { ...it, streaming: false } : it))
        setPhase(meta.session_phase)
        setWeakTopics(meta.weak_topics)
        if (meta.plan_ready) setPlanReady(true)
        setStreaming(false)
        textareaRef.current?.focus()
      },
      (errMsg) => {
        if (errMsg === '__RATE_LIMIT__') {
          setItems(prev => prev.filter(it => !(it.kind === 'msg' && it.id === alexId)))
          setRateLimited(true)
        } else {
          setItems(prev => prev.map(it => (it.kind === 'msg' && it.id === alexId) ? { ...it, content: errMsg, streaming: false } : it))
        }
        setStreaming(false)
      },
      (question) => {
        setItems(prev => [...prev, { kind: 'question', id: `q-${Date.now()}`, data: question, answered: false }])
      },
      (evaluation) => {
        setItems(prev => [...prev, { kind: 'evaluation', id: `e-${Date.now()}`, data: evaluation }])
      }
    )
  }, [id, input, streaming])

  async function handleEnd() {
    abortRef.current?.()
    await endSession(id).catch(() => {})
    router.push('/dashboard')
  }

  const phaseColor = PHASE_COLOR[phase] ?? '#94A3B8'
  const studentMsgCount = items.filter(it => it.kind === 'msg' && it.role === 'student').length
  const hasAnsweredAtLeastOne = items.length > 1

  // ── v3 focus-mode shell ──────────────────────────────────────────────────
  // Minimal transition + completion state for MVP. Real business logic
  // (advancing segments on backend, tracking completion via API, computing
  // readiness delta) is a TODO — left for the backend plumbing milestone.
  const [transitioningTo, setTransitioningTo] = useState<{
    prev: { intent: string };
    next: { intent: string; topic: string; minutes: number };
  } | null>(null)
  const [isComplete, setIsComplete] = useState(false)

  // Autosave: persist cursor position + input draft whenever they change.
  // Fires debounced PATCH /api/v1/sessions/{id}/state — failures are silent.
  useAutosave({ sessionId: id, state: { cursor: currentSegmentIdx, input_draft: input } })

  if (sessionV3) {
    // Convert legacy segment plan to SegmentDisplay format
    const segmentDisplays: SegmentDisplay[] = segmentPlan.map((s, i) => ({
      intent: s.intent,
      // Legacy plan has no topic — fall back to intent label
      topic: s.intent,
      state:
        i < currentSegmentIdx
          ? 'completed'
          : i === currentSegmentIdx
          ? 'current'
          : 'upcoming',
    }))

    // MOCK segment — real content plumbing is a future backend concern (noted in Task 10 report).
    // The page passes a hardcoded segment so SessionContent renders and the page compiles.
    const mockSegment: Segment = {
      intent: 'teach',
      blocks: [
        { type: 'prose', text: 'Welcome to your session. Content from the backend will appear here.' },
      ],
    }

    return (
      <SessionShell segments={segmentDisplays} sessionId={id}>
        <SessionContent segment={mockSegment} />

        {/* ActionBar: primary advances segment; right skips (MVP stubs). */}
        <ActionBar
          primary={{
            label: 'Continue',
            shortcut: '↵',
            // TODO: real advance-segment logic; for now shows transition overlay demo
            onClick: () => {
              if (segmentPlan.length > 1 && currentSegmentIdx < segmentPlan.length - 1) {
                const curr = segmentPlan[currentSegmentIdx]
                const nxt = segmentPlan[currentSegmentIdx + 1]
                setTransitioningTo({
                  prev: { intent: curr.intent },
                  next: { intent: nxt.intent, topic: nxt.intent, minutes: 6 },
                })
              } else {
                // No next segment → session complete
                setIsComplete(true)
              }
            },
          }}
          right={{ label: 'Skip', onClick: () => {} }}
        />

        {/* Segment transition overlay — shown between segments */}
        {transitioningTo && (
          <SegmentTransition
            prev={transitioningTo.prev}
            next={transitioningTo.next}
            onContinue={() => {
              // TODO: call API to advance segment index; update currentSegmentIdx
              setCurrentSegmentIdx(i => i + 1)
              setTransitioningTo(null)
            }}
          />
        )}

        {/* Session complete screen — shown when all segments done */}
        {isComplete && (
          <SessionComplete
            // TODO: compute real elapsed minutes from session start time
            totalMinutes={22}
            segmentCount={segmentPlan.length || 3}
            // TODO: fetch readiness from backend after session finalization
            readinessAfter={71}
          />
        )}
      </SessionShell>
    )
  }
  // ────────────────────────────────────────────────────────────────────────

  return (
    <div className="flex h-screen flex-col" style={{ background: 'var(--bg)' }}>
      <header className="flex items-center justify-between border-b border-slate-100 px-4 py-3 shrink-0 bg-white">
        {/* Segment progress — left side */}
        {segmentPlan.length > 0 && (
          <SegmentProgress plan={segmentPlan} currentIdx={currentSegmentIdx} />
        )}

        {/* Close button — right side */}
        <button
          onClick={() => setShowExit(true)}
          aria-label="Close session"
          className="ml-auto p-2 text-slate-400 hover:text-slate-700 text-lg"
        >
          ✕
        </button>
      </header>

      <div className="flex flex-1 overflow-hidden" style={{ background: 'var(--bg)' }}>

      {/* Left sidebar — topics */}
      <aside className={`
        ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'} lg:translate-x-0
        fixed lg:static inset-y-0 left-0 z-30
        w-60 shrink-0 border-r border-slate-100 bg-white flex flex-col transition-transform duration-200
      `}>
        <div className="px-5 py-5 border-b border-slate-100">
          <button onClick={() => router.push('/dashboard')} className="flex items-center gap-2 text-sm text-slate-500 hover:text-slate-800 font-medium">
            <span>←</span> Dashboard
          </button>
        </div>
        <div className="px-5 py-4 flex-1 overflow-y-auto">
          <p className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-4">Mathematics</p>
          {[
            ['Algebra & Functions', ['Quadratics', 'Polynomials', 'Inequalities']],
            ['Calculus', ['Differentiation', 'Integration', 'Differential Eq.']],
            ['Trigonometry', ['Identities', 'Equations', 'Graphs']],
            ['Statistics', ['Probability', 'Distributions', 'Hypothesis']],
          ].map(([section, topics]) => (
            <div key={section as string} className="mb-5">
              <p className="text-xs font-semibold text-slate-500 mb-2">{section as string}</p>
              {(topics as string[]).map(t => (
                <button
                  key={t}
                  onClick={() => { send(null, `Can we work on ${t.toLowerCase()}?`); setSidebarOpen(false) }}
                  disabled={streaming}
                  className="w-full text-left text-xs text-slate-500 hover:text-slate-800 py-1.5 px-2 rounded-lg hover:bg-slate-50 transition-colors disabled:opacity-40"
                >
                  {t}
                </button>
              ))}
            </div>
          ))}
        </div>
      </aside>

      {/* Mobile overlay */}
      {sidebarOpen && (
        <div className="fixed inset-0 z-20 bg-black/20 lg:hidden" onClick={() => setSidebarOpen(false)} />
      )}

      {/* Center — chat */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Chat header */}
        <header className="bg-white border-b border-slate-100 px-5 py-4 flex items-center gap-4 shrink-0">
          <button onClick={() => setSidebarOpen(s => !s)} className="lg:hidden text-slate-400 hover:text-slate-700 p-1">
            ☰
          </button>
          <div className="flex items-center gap-3 flex-1 min-w-0">
            <div className="w-9 h-9 rounded-full text-white text-sm font-bold flex items-center justify-center shrink-0" style={{ background: 'var(--navy)' }}>A</div>
            <div className="min-w-0">
              <p className="text-sm font-bold" style={{ color: 'var(--navy)' }}>Alex</p>
              <p className="text-xs truncate" style={{ color: phaseColor }}>
                {PHASE_LABEL[phase] ?? phase}
              </p>
            </div>
          </div>
          <button onClick={handleEnd} className="shrink-0 text-xs font-medium text-slate-400 hover:text-slate-700 border border-slate-200 px-3 py-1.5 rounded-lg hover:border-slate-300 transition-colors">
            End session
          </button>
        </header>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto px-5 py-6">
          <div className="max-w-2xl mx-auto">
            {items.map(item => {
              if (item.kind === 'msg') return <MessageBubble key={item.id} item={item} />
              if (item.kind === 'question') return (
                <QuestionCardView
                  key={item.id}
                  item={item}
                  disabled={streaming}
                  onSubmit={(ans) => {
                    track('question_submitted', {
                      topic: item.data.topic,
                      difficulty: item.data.difficulty,
                      marks_available: item.data.marks_available,
                      answer_length: ans.length,
                    })
                    send(null, ans)
                  }}
                />
              )
              return <EvaluationCardView key={item.id} data={item.data} />
            })}
            <div ref={bottomRef} />
          </div>
        </div>

        {/* Quick actions */}
        {!streaming && items.length > 1 && (
          <div className="px-5 pb-3">
            <div className="max-w-2xl mx-auto flex flex-wrap gap-2">
              {QUICK_ACTIONS.map(({ label, signal, preset }) => (
                <button
                  key={label}
                  onClick={() => {
                    if (preset) { send(null, preset) }
                    else if (signal && input.trim()) { send(signal) }
                    else if (preset === undefined && !input.trim()) {
                      if (signal === 'explain') setInput('Can you explain this concept?')
                      else setInput("I'm stuck, can you give me a hint?")
                    } else { send(signal) }
                  }}
                  className="text-xs border border-slate-200 bg-white text-slate-600 px-3 py-1.5 rounded-full hover:border-slate-300 hover:bg-slate-50 transition-colors"
                >
                  {label}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Study plan ready banner */}
        {planReady && (
          <div className="px-5 pb-3">
            <div className="max-w-2xl mx-auto rounded-2xl p-4 flex items-center justify-between gap-4" style={{ background: 'var(--navy)' }}>
              <div>
                <p className="text-sm font-semibold text-white">Study plan updated</p>
                <p className="text-xs text-slate-400 mt-0.5">Your dashboard reflects today's session.</p>
              </div>
              <button
                onClick={handleEnd}
                className="shrink-0 text-sm font-semibold text-white px-4 py-2 rounded-xl hover:opacity-90 transition-opacity"
                style={{ background: 'var(--blue)' }}
              >
                View dashboard →
              </button>
            </div>
          </div>
        )}

        {/* Rate limit banner */}
        {rateLimited && (
          <div className="px-5 py-4 border-t border-slate-100 bg-white shrink-0">
            <div className="max-w-2xl mx-auto rounded-2xl border border-amber-200 bg-amber-50 px-5 py-4 text-center">
              <p className="text-sm font-semibold text-amber-900 mb-1">You&apos;ve reached your 50 message limit</p>
              <p className="text-xs text-amber-700 mb-3">Upgrade to Pro for unlimited messages and full access to Alex.</p>
              <a
                href="/pricing"
                className="inline-block text-xs font-semibold text-white px-5 py-2 rounded-xl hover:opacity-90 transition-opacity"
                style={{ background: 'var(--navy)' }}
              >
                Upgrade to Pro
              </a>
            </div>
          </div>
        )}

        {/* Input */}
        <div className={`bg-white border-t border-slate-100 px-5 py-4 shrink-0 ${rateLimited ? 'opacity-40 pointer-events-none' : ''}`}>
          <div className="max-w-2xl mx-auto flex gap-3 items-end">
            <textarea
              ref={textareaRef}
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send() } }}
              placeholder="Type your answer or question…"
              rows={1}
              disabled={streaming}
              className="flex-1 resize-none border border-slate-200 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 disabled:opacity-50 max-h-36"
              style={{ fieldSizing: 'content', focusRingColor: 'var(--blue)' } as React.CSSProperties}
            />
            <button
              onClick={() => send()}
              disabled={!input.trim() || streaming}
              className="text-white rounded-xl px-4 py-3 text-sm font-semibold disabled:opacity-40 hover:opacity-90 transition-opacity shrink-0"
              style={{ background: 'var(--navy)' }}
            >
              {streaming
                ? <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                : '→'
              }
            </button>
          </div>
        </div>
      </div>

      {/* Right panel — learning */}
      <aside className="hidden xl:flex w-72 shrink-0 border-l border-slate-100 bg-white flex-col">
        {/* Alex card */}
        <div className="px-5 py-5 border-b border-slate-100">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-10 h-10 rounded-full text-white text-sm font-bold flex items-center justify-center shadow-sm" style={{ background: 'var(--navy)' }}>A</div>
            <div>
              <p className="text-sm font-bold" style={{ color: 'var(--navy)' }}>Alex</p>
              <p className="text-xs text-slate-400">A-Level Maths Tutor</p>
            </div>
          </div>
          <div className="rounded-xl px-3 py-2 text-xs" style={{ background: 'var(--bg)' }}>
            <span className="text-slate-500">Status: </span>
            <span className="font-medium" style={{ color: phaseColor }}>{PHASE_LABEL[phase] ?? phase}</span>
          </div>
        </div>

        {/* Session progress */}
        <div className="px-5 py-5 border-b border-slate-100">
          <p className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-3">Session</p>
          <div className="flex items-center justify-between mb-1.5">
            <span className="text-xs text-slate-500">Phase</span>
            <span className="text-xs font-semibold" style={{ color: phaseColor }}>{PHASE_LABEL[phase] ?? phase}</span>
          </div>
          <div className="w-full bg-slate-100 rounded-full h-1.5 mb-4">
            <div
              className="h-1.5 rounded-full transition-all duration-500"
              style={{
                background: phaseColor,
                width: { diagnostic: '10%', warmup: '35%', main: '70%', consolidation: '95%' }[phase] ?? '10%'
              }}
            />
          </div>
          <p className="text-xs text-slate-500 mb-1">Messages this session</p>
          <p className="text-2xl font-bold" style={{ color: 'var(--navy)' }}>{studentMsgCount}</p>
        </div>

        {/* Weak topics */}
        <div className="px-5 py-5 flex-1">
          <p className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-3">Weak topics</p>
          {weakTopics.length > 0 ? (
            <div className="space-y-2">
              {weakTopics.map(t => (
                <div key={t} className="flex items-center gap-2 px-3 py-2 rounded-xl border border-amber-100 bg-amber-50">
                  <span className="w-1.5 h-1.5 rounded-full bg-amber-400 shrink-0" />
                  <span className="text-xs text-amber-800 font-medium capitalize">{t.replace(/_/g, ' ')}</span>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-xs text-slate-400 leading-relaxed">Weak topics will appear here as Alex identifies them during your session.</p>
          )}
        </div>

        {/* End session / study plan */}
        <div className="px-5 py-5 border-t border-slate-100 space-y-2">
          {planReady && (
            <button
              onClick={handleEnd}
              className="w-full text-sm font-semibold text-white py-2.5 rounded-xl hover:opacity-90 transition-opacity"
              style={{ background: 'var(--blue)' }}
            >
              View study plan →
            </button>
          )}
          <button
            onClick={handleEnd}
            className="w-full text-sm font-medium text-slate-600 border border-slate-200 py-2.5 rounded-xl hover:border-slate-300 hover:text-slate-800 transition-colors"
          >
            End session
          </button>
        </div>
      </aside>
      </div>

      <ExitConfirmation
        open={showExit}
        onClose={() => setShowExit(false)}
        hasProgress={hasAnsweredAtLeastOne}
      />
    </div>
  )
}
