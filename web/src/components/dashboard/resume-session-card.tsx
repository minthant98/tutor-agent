import Link from "next/link";
import type { ResumeSessionOut } from "@/lib/types";

export function ResumeSessionCard({ data }: { data: ResumeSessionOut }) {
  return (
    <section className="rounded-lg border border-[var(--blue)] bg-blue-50 p-5">
      <h2 className="text-lg font-semibold">Resume today&apos;s session</h2>
      <p className="mt-1 text-sm text-[var(--text-secondary)]">
        Completed: {data.completed_segments} / {data.total_segments} segments
      </p>
      <Link
        href={`/session/${data.session_id}`}
        className="mt-3 inline-block rounded-lg bg-[var(--blue)] px-4 py-2 text-white"
      >
        Continue
      </Link>
    </section>
  );
}
