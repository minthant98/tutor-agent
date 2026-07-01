"use client";
import { useEffect, useState } from "react";
import { apiFetch } from "@/lib/api";

export default function InspectPage({ params }: { params: { id: string } }) {
  const [data, setData] = useState<Record<string, unknown> | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    apiFetch<Record<string, unknown>>(`/admin/students/${params.id}/inspect`)
      .then(setData)
      .catch((err: unknown) => {
        setError(err instanceof Error ? err.message : "Failed to load student data");
      });
  }, [params.id]);

  if (error) {
    return (
      <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-red-700">
        Error: {error}
      </div>
    );
  }

  if (!data) {
    return <p className="text-[var(--text-secondary)]">Loading...</p>;
  }

  const profile = data.profile as { name?: string } | undefined;

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-semibold">
        Inspect: {profile?.name ?? params.id}
      </h1>
      {Object.entries(data).map(([k, v]) => (
        <details key={k} className="rounded-lg border border-[var(--border)] bg-white p-3">
          <summary className="cursor-pointer font-semibold">{k}</summary>
          <pre className="mt-2 overflow-x-auto text-xs">
            {JSON.stringify(v, null, 2)}
          </pre>
        </details>
      ))}
    </div>
  );
}
