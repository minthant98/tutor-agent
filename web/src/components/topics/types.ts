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
