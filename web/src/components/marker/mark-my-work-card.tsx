"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { useStudent } from "@/lib/auth";
import { markerApi } from "@/lib/api/marker";

export function MarkMyWorkCard({ subject }: { subject: string }) {
  const student = useStudent();
  const [monthlyCount, setMonthlyCount] = useState<number | null>(null);

  useEffect(() => {
    if (student?.subscription_tier === "pro") return;
    markerApi.listSubmissions(100, 0)
      .then((rows) => {
        const now = new Date();
        const thisMonth = rows.filter((r) => {
          const d = new Date(r.created_at);
          return d.getFullYear() === now.getFullYear()
              && d.getMonth() === now.getMonth();
        });
        setMonthlyCount(thisMonth.length);
      })
      .catch(() => setMonthlyCount(null));
  }, [student?.subscription_tier]);

  const isPro = student?.subscription_tier === "pro";
  const counterText =
    !isPro && monthlyCount !== null ? `Free: ${monthlyCount}/5 this month` : null;

  return (
    <section className="rounded-lg border border-[var(--border)] bg-white p-5">
      <h2 className="text-lg font-semibold">Mark my work</h2>
      <p className="mt-1 text-sm text-[var(--text-secondary)]">
        Get your written work graded like an examiner would.
      </p>
      <div className="mt-3 flex items-center justify-between">
        <Link
          href="/mark"
          className="rounded-lg bg-[var(--blue)] px-4 py-2 text-white"
        >
          Mark my work
        </Link>
        {counterText && (
          <span className="text-xs text-[var(--text-secondary)]">
            {counterText}
          </span>
        )}
      </div>
    </section>
  );
}
