"use client";
import { useEffect, useState } from "react";
import { markerApi } from "@/lib/api/marker";
import type { SubmissionOut } from "@/lib/types";
import { HistoryList } from "@/components/marker/history-list";

const PAGE_SIZE = 10;

export default function HistoryPage() {
  const [items, setItems] = useState<SubmissionOut[]>([]);
  const [page, setPage] = useState(0);
  const [hasMore, setHasMore] = useState(true);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    markerApi.listSubmissions(PAGE_SIZE, page * PAGE_SIZE)
      .then((rows) => {
        setItems(rows);
        setHasMore(rows.length === PAGE_SIZE);
      })
      .finally(() => setLoading(false));
  }, [page]);

  return (
    <div className="mx-auto max-w-2xl space-y-4 px-4 py-6">
      <h1 className="text-xl font-semibold">Marked work history</h1>
      {loading && <p>Loading…</p>}
      {!loading && <HistoryList items={items} />}
      <div className="flex gap-2">
        <button
          disabled={page === 0}
          onClick={() => setPage(page - 1)}
          className="rounded-md border border-[var(--border)] px-3 py-1.5 text-sm disabled:opacity-50"
        >
          Previous
        </button>
        <button
          disabled={!hasMore}
          onClick={() => setPage(page + 1)}
          className="rounded-md border border-[var(--border)] px-3 py-1.5 text-sm disabled:opacity-50"
        >
          Next
        </button>
      </div>
    </div>
  );
}
