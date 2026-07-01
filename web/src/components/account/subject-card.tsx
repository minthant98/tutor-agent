"use client";
import { useState } from "react";
import { EditSubjectModal } from "./edit-subject-modal";
import type { SubjectOut } from "@/lib/types";

const SPEC_CODE: Record<string, string> = { edexcel: "9MA0", cambridge: "9709" };

export function SubjectCard({ subject, onUpdated }: { subject: SubjectOut; onUpdated: () => void }) {
  const [open, setOpen] = useState(false);
  return (
    <article className="rounded-lg border border-[var(--border)] bg-white p-4">
      <h3 className="font-semibold">{subject.subject.replace(/_/g, " ")}</h3>
      <p className="text-sm text-[var(--text-secondary)]">
        {subject.exam_board[0].toUpperCase() + subject.exam_board.slice(1)} · {SPEC_CODE[subject.exam_board] ?? subject.exam_board}
      </p>
      <dl className="mt-3 grid grid-cols-2 gap-y-1 text-sm">
        <dt className="text-[var(--text-secondary)]">Target grade</dt><dd>{subject.target_grade}</dd>
        <dt className="text-[var(--text-secondary)]">Exam</dt><dd>{subject.exam_date ?? "Not set"}</dd>
        <dt className="text-[var(--text-secondary)]">Readiness</dt><dd>{Math.round(subject.readiness_pct)}%</dd>
      </dl>
      <button onClick={() => setOpen(true)} className="mt-3 text-sm text-[var(--blue)]">Edit</button>
      {open && (
        <EditSubjectModal
          subject={subject}
          onClose={() => setOpen(false)}
          onSaved={() => { setOpen(false); onUpdated(); }}
        />
      )}
    </article>
  );
}
