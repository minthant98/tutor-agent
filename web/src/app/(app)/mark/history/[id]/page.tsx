"use client";
import { useEffect, useState, use } from "react";
import Link from "next/link";
import { markerApi } from "@/lib/api/marker";
import type { SubmissionOut } from "@/lib/types";
import { ResultsView } from "@/components/marker/results-view";

export default function HistoryDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const [submission, setSubmission] = useState<SubmissionOut | null>(null);
  const [error, setError] = useState(false);

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
