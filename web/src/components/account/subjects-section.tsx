"use client";

import { useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import type { SubjectOut } from "@/lib/types";

// Mastery band derived from readiness_pct
function masteryBand(pct: number): string {
  if (pct >= 80) return "Strong";
  if (pct >= 50) return "Developing";
  return "Needs work";
}

interface SubjectRowProps {
  subject: SubjectOut;
  onRemove: (s: SubjectOut) => void;
}

function SubjectRow({ subject, onRemove }: SubjectRowProps) {
  const label = subject.subject.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
  return (
    <div className="flex items-center justify-between border-b border-[var(--border-subtle)] py-3 last:border-0">
      <div>
        <p className="text-[14px] font-medium text-[var(--text-primary)]">
          {label}
        </p>
        <p className="text-[12px] text-[var(--text-secondary)]">
          {masteryBand(subject.readiness_pct)} · {Math.round(subject.readiness_pct)}% readiness
        </p>
      </div>
      <button
        type="button"
        onClick={() => onRemove(subject)}
        className="text-[13px] text-[var(--text-secondary)] hover:text-[var(--semantic-danger-text)] transition-colors duration-fast"
      >
        Remove
      </button>
    </div>
  );
}

interface ConfirmRemoveDialogProps {
  subject: SubjectOut | null;
  onCancel: () => void;
  onConfirm: () => void;
}

function ConfirmRemoveDialog({
  subject,
  onCancel,
  onConfirm,
}: ConfirmRemoveDialogProps) {
  if (!subject) return null;

  const label = subject.subject.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
  // session_count and submission_count come from the subject prop
  // The brief uses these fields in the test; we surface them directly.
  const sessionCount = (subject as SubjectOut & { session_count?: number }).session_count ?? 0;
  const submissionCount = (subject as SubjectOut & { submission_count?: number }).submission_count ?? 0;

  return (
    <Dialog open={!!subject} onOpenChange={(open) => !open && onCancel()}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Remove {label}?</DialogTitle>
        </DialogHeader>
        <p className="text-[14px] text-[var(--text-secondary)] mt-2">
          Removing {label} will archive {sessionCount} sessions and{" "}
          {submissionCount} graded submissions. Mastery data will be kept for 30
          days in case you re-enable.
        </p>
        <DialogFooter className="mt-4">
          <Button variant="secondary" size="sm" onClick={onCancel}>
            Cancel
          </Button>
          <Button variant="destructive" size="sm" onClick={onConfirm}>
            Remove
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

interface Props {
  subjects: (SubjectOut & { session_count?: number; submission_count?: number })[];
  onRefresh?: () => void;
}

export function SubjectsSection({ subjects, onRefresh }: Props) {
  const [pendingRemove, setPendingRemove] = useState<(SubjectOut & { session_count?: number; submission_count?: number }) | null>(null);
  const [addOpen, setAddOpen] = useState(false);

  function handleConfirmRemove() {
    // TODO: wire backend — call DELETE /account/subjects/:id
    console.warn("remove subject stub — wire backend", pendingRemove?.id);
    setPendingRemove(null);
    onRefresh?.();
  }

  return (
    <div className="space-y-4">
      <h2 className="text-lg font-semibold text-[var(--text-primary)]">
        Subjects
      </h2>

      <div>
        {subjects.length === 0 ? (
          <p className="text-[14px] text-[var(--text-secondary)]">
            No subjects added yet.
          </p>
        ) : (
          subjects.map((s) => (
            <SubjectRow
              key={s.id}
              subject={s}
              onRemove={setPendingRemove}
            />
          ))
        )}
      </div>

      <Button
        variant="secondary"
        size="sm"
        onClick={() => setAddOpen(true)}
      >
        + Add subject
      </Button>

      {/* Add subject stub dialog */}
      <Dialog open={addOpen} onOpenChange={setAddOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Add a subject</DialogTitle>
          </DialogHeader>
          <p className="text-[14px] text-[var(--text-secondary)] mt-2">
            Subject selection coming soon — choose your exam board and subject to
            get started.
          </p>
          <DialogFooter className="mt-4">
            <Button variant="secondary" size="sm" onClick={() => setAddOpen(false)}>
              Close
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <ConfirmRemoveDialog
        subject={pendingRemove}
        onCancel={() => setPendingRemove(null)}
        onConfirm={handleConfirmRemove}
      />
    </div>
  );
}
