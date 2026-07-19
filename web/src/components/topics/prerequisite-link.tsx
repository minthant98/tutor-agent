import type { TopicPrerequisite } from "./types";

interface PrerequisiteLinkProps {
  prerequisite: TopicPrerequisite;
}

export function PrerequisiteLink({ prerequisite }: PrerequisiteLinkProps) {
  // If alex_note is set (low prereq mastery variant), render that instead.
  const content = prerequisite.alex_note
    ? prerequisite.alex_note
    : `${prerequisite.label} fluency affects this topic`;

  return (
    <a
      href={`/topics/${prerequisite.id}`}
      className="text-[12px] text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-colors duration-fast underline-offset-2 hover:underline"
      onClick={(e) => e.stopPropagation()}
    >
      {content} →
    </a>
  );
}
