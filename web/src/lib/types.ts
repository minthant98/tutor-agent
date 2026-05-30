export interface Student {
  id: string
  email: string
  name: string
  exam_board: string
  exam_level: string
  subjects: string[]
  subscription_tier: 'free' | 'pro'
  subscription_status: 'active' | 'trialing' | 'past_due' | 'cancelled'
  exam_date: string | null
  onboarding_complete: boolean
}

export interface Message {
  role: 'student' | 'tutor'
  content: string
  metadata?: Record<string, unknown>
}

export interface Session {
  session_id: string
  message: string
  is_new_student: boolean
}

export interface MessageResponse {
  session_id: string
  response: string
  session_phase: string
  weak_topics: string[]
  turn_count: number
}

export interface ProgressResponse {
  subject: string
  overall_mastery: number
  weak_topics: TopicMastery[]
  strong_topics: TopicMastery[]
  total_sessions: number
}

export interface TopicMastery {
  topic: string
  mastery_score: number
  total_attempts: number
  is_weak: boolean
}

export type Signal = 'explain' | 'guide' | null
export type SessionPhase = 'diagnostic' | 'warmup' | 'main' | 'consolidation'
