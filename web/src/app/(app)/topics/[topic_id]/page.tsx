"use client";

/**
 * Topic detail page — v3 branch.
 *
 * Route: /topics/[topic_id]
 *
 * Guarded by `topics_v3` feature flag. When flag is off, renders legacy
 * fallback. When flag is on, fetches five-section payload from the API
 * and renders <TopicDetail />.
 *
 * Also reads `practice_v3` flag and passes it as context if needed in future.
 */

import { useCallback, useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { useFeatureFlag } from "@/lib/feature-flags";
import { useCurrentSubject } from "@/hooks/use-current-subject";
import { topicsApi } from "@/lib/api/topics";
import { TopicDetail } from "@/components/topics/topic-detail";
import type { TopicDetailV3 } from "@/components/topics/types";

// ── Skeleton ──────────────────────────────────────────────────────────────────

function TopicDetailSkeleton() {
  return (
    <div className="max-w-[720px] mx-auto pt-12 px-6 space-y-8 animate-pulse">
      <div className="space-y-3">
        <div className="h-8 w-2/3 rounded bg-[var(--surface-2)]" />
        <div className="h-12 w-24 rounded bg-[var(--surface-2)]" />
        <div className="h-4 w-1/3 rounded bg-[var(--surface-2)]" />
      </div>
      <div className="space-y-3">
        <div className="h-5 w-40 rounded bg-[var(--surface-2)]" />
        <div className="h-20 rounded bg-[var(--surface-2)]" />
      </div>
      <div className="space-y-3">
        <div className="h-5 w-32 rounded bg-[var(--surface-2)]" />
        <div className="h-16 rounded bg-[var(--surface-2)]" />
        <div className="h-16 rounded bg-[var(--surface-2)]" />
      </div>
    </div>
  );
}

// ── Legacy fallback ───────────────────────────────────────────────────────────

function LegacyTopicDetailPage() {
  return (
    <div className="max-w-[720px] mx-auto pt-12 px-6">
      <p className="text-[var(--text-secondary)]">
        Topic detail is available in v3. Enable the <code>topics_v3</code> flag.
      </p>
      <Link
        href="/topics"
        className="mt-4 inline-block text-[14px] underline text-[var(--text-primary)]"
      >
        Back to Topics
      </Link>
    </div>
  );
}

// ── Inner view ────────────────────────────────────────────────────────────────

function TopicDetailInner({ topicId, subject }: { topicId: string; subject: string }) {
  const [data, setData] = useState<TopicDetailV3 | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  // Read practice_v3 flag — available for downstream use (e.g. CTA deep-link)
  const _practiceV3 = useFeatureFlag("practice_v3", false);

  const fetchDetail = useCallback(() => {
    let cancelled = false;
    setIsLoading(true);
    setError(null);
    topicsApi
      .getTopicDetail(topicId, subject)
      .then((payload) => {
        if (!cancelled) {
          setData(payload);
          setIsLoading(false);
        }
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setError(err instanceof Error ? err : new Error("Failed to load topic detail"));
          setIsLoading(false);
        }
      });
    return () => {
      cancelled = true;
    };
  }, [topicId, subject]);

  useEffect(() => {
    return fetchDetail();
  }, [fetchDetail]);

  if (isLoading || (data === null && error === null)) return <TopicDetailSkeleton />;

  if (error) {
    return (
      <div className="max-w-[720px] mx-auto pt-12 px-6">
        <div className="rounded-card border border-[var(--border-subtle)] bg-[var(--surface-1)] p-6 space-y-3">
          <p className="text-[var(--text-primary)]">
            Could not load topic details. Try again in a moment.
          </p>
          <button
            type="button"
            onClick={fetchDetail}
            className="text-[14px] text-[var(--accent)] hover:underline"
          >
            Retry
          </button>
        </div>
        <Link
          href="/topics"
          className="mt-4 inline-block text-[14px] underline text-[var(--text-secondary)]"
        >
          Back to Topics
        </Link>
      </div>
    );
  }

  return <TopicDetail data={data!} />;
}

// ── Page ──────────────────────────────────────────────────────────────────────

export default function TopicDetailPage() {
  const params = useParams();
  const topicId = typeof params.topic_id === "string" ? params.topic_id : "";
  const topicsV3 = useFeatureFlag("topics_v3", false);
  const { subject } = useCurrentSubject();

  if (!topicsV3) return <LegacyTopicDetailPage />;

  return <TopicDetailInner topicId={topicId} subject={subject} />;
}
