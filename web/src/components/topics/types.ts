export interface TopicPrerequisite {
  id: string;
  label: string;
  affects_this: boolean;
  alex_note?: string | null;
}

export interface TopicV3 {
  id: string;
  label: string;
  mastery: number;           // 0..100
  last_practised: string;    // relative string or "Never"
  status: "Mastered" | "Practising" | "Needs review" | "Not started";
  prerequisite: TopicPrerequisite | null;
}

// ── Topic detail types ────────────────────────────────────────────────────────

export interface TopicDetailInfo {
  id: string;
  label: string;
  mastery: number;          // 0..100
  syllabus_ref: string;     // e.g. "Edexcel · Topic 14"
  target_grade: string;
}

export interface CommonMistake {
  text: string;
  evidence_submission_ids: string[];
}

export interface RecentAttempt {
  id: string;
  created_at: string;       // ISO 8601
  marks: number;
  max_marks: number;
  question_preview: string;
}

export interface RelatedTopic {
  id: string;
  label: string;
  relation: string;         // e.g. "prerequisite"
}

export interface TopicDetailV3 {
  topic: TopicDetailInfo;
  common_mistakes: CommonMistake[];
  recent_attempts: RecentAttempt[];
  recommended_practice_href: string;
  related_topics: RelatedTopic[];
}
