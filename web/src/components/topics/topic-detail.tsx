"use client";

/**
 * TopicDetail — renders exactly five sections in fixed order:
 *   1. Overview
 *   2. Common mistakes (hidden when empty — fresh student)
 *   3. Recent attempts
 *   4. Recommended practice
 *   5. Related topics (hidden when empty — no prereq graph in MVP)
 *
 * Each section is a <section role="region" aria-label="<name>"> for test targeting.
 * Typography: Geist Sans/Mono per brand spec.
 */

import Link from "next/link";
import { Badge } from "@/components/ui/badge";
import type { TopicDetailV3 } from "./types";

interface TopicDetailProps {
  data: TopicDetailV3;
}

// ── Overview section ─────────────────────────────────────────────────────────

function OverviewSection({ topic }: { topic: TopicDetailV3["topic"] }) {
  const masteryBand =
    topic.mastery >= 70
      ? "success"
      : topic.mastery >= 40
      ? "default"
      : topic.mastery > 0
      ? "warning"
      : "secondary";

  return (
    <section role="region" aria-label="Overview" className="space-y-3">
      {/* Topic name — Geist Sans 32 */}
      <h1 className="text-[32px] font-sans font-semibold text-[var(--text-primary)] leading-tight">
        {topic.label}
      </h1>

      {/* Mastery — Geist Mono 40 */}
      <div className="flex items-baseline gap-3">
        <span className="text-[40px] font-mono font-semibold text-[var(--text-primary)]">
          {topic.mastery}%
        </span>
        <Badge variant={masteryBand}>readiness</Badge>
      </div>

      {/* Syllabus ref — Geist Sans 12 text-secondary */}
      <p className="text-[12px] font-sans text-[var(--text-secondary)]">
        {topic.syllabus_ref}
      </p>

      {/* Target grade context */}
      <p className="text-[13px] font-sans text-[var(--text-secondary)]">
        Target grade: <span className="font-mono text-[var(--text-primary)]">{topic.target_grade}</span>
      </p>
    </section>
  );
}

// ── Common mistakes section ───────────────────────────────────────────────────
// Hidden entirely when list is empty (fresh student)

function CommonMistakesSection({ mistakes }: { mistakes: TopicDetailV3["common_mistakes"] }) {
  if (mistakes.length === 0) return null;

  return (
    <section role="region" aria-label="Common mistakes" className="space-y-3">
      <h2 className="text-[20px] font-sans font-semibold text-[var(--text-primary)]">
        Common mistakes
      </h2>
      <ul className="space-y-3">
        {mistakes.map((mistake, i) => (
          <li
            key={i}
            className="rounded-card border border-[var(--border-subtle)] bg-[var(--surface-1)] p-4 space-y-2"
          >
            <p className="text-[14px] font-sans text-[var(--text-primary)]">{mistake.text}</p>
            {mistake.evidence_submission_ids.length > 0 && (
              <span className="inline-block text-[11px] font-mono text-[var(--text-secondary)] bg-[var(--surface-2)] px-2 py-0.5 rounded">
                Evidence: {mistake.evidence_submission_ids.length}{" "}
                {mistake.evidence_submission_ids.length === 1 ? "attempt" : "attempts"}
              </span>
            )}
          </li>
        ))}
      </ul>
    </section>
  );
}

// ── Recent attempts section ───────────────────────────────────────────────────

function RecentAttemptsSection({ attempts }: { attempts: TopicDetailV3["recent_attempts"] }) {
  return (
    <section role="region" aria-label="Recent attempts" className="space-y-3">
      <h2 className="text-[20px] font-sans font-semibold text-[var(--text-primary)]">
        Recent attempts
      </h2>
      {attempts.length === 0 ? (
        <p className="text-[13px] text-[var(--text-secondary)]">No attempts yet.</p>
      ) : (
        <ul className="space-y-2">
          {attempts.map((attempt) => {
            const date = new Date(attempt.created_at).toLocaleDateString("en-GB", {
              day: "numeric",
              month: "short",
              year: "numeric",
            });
            return (
              <li key={attempt.id}>
                <Link
                  href={`/mark/${attempt.id}`}
                  className="flex items-start justify-between gap-4 rounded-card border border-[var(--border-subtle)] bg-[var(--surface-1)] p-3 hover:border-[var(--border-default)] transition-colors duration-fast"
                >
                  <span className="text-[13px] font-sans text-[var(--text-secondary)] shrink-0">
                    {date}
                  </span>
                  <span className="text-[13px] font-mono text-[var(--text-primary)] shrink-0">
                    {attempt.marks}/{attempt.max_marks}
                  </span>
                  <span className="text-[13px] font-sans text-[var(--text-secondary)] truncate">
                    {attempt.question_preview}
                  </span>
                </Link>
              </li>
            );
          })}
        </ul>
      )}
    </section>
  );
}

// ── Recommended practice section ─────────────────────────────────────────────

function RecommendedPracticeSection({ href }: { href: string }) {
  return (
    <section role="region" aria-label="Recommended practice" className="space-y-3">
      <h2 className="text-[20px] font-sans font-semibold text-[var(--text-primary)]">
        Recommended practice
      </h2>
      <Link
        href={href}
        className="inline-flex items-center gap-2 rounded-card bg-[var(--primary)] text-white px-5 py-2.5 text-[14px] font-sans font-medium hover:opacity-90 transition-opacity duration-fast"
      >
        Practice this topic
      </Link>
    </section>
  );
}

// ── Related topics section ───────────────────────────────────────────────────
// Hidden entirely when empty (no prereq graph in MVP)

function RelatedTopicsSection({ topics }: { topics: TopicDetailV3["related_topics"] }) {
  if (topics.length === 0) return null;

  return (
    <section role="region" aria-label="Related topics" className="space-y-3">
      <h2 className="text-[20px] font-sans font-semibold text-[var(--text-primary)]">
        Related topics
      </h2>
      <div className="flex flex-wrap gap-2">
        {topics.map((t) => (
          <Link
            key={t.id}
            href={`/topics/${t.id}`}
            className="rounded-card border border-[var(--border-subtle)] bg-[var(--surface-1)] px-3 py-1.5 text-[13px] font-sans text-[var(--text-secondary)] hover:border-[var(--border-default)] hover:text-[var(--text-primary)] transition-colors duration-fast"
          >
            <span className="text-[11px] font-mono text-[var(--text-secondary)] mr-1">
              {t.relation}
            </span>
            {t.label}
          </Link>
        ))}
      </div>
    </section>
  );
}

// ── TopicDetail — main export ─────────────────────────────────────────────────

export function TopicDetail({ data }: TopicDetailProps) {
  return (
    <div className="max-w-[720px] mx-auto pt-12 px-6 pb-16 space-y-10">
      {/* Section 1: Overview */}
      <OverviewSection topic={data.topic} />

      {/* Section 2: Common mistakes — hidden when empty */}
      <CommonMistakesSection mistakes={data.common_mistakes} />

      {/* Section 3: Recent attempts */}
      <RecentAttemptsSection attempts={data.recent_attempts} />

      {/* Section 4: Recommended practice */}
      <RecommendedPracticeSection href={data.recommended_practice_href} />

      {/* Section 5: Related topics — hidden when empty */}
      <RelatedTopicsSection topics={data.related_topics} />
    </div>
  );
}
