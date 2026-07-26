"use client";

import { useEffect, useState, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { markerApi } from "@/lib/api/marker";
import type { SubmissionOut } from "@/lib/types";
import { HistoryList } from "@/components/marker/history-list";
import { HistoryFilters } from "@/components/marker/history-filters";
import { useFeatureFlag } from "@/lib/feature-flags";

const PAGE_SIZE = 20;

function HistoryPageInner() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const markerEnabled = useFeatureFlag("marker_v2", true);

  const status = searchParams.get("status") ?? undefined;
  const difficulty = searchParams.get("difficulty") ?? undefined;
  const from = searchParams.get("from") ?? undefined;
  const to = searchParams.get("to") ?? undefined;

  const [items, setItems] = useState<SubmissionOut[]>([]);
  const [cursor, setCursor] = useState<string | undefined>(undefined);
  const [hasMore, setHasMore] = useState(false);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);

  useEffect(() => {
    if (!markerEnabled) {
      router.replace("/dashboard");
    }
  }, [markerEnabled, router]);

  // Reset and reload when filters change
  useEffect(() => {
    setLoading(true);
    setCursor(undefined);
    markerApi
      .listHistory({
        status: status !== "all" ? status : undefined,
        difficulty: difficulty !== "any" ? difficulty : undefined,
        from,
        to,
      })
      .then((rows) => {
        setItems(rows);
        setHasMore(rows.length === PAGE_SIZE);
        setCursor(rows.length > 0 ? rows[rows.length - 1].created_at : undefined);
      })
      .catch(() => setItems([]))
      .finally(() => setLoading(false));
  }, [status, difficulty, from, to]);

  const handleShowMore = () => {
    if (!cursor) return;
    setLoadingMore(true);
    markerApi
      .listHistory({
        status: status !== "all" ? status : undefined,
        difficulty: difficulty !== "any" ? difficulty : undefined,
        from,
        to,
        cursor,
      })
      .then((rows) => {
        setItems((prev) => [...prev, ...rows]);
        setHasMore(rows.length === PAGE_SIZE);
        setCursor(rows.length > 0 ? rows[rows.length - 1].created_at : undefined);
      })
      .catch(() => {})
      .finally(() => setLoadingMore(false));
  };

  return (
    <div className="mx-auto max-w-2xl space-y-4 px-4 py-6">
      <h1 className="font-sans text-[20px] font-semibold text-[var(--text-primary)]">
        Marked work history
      </h1>

      <HistoryFilters />

      {loading ? (
        <div className="flex flex-col gap-2">
          {[1, 2, 3].map((i) => (
            <div
              key={i}
              className="h-16 animate-pulse rounded-card bg-[var(--surface-1)]"
            />
          ))}
        </div>
      ) : (
        <HistoryList
          items={items}
          hasMore={hasMore}
          onShowMore={handleShowMore}
          loadingMore={loadingMore}
        />
      )}
    </div>
  );
}

export default function HistoryPage() {
  return (
    <Suspense
      fallback={
        <div className="mx-auto max-w-2xl space-y-4 px-4 py-6">
          <div className="h-8 w-48 animate-pulse rounded bg-[var(--surface-1)]" />
        </div>
      }
    >
      <HistoryPageInner />
    </Suspense>
  );
}
