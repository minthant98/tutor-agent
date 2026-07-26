"use client";
import { useEffect, useState, use } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { markerApi } from "@/lib/api/marker";
import type { SubmissionOut } from "@/lib/types";
import { ResultsView } from "@/components/marker/results-view";
import { useFeatureFlag } from "@/lib/feature-flags";

export default function HistoryDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const router = useRouter();
  const markerEnabled = useFeatureFlag("marker_v2", true);
  const markerV3 = useFeatureFlag("marker_v3", false);
  void markerV3; // flag read ensures PostHog initialises marker_v3 for this page
  const { id } = use(params);
  const [submission, setSubmission] = useState<SubmissionOut | null>(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    if (!markerEnabled) {
      router.replace("/dashboard");
    }
  }, [markerEnabled, router]);

  useEffect(() => {
    markerApi.getSubmission(id).then(setSubmission).catch(() => setError(true));
  }, [id]);

  return (
    <div className="mx-auto max-w-2xl space-y-4 px-4 py-6">
      <Link href="/mark/history" className="text-sm text-[var(--blue)]">
        ← Back to history
      </Link>
      {error && <p className="text-red-600">Couldn&apos;t load this submission.</p>}
      {!error && !submission && <p>Loading…</p>}
      {submission && <ResultsView submission={submission} readonly />}
    </div>
  );
}
