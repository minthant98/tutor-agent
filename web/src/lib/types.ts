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

export interface ActiveSession {
  session_id: string
  subject: string
  topic: string | null
  started_at: string
  message_count: number
  last_message: string | null
}

export interface StudyPlanWeek {
  week: number
  topics: string[]
  focus: string
}

export interface StudyPlanResponse {
  subject: string
  weeks_remaining: number
  plan: StudyPlanWeek[]
  generated_at: string
}

export interface QuestionCard {
  question: string
  marks_available: number
  difficulty: string
  topic: string
  mark_scheme: string
}

export interface EvaluationCard {
  marks_awarded: number
  marks_available: number
  score_pct: number
  topic: string
  correct_steps: string[]
  errors: string[]
}

// ── Onboarding ────────────────────────────────────────────────────────────────

export type WizardStep =
  | "subjects"
  | "exam-board"
  | "exam-date"
  | "target-grade"
  | "preferences"
  | "roadmap"
  | "done"

export interface WizardStateOut {
  next_step: WizardStep
  progress_pct: number
}

export interface SubjectsIn {
  subjects: string[]
}

export interface ExamBoardIn {
  exam_board: string
}

export interface ExamDateIn {
  exam_date: string | null // ISO date string yyyy-MM-dd, or null if not known
}

export interface TargetGradeIn {
  target_grade: string
}

export interface WizardPreferencesIn {
  worked_examples: boolean
  visual: boolean
  step_by_step: boolean
  practice: boolean
}

// ── Dashboard ─────────────────────────────────────────────────────────────────

export interface SegmentOut {
  idx: number
  intent: string
  handler: string
  topic: string | null
  why: string
  target_minutes: number
  status: string
}

export interface TodayFocusOut {
  shape: string
  segment_plan: SegmentOut[]
  total_minutes: number
  generated_at: string // ISO datetime
}

export interface ResumeSessionOut {
  session_id: string
  completed_segments: number
  total_segments: number
}

export interface TopicMasteryOut {
  topic: string
  topic_name: string
  mastery_pct: number
}

export interface TrendOut {
  prev_pct: number
  new_pct: number
  delta: number
}

export interface RecentActivityOut {
  last_studied: string | null // ISO date
  summary: string | null
  cold: boolean
}

export interface DashboardPayload {
  subject: string
  exam_date: string | null // ISO date
  days_until_exam: number | null
  target_grade: string
  predicted_grade: string | null
  readiness_pct: number
  readiness_trend: TrendOut | null
  today_focus: TodayFocusOut
  resume_session: ResumeSessionOut | null
  recent_activity: RecentActivityOut | null
  strong_topics: TopicMasteryOut[]
  weak_topics: TopicMasteryOut[]
  subject_options: string[]
}

// ── Account ───────────────────────────────────────────────────────────────────

export interface ProfileOut {
  name: string
  email: string
}

export interface SubjectOut {
  id: string
  subject: string
  exam_board: string
  exam_level: string
  exam_date: string | null // ISO date
  target_grade: string
  current_grade: string | null
  readiness_pct: number
}

export interface PreferencesOut {
  worked_examples: boolean
  visual: boolean
  step_by_step: boolean
  practice: boolean
}

export interface BillingOut {
  tier: string
  status: string
}

export interface AccountOut {
  profile: ProfileOut
  subjects: SubjectOut[]
  preferences: PreferencesOut
  billing: BillingOut
}

export interface SubjectPatch {
  exam_date?: string | null // ISO date
  target_grade?: string | null
  current_grade?: string | null
  exam_board?: string | null
}

export interface ProfilePatch {
  name?: string | null
}

// ── Notifications ─────────────────────────────────────────────────────────────

export interface NotificationOut {
  id: string
  type: string
  payload: Record<string, unknown>
  read_at: string | null // ISO datetime
  created_at: string     // ISO datetime
}

export interface NotificationListOut {
  items: NotificationOut[]
  unread_count: number
}

export interface MarkReadIn {
  ids: string[]
}
