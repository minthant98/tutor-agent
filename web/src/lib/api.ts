import { getToken } from './auth'
import type { ActiveSession, EvaluationCard, MessageResponse, ProgressResponse, QuestionCard, Session, Signal, Student, StudyPlanResponse } from './types'

const API = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000/api/v1'

class ApiError extends Error {
  constructor(public status: number, message: string, public detail?: unknown) {
    super(message)
  }
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const token = getToken()
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(init.headers as Record<string, string>),
  }
  if (token) headers['Authorization'] = `Bearer ${token}`

  const res = await fetch(`${API}${path}`, { ...init, headers })

  if (!res.ok) {
    let detail: unknown
    try { detail = await res.json() } catch { /* empty */ }
    throw new ApiError(res.status, `Request failed: ${res.status}`, detail)
  }

  if (res.status === 204) return undefined as T
  return res.json()
}

// ── Auth ──────────────────────────────────────────────────────────────────────

export async function register(email: string, name: string, password: string): Promise<Student> {
  return request('/auth/register', {
    method: 'POST',
    body: JSON.stringify({ email, name, password }),
  })
}

export async function login(email: string, password: string): Promise<{ access_token: string }> {
  const form = new URLSearchParams({ username: email, password })
  const res = await fetch(`${API}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: form.toString(),
  })
  if (!res.ok) throw new ApiError(res.status, 'Login failed')
  return res.json()
}

export async function getMe(): Promise<Student> {
  return request('/auth/me')
}

export async function updateProfile(data: {
  subjects?: string[]
  exam_board?: string
  exam_date?: string
}): Promise<Student> {
  return request('/auth/profile', {
    method: 'PATCH',
    body: JSON.stringify(data),
  })
}

// ── Sessions ──────────────────────────────────────────────────────────────────

export async function startSession(subject: string, examDate?: string): Promise<Session> {
  return request('/sessions/start', {
    method: 'POST',
    body: JSON.stringify({ subject, exam_date: examDate ?? null }),
  })
}

export async function sendMessage(
  sessionId: string,
  message: string,
  signal: Signal = null
): Promise<MessageResponse> {
  return request('/sessions/message', {
    method: 'POST',
    body: JSON.stringify({ session_id: sessionId, message, signal }),
  })
}

export async function endSession(sessionId: string) {
  return request(`/sessions/end?session_id=${sessionId}`, { method: 'POST' })
}

export async function getActiveSession(): Promise<ActiveSession | null> {
  return request('/sessions/active')
}

export async function resumeSession(sessionId: string): Promise<Session> {
  return request(`/sessions/resume/${sessionId}`, { method: 'POST' })
}

export async function getProgress(subject: string): Promise<ProgressResponse> {
  return request(`/sessions/progress?subject=${subject}`)
}

// ── Study Plan ────────────────────────────────────────────────────────────────

export async function getStudyPlan(subject: string): Promise<StudyPlanResponse> {
  return request(`/study-plan?subject=${subject}`)
}

export async function regenerateStudyPlan(subject: string): Promise<StudyPlanResponse> {
  return request(`/study-plan/regenerate?subject=${subject}`, { method: 'POST' })
}

// ── Billing ───────────────────────────────────────────────────────────────────

export async function createCheckout(): Promise<{ url: string }> {
  return request('/billing/checkout', { method: 'POST', body: JSON.stringify({}) })
}

export async function createPortal(): Promise<{ url: string }> {
  return request('/billing/portal', { method: 'POST' })
}

// ── SSE streaming ─────────────────────────────────────────────────────────────

export function streamMessage(
  sessionId: string,
  message: string,
  signal: Signal,
  onToken: (token: string) => void,
  onDone: (meta: { session_phase: string; weak_topics: string[]; turn_count: number; plan_ready?: boolean }) => void,
  onError: (msg: string) => void,
  onQuestion?: (q: QuestionCard) => void,
  onEvaluation?: (e: EvaluationCard) => void
): () => void {
  const token = getToken()
  const controller = new AbortController()

  fetch(`${API}/sessions/stream`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
    body: JSON.stringify({ session_id: sessionId, message, signal }),
    signal: controller.signal,
  }).then(async (res) => {
    if (res.status === 429) {
      onError('__RATE_LIMIT__')
      return
    }
    if (!res.ok || !res.body) {
      onError('Connection failed. Please try again.')
      return
    }

    const reader = res.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() ?? ''

      for (const line of lines) {
        if (!line.startsWith('data: ')) continue
        try {
          const data = JSON.parse(line.slice(6))
          if (data.token) onToken(data.token)
          else if (data.question) onQuestion?.(data.question as QuestionCard)
          else if (data.evaluation) onEvaluation?.(data.evaluation as EvaluationCard)
          else if (data.done) onDone({ session_phase: data.session_phase, weak_topics: data.weak_topics ?? [], turn_count: data.turn_count ?? 0, plan_ready: data.plan_ready ?? false })
          else if (data.error) onError(data.error)
        } catch { /* empty */ }
      }
    }
  }).catch((err) => {
    if (err.name !== 'AbortError') onError('Connection lost. Please try again.')
  })

  return () => controller.abort()
}

export { ApiError }
