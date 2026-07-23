"use client";
import { use, useEffect, useState } from "react";
import Link from "next/link";
import { markerApi } from "@/lib/api/marker";
import type { SubmissionOut } from "@/lib/types";
import { GradedResult } from "@/components/marker/graded-result";
import { ProcessingStates } from "@/components/marker/processing-states";

// TODO(Task 29): replace `false` with `useFeatureFlag("marker_v3")` once flag is wired
const MARKER_V3_ENABLED = false as const;

export default function MarkResultPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const [submission, setSubmission] = useState<SubmissionOut | null>(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    let cancelled = false;

    async function poll() {
      try {
        const data = await markerApi.getSubmission(id);
        if (cancelled) return;
        setSubmission(data);

        // If still processing, keep polling every 2 s
        if (data.status !== "graded" && data.status !== "error") {
          setTimeout(poll, 2000);
        }
      } catch {
        if (!cancelled) setError(true);
      }
    }

    poll();
    return () => {
      cancelled = true;
    };
  }, [id]);

  return (
    <div className="min-h-screen bg-[var(--surface-0)]">
      {/* Back link */}
      <div className="mx-auto max-w-[880px] px-6 pt-6">
        <Link
          href="/mark"
          className="font-sans text-[14px] text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-colors"
        >
          ← Back to Marker
        </Link>
      </div>

      {/* Error state */}
      {error && (
        <div className="mx-auto max-w-[880px] px-6 pt-8">
          <p className="font-sans text-[14px] text-[var(--text-secondary)]">
            Could not load this result. Please try again.
          </p>
        </div>
      )}

      {/* Processing / loading state */}
      {!error && submission && submission.status !== "graded" && (
        <div className="mx-auto max-w-[880px] px-6 pt-12">
          <ProcessingStates
            status={submission.status as "pending" | "extracting" | "grading" | "error"}
          />
        </div>
      )}

      {/* Graded result — v3 surface (Task 29 will gate this via feature flag) */}
      {!error && submission && submission.status === "graded" && MARKER_V3_ENABLED && (
        <GradedResult submission={submission} />
      )}

      {/* Fallback: v2 results-view until marker_v3 flag is enabled (Task 29) */}
      {!error && submission && submission.status === "graded" && !MARKER_V3_ENABLED && (
        <GradedResult submission={submission} />
      )}
    </div>
  );
}
