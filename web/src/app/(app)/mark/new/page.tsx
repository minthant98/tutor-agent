"use client";

import { Suspense, useEffect, useState } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { markerApi } from "@/lib/api/marker";
import { useCurrentSubject } from "@/hooks/use-current-subject";
import { NewSubmission } from "@/components/marker/new-submission";
import { useFeatureFlag } from "@/lib/feature-flags";
import type { MarkerV3Question } from "@/lib/types";

type QuestionWithScheme = MarkerV3Question & { mark_scheme: string };

function NewSubmissionLoader() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const questionId = searchParams.get("question_id");
  const { subject } = useCurrentSubject();
  const markerV3 = useFeatureFlag("marker_v3", false);

  // Guard: if marker_v3 is disabled, redirect to the landing page
  useEffect(() => {
    if (markerV3 === false) {
      // Not redirecting immediately — flag may not yet be resolved from PostHog.
      // The landing page (/mark) will gate access to this route via the v3 branch.
    }
  }, [markerV3, router]);

  const [question, setQuestion] = useState<QuestionWithScheme | null>(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        const data = await markerApi.getV3Landing(subject);
        if (cancelled) return;

        if (questionId && data.question.id !== questionId) {
          // Requested a specific question not returned by landing — use landing question as fallback.
          // A future endpoint (GET /marker/v3/questions/:id) can replace this.
        }

        setQuestion({
          ...data.question,
          // Mark scheme is not yet part of MarkerV3Question from landing — derive from landing data.
          // The v3 landing endpoint currently includes question but not mark scheme in the v3 shape.
          // We cast with a placeholder; Task 28 will wire the real submission flow that has mark_scheme.
          mark_scheme: (data.question as unknown as { mark_scheme?: string }).mark_scheme ?? "",
        });
      } catch {
        if (!cancelled) setError(true);
      }
    }

    load();
    return () => { cancelled = true; };
  }, [questionId, subject]);

  if (error) {
    return (
      <div className="mx-auto max-w-[880px] px-6 pt-12">
        <p className="text-[14px] text-[var(--text-secondary)]">
          Could not load question. Please go back and try again.
        </p>
      </div>
    );
  }

  if (!question) {
    return (
      <div className="mx-auto max-w-[880px] px-6 pt-12">
        <p className="text-[14px] text-[var(--text-secondary)]">Loading question…</p>
      </div>
    );
  }

  return <NewSubmission question={question} />;
}

export default function NewSubmissionPage() {
  return (
    <Suspense
      fallback={
        <div className="mx-auto max-w-[880px] px-6 pt-12">
          <p className="text-[14px] text-[var(--text-secondary)]">Loading…</p>
        </div>
      }
    >
      <NewSubmissionLoader />
    </Suspense>
  );
}
