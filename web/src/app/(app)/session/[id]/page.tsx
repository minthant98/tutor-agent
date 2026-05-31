'use client'
import { useEffect, useRef, useState, useCallback } from 'react'
import { useParams, useRouter, useSearchParams } from 'next/navigation'
import { streamMessage, endSession } from '@/lib/api'
import type { Message, Signal } from '@/lib/types'
import { renderMath } from '@/lib/math'

interface ChatMessage extends Message {
  id: string
  streaming?: boolean
}

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

function MessageBubble({ msg }: { msg: ChatMessage }) {
  const isAlex = msg.role === 'tutor'
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
        } ${msg.streaming ? 'after:content-["▋"] after:animate-pulse after:ml-0.5 after:text-slate-400' : ''}`}
        style={!isAlex ? { background: 'var(--navy)' } : {}}
        dangerouslySetInnerHTML={{ __html: renderMath(msg.content) }}
      />
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

  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [input, setInput] = useState('')
  const [streaming, setStreaming] = useState(false)
  const [phase, setPhase] = useState('diagnostic')
  const [weakTopics, setWeakTopics] = useState<string[]>([])
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [rateLimited, setRateLimited] = useState(false)
  const bottomRef = useRef<HTMLDivElement>(null)
  const abortRef = useRef<(() => void) | null>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  useEffect(() => {
    if (opening) {
      setMessages([{ id: 'opening', role: 'tutor', content: opening }])
    }
  }, [opening])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const send = useCallback((signalOverride?: Signal, presetText?: string) => {
    const text = (presetText ?? input).trim()
    if (!text || streaming) return

    const userMsg: ChatMessage = { id: Date.now().toString(), role: 'student', content: text }
    const alexMsgId = (Date.now() + 1).toString()
    const alexMsg: ChatMessage = { id: alexMsgId, role: 'tutor', content: '', streaming: true }

    setMessages(prev => [...prev, userMsg, alexMsg])
    setInput('')
    setStreaming(true)

    abortRef.current = streamMessage(
      id, text, signalOverride ?? null,
      (token) => {
        setMessages(prev => prev.map(m => m.id === alexMsgId ? { ...m, content: m.content + token } : m))
      },
      (meta) => {
        setMessages(prev => prev.map(m => m.id === alexMsgId ? { ...m, streaming: false } : m))
        setPhase(meta.session_phase)
        setWeakTopics(meta.weak_topics)
        setStreaming(false)
        textareaRef.current?.focus()
      },
      (errMsg) => {
        if (errMsg === '__RATE_LIMIT__') {
          setMessages(prev => prev.filter(m => m.id !== alexMsgId))
          setRateLimited(true)
        } else {
          setMessages(prev => prev.map(m => m.id === alexMsgId ? { ...m, content: errMsg, streaming: false } : m))
        }
        setStreaming(false)
      }
    )
  }, [id, input, streaming])

  async function handleEnd() {
    abortRef.current?.()
    await endSession(id).catch(() => {})
    router.push('/dashboard')
  }

  const phaseColor = PHASE_COLOR[phase] ?? '#94A3B8'

  return (
    <div className="flex h-screen overflow-hidden" style={{ background: 'var(--bg)' }}>

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
                <button key={t} className="w-full text-left text-xs text-slate-500 hover:text-slate-800 py-1.5 px-2 rounded-lg hover:bg-slate-50 transition-colors">
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
            {messages.map(msg => <MessageBubble key={msg.id} msg={msg} />)}
            <div ref={bottomRef} />
          </div>
        </div>

        {/* Quick actions */}
        {!streaming && messages.length > 1 && (
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

        {/* Rate limit banner */}
        {rateLimited && (
          <div className="px-5 py-4 border-t border-slate-100 bg-white shrink-0">
            <div className="max-w-2xl mx-auto rounded-2xl border border-amber-200 bg-amber-50 px-5 py-4 text-center">
              <p className="text-sm font-semibold text-amber-900 mb-1">You've reached your 20 message limit</p>
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
          <p className="text-2xl font-bold" style={{ color: 'var(--navy)' }}>{messages.filter(m => m.role === 'student').length}</p>
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

        {/* End session */}
        <div className="px-5 py-5 border-t border-slate-100">
          <button
            onClick={handleEnd}
            className="w-full text-sm font-medium text-slate-600 border border-slate-200 py-2.5 rounded-xl hover:border-slate-300 hover:text-slate-800 transition-colors"
          >
            End session
          </button>
        </div>
      </aside>
    </div>
  )
}
