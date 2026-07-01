"use client";
import { useState } from "react";
import { accountApi } from "@/lib/api/account";
import { GradePicker } from "@/components/onboarding/fields/grade-picker";
import { ExamDatePicker } from "@/components/onboarding/fields/exam-date-picker";
import type { SubjectOut } from "@/lib/types";

export function EditSubjectModal({
  subject,
  onClose,
  onSaved,
}: {
  subject: SubjectOut;
  onClose: () => void;
  onSaved: () => void;
}) {
  const [examDate, setExamDate] = useState<string | null>(subject.exam_date ?? null);
  const [targetGrade, setTargetGrade] = useState(subject.target_grade);

  const save = async () => {
    await accountApi.patchSubject(subject.id, {
      exam_date: examDate || null,
      target_grade: targetGrade,
    });
    onSaved();
  };

  return (
    <div className="fixed inset-0 z-50 grid place-items-center bg-black/40">
      <div className="w-full max-w-md rounded-lg bg-white p-5">
        <h3 className="mb-4 text-lg font-semibold">
          Edit {subject.subject.replace(/_/g, " ")}
        </h3>
        <label className="mb-2 block text-sm">Exam date</label>
        <ExamDatePicker
          initial={subject.exam_date ?? ""}
          onChange={(date) => setExamDate(date)}
        />
        <label className="mb-2 mt-4 block text-sm">Target grade</label>
        <GradePicker
          initial={subject.target_grade}
          onChange={(g) => setTargetGrade(g)}
        />
        <div className="mt-5 flex justify-end gap-2">
          <button onClick={onClose} className="px-3 py-2 text-sm">
            Cancel
          </button>
          <button
            onClick={save}
            className="rounded-md bg-[var(--blue)] px-3 py-2 text-sm text-white"
          >
            Save
          </button>
        </div>
      </div>
    </div>
  );
}
